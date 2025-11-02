# AgentSentry – LLM Safety Framework

AgentSentry lets you observe and control agent/tool actions from LLM apps. It records traces (user, assistant, tool calls), evaluates them against safety rules, and returns allow/warn/block decisions with reasons. It also supports async dynamic checks via a worker.

## Stack

- API: FastAPI + SQLAlchemy (Postgres or SQLite for dev)
- Queue: Redis + RQ worker
- UI: Next.js dashboard for sessions, traces, and rules CRUD
- SDK: Minimal Python client, tracer, and enforcer

## Quickstart (Dev)

1) Start infra (DB, Redis, API, Worker) with Docker Compose:

```bash
cd infra
docker compose up --build
```

2) Run the Web UI (optional, in another terminal):

```bash
cd web
npm install
npm run dev
```

3) Create a session and send traces with the Python examples:

```bash
# in repo root
python examples/send_trace.py
python examples/policy_demo.py
```

4) Try the Ollama demo (optional):

Requirements:
- Ollama running locally (default http://localhost:11434)
- At least one chat-capable model pulled (e.g., `llama3.1`)

Run the demo, which will:
- Create an AgentSentry session
- Send a user message to the LLM via Ollama
- Record the assistant reply and evaluate it through AgentSentry
- Print the final decision (allow/warn/block) and reasons

```bash
python examples/ollama_demo.py
```

Notes:
- The demo auto-detects a model via `GET /api/tags` and falls back to common names if needed.
- It prefers `/api/chat` and falls back to `/api/generate` if your Ollama build lacks chat.

4) Explore:

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/healthz
- UI (Next.js dev): http://localhost:3000

## Rules Management

- CRUD: UI at `/rules` or via REST `/rules` endpoints
- Import/Export YAML: POST `/rules/import`, GET `/rules/export`
- Reload verifier: POST `/rules/reload` (requires `AGENTSENTRY_API_KEY`)

Rules can be either regex or NLP (spaCy phrase) based (see `agentsentry/verifier/static_rules.py`). The API stores rules in the DB and loads them into an in-memory verifier on startup or on reload.

NLP rules use spaCy's PhraseMatcher for case-insensitive matching of plain phrases over the collected text of each trace. Define via YAML or UI:

```yaml
rules:
  - name: sensitive_plain_phrases
    type: nlp
    pattern: "leak password|share ssn|dump database"
    severity: warning
    decision: warn
    enabled: true
```

UI: choose the rule type from a dropdown on the Rules page. Pattern placeholder updates depending on type.

Runtime: If spaCy isn't installed, NLP rules are safely ignored. In Docker, spaCy and `en_core_web_sm` are installed via `requirements.txt`. You can set `SPACY_MODEL` (defaults to `en_core_web_sm`).

Regex rules look like this:

```yaml
rules:
  - name: sensitive_pattern
    type: regex
    pattern: "(?i)(password|ssn|api[_-]?key)"
    severity: critical
    decision: block
    enabled: true
```

## Security (Dev vs Prod)

- Set `AGENTSENTRY_API_KEY` to require a `Bearer` token for rule mutations and reloads.
- Without this env var, dev mode is open for convenience.

## Dynamic Checks (OpenRouter-only)

The worker elevates decisions using an OpenRouter-backed classifier.

- Required:
  - `OPENROUTER_API_KEY=...`
- Optional:
  - `OPENROUTER_MODEL` (defaults to `openai/gpt-4o-mini`)
  - `DYNAMIC_PROMPT_EXTENSION` – extra policy guidance appended to the classifier prompt.

## Database & Migrations

When running with Docker Compose, you may need to run Alembic migrations to create/update tables:

```bash
docker compose -f infra/docker-compose.yml exec api alembic upgrade head
```

## Web UI Notes (Next.js 16)

- App Router dynamic routes receive `params` as a Promise; pages should `await params` before use.
- To avoid stale data when viewing sessions or traces, the pages export `dynamic = "force-dynamic"` to bypass caching.
- Development server: `cd web && npm run dev` at http://localhost:3000.

## Repo Hygiene

This repo ships with a `.gitignore` that excludes local caches and databases. If you need a manual cleanup, you can safely remove:
- Python caches: `**/__pycache__/`, `*.pyc`
- Pytest cache: `.pytest_cache/`
- Local SQLite files used only for dev/tests: `*.db`, `*.sqlite3`, `*.sqlite`
- Node/Next build artifacts in `web/`: `.next/`, `node_modules/`

The Docker Compose workflow stores runtime data in containers; removing local caches doesn’t affect your DB container.

## Python SDK snippet

```python
from agentsentry.sdk import AgentSentryClient
from agentsentry.tracer import Tracer
from agentsentry.enforcer import Enforcer, EnforcementError

c = AgentSentryClient()  # uses AGENTSENTRY_API_URL if set
sid = c.create_session()
t = Tracer(c)
e = Enforcer(t)

# This will be WARN or BLOCK depending on rules
try:
    e.guard_and_call("shell", {"cmd": "rm -rf /"}, call_fn=lambda: "would run")
except EnforcementError:
    print("Blocked by policy")
```

## Tests

Install dev deps and run pytest:

```bash
pip install -r requirements.txt
pytest -q
```
