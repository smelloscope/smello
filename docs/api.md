# API

Smello Server provides a JSON API for exploring captured requests from the command line.

The full OpenAPI specification is available at [http://localhost:5110/openapi.json](http://localhost:5110/openapi.json), and an interactive playground at [http://localhost:5110/docs](http://localhost:5110/docs).

## List requests

```bash
curl -s http://localhost:5110/api/requests | python -m json.tool
```

### Query parameters

| Parameter | Example          | Description                         |
| --------- | ---------------- | ----------------------------------- |
| `method`  | `POST`           | Filter by HTTP method               |
| `host`    | `api.stripe.com` | Filter by hostname                  |
| `status`  | `500`            | Filter by response status code      |
| `search`  | `checkout`       | Full-text search across URLs, headers, and bodies |
| `limit`   | `10`             | Max results (default: 50, max: 200) |

Combine filters:

```bash
curl -s 'http://localhost:5110/api/requests?method=POST&host=api.stripe.com&limit=5'
```

## Get request details

Returns headers and bodies for both request and response.

```bash
curl -s http://localhost:5110/api/requests/{id} | python -m json.tool
```

## Get filter metadata

Returns distinct hosts and methods for populating filter dropdowns.

```bash
curl -s http://localhost:5110/api/meta | python -m json.tool
```

## Clear all requests

```bash
curl -X DELETE http://localhost:5110/api/requests
```
