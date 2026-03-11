"""Demo: send a variety of requests to httpbin.org and inspect them in Smello."""

import time

import smello

smello.init(
    server_url="http://localhost:5110",
    redact_query_params=["api_key", "token"],
)

import requests

# GET with query params
resp = requests.get(
    "https://httpbin.org/get", params={"lang": "python", "tool": "smello"}
)
print(f"GET  /get          → {resp.status_code}")

# POST with JSON body
resp = requests.post(
    "https://httpbin.org/post", json={"message": "hello from smello", "count": 42}
)
print(f"POST /post         → {resp.status_code}")

# PUT
resp = requests.put("https://httpbin.org/put", json={"updated": True})
print(f"PUT  /put          → {resp.status_code}")

# DELETE
resp = requests.delete("https://httpbin.org/delete")
print(f"DEL  /delete       → {resp.status_code}")

# Custom headers (Authorization is redacted by default)
resp = requests.get(
    "https://httpbin.org/headers",
    headers={"X-Custom-Header": "smello-demo", "Authorization": "Bearer sk-secret-key"},
)
print(f"GET  /headers      → {resp.status_code}  (Authorization will be redacted)")

# Query string with secret params (api_key and token are redacted via init config)
resp = requests.get(
    "https://httpbin.org/get",
    params={"q": "smello", "api_key": "sk-1234567890", "token": "xoxb-secret-token"},
)
print(f"GET  /get          → {resp.status_code}  (api_key and token will be redacted)")

# Different status codes
for code in [200, 201, 404, 418, 500]:
    resp = requests.get(f"https://httpbin.org/status/{code}")
    print(f"GET  /status/{code}  → {resp.status_code}")

# JSON with timestamps (annotations will appear in the dashboard)
resp = requests.post(
    "https://httpbin.org/anything",
    json={
        "event": "user.login",
        "created_at": int(time.time()),
        "scheduled_at_ms": int(time.time() * 1000),
        "user": {"id": 42, "name": "Alice"},
    },
)
print(f"POST /anything     → {resp.status_code}  (response contains timestamps)")

# Slow response
resp = requests.get("https://httpbin.org/delay/1")
print(f"GET  /delay/1      → {resp.status_code}  (check duration in dashboard)")

# Give the background thread time to flush
time.sleep(2)
print("\nDone. Open http://localhost:5110 to browse captured requests.")
