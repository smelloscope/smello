"""Tests for the logging patch."""

import logging
import logging.handlers

import pytest
from smello.config import SmelloConfig
from smello.patches import patch_logging as patch_logging_mod


def _make_config(**kwargs):
    defaults = {"capture_logs": True, "log_level": logging.DEBUG}
    defaults.update(kwargs)
    return SmelloConfig(server_url="http://localhost:5110", **defaults)


_original_callhandlers = logging.Logger.callHandlers


@pytest.fixture(autouse=True)
def _reset_logging_patch():
    patch_logging_mod._patched = False
    logging.Logger.callHandlers = _original_callhandlers
    yield
    patch_logging_mod._patched = False
    logging.Logger.callHandlers = _original_callhandlers


def test_skips_when_disabled():
    # Arrange
    original = logging.Logger.callHandlers
    config = _make_config(capture_logs=False)

    # Act
    patch_logging_mod.patch_logging(config)

    # Assert
    assert logging.Logger.callHandlers is original


def test_captures_log_record(mock_transport):
    # Arrange
    config = _make_config()
    patch_logging_mod.patch_logging(config)
    test_logger = logging.getLogger("test.capture")
    test_logger.setLevel(logging.DEBUG)

    # Act
    test_logger.warning("something went wrong: %s", "details")

    # Assert
    assert len(mock_transport.send_log_calls) >= 1
    payload = mock_transport.send_log_calls[-1]
    assert payload["id"]
    assert payload["timestamp"]
    data = payload["data"]
    assert data["level"] == "WARNING"
    assert data["logger_name"] == "test.capture"
    assert "something went wrong: details" in data["message"]
    assert data["lineno"] > 0


def test_ignores_smello_loggers(mock_transport):
    # Arrange
    config = _make_config()
    patch_logging_mod.patch_logging(config)
    smello_logger = logging.getLogger("smello.internal")
    smello_logger.setLevel(logging.DEBUG)

    # Act
    smello_logger.warning("internal noise")

    # Assert
    assert mock_transport.send_log_calls == []


def test_ignores_urllib3_loggers(mock_transport):
    # Arrange
    config = _make_config()
    patch_logging_mod.patch_logging(config)
    urllib_logger = logging.getLogger("urllib3.connectionpool")
    urllib_logger.setLevel(logging.DEBUG)

    # Act
    urllib_logger.warning("connection pool noise")

    # Assert
    assert mock_transport.send_log_calls == []


def test_respects_log_level(mock_transport):
    # Arrange
    config = _make_config(log_level=logging.ERROR)
    patch_logging_mod.patch_logging(config)
    test_logger = logging.getLogger("test.level")
    test_logger.setLevel(logging.DEBUG)

    # Act
    test_logger.warning("below threshold")

    # Assert
    assert mock_transport.send_log_calls == []


def test_log_still_works(mock_transport):
    """Verify the original log handling is not broken."""
    # Arrange
    config = _make_config()
    patch_logging_mod.patch_logging(config)
    handler = logging.handlers.MemoryHandler(capacity=100)
    test_logger = logging.getLogger("test.passthrough")
    test_logger.setLevel(logging.DEBUG)
    test_logger.addHandler(handler)

    # Act
    test_logger.info("should still work")

    # Assert
    # No exception means the original callHandlers worked
    test_logger.removeHandler(handler)


def test_captures_extra_attributes(mock_transport):
    # Arrange
    config = _make_config()
    patch_logging_mod.patch_logging(config)
    test_logger = logging.getLogger("test.extra")
    test_logger.setLevel(logging.DEBUG)

    # Act
    test_logger.warning("with extra", extra={"user_id": 42})

    # Assert
    data = mock_transport.send_log_calls[-1]["data"]
    assert data["extra"]["user_id"] == 42
