from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Optional
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy import select
from api.db import get_db
from api.models import Session as SessionModel
import uuid
from datetime import datetime

router = APIRouter(prefix="/sessions", tags=["sessions"])

def _now_iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None

@router.get("", response_model=List[Dict])
def list_sessions(
    db: OrmSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    cursor: Optional[str] = Query(None, description="Return items created before this ISO timestamp"),
):
    stmt = select(SessionModel).order_by(SessionModel.created_at.desc())
    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor)
            stmt = stmt.where(SessionModel.created_at < cursor_dt)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid cursor timestamp format; use ISO 8601")
    rows = db.execute(stmt.limit(limit)).scalars().all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "created_at": _now_iso(s.created_at),
            "updated_at": _now_iso(s.updated_at),
        }
        for s in rows
    ]

@router.post("", response_model=Dict)
def create_session(
    db: OrmSession = Depends(get_db),
    title: Optional[str] = Query(None, description="Optional session title"),
):
    sid = uuid.uuid4().hex[:16]
    obj = SessionModel(id=sid, title=title)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return {
        "id": obj.id,
        "title": obj.title,
        "created_at": _now_iso(obj.created_at),
        "updated_at": _now_iso(obj.updated_at),
    }

@router.get("/{session_id}", response_model=Dict)
def get_session(session_id: str, db: OrmSession = Depends(get_db)):
    obj = db.get(SessionModel, session_id)
    if not obj:
        raise HTTPException(status_code=404, detail="session not found")
    return {
        "id": obj.id,
        "title": obj.title,
        "created_at": _now_iso(obj.created_at),
        "updated_at": _now_iso(obj.updated_at),
    }

@router.delete("/{session_id}", response_model=Dict)
def delete_session(session_id: str, db: OrmSession = Depends(get_db)):
    obj = db.get(SessionModel, session_id)
    if not obj:
        raise HTTPException(status_code=404, detail="session not found")
    db.delete(obj)
    db.commit()
    return {"id": session_id, "deleted": True}
