# Getting Started

## Install

Install and start the server:

```bash
pip install smello-server
smello-server run
```

Or run with Docker:

```bash
docker run -p 5110:5110 ghcr.io/smelloscope/smello
```

Install the client SDK:

```bash
pip install smello
```

The server listens at [http://localhost:5110](http://localhost:5110).

!!! tip "Why port 5110?"
    Read it as **5-1-1-0** → **S-L-L-O** → **smello**.

## Add to your code

```python
import smello
smello.init(server_url="http://localhost:5110")
```

That's it. Smello monkey-patches `requests`, `httpx`, `grpc`, and `botocore` to capture all outgoing traffic.

```python
import requests
resp = requests.get("https://api.stripe.com/v1/charges")

import httpx
resp = httpx.get("https://api.openai.com/v1/models")

# Browse captured requests at http://localhost:5110
```

### Activation model

Smello only activates when a server URL is provided — either via the `server_url` parameter or the `SMELLO_URL` environment variable. Without a URL, `init()` is a safe no-op: no monkey-patching, no background threads, no side effects.

Leave `smello.init()` in your code and control activation via the environment:

```python
import smello
smello.init()  # does nothing unless SMELLO_URL is set
```

```bash
# Activate in development
export SMELLO_URL=http://localhost:5110
```

Like Sentry's `SENTRY_DSN`, this keeps instrumentation in place with zero production overhead.

### Google Cloud libraries

Many Google Cloud Python libraries use gRPC under the hood. Smello captures these calls automatically — no extra setup needed:

```python
import smello
smello.init(server_url="http://localhost:5110")

# BigQuery, Firestore, Pub/Sub, Analytics (GA4), Vertex AI,
# Speech-to-Text, Vision, Translation — all captured via gRPC
from google.cloud import bigquery
client = bigquery.Client()
rows = client.query("SELECT 1").result()
```

Any Python library that calls `grpc.secure_channel()` or `grpc.insecure_channel()` is captured.

### AWS libraries (boto3)

boto3 uses `botocore`, which calls `urllib3` directly, bypassing `requests` and `httpx`. Smello patches botocore's HTTP session to capture AWS API calls:

```python
import smello
smello.init(server_url="http://localhost:5110")

import boto3
s3 = boto3.client("s3")
buckets = s3.list_buckets()

# AWS calls appear at http://localhost:5110 — XML responses
# show as a collapsible tree, just like JSON.
```

## What Smello captures

For every outgoing request:

- Method, URL, headers, and body
- Response status code, headers, and body
- Duration in milliseconds
- Library used (requests, httpx, grpc, or botocore)

The dashboard recognizes Unix timestamps in JSON bodies and shows the human-readable date in a tooltip. XML responses (common in AWS S3, STS, EC2) appear as a collapsible tree, just like JSON. Both formats offer Tree and Raw tabs — Tree shows an expandable tree, Raw shows syntax-highlighted source.

gRPC calls are displayed with a `grpc://` URL scheme. Protobuf request and response bodies are automatically serialized to JSON.

Smello redacts sensitive headers (`Authorization`, `X-Api-Key`) by default and optionally redacts query string parameters ([details](configuration.md#redact_query_params)).

## Supported libraries

| Library      | What Smello patches                                    |
| ------------ | ------------------------------------------------------ |
| **requests** | `Session.send()`                                       |
| **httpx**    | `Client.send()` and `AsyncClient.send()`               |
| **grpc**     | `insecure_channel()` and `secure_channel()` (unary-unary) |
| **botocore** | `URLLib3Session.send()` (all boto3 / AWS SDK calls)    |

## Python version support

| Package                 | Python  |
| ----------------------- | ------- |
| **smello** (client SDK) | >= 3.10 |
| **smello-server**       | >= 3.14 |
