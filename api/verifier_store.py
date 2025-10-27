from typing import Optional
from sqlalchemy.orm import Session as OrmSession
from agentsentry.verifier.static_rules import StaticVerifier, DEFAULT_RULES, Rule
from .rule_loader import db_rules_to_static

class VerifierStore:
    def __init__(self) -> None:
        self._verifier: Optional[StaticVerifier] = None

    def get(self) -> StaticVerifier:
        if self._verifier is None:
            self._verifier = StaticVerifier()
        return self._verifier

    def load_from_db(self, db: OrmSession) -> StaticVerifier:
        rules = db_rules_to_static(db)
        if not rules:
            # Fallback to defaults
            self._verifier = StaticVerifier(rules=list(DEFAULT_RULES))
        else:
            self._verifier = StaticVerifier(rules=rules)
        return self._verifier

store = VerifierStore()
