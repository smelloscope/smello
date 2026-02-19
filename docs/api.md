# API

Smello Server provides a JSON API for exploring captured requests from the command line.

## List requests

```bash
curl -s http://localhost:5110/api/requests | python -m json.tool
```

### Query parameters

| Parameter | Example | Description |
|-----------|---------|-------------|
| `method` | `POST` | Filter by HTTP method |
| `host` | `api.stripe.com` | Filter by hostname |
| `status` | `500` | Filter by response status code |
| `search` | `checkout` | Search by URL substring |
| `limit` | `10` | Max results (default: 50, max: 200) |

Combine filters:

```bash
curl -s 'http://localhost:5110/api/requests?method=POST&host=api.stripe.com&limit=5'
```

## Get request details

Returns headers and bodies for both request and response.

```bash
curl -s http://localhost:5110/api/requests/{id} | python -m json.tool
```

## Clear all requests

```bash
curl -X DELETE http://localhost:5110/api/requests
```
