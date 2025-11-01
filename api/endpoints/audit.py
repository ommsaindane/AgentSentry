from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Optional
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy import select
from datetime import datetime

from api.db import get_db
from api.models import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs", response_model=List[Dict])
def list_audit_logs(
    db: OrmSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    cursor: Optional[str] = Query(None, description="Return items created before this ISO timestamp"),
    action: Optional[str] = Query(None),
    target_type: Optional[str] = Query(None),
):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if target_type:
        stmt = stmt.where(AuditLog.target_type == target_type)
    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor)
            stmt = stmt.where(AuditLog.created_at < cursor_dt)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid cursor timestamp format; use ISO 8601")
    rows = db.execute(stmt.limit(limit)).scalars().all()
    return [
        {
            "id": a.id,
            "actor": a.actor,
            "action": a.action,
            "target_type": a.target_type,
            "target_id": a.target_id,
            "details": a.details or {},
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in rows
    ]
