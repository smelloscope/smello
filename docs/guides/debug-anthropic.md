# Debug Anthropic with Smello

The Anthropic Python SDK uses httpx to communicate with the Claude API. Smello captures every API call, letting you inspect message payloads, tool definitions, token usage, and streaming responses in the dashboard.

## Setup

```bash
pip install smello smello-server
smello-server  # start the dashboard
```

Then run your script with `smello run`:

```bash
smello run my_claude_app.py
```

The Anthropic SDK uses `httpx` under the hood. Smello captures all API calls automatically. No code changes needed.

## Scenario: debugging a tool-use loop that makes too many API calls

You're building an agent with Claude's tool use, and it's making more API calls than expected. Is Claude calling tools unnecessarily? Is the loop terminating correctly?

```python
client = anthropic.Anthropic()
messages = [{"role": "user", "content": "What's the weather in Paris?"}]

while True:
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        messages=messages,
        tools=tools,
        max_tokens=1024,
    )
    if response.stop_reason == "end_turn":
        break
    # process tool calls and continue...
```

### Debug in the dashboard

Open the Smello dashboard. You'll see every `POST` to `api.anthropic.com/v1/messages`:

- **Request bodies**: see how the `messages` array grows with each loop iteration. Are previous tool results being appended correctly?
- **Response bodies**: check `stop_reason` for each response. Is Claude returning `tool_use` when it should be returning `end_turn`?
- **Token usage**: each response includes `usage.input_tokens` and `usage.output_tokens`. Watch how input tokens grow as the conversation gets longer.
- **Timeline order**: the dashboard shows requests in order, so you can trace the exact sequence of the agent loop.

### Debug with an AI agent

If you use [Claude Code](https://claude.ai/code) or another AI coding tool, the `/smello-debugger` skill can query captured events and cross-reference them with your source code. Install it once:

```bash
npx skills add smelloscope/smello --skill smello-debugger
```

Then ask your agent:

```
/smello-debugger
My Claude tool-use loop is making too many API calls
```

The skill is also invoked automatically when your agent recognizes a debugging question, but calling `/smello-debugger` explicitly gives the best results. See [AI Agent Skills](../ai-skills.md) for compatible tools.

## Tips

- **Streaming**: When using `client.messages.stream()`, Smello captures the full response body. You can see the complete output even though your code consumed it as server-sent events.
- **Token counting**: Each response's `usage` field is in the response body. Compare `input_tokens` across requests to understand how your context window fills up.
- **System prompts**: The system prompt is part of the request body. If you're debugging unexpected Claude behavior, check that the system prompt in the captured request matches what you intended.
- **Rate limits**: Anthropic returns rate limit headers (`anthropic-ratelimit-requests-remaining`, etc.) in every response. These are visible in the response headers panel.
- **Retries**: The Anthropic SDK retries on overloaded (529) and rate limit (429) errors. Each attempt shows up separately in the timeline.

--8<-- "includes/guide-next-steps.md"
