"""Pydantic AI (with Anthropic) example, captured by smello.

Run with:
    uv run --env-file=.env --with 'pydantic-ai-slim[anthropic]' python examples/llm/llm_pydantic_ai.py

Like the OpenAI Agents SDK — and unlike the Claude Agent SDK — Pydantic AI is pure
Python: it runs the agent loop *in this process* using the `anthropic` client, which
uses httpx. So smello's httpx patch captures the calls, and because they hit the
Anthropic Messages API (POST /v1/messages) they render in smello's LLM view.

The tool call means the agent loop makes two captured calls: one that returns a
tool_use, and one with the tool result that produces the final answer.
"""

import smello

smello.init(server_url="http://localhost:5110", debug=True)

from pydantic_ai import Agent

agent = Agent(
    "anthropic:claude-sonnet-4-6",
    system_prompt="You are a concise weather assistant. Use the tool for weather questions.",
)


@agent.tool_plain
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"The weather in {city} is 18°C and sunny."


result = agent.run_sync("What's the weather in Paris?")
print(f"Output: {result.output}")

smello.flush()
print("\nOpen http://localhost:5110 to see the captured calls (POST /v1/messages)")
