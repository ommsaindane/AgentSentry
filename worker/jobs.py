import os
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from typing import Dict, Any, List
from api.models import Base, Trace as TraceModel, DecisionEnum, AuditLog
from agentsentry.verifier.dynamic_verifier import classify_intent_llm

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///../agentsentry.db")

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)

# Heuristic dynamic classifier removed. LLM (OpenRouter) is the sole dynamic checker.

def dynamic_check_trace(trace_id: str) -> None:
    """
    Load trace, run dynamic check, and update decision/reasons if elevated.
    """
    db = SessionLocal()
    try:
        row = db.get(TraceModel, trace_id)
        if not row:
            return
        # LLM-only dynamic check via OpenRouter
        verdict = classify_intent_llm(row.content or {})
        new_decision = verdict["decision"]
        new_reasons = verdict["reasons"]
        # Only elevate decisions; do not downgrade
        elevated_to_block = False
        if DecisionEnum(new_decision).value != row.decision.value:
            priority = {"block": 3, "warn": 2, "allow": 1}
            if priority[new_decision] > priority[row.decision.value]:
                row.decision = DecisionEnum(new_decision)
                if new_decision == "block":
                    elevated_to_block = True
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
        # Audit dynamic elevation to block
        if elevated_to_block:
            try:
                db.add(
                    AuditLog(
                        actor="worker",
                        action="trace_block_dynamic",
                        target_type="trace",
                        target_id=row.id,
                        details={"reasons": new_reasons},
                    )
                )
                db.commit()
            except Exception:
                db.rollback()
    finally:
        db.close()