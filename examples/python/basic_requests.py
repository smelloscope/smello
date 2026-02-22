"""Example: Capture requests made with the `requests` library."""

import smello

smello.init(server_url="http://localhost:5110")

import requests

# These requests will be captured and visible at http://localhost:5110
resp = requests.get("https://httpbin.org/get")
print(f"GET /get: {resp.status_code}")

resp = requests.post("https://httpbin.org/post", json={"hello": "world"})
print(f"POST /post: {resp.status_code}")

resp = requests.get("https://httpbin.org/status/404")
print(f"GET /status/404: {resp.status_code}")

print("\nOpen http://localhost:5110 to see captured requests")

# Give the background thread time to flush
import time

time.sleep(1)
