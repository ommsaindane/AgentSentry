from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import re
import yaml

@dataclass
class Rule:
    name: str
    pattern: str
    severity: str  # info | warning | critical
    decision: str  # allow | warn | block
    enabled: bool = True
    description: Optional[str] = None

DEFAULT_RULES: List[Rule] = [
    Rule(
        name="no_shell_rm_rf",
        pattern=r"\brm\s+-rf\b|\brmdir\s+/s\s+/q\b",
        severity="critical",
        decision="block",
        description="Blocks destructive shell deletion commands."
    ),
    Rule(
        name="no_secrets",
        pattern=r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9-_]{16,}['\"]?",
        severity="warning",
        decision="warn",
        description="Flags likely hardcoded secrets."
    ),
    Rule(
        name="no_system_write",
        pattern=r"\b(/etc/|C:\\Windows\\|C:\\Program Files\\)\b",
        severity="warning",
        decision="warn",
        description="Flags writes to protected system paths."
    ),
]

DECISION_PRIORITY = {"block": 3, "warn": 2, "allow": 1}

class StaticVerifier:
    def __init__(self, rules: Optional[List[Rule]] = None):
        self.rules = rules or DEFAULT_RULES

    @staticmethod
    def _collect_text(content: Dict[str, Any]) -> str:
        parts: List[str] = []
        if isinstance(content.get("text"), str):
            parts.append(content["text"])
        tool = content.get("tool")
        if isinstance(tool, str):
            parts.append(f"tool:{tool}")
        args = content.get("args")
        if isinstance(args, dict):
            parts.append(str(args))
        error = content.get("error")
        if isinstance(error, str):
            parts.append(error)
        return "\n".join(parts) if parts else str(content)

    def evaluate(self, content: Dict[str, Any]) -> Dict[str, Any]:
        text = self._collect_text(content)
        matches: List[Dict[str, Any]] = []
        agg_decision = "allow"
        for rule in self.rules:
            if not rule.enabled:
                continue
            try:
                if re.search(rule.pattern, text):
                    matches.append({
                        "rule": rule.name,
                        "severity": rule.severity,
                        "decision": rule.decision,
                        "description": rule.description,
                    })
                    if DECISION_PRIORITY[rule.decision] > DECISION_PRIORITY[agg_decision]:
                        agg_decision = rule.decision
            except re.error:
                continue
        return {"decision": agg_decision, "reasons": matches}

    @classmethod
    def from_yaml(cls, yaml_text: str) -> "StaticVerifier":
        data = yaml.safe_load(yaml_text) or {}
        rules: List[Rule] = []
        for it in data.get("rules", []):
            rules.append(Rule(
                name=it["name"],
                pattern=it["pattern"],
                severity=it.get("severity", "warning"),
                decision=it.get("decision", "warn"),
                enabled=bool(it.get("enabled", True)),
                description=it.get("description"),
            ))
        return cls(rules=rules)
