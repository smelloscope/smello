# Configuration

`smello.init()` accepts these parameters:

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

## Parameters

### `server_url`

URL of the Smello server. Default: `http://localhost:5110`.

### `capture_hosts`

List of hostnames to capture. When set, Smello only captures requests to these hosts and ignores everything else.

### `capture_all`

Capture requests to all hosts. Default: `True`. Set to `False` when using `capture_hosts`.

### `ignore_hosts`

List of hostnames to skip. Smello always ignores the server's own hostname to prevent recursion.

### `redact_headers`

Header names whose values are replaced with `[REDACTED]`. Default: `["Authorization", "X-Api-Key"]`.

### `enabled`

Master switch. Set to `False` to disable all capturing. Default: `True`.

## Server CLI options

```bash
smello-server run --host 0.0.0.0 --port 5110 --db-path /tmp/smello.db
```

| Flag | Default | Description |
|------|---------|-------------|
| `--host` | `127.0.0.1` | Bind address |
| `--port` | `5110` | Port |
| `--db-path` | `smello.db` | SQLite database file |
