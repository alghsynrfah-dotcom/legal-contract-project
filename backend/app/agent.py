import json, uuid
from datetime import date
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from sqlalchemy import select, delete
from shared.db import SessionLocal
from shared.errors import AppError
from shared.models import ChatMessage
from .llm import llm
from .tools import build_agent_tools, _require_contract

HISTORY_TURNS = 6      # last N question/answer pairs given to the model
MAX_MSG_CHARS = 800    # per history message

REACT_PROMPT = PromptTemplate.from_template("""You are a legal-contract assistant for lawyers, working on ONE contract.
Today's date is {today}.
Contract record from the database (authoritative, may be incomplete): {contract_context}

You have access to the following tools:
{tools}

Use EXACTLY this format:

Question: the user's question
Thought: what do I need to answer this?
Action: the tool to use, one of [{tool_names}]
Action Input: the input for the tool (plain text, no quotes)
Observation: the tool result
... (Thought/Action/Action Input/Observation can repeat)
Thought: I now know the final answer
Final Answer: the answer

Rules:
- Basic info (parties, dates, value, duration) -> contract_information.
- A specific clause (payment, termination, confidentiality, ...) -> clause_extraction.
- Any other content question -> search_contract, and answer ONLY from the returned chunks.
- Questions about remaining time or expiry: use days_until_end from the contract record (negative = already expired). If it is unknown, call contract_information first.
- Use the conversation so far to resolve references such as "that clause" or "and the second party?".
- If tools return an error or nothing relevant, say so. Never invent contract content.
- Write the Final Answer in the same language as the Question, and mention the source (contract name / page) when it comes from the contract.
- If the question needs no tool (greeting, general legal explanation), go directly to Final Answer.

Conversation so far:
{history}

Question: {input}
Thought:{agent_scratchpad}""")

def _contract_context(c, today: date) -> str:
    days = (c.end_date - today).days if c.end_date else None
    return (f"name: {c.name}; status: {c.status}; start_date: {c.start_date or 'unknown'}; "
            f"end_date: {c.end_date or 'unknown'}; days_until_end: {days if days is not None else 'unknown'}")

def _format_history(rows: list[tuple[str, str]]) -> str:
    if not rows: return "(none)"
    cut = lambda t: t[:MAX_MSG_CHARS] + ("…" if len(t) > MAX_MSG_CHARS else "")
    return "\n".join(f"{'User' if r == 'user' else 'Assistant'}: {cut(c)}" for r, c in rows)

def _load_history(session_id: str, contract_id: str) -> list[tuple[str, str]]:
    with SessionLocal() as db:
        rows = db.execute(select(ChatMessage.role, ChatMessage.content)
                          .where(ChatMessage.session_id == session_id, ChatMessage.contract_id == contract_id)
                          .order_by(ChatMessage.id.desc()).limit(HISTORY_TURNS * 2)).all()
    return [(r, c) for r, c in reversed(rows)]

def _save_turn(session_id: str, contract_id: str, question: str, answer: str) -> None:
    with SessionLocal() as db:
        db.add_all([ChatMessage(session_id=session_id, contract_id=contract_id, role="user", content=question),
                    ChatMessage(session_id=session_id, contract_id=contract_id, role="assistant", content=answer)])
        db.commit()

def get_history(session_id: str, contract_id: str) -> list[dict]:
    _require_contract(contract_id)
    with SessionLocal() as db:
        rows = db.execute(select(ChatMessage).where(ChatMessage.session_id == session_id,
                          ChatMessage.contract_id == contract_id).order_by(ChatMessage.id).limit(200)).scalars().all()
    return [{"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} for m in rows]

def clear_history(session_id: str) -> dict:
    with SessionLocal() as db:
        n = db.execute(delete(ChatMessage).where(ChatMessage.session_id == session_id)).rowcount
        db.commit()
    return {"session_id": session_id, "deleted": n}

def run_agent(contract_id: str, message: str, session_id: str | None = None) -> dict:
    contract = _require_contract(contract_id)
    session_id = session_id or uuid.uuid4().hex
    today = date.today()
    tools = build_agent_tools(contract_id)
    executor = AgentExecutor(agent=create_react_agent(llm, tools, REACT_PROMPT), tools=tools,
                             max_iterations=3, handle_parsing_errors=True, return_intermediate_steps=True,verbose=True)
    try:
        out = executor.invoke({"input": message, "today": today.isoformat(),
                               "contract_context": _contract_context(contract, today),
                               "history": _format_history(_load_history(session_id, contract_id))})
    except Exception as e:
        raise AppError("TOOL_CALL_FAILED", f"Agent failed: {e}", 502)
    tools_used, sources = [], []
    for action, obs in out.get("intermediate_steps", []):
        tools_used.append(action.tool)
        try:
            d = json.loads(obs)
            for i in (d if isinstance(d, list) else [d]):
                if isinstance(i, dict):
                    if "source" in i: sources.append(i["source"])
                    sources += i.get("sources", [])
        except Exception: pass
    _save_turn(session_id, contract_id, message, out["output"])
    return {"session_id": session_id, "answer": out["output"], "tools_used": tools_used, "sources": sources}
