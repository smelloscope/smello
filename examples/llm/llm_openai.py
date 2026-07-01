"""Simple OpenAI Chat Completions call, captured by smello.

Run with:
    uv run --env-file=.env --with openai python examples/llm/llm_openai.py

The OpenAI SDK uses httpx under the hood, so smello's httpx patch captures the
call automatically. Open http://localhost:5110 and select the
POST /v1/chat/completions event to see the LLM view.
"""

import smello

smello.init(server_url="http://localhost:5110", debug=True)

import openai

client = openai.OpenAI()

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a concise assistant."},
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
print("\nOpen http://localhost:5110 to see the captured LLM call")
