import os
from openai import OpenAI

def get_openrouter_client() -> OpenAI:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    # OpenRouter is OpenAI-compatible
    return OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )
