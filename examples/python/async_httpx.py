"""Example: Capture async requests made with httpx.AsyncClient.

Demonstrates both regular and streaming requests. Streaming responses
(common with LLM APIs like OpenAI/Anthropic) are captured automatically —
the body is accumulated as chunks arrive and sent when the stream closes.
"""

import asyncio

import smello

smello.init(server_url="http://localhost:5110")

import httpx


async def main():
    async with httpx.AsyncClient() as client:
        # Regular (non-streaming) request
        resp = await client.get("https://httpbin.org/get")
        print(f"GET /get: {resp.status_code}")

        resp = await client.post("https://httpbin.org/post", json={"async": True})
        print(f"POST /post: {resp.status_code}")

        # Streaming request — body is captured lazily on close
        async with client.stream("GET", "https://httpbin.org/stream/3") as resp:
            async for line in resp.aiter_lines():
                print(f"  stream line: {line[:60]}...")
        print(f"GET /stream/3 (streaming): {resp.status_code}")

    print("\nOpen http://localhost:5110 to see captured requests")

    # Give the background thread time to flush
    await asyncio.sleep(1)


asyncio.run(main())
