# Debug aiohttp with Smello

`aiohttp` is a popular async HTTP client and server framework for Python. Smello patches `aiohttp.ClientSession._request` to capture all outgoing requests made through aiohttp's client.

## Setup

```bash
pip install smello smello-server
smello-server  # start the dashboard
```

Then run your script with `smello run`:

```bash
smello run my_app.py
```

All requests made via `aiohttp.ClientSession` are captured automatically. No code changes needed.

> **Example script**: [`basic_aiohttp.py`](https://github.com/smelloscope/smello/blob/main/examples/python/basic_aiohttp.py)

## Scenario: debugging connection pooling issues

You're making many concurrent requests with aiohttp and some are failing with `ClientConnectionError`. Is the target server throttling you? Are connections being reused properly?

```python
async with aiohttp.ClientSession() as session:
    tasks = [session.get(f"https://api.example.com/items/{i}") for i in range(100)]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    # Some responses are ClientConnectionError: which ones?
```

### Debug in the dashboard

Open the Smello dashboard. You can see every request that succeeded and every one that failed:

![Smello dashboard showing captured aiohttp requests](assets/debug-aiohttp-dashboard.png)

- **Filter by status code**: quickly find the 5xx or failed requests among hundreds.
- **Timing patterns**: sort by duration to spot requests that hung before failing.
- **Host filter**: if your code calls multiple services, filter to just `api.example.com` to focus.

### Debug with an AI agent

If you use [Claude Code](https://claude.ai/code) or another AI coding tool, the `/smello-debugger` skill can query captured events and cross-reference them with your source code. Install it once:

```bash
npx skills add smelloscope/smello --skill smello-debugger
```

Then ask your agent:

```
/smello-debugger
Some of my aiohttp requests are failing with ClientConnectionError
```

![Claude Code session using smello-debugger to diagnose aiohttp connection errors](assets/debug-aiohttp-claude.png)

The skill is also invoked automatically when your agent recognizes a debugging question, but calling `/smello-debugger` explicitly gives the best results. See [AI Agent Skills](../ai-skills.md) for compatible tools.

## Tips

- **Session methods**: Smello captures requests regardless of which session method you use (`get`, `post`, `put`, `request`, etc.): they all flow through the same patched method.
- **Connector limits**: If you're debugging throughput, pair the Smello timeline with aiohttp's `TCPConnector(limit=...)` setting to understand how connection limits affect your request patterns.
- **Response body reading**: Smello captures the response body at the transport level. Even if your code doesn't call `resp.json()` or `resp.text()`, the body is still visible in the dashboard.

--8<-- "includes/guide-next-steps.md"
