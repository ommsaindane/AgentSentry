from agentsentry.sdk import AgentSentryClient
from agentsentry.tracer import Tracer
from agentsentry.enforcer import Enforcer, EnforcementError

def dangerous_delete():
    # Stand-in for a destructive action
    return "would delete files"

def benign_action():
    return "ok"

def main():
    c = AgentSentryClient()
    sid = c.create_session()
    t = Tracer(c)
    e = Enforcer(t)

    print("Session:", sid)

    # Warn case (secret-like)
    try:
        res = e.guard_and_call(
            "kv_store.write",
            {"key": "api_key", "value": "ABCDEFGHIJKLMNOP"},
            call_fn=benign_action,
        )
        print("Warned call result:", res)
    except EnforcementError as ee:
        print("Unexpected block:", ee)

    # Block case (rm -rf)
    try:
        res = e.guard_and_call(
            "shell",
            {"cmd": "rm -rf /"},
            call_fn=dangerous_delete,
        )
        print("Block bypassed (unexpected):", res)
    except EnforcementError as ee:
        print("Blocked as expected:", str(ee))

if __name__ == "__main__":
    main()