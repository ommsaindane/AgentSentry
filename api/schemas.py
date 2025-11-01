from pydantic import BaseModel, field_validator
from typing import Optional

class RuleBase(BaseModel):
    name: str
    pattern: str
    rule_type: str = "regex"  # regex | nlp
    severity: str  # info | warning | critical
    decision: str  # allow | warn | block
    enabled: bool = True
    description: Optional[str] = None

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = {"info", "warning", "critical"}
        if v not in allowed:
            raise ValueError(f"severity must be one of {allowed}")
        return v

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, v: str) -> str:
        allowed = {"allow", "warn", "block"}
        if v not in allowed:
            raise ValueError(f"decision must be one of {allowed}")
        return v

    @field_validator("rule_type")
    @classmethod
    def validate_rule_type(cls, v: str) -> str:
        allowed = {"regex", "nlp"}
        if v not in allowed:
            raise ValueError(f"type must be one of {allowed}")
        return v

class RuleCreate(RuleBase):
    pass

class RuleUpdate(BaseModel):
    name: Optional[str] = None
    pattern: Optional[str] = None
    rule_type: Optional[str] = None
    severity: Optional[str] = None
    decision: Optional[str] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None

class RuleOut(RuleBase):
    id: int