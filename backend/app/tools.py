import json, uuid
from datetime import date, datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field
from shared.db import SessionLocal
from shared.models import Contract
from shared.errors import AppError, contract_not_found
from .llm import extract_structured
from shared.rag_store import retrieve_chunks
from shared.config import EXPIRING_SOON_DAYS

SUPPORTED_CLAUSES = ["payment", "termination", "confidentiality", "liability", "governing law", "renewal"]

def _require_contract(cid: str) -> Contract:
    try: uuid.UUID(str(cid))
    except ValueError: raise contract_not_found(cid)
    with SessionLocal() as db:
        c = db.get(Contract, cid)
    if not c: raise contract_not_found(cid)
    return c

# ---------- 1. Contract Information Tool ----------
class ContractInfo(BaseModel):
    parties: list[str] = Field(default_factory=list)
    start_date: Optional[str] = Field(None, description="ISO YYYY-MM-DD or null")
    end_date: Optional[str] = Field(None, description="ISO YYYY-MM-DD or null")
    value: Optional[str] = None
    duration: Optional[str] = None

def _parse_date(s):
    try: return datetime.strptime(s, "%Y-%m-%d").date() if s else None
    except ValueError: return None

def contract_information(contract_id: str) -> dict:
    _require_contract(contract_id)
    queries = ["parties to the agreement", "effective date start date", "end date expiration term duration", "contract value price total amount"]
    chunks = {c["text"]: c for q in queries for c in retrieve_chunks(contract_id, q, 3)}.values()
    if not chunks: raise AppError("NO_CONTENT", "No indexed content for this contract", 422)
    ctx = "\n---\n".join(c["text"] for c in chunks)
    info = extract_structured(ContractInfo, "Extract the basic contract information. Use null when missing.", ctx)
    with SessionLocal() as db:  # persist dates so the scheduled job can use them
        c = db.get(Contract, contract_id)
        c.start_date, c.end_date = _parse_date(info.start_date), _parse_date(info.end_date)
        c.status = compute_status(c.end_date) or c.status  # status is correct right after ingestion
        db.commit()
    return {"contract_id": contract_id, "info": info.model_dump(), "sources": [c["source"] for c in chunks]}

# ---------- 2. Clause Extraction Tool ----------
class ClauseResult(BaseModel):
    found: bool
    clause_text: Optional[str] = Field(None, description="Verbatim clause text")
    summary: Optional[str] = None

def clause_extraction(contract_id: str, clause_type: str) -> dict:
    _require_contract(contract_id)
    ct = clause_type.strip().lower()
    if ct not in SUPPORTED_CLAUSES:
        raise AppError("UNSUPPORTED_CLAUSE", f"clause_type must be one of {SUPPORTED_CLAUSES}", 422)
    chunks = retrieve_chunks(contract_id, f"{ct} clause", 4)
    if not chunks: raise AppError("NO_CONTENT", "No indexed content for this contract", 422)
    res = extract_structured(ClauseResult, f"Extract the '{ct}' clause. Set found=false if absent. Do not invent text.",
                             "\n---\n".join(c["text"] for c in chunks))
    return {"contract_id": contract_id, "clause_type": ct, **res.model_dump(), "sources": [c["source"] for c in chunks]}

# ---------- 3. Expiration Check Automation ----------
def compute_status(end: Optional[date], today: Optional[date] = None) -> Optional[str]:
    if not end: return None
    today = today or date.today()
    if end < today: return "Expired"
    return "Expiring Soon" if end <= today + timedelta(days=EXPIRING_SOON_DAYS) else "Active"

def check_expirations() -> dict:
    updated = []
    with SessionLocal() as db:
        for c in db.query(Contract).filter(Contract.end_date.isnot(None)).all():
            new = compute_status(c.end_date)
            if new != c.status:
                updated.append({"contract_id": c.contract_id, "from": c.status, "to": new}); c.status = new
        db.commit()
    return {"checked_at": datetime.utcnow().isoformat(), "updated": updated}

def post_ingestion(contract_id: str) -> dict:
    """For Rafah: call once after add_chunks() succeeded. Fills start/end dates and status immediately.
    Never raises: a failure here must not mark the ingestion itself as failed (the daily job retries)."""
    try: return contract_information(contract_id)
    except AppError as e: return {"error": e.code, "message": e.message}

def extract_missing_dates() -> dict:
    """Run Contract Information on ingested contracts that still have no end_date,
    so the expiration job has data to work with (no manual step needed after upload)."""
    with SessionLocal() as db:
        ids = [c for (c,) in db.query(Contract.contract_id)
               .filter(Contract.ingestion_status == "ready", Contract.end_date.is_(None)).all()]
    done, failed = [], []
    for cid in ids:
        try: contract_information(cid); done.append(cid)
        except Exception as e: failed.append({"contract_id": cid, "error": str(e)})
    return {"processed": done, "failed": failed}

def daily_job() -> dict:
    return {"extraction": extract_missing_dates(), "expiration": check_expirations()}

# ---------- Unified registry (used by API and Agent) ----------
TOOL_REGISTRY = {"contract_information": contract_information, "clause_extraction": clause_extraction,
                 "check_expirations": check_expirations,
                 "extract_missing_dates": extract_missing_dates}

# ---------- Tools for the ReAct Agent ----------
# ReAct is text-based: every tool takes ONE string. contract_id is bound per chat request (closure),
# so the LLM never has to pass it.
def _clean(s) -> str:
    return str(s).strip().strip("\"'` \n")

def _safe(fn) -> str:
    try: return json.dumps(fn(), ensure_ascii=False, default=str)
    except AppError as e: return json.dumps({"error": e.code, "message": e.message})
    except Exception as e: return json.dumps({"error": "TOOL_CALL_FAILED", "message": str(e)})

def build_agent_tools(contract_id: str):
    from langchain_core.tools import Tool
    return [
        Tool(name="contract_information",
             func=lambda _: _safe(lambda: contract_information(contract_id)),
             description="Get parties, start date, end date, value and duration of the contract. Action Input: any text (ignored)."),
        Tool(name="clause_extraction",
             func=lambda ct: _safe(lambda: clause_extraction(contract_id, _clean(ct))),
             description=f"Extract one specific clause. Action Input: the clause type, one of {SUPPORTED_CLAUSES}."),
        Tool(name="search_contract",
             func=lambda q: _safe(lambda: retrieve_chunks(contract_id, _clean(q), 5)),
             description="RAG search for any other question about the contract content; returns relevant chunks with sources. Action Input: the search question."),
    ]
