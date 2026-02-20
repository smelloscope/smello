"""Tests for smello.patches.patch_grpc — gRPC interception."""

import sys
import types
from unittest.mock import MagicMock, patch

import pytest
from smello.config import SmelloConfig
from smello.patches.patch_grpc import (
    _GRPC_STATUS_TO_HTTP,
    _extract_host,
    _grpc_status_to_http,
    _intercept_unary_unary,
    _make_interceptor_class,
    _metadata_to_dict,
    _proto_to_json,
    _send_capture,
    patch_grpc,
)


@pytest.fixture()
def config():
    return SmelloConfig(redact_headers=["authorization", "x-api-key"])


# ---------------------------------------------------------------------------
# _make_mock_grpc helper
# ---------------------------------------------------------------------------


def _make_mock_grpc():
    """Create a mock grpc module with the needed attributes."""
    mock_grpc = types.ModuleType("grpc")
    mock_grpc.insecure_channel = MagicMock(name="insecure_channel")
    mock_grpc.secure_channel = MagicMock(name="secure_channel")
    mock_grpc.intercept_channel = MagicMock(name="intercept_channel")
    mock_grpc.UnaryUnaryClientInterceptor = type("UnaryUnaryClientInterceptor", (), {})
    return mock_grpc


# ---------------------------------------------------------------------------
# patch_grpc()
# ---------------------------------------------------------------------------


def test_patch_skips_when_grpc_not_installed(config):
    """patch_grpc() should return silently when grpc is not importable."""
    with patch.dict(sys.modules, {"grpc": None}):
        patch_grpc(config)


def test_insecure_channel_wraps_with_interceptor(config):
    mock_grpc = _make_mock_grpc()
    original_insecure = mock_grpc.insecure_channel
    mock_channel = MagicMock()
    original_insecure.return_value = mock_channel

    with patch.dict(sys.modules, {"grpc": mock_grpc}):
        patch_grpc(config)

    mock_grpc.insecure_channel("localhost:50051")

    original_insecure.assert_called_once_with(
        "localhost:50051", options=None, compression=None
    )
    mock_grpc.intercept_channel.assert_called_once()
    args = mock_grpc.intercept_channel.call_args
    assert args[0][0] is mock_channel


def test_secure_channel_wraps_with_interceptor(config):
    mock_grpc = _make_mock_grpc()
    original_secure = mock_grpc.secure_channel
    mock_channel = MagicMock()
    original_secure.return_value = mock_channel
    mock_creds = MagicMock()

    with patch.dict(sys.modules, {"grpc": mock_grpc}):
        patch_grpc(config)

    mock_grpc.secure_channel("host:443", mock_creds)

    original_secure.assert_called_once_with(
        "host:443", mock_creds, options=None, compression=None
    )
    mock_grpc.intercept_channel.assert_called_once()
    args = mock_grpc.intercept_channel.call_args
    assert args[0][0] is mock_channel


def test_secure_channel_forwards_options_and_compression(config):
    """Extra kwargs like options should be forwarded to the original."""
    mock_grpc = _make_mock_grpc()
    original_secure = mock_grpc.secure_channel
    original_secure.return_value = MagicMock()
    mock_creds = MagicMock()

    with patch.dict(sys.modules, {"grpc": mock_grpc}):
        patch_grpc(config)

    opts = [("grpc.max_send_message_length", -1)]
    mock_grpc.secure_channel("host:443", mock_creds, options=opts, compression=1)

    original_secure.assert_called_once_with(
        "host:443", mock_creds, options=opts, compression=1
    )


# ---------------------------------------------------------------------------
# _make_interceptor_class()
# ---------------------------------------------------------------------------


def test_make_interceptor_class_inherits_base():
    """Returned class should inherit from the provided base class."""
    base = type("FakeBase", (), {})
    cls = _make_interceptor_class(base)
    assert issubclass(cls, base)


def test_make_interceptor_class_delegates_to_intercept(config):
    """intercept_unary_unary should delegate to _intercept_unary_unary."""
    base = type("FakeBase", (), {})
    cls = _make_interceptor_class(base)
    interceptor = cls(config, "host:443")

    with patch("smello.patches.patch_grpc._intercept_unary_unary") as mock_fn:
        mock_fn.return_value = "result"
        result = interceptor.intercept_unary_unary("cont", "details", "req")

    assert result == "result"
    mock_fn.assert_called_once_with(config, "host:443", "cont", "details", "req")


# ---------------------------------------------------------------------------
# _intercept_unary_unary() — success path
# ---------------------------------------------------------------------------


