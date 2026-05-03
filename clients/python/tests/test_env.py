"""Tests for smello._env helpers and env-var-based init()."""

import logging
import os
from unittest.mock import patch

import pytest
import smello
from smello._env import _env_bool, _env_list, _env_str

# --- _env_str ---


def test_env_str_returns_value():
    with patch.dict(os.environ, {"SMELLO_URL": "http://example.com:9000"}):
        assert _env_str("URL") == "http://example.com:9000"


def test_env_str_strips_whitespace():
    with patch.dict(os.environ, {"SMELLO_URL": "  http://host:1234  "}):
        assert _env_str("URL") == "http://host:1234"


def test_env_str_returns_none_when_unset():
    with patch.dict(os.environ, {}, clear=True):
        assert _env_str("URL") is None


def test_env_str_returns_none_when_empty():
    with patch.dict(os.environ, {"SMELLO_URL": ""}):
        assert _env_str("URL") is None


def test_env_str_returns_none_when_only_whitespace():
    with patch.dict(os.environ, {"SMELLO_URL": "   "}):
        assert _env_str("URL") is None


# --- _env_bool ---


@pytest.mark.parametrize("value", ["true", "True", "TRUE", "1", "yes", "Yes", "YES"])
def test_env_bool_truthy(value):
    with patch.dict(os.environ, {"SMELLO_CAPTURE_ALL": value}):
        assert _env_bool("CAPTURE_ALL") is True


@pytest.mark.parametrize("value", ["false", "False", "FALSE", "0", "no", "No", "NO"])
def test_env_bool_falsy(value):
    with patch.dict(os.environ, {"SMELLO_CAPTURE_ALL": value}):
        assert _env_bool("CAPTURE_ALL") is False


def test_env_bool_returns_none_when_unset():
    with patch.dict(os.environ, {}, clear=True):
        assert _env_bool("CAPTURE_ALL") is None


def test_env_bool_returns_none_when_empty():
    with patch.dict(os.environ, {"SMELLO_CAPTURE_ALL": ""}):
        assert _env_bool("CAPTURE_ALL") is None


def test_env_bool_returns_none_for_unrecognised():
    with patch.dict(os.environ, {"SMELLO_CAPTURE_ALL": "maybe"}):
        assert _env_bool("CAPTURE_ALL") is None


# --- _env_list ---


def test_env_list_comma_separated():
    with patch.dict(os.environ, {"SMELLO_CAPTURE_HOSTS": "a.com,b.com,c.com"}):
        assert _env_list("CAPTURE_HOSTS") == ["a.com", "b.com", "c.com"]


def test_env_list_strips_items():
    with patch.dict(os.environ, {"SMELLO_CAPTURE_HOSTS": " a.com , b.com "}):
        assert _env_list("CAPTURE_HOSTS") == ["a.com", "b.com"]


def test_env_list_skips_empty_items():
    with patch.dict(os.environ, {"SMELLO_CAPTURE_HOSTS": "a.com,,b.com,"}):
        assert _env_list("CAPTURE_HOSTS") == ["a.com", "b.com"]


def test_env_list_returns_none_when_unset():
    with patch.dict(os.environ, {}, clear=True):
        assert _env_list("CAPTURE_HOSTS") is None


def test_env_list_returns_none_when_empty():
    with patch.dict(os.environ, {"SMELLO_CAPTURE_HOSTS": ""}):
        assert _env_list("CAPTURE_HOSTS") is None


def test_env_list_single_item():
    with patch.dict(os.environ, {"SMELLO_CAPTURE_HOSTS": "api.stripe.com"}):
        assert _env_list("CAPTURE_HOSTS") == ["api.stripe.com"]


# --- init() env var integration ---


def test_init_no_url_does_nothing():
    with patch.dict(os.environ, {}, clear=True):
        smello._config = None
        smello.init()
        assert smello._config is None


def test_init_no_url_logs_warning(caplog):
    with (
        patch.dict(os.environ, {}, clear=True),
        caplog.at_level(logging.WARNING, logger="smello"),
    ):
        smello._config = None
        smello.init()
        assert "server URL" in caplog.text


def test_init_server_url_from_env():
    with (
        patch.dict(os.environ, {"SMELLO_URL": "http://smello:9999"}),
        patch("smello._start_worker"),
        patch("smello._apply_all"),
    ):
        smello._config = None
        smello.init()
        assert smello._config.server_url == "http://smello:9999"


def test_init_explicit_server_url_overrides_env():
    with (
        patch.dict(os.environ, {"SMELLO_URL": "http://from-env:1111"}),
        patch("smello._start_worker"),
        patch("smello._apply_all"),
    ):
        smello._config = None
        smello.init(server_url="http://explicit:2222")
        assert smello._config.server_url == "http://explicit:2222"


