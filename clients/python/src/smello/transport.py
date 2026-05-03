"""Background transport: sends captured events to the Smello server without blocking."""

import json
import logging
import queue
import threading
import urllib.request

logger = logging.getLogger(__name__)

# Each queue item is (path, payload). The worker uses the path to choose
# the typed capture endpoint.
_queue: queue.Queue[tuple[str, dict]] = queue.Queue(maxsize=1000)
_server_url: str = ""
_started: bool = False


def start_worker(server_url: str) -> None:
    """Start the background worker thread."""
    global _server_url, _started
    _server_url = server_url

    if _started:
        return
    _started = True

    thread = threading.Thread(target=_worker, daemon=True, name="smello-transport")
    thread.start()


def send_http(payload: dict) -> None:
    """Queue an HTTP capture payload for `/api/capture/http`."""
    _enqueue("/api/capture/http", payload)


def send_log(data: dict) -> None:
    """Queue a log capture payload for `/api/capture/log`."""
    _enqueue("/api/capture/log", {"data": data})


def send_exception(data: dict) -> None:
    """Queue an exception capture payload for `/api/capture/exception`."""
    _enqueue("/api/capture/exception", {"data": data})


def flush(timeout: float = 2.0) -> bool:
    """Block until all queued payloads are sent, or *timeout* seconds elapse.

    Returns ``True`` if the queue drained in time, ``False`` otherwise.
    """
    # Queue.join() has no timeout parameter. Access the underlying
    # condition variable directly — same technique Sentry's SDK uses.
    with _queue.all_tasks_done:
        if _queue.unfinished_tasks:
            logger.debug("Flushing %d pending capture(s)…", _queue.unfinished_tasks)
            _queue.all_tasks_done.wait(timeout=timeout)

    drained = _queue.unfinished_tasks == 0
    if not drained:
        logger.warning(
            "Flush timed out with %d capture(s) still pending",
            _queue.unfinished_tasks,
        )
    return drained


def shutdown(timeout: float = 2.0) -> bool:
    """Flush pending payloads then stop accepting new ones.

    Returns ``True`` if the queue drained in time, ``False`` otherwise.
    """
    return flush(timeout=timeout)


def _enqueue(path: str, payload: dict) -> None:
    try:
        _queue.put_nowait((path, payload))
    except queue.Full:
        logger.warning("Payload dropped: capture queue is full")


def _worker() -> None:
    """Background worker that sends queued payloads to the server."""
    while True:
        path, payload = _queue.get()
        try:
            _send_to_server(path, payload)
        except Exception as err:
            logger.warning("Failed to send capture to %s: %s", _server_url, err)
        _queue.task_done()


def _send_to_server(path: str, payload: dict) -> None:
    """Send a payload to the Smello server using urllib (to avoid recursion)."""
    data = json.dumps(payload, default=_json_default).encode("utf-8")
    req = urllib.request.Request(
        f"{_server_url}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req, timeout=5)


def _json_default(obj: object) -> str:
    """Fallback serializer for types that json.dumps cannot handle (e.g. bytes)."""
    try:
        return repr(obj)
    except Exception:
        return "<unserializable>"
