from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy import select
from api.db import get_db
from api.models import Rule as RuleModel
from api.schemas import RuleCreate, RuleUpdate, RuleOut
import re
import yaml

router = APIRouter(prefix="/rules", tags=["rules"])

def _validate_regex(pattern: str):
    try:
        re.compile(pattern)
    except re.error as e:
        raise HTTPException(status_code=422, detail=f"Invalid regex: {e}")

@router.get("", response_model=List[RuleOut])
def list_rules(db: OrmSession = Depends(get_db)):
    rows = db.execute(select(RuleModel).order_by(RuleModel.id.asc())).scalars().all()
    return [
        RuleOut(
            id=r.id,
            name=r.name,
            pattern=r.pattern,
            severity=r.severity,
            decision=r.decision,
            enabled=bool(r.enabled),
            description=r.description,
        )
        for r in rows
    ]

@router.post("", response_model=RuleOut)
def create_rule(payload: RuleCreate, db: OrmSession = Depends(get_db)):
    _validate_regex(payload.pattern)
    # name uniqueness
    exists = db.execute(select(RuleModel).where(RuleModel.name == payload.name)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="Rule name already exists")
    row = RuleModel(
        name=payload.name,
        pattern=payload.pattern,
        severity=payload.severity,
        decision=payload.decision,
        enabled=1 if payload.enabled else 0,
        description=payload.description,
    )
    db.add(row); db.commit(); db.refresh(row)
    return RuleOut(
        id=row.id,
        name=row.name,
        pattern=row.pattern,
        severity=row.severity,
        decision=row.decision,
        enabled=bool(row.enabled),
        description=row.description,
    )

@router.put("/{rule_id}", response_model=RuleOut)
def update_rule(rule_id: int, payload: RuleUpdate, db: OrmSession = Depends(get_db)):
    row = db.get(RuleModel, rule_id)
    if not row:
        raise HTTPException(status_code=404, detail="rule not found")
    if payload.pattern is not None:
        _validate_regex(payload.pattern)
        row.pattern = payload.pattern
    if payload.name is not None and payload.name != row.name:
        exists = db.execute(select(RuleModel).where(RuleModel.name == payload.name)).scalar_one_or_none()
        if exists:
            raise HTTPException(status_code=409, detail="Rule name already exists")
        row.name = payload.name
    if payload.severity is not None:
        row.severity = payload.severity
    if payload.decision is not None:
        row.decision = payload.decision
    if payload.enabled is not None:
        row.enabled = 1 if payload.enabled else 0
    if payload.description is not None:
        row.description = payload.description
    db.add(row); db.commit(); db.refresh(row)
    return RuleOut(
        id=row.id,
        name=row.name,
        pattern=row.pattern,
        severity=row.severity,
        decision=row.decision,
        enabled=bool(row.enabled),
        description=row.description,
    )

@router.patch("/{rule_id}/toggle", response_model=RuleOut)
def toggle_rule(rule_id: int, enabled: bool = Body(..., embed=True), db: OrmSession = Depends(get_db)):
    row = db.get(RuleModel, rule_id)
    if not row:
        raise HTTPException(status_code=404, detail="rule not found")
    row.enabled = 1 if enabled else 0
    db.add(row); db.commit(); db.refresh(row)
    return RuleOut(
        id=row.id,
        name=row.name,
        pattern=row.pattern,
        severity=row.severity,
        decision=row.decision,
        enabled=bool(row.enabled),
        description=row.description,
    )

@router.delete("/{rule_id}")
def delete_rule(rule_id: int, db: OrmSession = Depends(get_db)):
    row = db.get(RuleModel, rule_id)
    if not row:
        raise HTTPException(status_code=404, detail="rule not found")
    db.delete(row); db.commit()
    return {"ok": True}

@router.post("/import")
def import_rules(yaml_text: str = Body(..., media_type="text/plain"), db: OrmSession = Depends(get_db)):
    try:
        data = yaml.safe_load(yaml_text) or {}
    except yaml.YAMLError as e:
        raise HTTPException(status_code=422, detail=f"Invalid YAML: {e}")
    rules = data.get("rules") or []
    created = 0
    for it in rules:
        name = it.get("name")
        pattern = it.get("pattern")
        severity = it.get("severity", "warning")
        decision = it.get("decision", "warn")
        enabled = bool(it.get("enabled", True))
        description = it.get("description")
        if not name or not pattern:
            continue
        _validate_regex(pattern)
        exists = db.execute(select(RuleModel).where(RuleModel.name == name)).scalar_one_or_none()
        if exists:
            continue
        row = RuleModel(
            name=name,
            pattern=pattern,
            severity=severity,
            decision=decision,
            enabled=1 if enabled else 0,
            description=description,
        )
        db.add(row); created += 1
    db.commit()
    return {"created": created}

@router.get("/export")
def export_rules(db: OrmSession = Depends(get_db)):
    rows = db.execute(select(RuleModel).order_by(RuleModel.id.asc())).scalars().all()
    payload = {
        "rules": [
            {
                "name": r.name,
                "pattern": r.pattern,
                "severity": r.severity,
                "decision": r.decision,
                "enabled": bool(r.enabled),
                "description": r.description,
            }
            for r in rows
        ]
    }
    text = yaml.safe_dump(payload, sort_keys=False)
    return {"yaml": text}