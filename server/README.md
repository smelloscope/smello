<p align="center">
  <img src="https://raw.githubusercontent.com/smelloscope/smello/main/docs/assets/logo.png" alt="Smello logo" width="160">
</p>

# Smello Server

A local web dashboard for inspecting HTTP requests, logs, and exceptions captured by the [smello](https://pypi.org/project/smello/) client SDK.

## Setup

```bash
pip install smello-server
smello-server
```

Or run with Docker:

```bash
docker run -p 5110:5110 ghcr.io/smelloscope/smello
```

The server listens at `http://localhost:5110`.

Then add the client SDK to your Python code:

```bash
pip install smello
```

```python
import smello
smello.init(server_url="http://localhost:5110")

# HTTP requests, unhandled exceptions, and (optionally) log records
# are now captured and visible in the dashboard
```

Or run any program without code changes:

```bash
smello run --server http://localhost:5110 my_app.py
```

## API

Smello Server provides a JSON API for exploring captured events from the command line.

```bash
# List all captured events (unified timeline)
curl -s http://localhost:5110/api/events | python -m json.tool

# Filter by event type (http, log, exception)
curl -s 'http://localhost:5110/api/events?event_type=exception'

# Filter by method, host, status, or full-text search
curl -s 'http://localhost:5110/api/events?method=POST&host=api.stripe.com'

# Get full event details
curl -s http://localhost:5110/api/events/{id} | python -m json.tool

# Clear all events
curl -X DELETE http://localhost:5110/api/events
```

## CLI Options

```bash
smello-server --host 0.0.0.0 --port 5110 --db-path /tmp/smello.db
```

## Requires

- Python >= 3.14

## Links

- [Documentation & Source](https://github.com/smelloscope/smello)
- [smello client SDK on PyPI](https://pypi.org/project/smello/)
