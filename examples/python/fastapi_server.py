"""Demo: FastAPI server with Smello capturing incoming requests, outgoing HTTP, logs, and exceptions.

Start the Smello server first (uv run smello-server), then run this example:

    uv run examples/python/fastapi_server.py

Open http://localhost:8000/docs to try the endpoints, then check
http://localhost:5110 to see everything Smello captured.
"""

import logging

import smello

smello.init(
    server_url="http://localhost:5110",
    capture_logs=True,
    log_level=logging.INFO,
    ignore_loggers=["uvicorn.access", "uvicorn.error"],
)

import httpx
from fastapi import FastAPI, HTTPException
from smello.integrations.fastapi import SmelloMiddleware

app = FastAPI(title="Smello FastAPI Demo")
app.add_middleware(
    SmelloMiddleware,
    ignore_paths=["/docs", "/openapi.json", "/favicon.ico"],
)

logger = logging.getLogger("fastapi_demo")


@app.get("/hello")
def hello(name: str = "world"):
    """Simple endpoint that logs and returns a greeting."""
    logger.info("greeting requested", extra={"name": name})
    return {"message": f"Hello, {name}!"}


@app.get("/fetch")
def fetch_external(url: str = "https://httpbin.org/get"):
    """Makes an outgoing HTTP request so Smello captures both sides."""
    logger.info("fetching external URL", extra={"url": url})
    resp = httpx.get(url, params={"source": "smello-demo"})
    return {"status": resp.status_code, "body": resp.json()}


@app.get("/warn")
def with_warning():
    """Endpoint that emits a warning log."""
    logger.warning("this is a demo warning", extra={"reason": "just testing"})
    return {"ok": True}


@app.get("/error")
def raise_error():
    """Raises an HTTPException (4xx) — captured as a normal response."""
    logger.error("about to return a 404")
    raise HTTPException(status_code=404, detail="item not found")


@app.get("/crash")
def crash():
    """Raises an unhandled exception — Smello captures it with exc_type/exc_value."""
    logger.info("about to crash")
    raise RuntimeError("something went terribly wrong")


if __name__ == "__main__":
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    print(f"Open http://localhost:{args.port}/docs to try the endpoints.")
    print("Open http://localhost:5110 to see what Smello captured.\n")
    uvicorn.run(app, host="0.0.0.0", port=args.port)
