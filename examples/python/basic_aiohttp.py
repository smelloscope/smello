"""Example: Capture async requests made with aiohttp."""

import asyncio

import smello

smello.init(server_url="http://localhost:5110")

import aiohttp


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://httpbin.org/get") as resp:
            print(f"GET /get: {resp.status}")
            await resp.text()

        async with session.post(
            "https://httpbin.org/post", json={"async": True}
        ) as resp:
            print(f"POST /post (json): {resp.status}")
            await resp.text()

        async with session.post(
            "https://httpbin.org/post", data="key=value&foo=bar"
        ) as resp:
            print(f"POST /post (data): {resp.status}")
            await resp.text()

    print("\nOpen http://localhost:5110 to see captured requests")

    # Give the background thread time to flush
    await asyncio.sleep(1)


asyncio.run(main())
