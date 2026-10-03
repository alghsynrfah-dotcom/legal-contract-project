"""Shahd's API: agent chat + unified tools API (an APIRouter, included by app/main.py)."""
import inspect
from fastapi import APIRouter
from pydantic import BaseModel, Field
from shared.errors import AppError
from .agent import run_agent, get_history, clear_history
from .tools import TOOL_REGISTRY

router = APIRouter(prefix="/api", tags=["agent & tools"])

class ChatIn(BaseModel):
    contract_id: str
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = Field(None, max_length=64)  # omit on first message; reuse the returned id afterwards

class ToolIn(BaseModel):
    contract_id: str | None = None
    clause_type: str | None = None

@router.post("/agent/chat")
def chat(body: ChatIn): return run_agent(body.contract_id, body.message, body.session_id)

@router.get("/agent/chat/{session_id}")
def chat_history(session_id: str, contract_id: str):
    return {"session_id": session_id, "messages": get_history(session_id, contract_id)}

@router.delete("/agent/chat/{session_id}")
def chat_clear(session_id: str): return clear_history(session_id)

@router.get("/tools")
def list_tools(): return {"tools": list(TOOL_REGISTRY)}

@router.post("/tools/{tool_name}")  # unified API for all tools
def call_tool(tool_name: str, body: ToolIn):
    name = tool_name.strip()
    fn = TOOL_REGISTRY.get(name)
    if not fn: raise AppError("TOOL_NOT_FOUND", f"Unknown tool '{name}'", 404)
    params = inspect.signature(fn).parameters
    args = {k: v for k, v in body.model_dump().items() if v is not None and k in params}
    try:
        return fn(**args)
    except AppError: raise
    except TypeError as e: raise AppError("INVALID_ARGS", str(e), 422)
    except Exception as e: raise AppError("TOOL_CALL_FAILED", str(e), 500)
