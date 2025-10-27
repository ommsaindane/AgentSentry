from typing import Any, Dict, Optional
from .sdk import AgentSentryClient

class Tracer:
    def __init__(self, client: AgentSentryClient):
        self.client = client

    def user(self, text: str, extra: Optional[Dict[str, Any]] = None):
        content = {"text": text}
        if extra:
            content.update(extra)
        return self.client.send_trace(role="user", content=content)

    def assistant(self, text: str, extra: Optional[Dict[str, Any]] = None):
        content = {"text": text}
        if extra:
            content.update(extra)
        return self.client.send_trace(role="assistant", content=content)

    def tool(self, name: str, args: Dict[str, Any], result: Any = None, error: str = None):
        content: Dict[str, Any] = {"tool": name, "args": args}
        if result is not None:
            content["result"] = result
        if error is not None:
            content["error"] = error
        return self.client.send_trace(role="tool", content=content)