import os
import sys
import json
import time
from typing import Dict, Any

import requests

from agentsentry.sdk import AgentSentryClient
from agentsentry.tracer import Tracer


def call_ollama(prompt: str, model: str = "llama3", stream: bool = False, timeout: float = 60.0) -> Dict[str, Any]:
    base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    # Prefer chat API; fall back to generate if unavailable
    chat_url = f"{base}/api/chat"
    chat_payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "stream": stream,
    }
    try:
        resp = requests.post(chat_url, json=chat_payload, timeout=timeout)
        if resp.status_code == 404:
            raise requests.HTTPError("chat endpoint not found", response=resp)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and "message" in data:
            msg = data["message"] or {}
            return {"role": msg.get("role", "assistant"), "text": msg.get("content", "")}
        if isinstance(data, dict) and "response" in data:
            return {"role": "assistant", "text": data.get("response", "")}
        return {"role": "assistant", "text": json.dumps(data)}
    except Exception:
        # Fallback to generate API
        gen_url = f"{base}/api/generate"
        gen_payload = {"model": model, "prompt": prompt, "stream": stream}
        resp = requests.post(gen_url, json=gen_payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and "response" in data:
            return {"role": "assistant", "text": data.get("response", "")}
        return {"role": "assistant", "text": json.dumps(data)}


def pick_default_model(base: str) -> str:
    try:
        tags = requests.get(f"{base}/api/tags", timeout=5)
        if tags.ok:
            data = tags.json()
            models = data.get("models", [])
            if models:
                # prefer llama family if present, else first
                for m in models:
                    fams = (m.get("details", {}) or {}).get("families", [])
                    if "llama" in fams:
                        return m.get("name") or m.get("model") or "mistral:latest"
                m = models[0]
                return m.get("name") or m.get("model") or "mistral:latest"
    except Exception:
        pass
    return "mistral:latest"


def main():
    if len(sys.argv) > 1:
        user_prompt = " ".join(sys.argv[1:])
    else:
        user_prompt = os.getenv("PROMPT", "Tell me a short joke about databases.")

    base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL") or pick_default_model(base)

    # Init AgentSentry client and session
    c = AgentSentryClient()
    sid = c.create_session()
    tracer = Tracer(c)

    print(f"Session: {sid}")
    # Record user message
    tracer.user(user_prompt)

    # Call LLM (Ollama)
    print(f"Calling Ollama model={model} ...")
    t0 = time.time()
    llm_msg = call_ollama(user_prompt, model=model, stream=False)
    dt = time.time() - t0
    llm_text = llm_msg.get("text", "")
    print(f"Ollama responded in {dt:.2f}s, {len(llm_text)} chars")

    # Send assistant output through AgentSentry
    verdict = tracer.assistant(llm_text)

    decision = verdict.get("decision", "allow")
    reasons = verdict.get("reasons", [])

    print("\nAgentSentry decision:")
    print(f"  decision = {decision}")
    if reasons:
        for r in reasons:
            print(f"  - rule={r.get('rule')} type={r.get('type','regex')} severity={r.get('severity')} decision={r.get('decision')} desc={r.get('description')}")
    else:
        print("  (no reasons)")

    print("\nAssistant output:")
    if decision == "block":
        print("[BLOCKED by policy; not displaying full content]")
    else:
        print(llm_text)


if __name__ == "__main__":
    main()
