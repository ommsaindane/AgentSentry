from typing import Any, Callable, Dict, Optional
from .tracer import Tracer
from .policy import PolicyEngine

class EnforcementError(Exception):
    pass

class Enforcer:
    def __init__(self, tracer: Tracer, policy: Optional[PolicyEngine] = None):
        self.tracer = tracer
        self.policy = policy or PolicyEngine()

    def guard_and_call(
        self,
        tool_name: str,
        args: Dict[str, Any],
        call_fn: Callable[[], Any],
        preview_payload: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        - Emits a pre-call tool trace to get a decision from the API.
        - If block: emits a blocked tool trace and raises EnforcementError.
        - If warn: emits a warned tool trace, proceeds with call, and logs result.
        - If allow: proceeds and logs result.
        """
        # Send a pre-call trace so the API (StaticVerifier) returns decision + reasons
        verdict = self.tracer.tool(tool_name, args, result=None)
        decision = verdict.get("decision", "allow")
        reasons = verdict.get("reasons", [])

        agg = self.policy.aggregate(reasons)
        # Prefer explicit API decision if provided
        if decision and decision != "allow":
            agg = decision

        if agg == "block":
            # Log explicit block trace for observability and raise
            self.tracer.tool(tool_name, args, result=None, error="blocked by policy")
            raise EnforcementError(f"Tool '{tool_name}' blocked by policy: {reasons}")

        # Proceed with call for warn/allow
        try:
            result = call_fn()
            # Log the outcome
            self.tracer.tool(tool_name, args, result=result)
            return result
        except Exception as e:
            # Log error outcome
            self.tracer.tool(tool_name, args, result=None, error=str(e))
            raise