# Smello Server

A local web dashboard for inspecting outgoing HTTP requests captured by the [smello](https://pypi.org/project/smello/) client SDK — including gRPC calls made by Google Cloud libraries.

## Setup

```bash
pip install smello-server
smello-server run
```

The dashboard opens at `http://localhost:5110`.

Or with Docker:

```bash
docker run -p 5110:5110 ghcr.io/smelloscope/smello
```

Then add the client SDK to your Python code:

```bash
pip install smello
```

```python
import smello
smello.init()

# All outgoing requests are now captured (HTTP and gRPC)
```

## API

Smello Server provides a JSON API for exploring captured requests from the command line.

```bash
# List all captured requests
curl -s http://localhost:5110/api/requests | python -m json.tool

# Filter by method, host, status, or URL substring
curl -s 'http://localhost:5110/api/requests?method=POST&host=api.stripe.com'

# Get full request/response details
curl -s http://localhost:5110/api/requests/{id} | python -m json.tool

# Clear all requests
curl -X DELETE http://localhost:5110/api/requests
```

## CLI Options

```bash
smello-server run --host 0.0.0.0 --port 5110 --db-path /tmp/smello.db
```

## Requires

- Python >= 3.14

## Links

- [Documentation & Source](https://github.com/smelloscope/smello)
- [smello client SDK on PyPI](https://pypi.org/project/smello/)
