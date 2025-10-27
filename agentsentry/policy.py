from typing import Dict, Any, List

DECISION_PRIORITY = {"block": 3, "warn": 2, "allow": 1}

class PolicyEngine:
    def aggregate(self, reasons: List[Dict[str, Any]]) -> str:
        """
        Aggregate decisions from static matches into a single action.
        Priority: block > warn > allow
        """
        agg = "allow"
        for r in reasons or []:
            d = r.get("decision", "warn")
            if DECISION_PRIORITY[d] > DECISION_PRIORITY[agg]:
                agg = d
        return agg