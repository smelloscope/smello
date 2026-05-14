"""Example: Capture requests made with the `httpx` library (sync).

Demonstrates both regular and streaming requests. Smello captures
streaming response bodies by wrapping the byte-stream with a tee —
the capture is sent when the stream is closed.
"""

import time

import smello

smello.init(server_url="http://localhost:5110")

import httpx

with httpx.Client() as client:
    # Regular (non-streaming) request
    resp = client.get("https://httpbin.org/get")
    print(f"GET /get: {resp.status_code}")

    resp = client.post("https://httpbin.org/post", json={"hello": "httpx"})
    print(f"POST /post: {resp.status_code}")

    # Streaming request — body is captured lazily on close
    with client.stream("GET", "https://httpbin.org/stream/3") as resp:
        for line in resp.iter_lines():
            print(f"  stream line: {line[:60]}...")
    print(f"GET /stream/3 (streaming): {resp.status_code}")

print("\nOpen http://localhost:5110 to see captured requests")

# Give the background thread time to flush
time.sleep(1)
