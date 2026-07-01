"""Simple Anthropic Messages call, captured by smello.

Run with:
    uv run --env-file=.env --with anthropic python examples/llm/llm_anthropic.py

The Anthropic SDK uses httpx under the hood, so smello's httpx patch captures the
call automatically. Open http://localhost:5110 and select the POST /v1/messages
event to see the LLM view.
"""

import smello

smello.init(server_url="http://localhost:5110", debug=True)

import anthropic

client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=256,
    system="You are a concise weather assistant.",
    tools=[
        {
            "name": "get_weather",
            "description": "Get the current weather for a city",
            "input_schema": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        }
    ],
    messages=[{"role": "user", "content": "What's the weather in Paris? Use the tool."}],
)

print(f"Stop reason: {message.stop_reason}")
for block in message.content:
    print(f"Block: {block}")

smello.flush()
print("\nOpen http://localhost:5110 to see the captured LLM call")
