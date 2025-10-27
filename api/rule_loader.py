from typing import List
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy import select
from agentsentry.verifier.static_rules import Rule
from api.models import Rule as RuleModel

def db_rules_to_static(db: OrmSession) -> List[Rule]:
    rows = (
        db.execute(
            select(RuleModel)
            .where(RuleModel.enabled == 1)
            .order_by(RuleModel.id.asc())
        )
        .scalars()
        .all()
    )
    rules: List[Rule] = []
    for r in rows:
        try:
            rules.append(
                Rule(
                    name=r.name,
                    pattern=r.pattern,
                    severity=r.severity,
                    decision=r.decision,
                    enabled=bool(r.enabled),
                    description=r.description,
                )
            )
        except Exception:
            # Skip malformed rows instead of breaking startup
            continue
    return rules
