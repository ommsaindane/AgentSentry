import os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from typing import Dict, Any, List
from api.models import Base, Trace as TraceModel, DecisionEnum

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///../agentsentry.db")

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)

def _classify_intent(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder dynamic check: heuristic classification.
    Replace with LLM call later (e.g., OpenAI) to score risk levels.
    """
    text = ""
    if isinstance(content, dict):
        text = (content.get("text") or str(content)).lower()
    score = 0
    reasons: List[Dict[str, Any]] = []
    if "rm -rf" in text or ("tool" in content and content.get("args", {}).get("cmd", "").startswith("rm -rf")):
        score = 100
        reasons.append({"rule": "dynamic_intent_destructive", "severity": "critical", "decision": "block", "description": "Dynamic: destructive intent detected."})
    elif "api_key" in text or "token" in text:
        score = 50
        reasons.append({"rule": "dynamic_intent_secret", "severity": "warning", "decision": "warn", "description": "Dynamic: secret-like intent."})
    decision = "allow"
    for r in reasons:
        if r["decision"] == "block":
            decision = "block"
            break
        if r["decision"] == "warn":
            decision = "warn"
    return {"decision": decision, "reasons": reasons, "score": score}

def dynamic_check_trace(trace_id: str) -> None:
    """
    Load trace, run dynamic check, and update decision/reasons if elevated.
    """
    db = SessionLocal()
    try:
        row = db.get(TraceModel, trace_id)
        if not row:
            return
        verdict = _classify_intent(row.content or {})
        new_decision = verdict["decision"]
        new_reasons = verdict["reasons"]
        # Only elevate decisions; do not downgrade
        if DecisionEnum(new_decision).value != row.decision.value:
            priority = {"block": 3, "warn": 2, "allow": 1}
            if priority[new_decision] > priority[row.decision.value]:
                row.decision = DecisionEnum(new_decision)
        if new_reasons:
            # Merge reasons
            existing = row.reasons or []
            # Simple de-dup based on rule name
            seen = {r.get("rule") for r in existing}
            for r in new_reasons:
                if r.get("rule") not in seen:
                    existing.append(r)
            row.reasons = existing
        db.add(row); db.commit()
    finally:
        db.close()