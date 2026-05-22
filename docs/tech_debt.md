# Tech Debt

## Testability: replace `patch("smello._config")` with a proper abstraction

**Problem.** Client SDK tests patch `smello._config` and transport functions directly via `unittest.mock.patch`. This applies across the board — FastAPI integration tests, httpx/grpc/aiohttp patch tests, and any future integration. Every test file needs to know the exact internal module path where the transport function is imported. This couples tests to internal module layout and makes refactoring fragile.

**Desired state.** A first-class way to inject a test-friendly transport without patching internals. For example:

- A swappable transport abstraction (`SmelloConfig(transport=...)`) so tests can pass a recording/mock transport at init time.
- Or a test helper like `smello.init_test()` that returns a collector object, wiring everything up without starting the background thread.

Either approach would let tests inspect captured payloads without knowing where `_config` or `send_http` live internally.
