# examples/langchain_agent.py
import os
import json
import requests
from typing import Dict, Any

from agentsentry.sdk import AgentSentryClient
from agentsentry.tracer import Tracer
from agentsentry.enforcer import Enforcer, EnforcementError

# Simple "tools"
def kv_store_write(kv: Dict[str, Any], key: str, value: str) -> str:
    kv[key] = value
    return "ok"

def shell_run(cmd: str) -> str:
    # For demo, just echo what would run
    return f"would run: {cmd}"

def call_openrouter(messages, model: str) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        # Optional but recommended headers:
        "HTTP-Referer": os.getenv("OPENROUTER_REFERRER", "http://localhost"),
        "X-Title": os.getenv("OPENROUTER_TITLE", "AgentSentry Demo"),
    }
    payload = {
        "model": model,
        "messages": messages,
    }
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        data=json.dumps(payload),
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]

def main():
    # Configure Sentry + session
    c = AgentSentryClient()
    sid = c.create_session()
    t = Tracer(c)
    e = Enforcer(t)

    kv: Dict[str, Any] = {}

    # Pick a model via env or default
    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

    # A simple prompt where LLM proposes a tool call
    user_msg = "Store an api_key 'ABCDEFGHIJKLMNOP' and then run rm -rf /"
    t.user(user_msg)

    # Get an assistant thought/plan from OpenRouter
    assistant_text = call_openrouter(
        messages=[
            {"role": "system", "content": "You are a tool-using assistant. Propose safe actions only."},
            {"role": "user", "content": user_msg},
        ],
        model=model,
    )
    t.assistant(assistant_text or "")
    print("Assistant:", assistant_text)

    # Naive tool policy from the message: demonstrate both warn and block
    # 1) Secret-like write: expect warn, but allow
    try:
        res = e.guard_and_call(
            "kv_store.write",
            {"key": "api_key", "value": "ABCDEFGHIJKLMNOP"},
            call_fn=lambda: kv_store_write(kv, "api_key", "ABCDEFGHIJKLMNOP"),
        )
        print("kv_store.write ->", res)
    except EnforcementError as ee:
        print("kv_store.write blocked:", ee)

    # 2) Destructive shell: expect block and exception
    try:
        res = e.guard_and_call(
            "shell",
            {"cmd": "rm -rf /"},
            call_fn=lambda: shell_run("rm -rf /"),
        )
        print("shell ->", res)
    except EnforcementError as ee:
        print("shell blocked:", ee)

    print("KV now:", kv)

if __name__ == "__main__":
    main()
