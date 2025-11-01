import os
import json
import sys
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

try:
    import spacy  # type: ignore
    _SPACY_OK = True
except Exception:
    _SPACY_OK = False

# Ensure repo root on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def setup_module(module):
    # Use a local sqlite DB for tests
    os.environ.setdefault("DATABASE_URL", "sqlite:///./test_agentsentry.db")
    # Ensure models are created
    from api.db import engine
    from api.models import Base
    Base.metadata.create_all(bind=engine)


def get_client():
    from api.main import app
    return TestClient(app)


def test_session_create_and_list():
    c = get_client()
    # Create session
    r = c.post("/sessions")
    assert r.status_code == 200
    sid = r.json()["id"]
    assert isinstance(sid, str) and len(sid) > 0

    # List sessions
    r = c.get("/sessions")
    assert r.status_code == 200
    items = r.json()
    assert any(it["id"] == sid for it in items)


def test_trace_static_block_and_listing():
    c = get_client()
    # Create session
    r = c.post("/sessions")
    sid = r.json()["id"]

    # Post a clearly destructive tool trace
    payload = {
        "session_id": sid,
        "role": "tool",
        "content": {"tool": "shell", "args": {"cmd": "rm -rf /"}},
    }
    r = c.post("/traces", data=json.dumps(payload), headers={"Content-Type": "application/json"})
    assert r.status_code == 200
    data = r.json()
    assert data["decision"] in {"warn", "block"}

    # List traces by session
    r = c.get(f"/sessions/{sid}/traces")
    assert r.status_code == 200
    items = r.json()
    assert any(it["id"] == data["id"] for it in items)


def test_rule_create_requires_api_key():
    c = get_client()
    import uuid
    unique = uuid.uuid4().hex[:8]
    rule = {
        "name": f"no_test_pattern_{unique}",
        "pattern": "test123",
        "severity": "warning",
        "decision": "warn",
        "enabled": True,
        "description": "unit test rule",
    }

    # Require API key
    os.environ["AGENTSENTRY_API_KEY"] = "secret"
    # Update live settings since app was already imported
    from api.settings import settings as live_settings
    live_settings.api_key = "secret"
    # Without key -> 401/403
    r = c.post("/rules", json=rule)
    assert r.status_code in {401, 403}

    # With key -> 200
    headers = {"Authorization": "Bearer secret"}
    r = c.post("/rules", json=rule, headers=headers)
    assert r.status_code == 200
    out = r.json()
    assert out["name"] == rule["name"]


def test_audit_logs_list():
    c = get_client()
    # Create a session to generate at least some activity
    r = c.post("/sessions")
    assert r.status_code == 200

    # Fetch audit logs (may be empty if no secured actions yet)
    r = c.get("/audit/logs")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.skipif(not _SPACY_OK, reason="spaCy not installed")
def test_nlp_rule_blocks_plain_text_when_enabled():
    c = get_client()
    # Configure API key for rule creation
    os.environ["AGENTSENTRY_API_KEY"] = "secret"
    from api.settings import settings as live_settings
    live_settings.api_key = "secret"

    # Create NLP rule
    import uuid
    unique = uuid.uuid4().hex[:8]
    rule = {
        "name": f"block_sensitive_phrase_{unique}",
        "pattern": "share ssn",
        "rule_type": "nlp",
        "severity": "critical",
        "decision": "block",
        "enabled": True,
        "description": "Block sharing SSN phrase",
    }
    r = c.post("/rules", json=rule, headers={"Authorization": "Bearer secret"})
    assert r.status_code == 200, r.text

    # Reload verifier to pick up DB rules
    r = c.post("/rules/reload", headers={"Authorization": "Bearer secret"})
    assert r.status_code == 200

    # Create session
    r = c.post("/sessions")
    sid = r.json()["id"]

    # Send a trace containing the phrase (case varies to test case-insensitive)
    payload = {
        "session_id": sid,
        "role": "user",
        "content": {"text": "User asks to SHARE SSN with third parties"},
    }
    r = c.post("/traces", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    # Should be blocked by NLP rule
    assert data["decision"] in {"warn", "block"}
    # Ensure reasons include our rule
    assert any((rule["name"] == rsn.get("rule")) for rsn in data.get("reasons", []))
