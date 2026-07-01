"""OpenAI Agents SDK example, captured by smello.

Run with:
    uv run --env-file=.env --with openai-agents python examples/llm/llm_openai_agents.py

Unlike the Claude Agent SDK (which spawns the `claude` CLI subprocess, see
llm_agent_sdk.py), the OpenAI Agents SDK is pure Python: it runs the agent loop
*in this process* and makes its API calls through the `openai` client, which uses
httpx. So smello's httpx patch DOES capture them.

Note: the OpenAI Agents SDK defaults to the Responses API (POST /v1/responses),
not Chat Completions. The agent loop here makes two calls — one that returns a
tool call, and one with the tool result that produces the final answer.
"""

import smello

smello.init(server_url="http://localhost:5110", debug=True)

from agents import Agent, Runner, function_tool, set_tracing_disabled

# Don't upload traces to OpenAI's platform — keep the run local.
set_tracing_disabled(True)


@function_tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"The weather in {city} is 18°C and sunny."


agent = Agent(
    name="Weather assistant",
    instructions="You are a concise weather assistant. Use the tool for weather questions.",
    model="gpt-4o-mini",
    tools=[get_weather],
)

result = Runner.run_sync(agent, "What's the weather in Paris?")
print(f"Final output: {result.final_output}")

smello.flush()
print("\nOpen http://localhost:5110 to see the captured calls (POST /v1/responses)")
