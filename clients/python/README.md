# Smello

Capture outgoing HTTP requests from your Python code and browse them in a local web dashboard.

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

Smello monkey-patches `requests` and `httpx` to capture all outgoing HTTP traffic. Browse results at `http://localhost:5110`.

## What Smello Captures

- Method, URL, headers, and body
- Response status code, headers, and body
- Duration in milliseconds
- HTTP library used (requests or httpx)

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

## Supported Libraries

- **requests** — patches `Session.send()`
- **httpx** — patches `Client.send()` and `AsyncClient.send()`

## Requires

- Python >= 3.10
- [smello-server](https://pypi.org/project/smello-server/) running locally

## Links

- [Documentation & Source](https://github.com/smelloscope/smello)
- [smello-server on PyPI](https://pypi.org/project/smello-server/)
