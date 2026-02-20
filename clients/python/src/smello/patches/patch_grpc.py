"""Monkey-patch for the `grpc` library (unary-unary calls)."""

import logging
import time

from smello.config import SmelloConfig

logger = logging.getLogger(__name__)

_GRPC_STATUS_TO_HTTP = {
    0: 200,  # OK
    1: 499,  # CANCELLED
    2: 500,  # UNKNOWN
    3: 400,  # INVALID_ARGUMENT
    4: 504,  # DEADLINE_EXCEEDED
    5: 404,  # NOT_FOUND
    6: 409,  # ALREADY_EXISTS
    7: 403,  # PERMISSION_DENIED
    8: 429,  # RESOURCE_EXHAUSTED
    9: 400,  # FAILED_PRECONDITION
    10: 409,  # ABORTED
    11: 400,  # OUT_OF_RANGE
    12: 501,  # UNIMPLEMENTED
    13: 500,  # INTERNAL
    14: 503,  # UNAVAILABLE
    15: 500,  # DATA_LOSS
    16: 401,  # UNAUTHENTICATED
}


def patch_grpc(config: SmelloConfig) -> None:
    """Patch grpc.insecure_channel and grpc.secure_channel to capture unary-unary calls."""
    try:
        import grpc
    except ImportError:
        return  # grpc not installed, skip

    # Define interceptor class here so it can inherit from the real
    # grpc.UnaryUnaryClientInterceptor (required by grpc.intercept_channel).
    Interceptor = _make_interceptor_class(grpc.UnaryUnaryClientInterceptor)

    original_insecure = grpc.insecure_channel
    original_secure = grpc.secure_channel

    def patched_insecure_channel(target, options=None, compression=None):
        channel = original_insecure(target, options=options, compression=compression)
        return grpc.intercept_channel(channel, Interceptor(config, target))

    def patched_secure_channel(target, credentials, options=None, compression=None):
        channel = original_secure(
            target, credentials, options=options, compression=compression
        )
        return grpc.intercept_channel(channel, Interceptor(config, target))

    grpc.insecure_channel = patched_insecure_channel  # type: ignore[assignment]
    grpc.secure_channel = patched_secure_channel  # type: ignore[assignment]


def _grpc_status_to_http(code_value: int) -> int:
    return _GRPC_STATUS_TO_HTTP.get(code_value, 500)


def _extract_host(target: str) -> str:
    """Extract hostname from a gRPC target string, stripping prefixes and port."""
    # Strip common gRPC target prefixes
    for prefix in ("dns:///", "dns://", "ipv4:", "ipv6:", "unix:"):
        if target.startswith(prefix):
            target = target[len(prefix) :]
            break

    # dns://authority/host — strip the authority component
    if "/" in target:
        target = target.rsplit("/", 1)[-1]

    # Remove port
    if ":" in target:
        target = target.rsplit(":", 1)[0]

    return target


def _metadata_to_dict(metadata) -> dict:
    """Convert gRPC metadata (list of tuples) to a dict."""
    if metadata is None:
        return {}
    return {k: v for k, v in metadata}


def _proto_to_json(message) -> str:
    """Convert a protobuf message to JSON string, falling back to str()."""
    try:
        from google.protobuf.json_format import MessageToJson

        return MessageToJson(message)
    except Exception:
        return str(message)


def _make_interceptor_class(base_class):
    """Create the interceptor class with the correct gRPC base class.

    We can't inherit from grpc.UnaryUnaryClientInterceptor at module level
    because grpc is an optional dependency. This factory is called from
    patch_grpc() after grpc has been successfully imported.
    """

    class _SmelloInterceptor(base_class):
        """gRPC unary-unary client interceptor that captures calls."""

        def __init__(self, config: SmelloConfig, target: str):
            self._config = config
            self._target = target

        def intercept_unary_unary(self, continuation, client_call_details, request):
            return _intercept_unary_unary(
                self._config, self._target, continuation, client_call_details, request
            )

    return _SmelloInterceptor


def _intercept_unary_unary(config, target, continuation, client_call_details, request):
    host = _extract_host(target)

    if not config.should_capture(host):
        return continuation(client_call_details, request)

    method = client_call_details.method
    if isinstance(method, bytes):
        method = method.decode("utf-8")

    url = f"grpc://{target}{method}"

    request_headers = _metadata_to_dict(client_call_details.metadata)
    request_body = _proto_to_json(request)

    start = time.monotonic()
    try:
        response = continuation(client_call_details, request)
        result = response.result()
        duration = time.monotonic() - start

        status_code = _grpc_status_to_http(0)
        response_body = _proto_to_json(result)
        response_headers = {
            "grpc-status": "0",
            "grpc-status-name": "OK",
        }
        trailing = getattr(response, "trailing_metadata", None)
        if callable(trailing):
            trailing = trailing()
        if trailing:
            response_headers.update(_metadata_to_dict(trailing))
    except Exception as err:
        duration = time.monotonic() - start

        grpc_code = 2  # UNKNOWN
        grpc_name = "UNKNOWN"
        response_body = str(err)

        if hasattr(err, "code") and callable(err.code):
            code_obj = err.code()  # type: ignore[call-top-callable]
            if hasattr(code_obj, "value"):
                grpc_code = code_obj.value[0]  # type: ignore[not-subscriptable]
                grpc_name = code_obj.name if hasattr(code_obj, "name") else grpc_name

        status_code = _grpc_status_to_http(grpc_code)
        response_headers = {
            "grpc-status": str(grpc_code),
            "grpc-status-name": grpc_name,
        }

        try:
            _send_capture(
                config=config,
                method="POST",
                url=url,
                request_headers=request_headers,
                request_body=request_body,
                status_code=status_code,
                response_headers=response_headers,
                response_body=response_body,
                duration_s=duration,
            )
        except Exception as capture_err:
            logger.debug("Failed to capture gRPC request: %s", capture_err)

        raise

    try:
        _send_capture(
            config=config,
            method="POST",
            url=url,
            request_headers=request_headers,
            request_body=request_body,
            status_code=status_code,
            response_headers=response_headers,
            response_body=response_body,
            duration_s=duration,
        )
    except Exception as capture_err:
        logger.debug("Failed to capture gRPC request: %s", capture_err)

    return response


def _send_capture(
    config: SmelloConfig,
    method: str,
    url: str,
    request_headers: dict,
    request_body: str,
    status_code: int,
    response_headers: dict,
    response_body: str,
    duration_s: float,
) -> None:
    from smello import capture as _capture
    from smello import transport as _transport

    payload = _capture.serialize_request_response(
        config=config,
        method=method,
        url=url,
        request_headers=request_headers,
        request_body=request_body,
        status_code=status_code,
        response_headers=response_headers,
        response_body=response_body,
        duration_s=duration_s,
        library="grpc",
    )
    _transport.send(payload)
