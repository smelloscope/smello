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

That's it. Smello monkey-patches `requests` and `httpx` to capture all outgoing HTTP traffic.

```python
import requests
resp = requests.get("https://api.stripe.com/v1/charges")

import httpx
resp = httpx.get("https://api.openai.com/v1/models")

# Browse captured requests at http://localhost:5110
```

## What Smello captures

For every outgoing HTTP request:

- Method, URL, headers, and body
- Response status code, headers, and body
- Duration in milliseconds
- HTTP library used (requests or httpx)

Smello redacts sensitive headers (`Authorization`, `X-Api-Key`) by default.

## Supported libraries

| Library | What Smello patches |
|---------|---------------------|
| **requests** | `Session.send()` |
| **httpx** | `Client.send()` and `AsyncClient.send()` |

## Python version support

| Package | Python |
|---------|--------|
| **smello** (client SDK) | >= 3.10 |
| **smello-server** | >= 3.14 |
