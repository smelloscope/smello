"""Example: Capture async requests made with httpx.AsyncClient."""

import asyncio

import smello

smello.init(server_url="http://localhost:5110")

import httpx


async def main():
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://httpbin.org/get")
        print(f"GET /get: {resp.status_code}")

        resp = await client.post("https://httpbin.org/post", json={"async": True})
        print(f"POST /post: {resp.status_code}")

    print("\nOpen http://localhost:5110 to see captured requests")

    # Give the background thread time to flush
    await asyncio.sleep(1)


asyncio.run(main())
