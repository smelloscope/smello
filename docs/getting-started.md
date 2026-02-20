# Getting Started

## Install

Install the client SDK and server:

```bash
pip install smello smello-server
```

Or install the server with Docker:

```bash
docker run -p 5110:5110 ghcr.io/smelloscope/smello
```

## Start the server

```bash
smello-server run
```

The web dashboard opens at [http://localhost:5110](http://localhost:5110).

!!! tip "Why port 5110?"
    Read it as **5-1-1-0** → **S-L-L-O** → **smello**.

## Add to your code

```python
import smello
smello.init()
```

That's it. Smello monkey-patches `requests`, `httpx`, and `grpc` to capture all outgoing traffic.

```python
import requests
resp = requests.get("https://api.stripe.com/v1/charges")

import httpx
resp = httpx.get("https://api.openai.com/v1/models")

# Browse captured requests at http://localhost:5110
```

### Google Cloud libraries

Many Google Cloud Python libraries use gRPC under the hood. Smello captures these calls automatically — no extra setup needed:

```python
import smello
smello.init()

# BigQuery, Firestore, Pub/Sub, Analytics (GA4), Vertex AI,
# Speech-to-Text, Vision, Translation — all captured via gRPC
from google.cloud import bigquery
client = bigquery.Client()
rows = client.query("SELECT 1").result()
```

Any Python library that calls `grpc.secure_channel()` or `grpc.insecure_channel()` is captured.

## What Smello captures

For every outgoing request:

- Method, URL, headers, and body
- Response status code, headers, and body
- Duration in milliseconds
- Library used (requests, httpx, or grpc)

gRPC calls are displayed with a `grpc://` URL scheme. Protobuf request and response bodies are automatically serialized to JSON.

Smello redacts sensitive headers (`Authorization`, `X-Api-Key`) by default.

## Supported libraries

| Library      | What Smello patches                                    |
| ------------ | ------------------------------------------------------ |
| **requests** | `Session.send()`                                       |
| **httpx**    | `Client.send()` and `AsyncClient.send()`               |
| **grpc**     | `insecure_channel()` and `secure_channel()` (unary-unary) |

## Python version support

| Package                 | Python  |
| ----------------------- | ------- |
| **smello** (client SDK) | >= 3.10 |
| **smello-server**       | >= 3.14 |
