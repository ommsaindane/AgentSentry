from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import os
import re
import yaml

_SPACY_AVAILABLE = False
try:
    import spacy  # type: ignore
    from spacy.matcher import PhraseMatcher  # type: ignore
    _SPACY_AVAILABLE = True
except Exception:
    # spaCy is optional at install time; NLP rules will be ignored if unavailable
    _SPACY_AVAILABLE = False

@dataclass
class Rule:
    name: str
    pattern: str
    severity: str  # info | warning | critical
    decision: str  # allow | warn | block
    enabled: bool = True
    description: Optional[str] = None
    rule_type: str = "regex"  # "regex" | "nlp"

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
        # Pre-compile regex patterns
        self._compiled_regex: List[Tuple[Rule, re.Pattern]] = []
        # Prepare spaCy matcher if available and rules include NLP
        self._nlp = None
        self._nlp_matcher = None
        self._nlp_rules: List[Rule] = []
        self._prepare()

    def _prepare(self) -> None:
        # Compile regex rules
        self._compiled_regex = []
        self._nlp_rules = []
        for r in self.rules:
            if not r.enabled:
                continue
            if (r.rule_type or "regex") == "regex":
                try:
                    self._compiled_regex.append((r, re.compile(r.pattern)))
                except re.error:
                    # Skip invalid regex at runtime
                    continue
            elif r.rule_type == "nlp":
                self._nlp_rules.append(r)

        # Initialize spaCy matcher if needed
        if self._nlp_rules and _SPACY_AVAILABLE:
            model = os.getenv("SPACY_MODEL", "en_core_web_sm")
            try:
                self._nlp = spacy.load(model, disable=["ner"])  # NER not needed for phrase matching
                self._nlp_matcher = PhraseMatcher(self._nlp.vocab, attr="LOWER")
                # Add phrase patterns
                # Each rule's pattern is treated as a plain phrase (can be multi-word)
                for r in self._nlp_rules:
                    # Allow multiple phrases separated by | for convenience
                    phrases = [p.strip() for p in r.pattern.split("|") if p.strip()]
                    docs = [self._nlp.make_doc(p) for p in phrases]
                    # Use unique label per rule
                    label = f"RULE_{r.name}"
                    if docs:
                        try:
                            self._nlp_matcher.add(label, docs)
                        except Exception:
                            # Continue even if one rule fails to register
                            continue
            except Exception:
                # spaCy model failed to load; disable NLP
                self._nlp = None
                self._nlp_matcher = None

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

        # Regex evaluation
        for r, cregex in self._compiled_regex:
            try:
                if cregex.search(text):
                    matches.append({
                        "rule": r.name,
                        "severity": r.severity,
                        "decision": r.decision,
                        "description": r.description,
                        "type": "regex",
                    })
                    if DECISION_PRIORITY[r.decision] > DECISION_PRIORITY[agg_decision]:
                        agg_decision = r.decision
            except Exception:
                continue

        # NLP phrase evaluation
        if self._nlp and self._nlp_matcher and self._nlp_rules:
            try:
                doc = self._nlp(text)
                spans = self._nlp_matcher(doc)
                # spans are tuples (match_id, start, end); map back to rules by label
                seen_rules: set[str] = set()
                for match_id, start, end in spans:
                    label = self._nlp.vocab.strings[match_id]
                    # label format: RULE_<name>
                    rname = label.removeprefix("RULE_")
                    if rname in seen_rules:
                        continue
                    seen_rules.add(rname)
                    # find rule by name
                    for r in self._nlp_rules:
                        if r.name == rname:
                            matches.append({
                                "rule": r.name,
                                "severity": r.severity,
                                "decision": r.decision,
                                "description": r.description,
                                "type": "nlp",
                            })
                            if DECISION_PRIORITY[r.decision] > DECISION_PRIORITY[agg_decision]:
                                agg_decision = r.decision
                            break
            except Exception:
                # Do not fail if spaCy processing errors
                pass

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
                rule_type=it.get("type", "regex"),
            ))
        return cls(rules=rules)
