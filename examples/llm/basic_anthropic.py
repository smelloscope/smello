"""Example: Capture requests made by the Anthropic Python SDK.

The SDK uses httpx under the hood, so smello's httpx patch
captures all API calls automatically.
"""

import smello

smello.init(server_url="http://localhost:5110", debug=True)

import anthropic

client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=64,
    messages=[{"role": "user", "content": "Say hello in one sentence."}],
)
print(f"Response: {message.content[0].text}")

smello.flush()
print("\nOpen http://localhost:5110 to see captured requests")
