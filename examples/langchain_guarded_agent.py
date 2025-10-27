from typing import Any, Dict, Optional, Callable
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain_community.chat_models import ChatOpenAI  # or adjust to your preferred LLM
import os

from agentsentry.sdk import AgentSentryClient
from agentsentry.tracer import Tracer
from agentsentry.enforcer import Enforcer, EnforcementError

# Demo tool implementations
def shell_run_impl(cmd: str) -> str:
    # DO NOT execute shell in demo; just echo to simulate
    return f"[simulated] would run: {cmd}"

def kv_write_impl(key: str, value: str) -> str:
    # Simulate a write
    return f"[simulated] wrote {key}={value}"

def guard_tool(enforcer: Enforcer, tool_name: str, fn: Callable[..., Any]) -> Callable[..., Any]:
    """
    Wrap a tool callable with policy enforcement.
    We trace a pre-call with args; on allow/warn we run, on block we raise.
    """
    def wrapped(*args, **kwargs):
        # Flatten args/kwargs into a dict for policy evaluation
        # LangChain Tool typically passes a single string input; adapt accordingly.
        if args and isinstance(args[0], str) and not kwargs:
            # naive parse of "key=value" pairs for demo
            inp = args[0]
            if tool_name == "shell":
                call_args = {"cmd": inp}
            else:
                # Expect "key=value" CSV-like
                parts = [p.strip() for p in inp.split(",")]
                parsed = {}
                for p in parts:
                    if "=" in p:
                        k, v = p.split("=", 1)
                        parsed[k.strip()] = v.strip()
                call_args = parsed or {"input": inp}
        else:
            call_args = {**kwargs}
        return enforcer.guard_and_call(tool_name, call_args, lambda: fn(**call_args))
    return wrapped

def main():
    # Setup AgentSentry
    base_url = os.getenv("AGENTSENTRY_API_URL", "http://localhost:8000")
    c = AgentSentryClient(base_url=base_url)
    sid = c.create_session()
    t = Tracer(c)
    e = Enforcer(t)
    print("Session:", sid)

    # Model setup (pick any local/hosted LLM; here we just set a dummy for interface)
    # For a real run, set OPENAI_API_KEY in env and use gpt-4o-mini or similar
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # Guarded tools
    shell_tool = Tool(
        name="shell",
        description="Execute shell commands. Input: raw shell command string.",
        func=guard_tool(e, "shell", shell_run_impl),
    )
    kv_tool = Tool(
        name="kv_write",
        description="Write key/value. Input format: 'key=<k>, value=<v>'",
        func=guard_tool(e, "kv_write", kv_write_impl),
    )

    agent = initialize_agent(
        tools=[shell_tool, kv_tool],
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
    )

    # Benign request (should allow)
    print("=== benign ===")
    out1 = agent.run("Write a greeting into kv_write. Use key=greeting, value=hello")
    print(out1)

    # Secret-like (should warn)
    print("=== warn ===")
    out2 = agent.run("Write into kv_write using key=api_key, value=ABCDEFGHIJKLMNOP")
    print(out2)

    # Destructive (should block)
    print("=== block ===")
    try:
        out3 = agent.run("Run shell to delete everything: rm -rf /")
        print(out3)
    except EnforcementError as ee:
        print("Blocked as expected:", ee)

if __name__ == "__main__":
    main()