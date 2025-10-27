from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from sqlalchemy.orm import Session as OrmSession
from api.db import get_db
from api.models import Trace as TraceModel, Session as SessionModel, DecisionEnum
import uuid
from agentsentry.verifier.static_rules import StaticVerifier

router = APIRouter(prefix="/traces", tags=["traces"])
_verifier = StaticVerifier()

@router.post("", response_model=Dict)
def ingest_trace(payload: Dict[str, Any], db: OrmSession = Depends(get_db)):
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=422, detail="session_id is required")
    if not db.get(SessionModel, session_id):
        raise HTTPException(status_code=404, detail="session not found")

    role = payload.get("role", "assistant")
    content = payload.get("content", {})

    # Static verification
    verdict = _verifier.evaluate(content)
    decision = verdict["decision"]
    reasons = verdict["reasons"]

    tid = uuid.uuid4().hex[:16]
    row = TraceModel(
        id=tid,
        session_id=session_id,
        role=role,
        content=content,
        decision=DecisionEnum(decision),
        reasons=reasons,
    )
    db.add(row); db.commit(); db.refresh(row)

    # Enqueue dynamic check
    try:
        from api.queue import get_queue
        q = get_queue()
        q.enqueue("worker.jobs.dynamic_check_trace", row.id)
    except Exception:
        # Do not fail the request if queue is not available
        pass

    return {"id": row.id, "decision": row.decision.value, "reasons": row.reasons or [], "payload": content}

@router.get("/{trace_id}", response_model=Dict)
def get_trace(trace_id: str, db: OrmSession = Depends(get_db)):
    row = db.get(TraceModel, trace_id)
    if not row:
        raise HTTPException(status_code=404, detail="trace not found")
    return {
        "id": row.id,
        "session_id": row.session_id,
        "role": row.role,
        "content": row.content,
        "decision": row.decision.value,
        "reasons": row.reasons or [],
        "created_at": str(row.created_at),
    }
