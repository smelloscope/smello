# Smello

Capture outgoing HTTP requests from your Python code and browse them in a local web dashboard.

Like [Mailpit](https://mailpit.axllent.org/), but for HTTP requests. Add two lines to your code, and Smello captures every request/response at `http://localhost:5110`.

> **Why port 5110?** Read it as **5-1-1-0** → **S-L-L-O** → **smello**.

## Quick Start

### 1. Start the server

```bash
pip install smello-server
smello-server run
```

Or with Docker:

```bash
docker run -p 5110:5110 ghcr.io/smelloscope/smello
```

### 2. Add to your code

```python
import smello
smello.init()

# Smello now captures all outgoing requests via requests and httpx
import requests
resp = requests.get("https://api.stripe.com/v1/charges")

import httpx
resp = httpx.get("https://api.openai.com/v1/models")

# Browse captured requests at http://localhost:5110
```

Two lines, no configuration.

## What Smello Captures

For every outgoing HTTP request:

- Method, URL, headers, and body
- Response status code, headers, and body
- Duration in milliseconds
- HTTP library used (requests or httpx)

Smello redacts sensitive headers (`Authorization`, `X-Api-Key`) by default.

## Configuration

```python
smello.init(
    server_url="http://localhost:5110",       # where to send captured data
    capture_hosts=["api.stripe.com"],         # only capture these hosts
    capture_all=True,                          # capture everything (default)
    ignore_hosts=["localhost"],               # skip these hosts
    redact_headers=["Authorization"],         # replace values with [REDACTED]
    enabled=True,                              # kill switch
)
```

## API

Smello provides a JSON API for exploring captured requests from the command line.

### List requests

```bash
# All captured requests (summary)
curl -s http://localhost:5110/api/requests | python -m json.tool

# Filter by method
curl -s 'http://localhost:5110/api/requests?method=POST'

# Filter by host
curl -s 'http://localhost:5110/api/requests?host=api.stripe.com'

# Filter by status code
curl -s 'http://localhost:5110/api/requests?status=500'

# Search by URL substring
curl -s 'http://localhost:5110/api/requests?search=checkout'

# Limit results (default: 50, max: 200)
curl -s 'http://localhost:5110/api/requests?limit=10'
```

### Get request details

Returns headers and bodies for both request and response.

```bash
curl -s http://localhost:5110/api/requests/{id} | python -m json.tool
```

### Clear all requests

```bash
curl -X DELETE http://localhost:5110/api/requests
```

## Python Version Support

| Package | Python |
|---------|--------|
| **smello** (client SDK) | >= 3.10 |
| **smello-server** | >= 3.14 |

## Supported Libraries

- **requests** — patches `Session.send()`
- **httpx** — patches `Client.send()` and `AsyncClient.send()`

## Development

Requires [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/smelloscope/smello.git
cd smello
uv sync

# Run the server
uv run smello-server run

# Run an example (in another terminal)
uv run python examples/python/basic_requests.py
```

## Architecture

```
Your Python App ──→ Smello Server ──→ Web Dashboard
(smello.init())     (FastAPI+SQLite)   (localhost:5110)
```

- **smello** (client SDK): Monkey-patches `requests` and `httpx` to capture traffic. Sends data to the server in a background thread.
- **smello-server**: FastAPI app with Jinja2 templates and SQLite. Receives captured data and serves the dashboard.

## Project Structure

```
smello/
├── server/              # smello-server (FastAPI + Tortoise ORM + SQLite)
│   └── tests/
├── clients/python/      # smello client SDK
│   └── tests/
├── tests/test_e2e/      # End-to-end tests
└── examples/python/
```

## License

MIT
