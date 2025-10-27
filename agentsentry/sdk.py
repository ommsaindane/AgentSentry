import os
import json
from typing import Any, Dict, Optional
import requests

class AgentSentryClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        session_id: Optional[str] = None,
        timeout: float = 10.0,
    ):
        # Base URL of the AgentSentry API, default local dev
        self.base_url = base_url or os.getenv("AGENTSENTRY_API_URL", "http://localhost:8000")
        self.api_key = api_key or os.getenv("AGENTSENTRY_API_KEY")
        self.session_id = session_id
        self.timeout = timeout
        self._session = requests.Session()
        if self.api_key:
            self._session.headers.update({"Authorization": f"Bearer {self.api_key}"})
        self._session.headers.update({"Content-Type": "application/json"})

    def set_session(self, session_id: str):
        self.session_id = session_id

    def create_session(self) -> str:
        url = f"{self.base_url}/sessions"
        resp = self._session.post(url, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        sid = data["id"]
        self.session_id = sid
        return sid

    def send_trace(self, role: str, content: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
        sid = session_id or self.session_id
        if not sid:
            raise ValueError("session_id is required; call create_session() or pass session_id")
        payload = {"session_id": sid, "role": role, "content": content}
        url = f"{self.base_url}/traces"
        resp = self._session.post(url, data=json.dumps(payload), timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()