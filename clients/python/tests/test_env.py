"""Tests for smello._env helpers and env-var-based init()."""

import logging
import os
from unittest.mock import patch

import pytest
import smello
from smello._env import _env_bool, _env_list, _env_str

# --- _env_str ---


class TestEnvStr:
    def test_returns_value(self):
        with patch.dict(os.environ, {"SMELLO_URL": "http://example.com:9000"}):
            assert _env_str("URL") == "http://example.com:9000"

    def test_strips_whitespace(self):
        with patch.dict(os.environ, {"SMELLO_URL": "  http://host:1234  "}):
            assert _env_str("URL") == "http://host:1234"

    def test_returns_none_when_unset(self):
        with patch.dict(os.environ, {}, clear=True):
            assert _env_str("URL") is None

    def test_returns_none_when_empty(self):
        with patch.dict(os.environ, {"SMELLO_URL": ""}):
            assert _env_str("URL") is None

    def test_returns_none_when_only_whitespace(self):
        with patch.dict(os.environ, {"SMELLO_URL": "   "}):
            assert _env_str("URL") is None


# --- _env_bool ---


class TestEnvBool:
    @pytest.mark.parametrize(
        "value", ["true", "True", "TRUE", "1", "yes", "Yes", "YES"]
    )
    def test_truthy(self, value):
        with patch.dict(os.environ, {"SMELLO_CAPTURE_ALL": value}):
            assert _env_bool("CAPTURE_ALL") is True

    @pytest.mark.parametrize(
        "value", ["false", "False", "FALSE", "0", "no", "No", "NO"]
    )
    def test_falsy(self, value):
        with patch.dict(os.environ, {"SMELLO_CAPTURE_ALL": value}):
            assert _env_bool("CAPTURE_ALL") is False

    def test_returns_none_when_unset(self):
        with patch.dict(os.environ, {}, clear=True):
            assert _env_bool("CAPTURE_ALL") is None

    def test_returns_none_when_empty(self):
        with patch.dict(os.environ, {"SMELLO_CAPTURE_ALL": ""}):
            assert _env_bool("CAPTURE_ALL") is None

    def test_returns_none_for_unrecognised(self):
        with patch.dict(os.environ, {"SMELLO_CAPTURE_ALL": "maybe"}):
            assert _env_bool("CAPTURE_ALL") is None


# --- _env_list ---


class TestEnvList:
    def test_comma_separated(self):
        with patch.dict(os.environ, {"SMELLO_CAPTURE_HOSTS": "a.com,b.com,c.com"}):
            assert _env_list("CAPTURE_HOSTS") == ["a.com", "b.com", "c.com"]

    def test_strips_items(self):
        with patch.dict(os.environ, {"SMELLO_CAPTURE_HOSTS": " a.com , b.com "}):
            assert _env_list("CAPTURE_HOSTS") == ["a.com", "b.com"]

    def test_skips_empty_items(self):
        with patch.dict(os.environ, {"SMELLO_CAPTURE_HOSTS": "a.com,,b.com,"}):
            assert _env_list("CAPTURE_HOSTS") == ["a.com", "b.com"]

    def test_returns_none_when_unset(self):
        with patch.dict(os.environ, {}, clear=True):
            assert _env_list("CAPTURE_HOSTS") is None

    def test_returns_none_when_empty(self):
        with patch.dict(os.environ, {"SMELLO_CAPTURE_HOSTS": ""}):
            assert _env_list("CAPTURE_HOSTS") is None

    def test_single_item(self):
        with patch.dict(os.environ, {"SMELLO_CAPTURE_HOSTS": "api.stripe.com"}):
            assert _env_list("CAPTURE_HOSTS") == ["api.stripe.com"]


# --- init() env var integration ---


class TestInitEnvVars:
    """Test that smello.init() resolves env vars correctly."""

    def test_no_url_does_nothing(self):
        """init() without a URL should not activate."""
        with patch.dict(os.environ, {}, clear=True):
            smello._config = None
            smello.init()
            assert smello._config is None

    def test_no_url_logs_warning(self, caplog):
        """init() without a URL should log a warning."""
        with (
            patch.dict(os.environ, {}, clear=True),
            caplog.at_level(logging.WARNING, logger="smello"),
        ):
            smello._config = None
            smello.init()
            assert "server URL" in caplog.text

    def test_server_url_from_env(self):
        """SMELLO_URL should set the server URL."""

        with (
            patch.dict(os.environ, {"SMELLO_URL": "http://smello:9999"}),
            patch("smello._start_worker"),
            patch("smello._apply_all"),
        ):
            smello._config = None
            smello.init()
            assert smello._config.server_url == "http://smello:9999"

    def test_explicit_server_url_overrides_env(self):
        """Explicit server_url should win over SMELLO_URL."""

        with (
            patch.dict(os.environ, {"SMELLO_URL": "http://from-env:1111"}),
            patch("smello._start_worker"),
            patch("smello._apply_all"),
        ):
            smello._config = None
            smello.init(server_url="http://explicit:2222")
            assert smello._config.server_url == "http://explicit:2222"

    def test_capture_hosts_from_env(self):
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

    def test_ignore_hosts_from_env(self):
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

    def test_redact_headers_from_env(self):
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

    def test_redact_headers_default_without_env(self):
        with (
            patch.dict(os.environ, {"SMELLO_URL": "http://test:5110"}, clear=True),
            patch("smello._start_worker"),
            patch("smello._apply_all"),
        ):
            smello._config = None
            smello.init()
            assert smello._config.redact_headers == ["authorization", "x-api-key"]

    def test_capture_all_false_from_env(self):
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

    def test_defaults_with_explicit_url(self):
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
