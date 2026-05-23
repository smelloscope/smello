"""Demo: Django server with Smello capturing incoming requests, outgoing HTTP, logs, and exceptions.

Start the Smello server first (uv run smello-server), then run this example:

    uv run examples/python/django_server.py

Open http://localhost:8000/ to try the endpoints, then check
http://localhost:5110 to see everything Smello captured.
"""

import logging

import smello

smello.init(
    server_url="http://localhost:5110",
    capture_logs=True,
    log_level=logging.INFO,
    ignore_loggers=["django.server", "django.request"],
)

import django  # noqa: E402
from django.conf import settings  # noqa: E402

settings.configure(
    DEBUG=True,
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=["*"],
    SECRET_KEY="smello-demo",
    MIDDLEWARE=[
        "smello.integrations.django.SmelloMiddleware",
    ],
    SMELLO_IGNORE_PATHS=["/favicon.ico"],
)
django.setup()

import httpx  # noqa: E402
from django.http import Http404, HttpResponse, JsonResponse  # noqa: E402
from django.urls import path, reverse  # noqa: E402

demo_logger = logging.getLogger("django_demo")

ENDPOINTS = [
    ("hello", "Simple greeting (try ?name=Alice)"),
    ("fetch", "Outgoing HTTP call (captures both sides)"),
    ("warn", "Emits a warning log"),
    ("error", "Returns a 404 via Http404"),
    ("crash", "Raises an unhandled RuntimeError"),
]


def index(request):
    """Landing page with links to all demo endpoints."""
    links = "".join(
        f'<li><a href="{reverse(name)}">{reverse(name)}</a> — {desc}</li>'
        for name, desc in ENDPOINTS
    )
    html = (
        "<h1>Smello Django Demo</h1>"
        f"<ul>{links}</ul>"
        '<p>Open <a href="http://localhost:5110">localhost:5110</a>'
        " to see what Smello captured.</p>"
    )
    return HttpResponse(html)


def hello(request):
    """Simple endpoint that logs and returns a greeting."""
    name = request.GET.get("name", "world")
    demo_logger.info("greeting requested", extra={"name": name})
    return JsonResponse({"message": f"Hello, {name}!"})


def fetch_external(request):
    """Makes an outgoing HTTP request so Smello captures both sides."""
    url = request.GET.get("url", "https://httpbin.org/get")
    demo_logger.info("fetching external URL", extra={"url": url})
    resp = httpx.get(url, params={"source": "smello-demo"})
    return JsonResponse({"status": resp.status_code, "body": resp.json()})


def with_warning(request):
    """Endpoint that emits a warning log."""
    demo_logger.warning("this is a demo warning", extra={"reason": "just testing"})
    return JsonResponse({"ok": True})


def raise_error(request):
    """Raises Http404 — captured as a normal 404 response."""
    demo_logger.error("about to return a 404")
    raise Http404("item not found")


def crash(request):
    """Raises an unhandled exception — Smello captures it with exc_type/exc_value."""
    demo_logger.info("about to crash")
    raise RuntimeError("something went terribly wrong")


urlpatterns = [
    path("", index),
    path("hello", hello, name="hello"),
    path("fetch", fetch_external, name="fetch"),
    path("warn", with_warning, name="warn"),
    path("error", raise_error, name="error"),
    path("crash", crash, name="crash"),
]

if __name__ == "__main__":
    import argparse

    from django.core.management import execute_from_command_line

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    print(f"Open http://localhost:{args.port}/ to try the endpoints.")
    print("Open http://localhost:5110 to see what Smello captured.\n")
    execute_from_command_line(["", "runserver", f"0.0.0.0:{args.port}", "--noreload"])