def test_init_capture_hosts_from_env():
    with (
        patch.dict(
            os.environ,
            {
                "SMELLO_URL": "http://test:5110",
                "SMELLO_CAPTURE_HOSTS": "a.com,b.com",
            },
        ),
        patch("smello._start_worker"),
        patch("smello._apply_all"),
    ):
        smello._config = None
        smello.init()
        assert smello._config.capture_hosts == ["a.com", "b.com"]


def test_init_ignore_hosts_from_env():
    with (
        patch.dict(
            os.environ,
            {
                "SMELLO_URL": "http://test:5110",
                "SMELLO_IGNORE_HOSTS": "internal.svc,localhost",
            },
        ),
        patch("smello._start_worker"),
        patch("smello._apply_all"),
    ):
        smello._config = None
        smello.init()
        assert "internal.svc" in smello._config.ignore_hosts
        assert "localhost" in smello._config.ignore_hosts


def test_init_redact_headers_from_env():
    with (
        patch.dict(
            os.environ,
            {
                "SMELLO_URL": "http://test:5110",
                "SMELLO_REDACT_HEADERS": "X-Secret,X-Token",
            },
        ),
        patch("smello._start_worker"),
        patch("smello._apply_all"),
    ):
        smello._config = None
        smello.init()
        assert smello._config.redact_headers == ["x-secret", "x-token"]


def test_init_redact_query_params_from_env():
    with (
        patch.dict(
            os.environ,
            {
                "SMELLO_URL": "http://test:5110",
                "SMELLO_REDACT_QUERY_PARAMS": "api_key,token",
            },
        ),
        patch("smello._start_worker"),
        patch("smello._apply_all"),
    ):
        smello._config = None
        smello.init()
        assert smello._config.redact_query_params == ["api_key", "token"]


def test_init_redact_query_params_default_empty():
    with (
        patch.dict(os.environ, {"SMELLO_URL": "http://test:5110"}, clear=True),
        patch("smello._start_worker"),
        patch("smello._apply_all"),
    ):
        smello._config = None
        smello.init()
        assert smello._config.redact_query_params == []


def test_init_redact_headers_default_without_env():
    with (
        patch.dict(os.environ, {"SMELLO_URL": "http://test:5110"}, clear=True),
        patch("smello._start_worker"),
        patch("smello._apply_all"),
    ):
        smello._config = None
        smello.init()
        assert smello._config.redact_headers == ["authorization", "x-api-key"]


def test_init_capture_all_false_from_env():
    with (
        patch.dict(
            os.environ,
            {"SMELLO_URL": "http://test:5110", "SMELLO_CAPTURE_ALL": "false"},
        ),
        patch("smello._start_worker"),
        patch("smello._apply_all"),
    ):
        smello._config = None
        smello.init()
        assert smello._config.capture_all is False


def test_init_defaults_with_explicit_url():
    """With only a URL and no other config, hardcoded defaults apply."""
    with (
        patch.dict(os.environ, {}, clear=True),
        patch("smello._start_worker"),
        patch("smello._apply_all"),
    ):
        smello._config = None
        smello.init(server_url="http://test:5110")
        assert smello._config.server_url == "http://test:5110"
        assert smello._config.capture_all is True
        assert smello._config.capture_hosts == []
        assert "test" in smello._config.ignore_hosts  # auto-added
        assert smello._config.redact_headers == ["authorization", "x-api-key"]
        assert smello._config.redact_query_params == []


# --- init() idempotency ---


def test_init_second_call_does_not_repatch():
    """The second init() call must not re-invoke apply_all.

    Re-applying patches nests wrappers: the second patch captures the
    first patched_send as its original_send, so every request gets
    double-captured.
    """
    with (
        patch.dict(os.environ, {}, clear=True),
        patch("smello._start_worker"),
        patch("smello._apply_all") as mock_apply,
    ):
        smello._config = None
        smello._patched = False
        smello.init(server_url="http://test:5110")
        smello.init(server_url="http://other:5110")
        assert mock_apply.call_count == 1


def test_init_second_call_updates_config_in_place():
    """The same SmelloConfig object must survive the second init().

    Patches captured a reference to it via closure; mutating in place
    means new args (filtering, redaction) take effect immediately
    without re-patching.
    """
    with (
        patch.dict(os.environ, {}, clear=True),
        patch("smello._start_worker"),
        patch("smello._apply_all"),
    ):
        smello._config = None
        smello._patched = False
        smello.init(
            server_url="http://test:5110",
            ignore_hosts=["a.com"],
            capture_all=True,
        )
        first_config = smello._config

        smello.init(
            server_url="http://other:5110",
            ignore_hosts=["b.com"],
            capture_all=False,
        )

        assert smello._config is first_config  # same object, mutated
        assert smello._config.server_url == "http://other:5110"
        assert "b.com" in smello._config.ignore_hosts
        assert "a.com" not in smello._config.ignore_hosts
        assert smello._config.capture_all is False
