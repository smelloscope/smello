# Smello

Capture outgoing HTTP requests from your Python code and browse them in a local web dashboard — including gRPC calls made by Google Cloud libraries.

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
smello.init(server_url="http://localhost:5110")

# Smello now captures all outgoing requests — HTTP and gRPC
import requests
resp = requests.get("https://api.stripe.com/v1/charges")

import httpx
resp = httpx.get("https://api.openai.com/v1/models")

# Google Cloud libraries use gRPC under the hood — Smello captures those too
from google.cloud import bigquery
client = bigquery.Client()
rows = client.query("SELECT 1").result()

# Browse captured requests at http://localhost:5110
```

Or leave `smello.init()` without arguments and set `SMELLO_URL` in your environment. Without a URL, `init()` is a safe no-op: no monkey-patching, no background threads, no side effects.

## AI Agent Skills

Smello ships with [Agent Skills](https://agentskills.io) for Claude Code, Cursor, GitHub Copilot, and [20+ other AI coding tools](https://skills.sh/).

```bash
npx skills add smelloscope/smello
```

| Skill            | Install individually                                      | Description                                                                                                                                                                       |
| ---------------- | --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/setup-smello`  | `npx skills add smelloscope/smello --skill setup-smello`  | Explores your codebase and proposes a plan to integrate Smello (package install, entrypoint placement, Docker Compose, env vars). Does not make changes without approval.         |
| `/http-debugger` | `npx skills add smelloscope/smello --skill http-debugger` | Queries the Smello API to inspect captured traffic, debug failed API calls, and analyze request/response details. Also activates automatically when you ask about HTTP debugging. |

## What Smello Captures

For every outgoing request:

- Method, URL, headers, and body
- Response status code, headers, and body
- Duration in milliseconds
- Library used (requests, httpx, or grpc)

gRPC calls are displayed with a `grpc://` URL scheme (e.g. `grpc://bigquery.googleapis.com:443/...`). Protobuf request and response bodies are automatically serialized to JSON.

Smello redacts sensitive headers (`Authorization`, `X-Api-Key`) by default.

## Configuration

```python
smello.init(
    server_url="http://localhost:5110",       # where to send captured data
    capture_hosts=["api.stripe.com"],         # only capture these hosts
    capture_all=True,                          # capture everything (default)
    ignore_hosts=["localhost"],               # skip these hosts
    redact_headers=["Authorization"],         # replace values with [REDACTED]
)
```

All parameters fall back to `SMELLO_*` environment variables when not passed explicitly:

| Parameter        | Env variable            | Default                          |
| ---------------- | ----------------------- | -------------------------------- |
| `server_url`     | `SMELLO_URL`            | `None` (inactive)                |
| `capture_all`    | `SMELLO_CAPTURE_ALL`    | `True`                           |
| `capture_hosts`  | `SMELLO_CAPTURE_HOSTS`  | `[]`                             |
| `ignore_hosts`   | `SMELLO_IGNORE_HOSTS`   | `[]`                             |
| `redact_headers` | `SMELLO_REDACT_HEADERS` | `["Authorization", "X-Api-Key"]` |

The server URL is the activation signal — `init()` does nothing unless `server_url` is passed or `SMELLO_URL` is set. Boolean env vars accept `true`/`1`/`yes` and `false`/`0`/`no` (case-insensitive). List env vars are comma-separated.

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

| Package                 | Python  |
| ----------------------- | ------- |
| **smello** (client SDK) | >= 3.10 |
| **smello-server**       | >= 3.14 |

## Supported Libraries

- **requests** — patches `Session.send()`
- **httpx** — patches `Client.send()` and `AsyncClient.send()`
- **grpc** — patches `insecure_channel()` and `secure_channel()` to intercept unary-unary calls

### Google Cloud libraries

Many Google Cloud Python libraries use gRPC under the hood. Smello automatically captures these calls with zero additional configuration:

- **Google BigQuery** (`google-cloud-bigquery`)
- **Google Cloud Firestore** (`google-cloud-firestore`)
- **Google Cloud Pub/Sub** (`google-cloud-pubsub`)
- **Google Analytics Data API** (`google-analytics-data`) — GA4 reporting
- **Google Cloud Vertex AI** (`google-cloud-aiplatform`)
- **Google Cloud Speech-to-Text** (`google-cloud-speech`)
- **Google Cloud Vision** (`google-cloud-vision`)
- **Google Cloud Translation** (`google-cloud-translate`)
- **Google Cloud Secret Manager** (`google-cloud-secret-manager`)
- **Google Cloud Spanner** (`google-cloud-spanner`)
- **Google Cloud Bigtable** (`google-cloud-bigtable`)

Any library that calls `grpc.secure_channel()` or `grpc.insecure_channel()` is automatically captured.

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

- **smello** (client SDK): Monkey-patches `requests`, `httpx`, and `grpc` to capture traffic. Sends data to the server in a background thread.
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
