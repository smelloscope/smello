# Smello

Capture outgoing HTTP requests from your Python code and browse them in a local web dashboard — including gRPC calls made by Google Cloud libraries.

Like [Mailpit](https://mailpit.axllent.org/), but for HTTP requests.

## Setup

Install the client SDK and the server:

```bash
pip install smello smello-server
```

Start the server:

```bash
smello-server run
```

Add two lines to your code:

```python
import smello
smello.init()

import requests
resp = requests.get("https://api.stripe.com/v1/charges")

# Browse captured requests at http://localhost:5110
```

Smello monkey-patches `requests`, `httpx`, and `grpc` to capture all outgoing traffic. Browse results at `http://localhost:5110`.

### Google Cloud libraries

Many Google Cloud Python libraries — BigQuery, Firestore, Pub/Sub, Analytics Data API (GA4), Vertex AI, Speech-to-Text, Vision, Translation, and others — use gRPC under the hood. Smello captures these calls automatically:

```python
import smello
smello.init()

from google.cloud import bigquery
client = bigquery.Client()
rows = client.query("SELECT 1").result()

# gRPC calls to bigquery.googleapis.com appear at http://localhost:5110
```

Any library that calls `grpc.secure_channel()` or `grpc.insecure_channel()` is automatically captured.

## What Smello Captures

- Method, URL, headers, and body
- Response status code, headers, and body
- Duration in milliseconds
- Library used (requests, httpx, or grpc)

Smello redacts sensitive headers (`Authorization`, `X-Api-Key`) by default.

## Configuration

```python
smello.init(
    server_url="http://localhost:5110",  # where to send captured data
    capture_hosts=["api.stripe.com"],    # only capture these hosts
    capture_all=True,                     # capture everything (default)
    ignore_hosts=["localhost"],          # skip these hosts
    redact_headers=["Authorization"],    # replace values with [REDACTED]
    enabled=True,                         # kill switch
)
```

All parameters fall back to `SMELLO_*` environment variables when not passed explicitly:

| Parameter | Env variable | Default |
|-----------|-------------|---------|
| `enabled` | `SMELLO_ENABLED` | `True` |
| `server_url` | `SMELLO_URL` | `http://localhost:5110` |
| `capture_all` | `SMELLO_CAPTURE_ALL` | `True` |
| `capture_hosts` | `SMELLO_CAPTURE_HOSTS` | `[]` |
| `ignore_hosts` | `SMELLO_IGNORE_HOSTS` | `[]` |
| `redact_headers` | `SMELLO_REDACT_HEADERS` | `["Authorization", "X-Api-Key"]` |

Boolean env vars accept `true`/`1`/`yes` and `false`/`0`/`no` (case-insensitive). List env vars are comma-separated.

## Supported Libraries

- **requests** — patches `Session.send()`
- **httpx** — patches `Client.send()` and `AsyncClient.send()`
- **grpc** — patches `insecure_channel()` and `secure_channel()` to intercept unary-unary calls

## Requires

- Python >= 3.10
- [smello-server](https://pypi.org/project/smello-server/) running locally

## Links

- [Documentation & Source](https://github.com/smelloscope/smello)
- [smello-server on PyPI](https://pypi.org/project/smello-server/)
