# Integration guides

Practical walkthroughs for debugging specific libraries and frameworks with Smello.
Each guide shows a real scenario, the setup needed, and what you'll see in the dashboard.

## Outgoing HTTP (auto-patched)

These libraries are monkey-patched automatically when you use `smello run`.

- [Debug requests](debug-requests.md): inspect headers, bodies, and redirects
- [Debug httpx](debug-httpx.md): async and sync HTTP debugging
- [Debug aiohttp](debug-aiohttp.md): async HTTP client debugging
- [Debug gRPC](debug-grpc.md): see protobuf payloads as JSON
- [Debug boto3 / AWS](debug-boto3.md): AWS API calls and XML responses
- [Debug Google Cloud](debug-google-cloud.md): BigQuery, Firestore, Pub/Sub via gRPC

## SDKs that use patched libraries under the hood

These SDKs use `httpx` or `requests` internally, so Smello captures their traffic automatically.

- [Debug OpenAI](debug-openai.md): see raw API calls behind the SDK
- [Debug Anthropic](debug-anthropic.md): inspect Claude API requests
- [Debug Stripe](debug-stripe.md): webhook debugging and API call inspection

## Server frameworks (middleware)

Explicit middleware for capturing incoming HTTP requests.

- [Debug FastAPI](debug-fastapi.md): incoming request inspection and exception capture
