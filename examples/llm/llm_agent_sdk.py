"""Claude Agent SDK example — and a demonstration of smello's capture boundary.

Run with:
    uv run --env-file=.env --with claude-agent-sdk python examples/llm/llm_agent_sdk.py

IMPORTANT: unlike the `anthropic` client SDK (see llm_anthropic.py), the Claude
Agent SDK does NOT make API calls in this Python process. `query()` spawns the
Claude Code CLI as a *subprocess*, and that subprocess is what talks to
api.anthropic.com. smello monkey-patches httpx/requests *in-process*, so it does
not see traffic that originates in a child process.

Expected result: this script runs and prints Claude's answer, but NO new
`POST /v1/messages` event shows up in the smello dashboard — the LLM call happened
outside the instrumented process. Contrast with llm_anthropic.py, which is captured.

Requires the `claude` CLI to be installed and ANTHROPIC_API_KEY to be set (both
provided via --env-file and the local Claude Code install).
"""

import asyncio

import smello

smello.init(server_url="http://localhost:5110", debug=True)

from claude_agent_sdk import ClaudeAgentOptions, query


async def main() -> None:
    # Trivial, tool-free prompt so the agent just answers without touching files.
    options = ClaudeAgentOptions(
        allowed_tools=[],
        setting_sources=[],  # don't load local .claude/CLAUDE.md config
    )
    async for message in query(
        prompt="What is 2 + 2? Reply with just the number.",
        options=options,
    ):
        if hasattr(message, "result"):
            print(f"Result: {message.result}")

    smello.flush()
    print(
        "\nCheck http://localhost:5110 — note there is NO new POST /v1/messages event: "
        "the Agent SDK's API call ran in the `claude` subprocess, outside smello's reach."
    )


asyncio.run(main())
