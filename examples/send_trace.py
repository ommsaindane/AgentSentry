from agentsentry.sdk import AgentSentryClient
from agentsentry.tracer import Tracer

def main():
    client = AgentSentryClient()  # reads AGENTSENTRY_API_URL if set; defaults to http://localhost:8000
    # Create a session
    session_id = client.create_session()
    print("Created session:", session_id)

    tracer = Tracer(client)
    # Send a user message
    r1 = tracer.user("Hello, AgentSentry!")
    print("User trace:", r1)

    # Send an assistant response
    r2 = tracer.assistant("Hi! Tracing is online.")
    print("Assistant trace:", r2)

    # Simulate a tool call
    r3 = tracer.tool("search_files", {"query": "policy docs"}, result={"hits": 3})
    print("Tool trace:", r3)

if __name__ == "__main__":
    main()