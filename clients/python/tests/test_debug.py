"""Tests for smello._debug (debug logging helpers)."""

import logging
import sys
from unittest.mock import patch

import pytest
from smello._debug import (
    check_connectivity,
    log_resolved_config,
    setup_debug_logging,
    teardown_debug_logging,
)


@pytest.fixture(autouse=True)
def _clean_smello_logger():
    """Remove handlers added by setup_debug_logging between tests."""
    smello_logger = logging.getLogger("smello")
    original_handlers = list(smello_logger.handlers)
    original_level = smello_logger.level
    original_propagate = smello_logger.propagate
    yield
    smello_logger.handlers = original_handlers
    smello_logger.level = original_level
    smello_logger.propagate = original_propagate


# -- setup_debug_logging -----------------------------------------------------


def test_setup_adds_tagged_stderr_handler():
    setup_debug_logging()
    smello_logger = logging.getLogger("smello")

    assert smello_logger.level == logging.DEBUG
    assert smello_logger.propagate is False
    tagged = [
        h for h in smello_logger.handlers if getattr(h, "_smello_debug_handler", False)
    ]
    assert len(tagged) == 1


def test_setup_is_idempotent():
    setup_debug_logging()
    setup_debug_logging()

    tagged = [
        h
        for h in logging.getLogger("smello").handlers
        if getattr(h, "_smello_debug_handler", False)
    ]
    assert len(tagged) == 1


def test_setup_messages_go_to_stderr(capsys):
    setup_debug_logging()

    logging.getLogger("smello.test").debug("hello from test")

    captured = capsys.readouterr()
    assert "smello: hello from test" in captured.err


def test_silent_without_setup(capsys):
    logging.getLogger("smello.test").debug("should not appear")

    captured = capsys.readouterr()
    assert "should not appear" not in captured.err


# -- teardown_debug_logging ---------------------------------------------------


def test_teardown_removes_tagged_handler():
    setup_debug_logging()

    teardown_debug_logging()

    tagged = [
        h
        for h in logging.getLogger("smello").handlers
        if getattr(h, "_smello_debug_handler", False)
    ]
    assert len(tagged) == 0


def test_teardown_preserves_user_handlers():
    smello_logger = logging.getLogger("smello")
    user_handler = logging.StreamHandler(sys.stderr)
    smello_logger.addHandler(user_handler)
    setup_debug_logging()

    teardown_debug_logging()

    assert user_handler in smello_logger.handlers


def test_teardown_silences_output(capsys):
    setup_debug_logging()

    teardown_debug_logging()
    logging.getLogger("smello.test").debug("should be gone")

    captured = capsys.readouterr()
    assert "should be gone" not in captured.err


def test_teardown_noop_when_not_setup():
    teardown_debug_logging()


# -- check_connectivity -------------------------------------------------------


def test_connectivity_success(caplog):
    mock_resp = type("Resp", (), {"status": 200})()

    with (
        patch("smello._debug.urllib.request.urlopen", return_value=mock_resp),
        caplog.at_level(logging.DEBUG, logger="smello"),
    ):
        check_connectivity("http://localhost:5110")

    assert "connected to http://localhost:5110 (200)" in caplog.text


def test_connectivity_failure(caplog):
    with (
        patch(
            "smello._debug.urllib.request.urlopen",
            side_effect=ConnectionRefusedError("Connection refused"),
        ),
        caplog.at_level(logging.WARNING, logger="smello"),
    ):
        check_connectivity("http://localhost:5110")

    assert "failed to reach http://localhost:5110" in caplog.text
    assert "Connection refused" in caplog.text


def test_connectivity_never_raises():
    with patch(
        "smello._debug.urllib.request.urlopen",
        side_effect=Exception("boom"),
    ):
        check_connectivity("http://localhost:5110")


# -- log_resolved_config ------------------------------------------------------


def test_log_config_formats_provenance(caplog):
    provenance = {
        "server_url": "SMELLO_URL",
        "debug": "param",
        "capture_all": "default",
    }

    with caplog.at_level(logging.DEBUG, logger="smello"):
        log_resolved_config(
            provenance,
            server_url="http://localhost:5110",
            debug=True,
            capture_all=True,
        )

    assert "resolved config:" in caplog.text
    assert "server_url = http://localhost:5110 (SMELLO_URL)" in caplog.text
    assert "debug = True (param)" in caplog.text


def test_log_config_includes_defaults(caplog):
    provenance = {
        "server_url": "default",
        "debug": "default",
        "capture_all": "default",
    }

    with caplog.at_level(logging.DEBUG, logger="smello"):
        log_resolved_config(
            provenance,
            server_url="http://localhost:5110",
            debug=False,
            capture_all=True,
        )

    assert "server_url = http://localhost:5110 (default)" in caplog.text
    assert "debug = False (default)" in caplog.text
    assert "capture_all = True (default)" in caplog.text


def test_log_config_shows_cli_flags(caplog):
    provenance = {
        "server_url": "default",
        "debug": "--debug",
    }

    with caplog.at_level(logging.DEBUG, logger="smello"):
        log_resolved_config(
            provenance,
            server_url="http://localhost:5110",
            debug=True,
        )

    assert "debug = True (--debug)" in caplog.text