@patch("smello.transport.send")
@patch("smello.capture.serialize_request_response")
def test_interceptor_captures_successful_call(mock_serialize, mock_send, config):
    call_details = MagicMock()
    call_details.method = "/pkg.Service/Method"
    call_details.metadata = [("x-custom", "val")]

    mock_request = MagicMock()
    mock_request.__str__ = lambda self: "request_str"

    mock_response = MagicMock()
    mock_result = MagicMock()
    mock_result.__str__ = lambda self: "result_str"
    mock_response.result.return_value = mock_result
    mock_response.trailing_metadata.return_value = []

    continuation = MagicMock(return_value=mock_response)
    mock_serialize.return_value = {"id": "test"}

    result = _intercept_unary_unary(
        config, "api.example.com:443", continuation, call_details, mock_request
    )

    assert result is mock_response
    continuation.assert_called_once_with(call_details, mock_request)
    mock_serialize.assert_called_once()

    kw = mock_serialize.call_args[1]
    assert kw["method"] == "POST"
    assert kw["url"] == "grpc://api.example.com:443/pkg.Service/Method"
    assert kw["status_code"] == 200
    assert kw["library"] == "grpc"
    assert kw["request_headers"] == {"x-custom": "val"}

    mock_send.assert_called_once_with({"id": "test"})


@patch("smello.transport.send")
@patch("smello.capture.serialize_request_response")
def test_trailing_metadata_merged_into_response_headers(
    mock_serialize, mock_send, config
):
    """Trailing metadata from the response should appear in response_headers."""
    call_details = MagicMock()
    call_details.method = "/pkg.Service/Method"
    call_details.metadata = None

    mock_response = MagicMock()
    mock_response.result.return_value = MagicMock()
    mock_response.trailing_metadata.return_value = [
        ("x-trace-id", "abc123"),
        ("x-request-id", "def456"),
    ]

    continuation = MagicMock(return_value=mock_response)
    mock_serialize.return_value = {"id": "test"}

    _intercept_unary_unary(config, "host:443", continuation, call_details, MagicMock())

    kw = mock_serialize.call_args[1]
    assert kw["response_headers"]["grpc-status"] == "0"
    assert kw["response_headers"]["grpc-status-name"] == "OK"
    assert kw["response_headers"]["x-trace-id"] == "abc123"
    assert kw["response_headers"]["x-request-id"] == "def456"


@patch("smello.transport.send")
@patch("smello.capture.serialize_request_response")
def test_success_still_returned_when_send_capture_fails(
    mock_serialize, mock_send, config
):
    """If _send_capture raises, the response should still be returned."""
    call_details = MagicMock()
    call_details.method = "/svc/Method"
    call_details.metadata = None

    mock_response = MagicMock()
    mock_response.result.return_value = MagicMock()
    mock_response.trailing_metadata.return_value = []
    continuation = MagicMock(return_value=mock_response)

    mock_serialize.side_effect = RuntimeError("serialize boom")

    result = _intercept_unary_unary(
        config, "host:443", continuation, call_details, MagicMock()
    )

    assert result is mock_response


# ---------------------------------------------------------------------------
# _intercept_unary_unary() — error path
# ---------------------------------------------------------------------------


@patch("smello.transport.send")
@patch("smello.capture.serialize_request_response")
def test_interceptor_captures_error_call(mock_serialize, mock_send, config):
    call_details = MagicMock()
    call_details.method = "/pkg.Service/Method"
    call_details.metadata = None
    mock_request = MagicMock()

    mock_code = MagicMock()
    mock_code.value = (5,)  # NOT_FOUND
    mock_code.name = "NOT_FOUND"

    rpc_error = Exception("not found")
    rpc_error.code = MagicMock(return_value=mock_code)

    mock_response = MagicMock()
    mock_response.result.side_effect = rpc_error

    continuation = MagicMock(return_value=mock_response)
    mock_serialize.return_value = {"id": "err"}

    with pytest.raises(Exception, match="not found"):
        _intercept_unary_unary(
            config, "api.example.com:443", continuation, call_details, mock_request
        )

    mock_serialize.assert_called_once()
    kw = mock_serialize.call_args[1]
    assert kw["status_code"] == 404
    assert kw["response_headers"]["grpc-status"] == "5"
    assert kw["response_headers"]["grpc-status-name"] == "NOT_FOUND"
    mock_send.assert_called_once_with({"id": "err"})


@patch("smello.transport.send")
@patch("smello.capture.serialize_request_response")
def test_error_without_code_attr_falls_back_to_unknown(
    mock_serialize, mock_send, config
):
    """A plain Exception (no .code()) should map to UNKNOWN / 500."""
    call_details = MagicMock()
    call_details.method = "/svc/Method"
    call_details.metadata = None

    plain_error = ValueError("something broke")

    mock_response = MagicMock()
    mock_response.result.side_effect = plain_error
    continuation = MagicMock(return_value=mock_response)
    mock_serialize.return_value = {"id": "unk"}

    with pytest.raises(ValueError, match="something broke"):
        _intercept_unary_unary(
            config, "host:443", continuation, call_details, MagicMock()
        )

    kw = mock_serialize.call_args[1]
    assert kw["status_code"] == 500
    assert kw["response_headers"]["grpc-status"] == "2"
    assert kw["response_headers"]["grpc-status-name"] == "UNKNOWN"
    assert "something broke" in kw["response_body"]


