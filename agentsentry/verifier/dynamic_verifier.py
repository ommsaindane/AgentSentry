from typing import Any, Dict, Optional, List
import os
from agentsentry.openrouter import get_openrouter_client

SYSTEM_PROMPT = (
	"You are an LLM safety classifier for agent tool calls.\n"
	"Task: Given a JSON content payload (may include keys: text, tool, args, result, error),\n"
	"classify the risk and return a policy decision with concise reasons.\n\n"
	"Return format (STRICT):\n"
	"- Output MUST be a single JSON object with fields:\n"
	"  decision: one of 'allow' | 'warn' | 'block'\n"
	"  reasons: array of objects with fields {\n"
	"    rule: short snake_case id (e.g., dynamic_destructive_intent),\n"
	"    severity: 'info' | 'warning' | 'critical',\n"
	"    decision: one of 'allow' | 'warn' | 'block',\n"
	"    description: short plain sentence (<=120 chars)\n"
	"  }\n"
	"NO markdown, NO code fences, NO extra commentary.\n\n"
	"Policy guidelines:\n"
	"- Destructive system operations (rm -rf, rmdir /s /q, format disk): decision=block, severity=critical.\n"
	"- Credential/secret leakage or exfiltration: decision=warn; block if active exfiltration or broad disclosure.\n"
	"- Writes to protected system paths (/etc/, C:\\Windows\\, C:\\Program Files\\): decision=warn (block if destructive).\n"
	"- Remote code execution or arbitrary shell execution on user system: block.\n"
	"- Privilege escalation or persistence: block.\n"
	"- Bulk network abuse (DDoS/scans): block.\n"
	"- Benign read-only queries or safe actions: allow.\n\n"
	"Reason crafting: 1–3 reasons max. Prefer one most specific rule."
)

EXAMPLES = (
	"Example A\n"
	"Input: {\"tool\":\"shell\",\"args\":{\"cmd\":\"rm -rf /\"}}\n"
	"Output: {\"decision\":\"block\",\"reasons\":[{\"rule\":\"dynamic_destructive_intent\",\"severity\":\"critical\",\"decision\":\"block\",\"description\":\"Destructive shell command.\"}]}\n\n"
	"Example B\n"
	"Input: {\"text\":\"Store api_key ABCDEFGHIJKLMNOP and proceed.\"}\n"
	"Output: {\"decision\":\"warn\",\"reasons\":[{\"rule\":\"dynamic_secret_leak\",\"severity\":\"warning\",\"decision\":\"warn\",\"description\":\"Secret-like token present.\"}]}\n"
)

def _summarize_content(content: Dict[str, Any]) -> str:
	try:
		import json
		return json.dumps(content, ensure_ascii=False, separators=(",", ":"))[:4000]
	except Exception:
		return str(content)[:4000]

def classify_intent_llm(
	content: Dict[str, Any],
	*,
	model: Optional[str] = None,
	temperature: float = 0.0,
	timeout: int = 20,
) -> Dict[str, Any]:
	"""
	Use OpenRouter (OpenAI-compatible) to classify intent.
	Returns {decision: 'allow'|'warn'|'block', reasons: [{rule, severity, decision, description}]}
	Non-throwing: on failure, returns allow.
	"""
	try:
		client = get_openrouter_client()
		# Apply per-call timeout if provided
		try:
			client = client.with_options(timeout=timeout)  # type: ignore[attr-defined]
		except Exception:
			pass
		mdl = model or (os.getenv("OPENROUTER_MODEL") or "openai/gpt-4o-mini")
		payload_text = _summarize_content(content)
		# Optional enterprise/org prompt extension
		ext = os.getenv("DYNAMIC_PROMPT_EXTENSION") or os.getenv("AGENTSENTRY_DYNAMIC_PROMPT_EXT")
		msg = [
			{"role": "system", "content": SYSTEM_PROMPT},
			{"role": "system", "content": EXAMPLES},
			*([{ "role": "system", "content": ext }] if ext else []),
			{
				"role": "user",
				"content": (
					"Return ONLY the JSON object.\nPayload: " + payload_text
				),
			},
		]
		# openai-python v1
		resp = client.chat.completions.create(
			model=mdl,
			messages=msg,
			temperature=temperature,
		)
		raw = resp.choices[0].message.content or "{}"
		text = raw.strip()
		# Try to extract JSON if the model wrapped it in code fences
		if text.startswith("```"):
			# Strip triple backticks and possible language hints
			text = text.strip('`')
			# Remove leading json hints
			if text.lower().startswith("json\n"):
				text = text[5:]
		import json
		try:
			data = json.loads(text)
		except Exception:
			# Last resort: find first {...} block
			import re
			m = re.search(r"\{[\s\S]*\}", text)
			data = json.loads(m.group(0)) if m else {}
		decision = str(data.get("decision", "allow")).lower()
		if decision not in {"allow", "warn", "block"}:
			decision = "allow"
		reasons_in = data.get("reasons") or []
		reasons: List[Dict[str, Any]] = []
		for r in reasons_in:
			if not isinstance(r, dict):
				continue
			reasons.append(
				{
					"rule": str(r.get("rule") or "dynamic_classifier"),
					"severity": str(r.get("severity") or ("critical" if decision == "block" else "warning")),
					"decision": decision,
					"description": r.get("description") or "Dynamic classifier verdict.",
				}
			)
		if not reasons:
			reasons = [
				{
					"rule": "dynamic_classifier",
					"severity": "critical" if decision == "block" else ("warning" if decision == "warn" else "info"),
					"decision": decision,
					"description": "Dynamic classifier verdict.",
				}
			]
		return {"decision": decision, "reasons": reasons}
	except Exception:
		# On any failure, do not block; caller can fall back to heuristic
		return {"decision": "allow", "reasons": []}
