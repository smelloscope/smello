"""Example: Capture requests made with the `httpx` library."""

import smello

smello.init(server_url="http://localhost:5110")

import httpx

# Sync client
with httpx.Client() as client:
    resp = client.get("https://httpbin.org/get")
    print(f"GET /get: {resp.status_code}")

    resp = client.post("https://httpbin.org/post", json={"hello": "httpx"})
    print(f"POST /post: {resp.status_code}")

print("\nOpen http://localhost:5110 to see captured requests")

# Give the background thread time to flush
import time

time.sleep(1)