@patch("smello.transport.send")
@patch("smello.capture.serialize_request_response")
def test_error_still_raised_when_send_capture_fails(mock_serialize, mock_send, config):
    """If _send_capture raises on the error path, the original error is still re-raised."""
    call_details = MagicMock()
    call_details.method = "/svc/Method"
    call_details.metadata = None

    rpc_error = Exception("original error")
    mock_response = MagicMock()
    mock_response.result.side_effect = rpc_error
    continuation = MagicMock(return_value=mock_response)

    mock_serialize.side_effect = RuntimeError("capture boom")

    with pytest.raises(Exception, match="original error"):
        _intercept_unary_unary(
            config, "host:443", continuation, call_details, MagicMock()
        )


# ---------------------------------------------------------------------------
# _intercept_unary_unary() — skip path
# ---------------------------------------------------------------------------


@patch("smello.capture.serialize_request_response")
def test_interceptor_skips_ignored_host(mock_serialize, config):
    config.ignore_hosts = ["ignored.example.com"]

    call_details = MagicMock()
    call_details.method = "/pkg.Service/Method"
    mock_request = MagicMock()
    mock_response = MagicMock()
    continuation = MagicMock(return_value=mock_response)

    result = _intercept_unary_unary(
        config, "ignored.example.com:443", continuation, call_details, mock_request
    )

    assert result is mock_response
    mock_serialize.assert_not_called()


@patch("smello.transport.send")
@patch("smello.capture.serialize_request_response")
def test_bytes_method_decoded(mock_serialize, mock_send, config):
    call_details = MagicMock()
    call_details.method = b"/pkg.Service/Method"
    call_details.metadata = None

    mock_response = MagicMock()
    mock_response.result.return_value = MagicMock()
    mock_response.trailing_metadata.return_value = []
    continuation = MagicMock(return_value=mock_response)
    mock_serialize.return_value = {"id": "test"}

    _intercept_unary_unary(config, "host:443", continuation, call_details, MagicMock())

    kw = mock_serialize.call_args[1]
    assert kw["url"] == "grpc://host:443/pkg.Service/Method"


# ---------------------------------------------------------------------------
# _send_capture()
# ---------------------------------------------------------------------------


@patch("smello.transport.send")
@patch("smello.capture.serialize_request_response")
def test_send_capture(mock_serialize, mock_send, config):
    mock_serialize.return_value = {"id": "payload"}

    _send_capture(
        config=config,
        method="POST",
        url="grpc://host:443/svc/Method",
        request_headers={"k": "v"},
        request_body='{"a": 1}',
        status_code=200,
        response_headers={"grpc-status": "0"},
        response_body='{"b": 2}',
        duration_s=0.5,
    )

    mock_serialize.assert_called_once_with(
        config=config,
        method="POST",
        url="grpc://host:443/svc/Method",
        request_headers={"k": "v"},
        request_body='{"a": 1}',
        status_code=200,
        response_headers={"grpc-status": "0"},
        response_body='{"b": 2}',
        duration_s=0.5,
        library="grpc",
    )
    mock_send.assert_called_once_with({"id": "payload"})


# ---------------------------------------------------------------------------
# _grpc_status_to_http()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("grpc_code", "expected_http"),
    list(_GRPC_STATUS_TO_HTTP.items()),
)
def test_grpc_status_to_http_mapping(grpc_code, expected_http):
    assert _grpc_status_to_http(grpc_code) == expected_http


def test_grpc_status_to_http_unknown_code():
    assert _grpc_status_to_http(99) == 500


# ---------------------------------------------------------------------------
# _extract_host()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        ("host:443", "host"),
        ("dns:///host:443", "host"),
        ("dns:///host", "host"),
        ("host", "host"),
        ("dns://authority/host:443", "host"),
        ("ipv4:127.0.0.1:50051", "127.0.0.1"),
    ],
)
def test_extract_host_variants(target, expected):
    assert _extract_host(target) == expected


# ---------------------------------------------------------------------------
# _proto_to_json()
# ---------------------------------------------------------------------------


def test_proto_to_json_fallback():
    obj = MagicMock()
    obj.__str__ = lambda self: "mock_string_repr"

    with patch.dict(sys.modules, {"google.protobuf.json_format": None}):
        result = _proto_to_json(obj)

    assert result == "mock_string_repr"


def test_proto_to_json_with_protobuf():
    mock_json_format = MagicMock()
    mock_json_format.MessageToJson.return_value = '{"field": "value"}'

    with patch.dict(
        sys.modules,
        {
            "google": MagicMock(),
            "google.protobuf": MagicMock(),
            "google.protobuf.json_format": mock_json_format,
        },
    ):
        msg = MagicMock()
        result = _proto_to_json(msg)

    assert result == '{"field": "value"}'


# ---------------------------------------------------------------------------
# _metadata_to_dict()
# ---------------------------------------------------------------------------


def test_metadata_to_dict_none():
    assert _metadata_to_dict(None) == {}


def test_metadata_to_dict_tuples():
    metadata = [("key1", "val1"), ("key2", "val2")]
    assert _metadata_to_dict(metadata) == {"key1": "val1", "key2": "val2"}
