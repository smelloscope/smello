# HTTP Library Patching Guide

Lessons learned from building patches for requests, httpx, botocore, gRPC,
and aiohttp.  Read this before adding a new patch or modifying an existing one.


## 1. Choosing a patch point

The patch point determines how much work you do yourself.  Three tiers, from
best to worst:

### Tier 1: Library-provided instrumentation hooks (best)

Some libraries have a first-class signal/tracing API.  aiohttp has
`TraceConfig`, which provides lifecycle signals (`on_request_start`,
`on_request_end`, `on_request_redirect`, `on_request_exception`, etc.).
These signals fire at the right points in the lifecycle — after headers are
merged, after URLs are resolved, per redirect hop, on errors.

**Our aiohttp patch uses this approach** (following the Sentry Python SDK
pattern): patch `ClientSession.__init__` to inject a `TraceConfig`, then
handle everything via signals.

Advantages:
- Merged headers, resolved URLs, correct method per hop — all by construction
- Redirect hops, `raise_for_status` errors — handled via dedicated signals
- Minimal monkey-patching (only `__init__`, not internal methods)
- Composes with other instrumentors (multiple TraceConfigs can coexist)

### Tier 2: Low-level `send(prepared_request)` (good)

If the library has a method like `Session.send(prepared_request)` where the
request is fully built — headers merged, body serialized, URL resolved — patch
that.  **Our requests, httpx, and botocore patches use this approach.**

Advantages:
- Headers, body, URL are already correct — no re-serialization needed
- Redirects often call `send()` per hop (requests and httpx do), so each hop
  is captured automatically

Disadvantages vs Tier 1:
- You're replacing an internal method, not using a public API
- Must handle streaming response bodies yourself (botocore does this well)

### Tier 3: High-level orchestrator (avoid)

Patching a method like `_request(method, url, **kwargs)` that receives raw
kwargs and does all preparation internally.  **Our aiohttp patch originally
used this approach** and required 6 rounds of review fixes.

Every item in the checklist below must be handled manually.  Avoid unless
no better option exists.

### When evaluating a new library

1. Check for a tracing/instrumentation API (signals, hooks, middleware)
2. Check what the Sentry Python SDK does — `sentry_sdk/integrations/`
3. Look for a `send(prepared_request)` style method
4. Only fall back to high-level patching as a last resort


## 2. Checklist

### Request data

- [ ] **Headers**: Capture the actual headers sent on the wire, not just
  what the caller passed.  Session defaults, auth, cookies, and
  Content-Type are added by the library.  Prefer `request_info.headers`,
  `prepared_request.headers`, or a signal that fires after merge.

- [ ] **Request body**: If intercepting raw kwargs (`json=`, `data=`),
  the library handles serialization — your re-serialization may differ
  (custom `json_serialize`, FormData).  Prefer observing the actual bytes
  sent (e.g. `on_request_chunk_sent`), or reading from the built request
  object.

- [ ] **Large/streaming uploads**: Cap accumulated body data (we use 1 MB).
  Beyond the cap, use a placeholder like `"[large upload]"`.  File-like
  and generator bodies get `"[file upload]"`.

### Response data

- [ ] **Don't consume the stream**: Never eagerly call `response.read()` if
  it would exhaust a stream the caller needs (SSE, chunked downloads).
  Options: observe via a signal (`on_response_chunk_received`), wrap
  `read()` to capture lazily, read from a post-read cache, or use
  `"[streaming response]"` as a placeholder.

- [ ] **Fallback for unread responses**: If the caller never calls `read()`
  (streaming, or `close()` without reading), you still need to capture the
  request metadata.  Hook `release()` and `close()` as fallbacks — both
  are separate code paths.

- [ ] **Error responses**: If the library raises on error status codes inside
  the patched method (e.g. aiohttp's `raise_for_status=True`), the response
  is never returned.  Catch the exception, capture from its metadata, and
  re-raise — or use a signal like `on_request_exception`.

### URL and host filtering

- [ ] **URL resolution**: If the library supports `base_url`, the URL may be
  relative (no hostname).  Either use a signal that fires after resolution,
  or defer `should_capture()` until the resolved URL is available.

- [ ] **Redirects**: If the patched method follows redirects internally, only
  the final response is visible.  Use `on_request_redirect` (signal) or
  `response.history` (post-hoc) to capture intermediate 3xx hops.

- [ ] **Method changes on redirect**: 301/302/303 change POST → GET.
  307/308 preserve the method and body.  The final capture must use the
  post-redirect method, not the original.

### Timing

- [ ] **Measure duration at capture time**: For async libraries, the response
  headers may arrive before the body.  Measure `duration` when you actually
  send the capture (after body is read or on release), not when headers
  arrive.

### General

- [ ] **Fail-safe**: All capture logic must be in try/except.  A bug in the
  patch must never break the caller's HTTP call.

- [ ] **No dependencies**: The smello client SDK has zero dependencies.
  Transport uses `urllib.request` to avoid triggering its own patches.

- [ ] **Graceful skip**: `try: import lib except ImportError: return`.

- [ ] **Async support**: Patch both sync and async APIs if the library has
  both.


## 3. Common pitfalls

**Signal names can be misleading.**  aiohttp's `on_response_chunk_received`
sounds like it fires per chunk, but it actually fires once inside
`response.read()` with the complete body.  Always verify behavior against
the library source code, not just the name.

**AI code reviewers can be wrong about library internals.**  We had multiple
review rounds where the reviewer made incorrect claims about aiohttp's
behavior (e.g. that `on_response_chunk_received` fires per-chunk, or that
307/308 redirects don't re-fire `on_request_chunk_sent`).  Verify claims
against the actual source before making changes.

**Module reloading in tests is tricky.**  For aiohttp, `importlib.reload(aiohttp)`
doesn't reload `aiohttp.client` (where `ClientSession` lives).  You need
`importlib.reload(aiohttp.client)` followed by `importlib.reload(aiohttp)`.

**`trace_config_ctx_factory`** lets you define a typed context class instead
of setting attributes ad-hoc on a `SimpleNamespace`.  Pre-initialized state
eliminates `getattr`/`hasattr` guards.


## 4. Reference: current patches

| Library    | Approach     | Patch point                              |
|------------|-------------|------------------------------------------|
| requests   | Tier 2      | `Session.send(prepared_request)`         |
| httpx      | Tier 2      | `Client.send(request)` + `AsyncClient.send(request)` |
| botocore   | Tier 2      | `URLLib3Session.send(request)`           |
| grpc       | Tier 2      | Channel wrapping via interceptor         |
| aiohttp    | Tier 1      | `TraceConfig` signals via `__init__` patch |
