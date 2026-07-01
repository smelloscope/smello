"""OpenRouter (DeepSeek V4 Flash) example, captured by smello.

Run with:
    uv run --env-file=.env --with openai python examples/llm/llm_openrouter.py

OpenRouter exposes an OpenAI-compatible Chat Completions API, so we just point the
`openai` client at OpenRouter's base URL. The call runs in-process via httpx, so
smello captures it — and because the body is OpenAI Chat Completions shaped, the
LLM view renders it out of the box (detection is by body shape, not host, so the
openrouter.ai host makes no difference).

Requires OPENROUTER_API_KEY (provided via --env-file).
"""

import os

import smello

smello.init(server_url="http://localhost:5110", debug=True)

from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

response = client.chat.completions.create(
    model="deepseek/deepseek-v4-flash",
    messages=[
        {"role": "system", "content": "You are a concise weather assistant."},
        {"role": "user", "content": "What's the weather in Paris? Use the tool."},
    ],
    tools=[
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a city",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            },
        }
    ],
)

print(f"Finish reason: {response.choices[0].finish_reason}")
print(f"Message: {response.choices[0].message}")

smello.flush()
print("\nOpen http://localhost:5110 to see the captured call (POST /api/v1/chat/completions)")
