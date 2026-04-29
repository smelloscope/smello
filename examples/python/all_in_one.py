"""Demo: exercise every Smello capture type — HTTP, logs, and exceptions.

Run this with a Smello server on :5110, then open http://localhost:5110 to see
the unified timeline of HTTP requests, log records, and the unhandled exception.
"""

import logging
import time

import smello

smello.init(
    server_url="http://localhost:5110",
    capture_logs=True,
    log_level=logging.INFO,
)

import requests

logger = logging.getLogger("all_in_one")

# --- HTTP requests ---------------------------------------------------------

resp = requests.get("https://httpbin.org/get", params={"tool": "smello"})
print(f"GET  /get          → {resp.status_code}")

resp = requests.post("https://httpbin.org/post", json={"hello": "world"})
print(f"POST /post         → {resp.status_code}")

resp = requests.get("https://httpbin.org/status/404")
print(f"GET  /status/404   → {resp.status_code}")

# --- Log records -----------------------------------------------------------

logger.info("starting checkout flow", extra={"order_id": 42})
logger.warning("payment retry scheduled", extra={"attempt": 2})
logger.error("payment provider returned 500", extra={"provider": "stripe"})

# --- Unhandled exception (must come last; flushes the queue and exits) -----


def charge_card(amount_cents: int) -> None:
    if amount_cents <= 0:
        raise RuntimeError(f"invalid charge amount: {amount_cents}")
    raise RuntimeError("payment provider rejected the charge")


def process_payment(order_id: int, amount_cents: int) -> None:
    logger.info("processing payment", extra={"order_id": order_id})
    charge_card(amount_cents)


def checkout(order_id: int) -> None:
    process_payment(order_id, amount_cents=4999)


time.sleep(1)  # let the background thread flush HTTP + log events first
print("\nOpen http://localhost:5110 to see HTTP requests, logs, and the exception.")

checkout(order_id=42)
