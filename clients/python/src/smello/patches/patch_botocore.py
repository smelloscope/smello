"""Monkey-patch for ``botocore`` (used by boto3 / AWS CLI).

botocore uses ``urllib3`` directly (not ``requests``), so the requests patch
does not cover AWS SDK traffic.  We patch
``botocore.httpsession.URLLib3Session.send`` to capture every HTTP call that
boto3 makes to AWS services.
"""

import logging
import time
from urllib.parse import urlparse

from smello.capture import serialize_request_response
from smello.config import SmelloConfig
from smello.transport import send

logger = logging.getLogger(__name__)


def _decode_headers(headers: dict) -> dict[str, str]:
    """Decode botocore header values from bytes to str."""
    return {
        k: v.decode("utf-8", errors="replace") if isinstance(v, bytes) else str(v)
        for k, v in headers.items()
    }


def patch_botocore(config: SmelloConfig) -> None:
    """Patch botocore's HTTP session to capture outgoing AWS traffic."""
    try:
        from botocore.httpsession import URLLib3Session  # noqa: PLC0415
    except ImportError:
        return  # botocore not installed, skip

    original_send = URLLib3Session.send

    def patched_send(self, request):
        host = urlparse(request.url).hostname or ""

        if not config.should_capture(host):
            return original_send(self, request)

        start = time.monotonic()
        response = original_send(self, request)
        duration = time.monotonic() - start

        try:
            # Read the body — for non-streaming responses this is already
            # buffered; for streaming ones (e.g. S3 GetObject) we read what
            # is available without consuming the stream the caller needs.
            response_body: str | bytes | None = None
            if response._content is not None:
                response_body = response.content
            else:
                # Streaming response — don't consume the stream.  Record
                # a placeholder so the request still shows up in the UI.
                response_body = "[streaming response]"

            request_body: str | bytes | None = None
            if request.body is not None:
                if isinstance(request.body, (str, bytes)):
                    request_body = request.body
                else:
                    # File-like upload body — don't read it
                    request_body = "[file upload]"

            payload = serialize_request_response(
                config=config,
                method=request.method,
                url=request.url,
                request_headers=_decode_headers(request.headers),
                request_body=request_body,
                status_code=response.status_code,
                response_headers=dict(response.headers),
                response_body=response_body,
                duration_s=duration,
                library="botocore",
            )
            send(payload)
        except Exception as err:
            logger.debug("Failed to capture botocore request: %s", err)

        return response

    URLLib3Session.send = patched_send  # type: ignore[assignment]
