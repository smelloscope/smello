"""Tests for the logging patch."""

import logging
from unittest.mock import patch

from smello.config import SmelloConfig
from smello.patches import patch_logging as patch_logging_mod


def _make_config(**kwargs):
    defaults = {"capture_logs": True, "log_level": logging.DEBUG}
    defaults.update(kwargs)
    return SmelloConfig(server_url="http://localhost:5110", **defaults)


_original_callhandlers = logging.Logger.callHandlers


class TestPatchLogging:
    def setup_method(self):
        patch_logging_mod._patched = False
        logging.Logger.callHandlers = _original_callhandlers

    def test_skips_when_disabled(self):
        original = logging.Logger.callHandlers
        config = _make_config(capture_logs=False)
        patch_logging_mod.patch_logging(config)
        assert logging.Logger.callHandlers is original

    @patch("smello.patches.patch_logging.transport")
    def test_captures_log_record(self, mock_transport):
        config = _make_config()
        patch_logging_mod.patch_logging(config)

        test_logger = logging.getLogger("test.capture")
        test_logger.setLevel(logging.DEBUG)
        test_logger.warning("something went wrong: %s", "details")

        mock_transport.send_event.assert_called()
        call_args = mock_transport.send_event.call_args
        assert call_args[0][0] == "log"
        data = call_args[0][1]
        assert data["level"] == "WARNING"
        assert data["logger_name"] == "test.capture"
        assert "something went wrong: details" in data["message"]
        assert data["lineno"] > 0

    @patch("smello.patches.patch_logging.transport")
    def test_ignores_smello_loggers(self, mock_transport):
        config = _make_config()
        patch_logging_mod.patch_logging(config)

        smello_logger = logging.getLogger("smello.internal")
        smello_logger.setLevel(logging.DEBUG)
        smello_logger.warning("internal noise")

        mock_transport.send_event.assert_not_called()

    @patch("smello.patches.patch_logging.transport")
    def test_ignores_urllib3_loggers(self, mock_transport):
        config = _make_config()
        patch_logging_mod.patch_logging(config)

        urllib_logger = logging.getLogger("urllib3.connectionpool")
        urllib_logger.setLevel(logging.DEBUG)
        urllib_logger.warning("connection pool noise")

        mock_transport.send_event.assert_not_called()

    @patch("smello.patches.patch_logging.transport")
    def test_respects_log_level(self, mock_transport):
        config = _make_config(log_level=logging.ERROR)
        patch_logging_mod.patch_logging(config)

        test_logger = logging.getLogger("test.level")
        test_logger.setLevel(logging.DEBUG)
        test_logger.warning("below threshold")

        mock_transport.send_event.assert_not_called()

    @patch("smello.patches.patch_logging.transport")
    def test_log_still_works(self, mock_transport):
        """Verify the original log handling is not broken."""
        config = _make_config()
        patch_logging_mod.patch_logging(config)

        handler = (
            logging.handlers.MemoryHandler(capacity=100)
            if hasattr(logging, "handlers")
            else logging.StreamHandler()
        )
        test_logger = logging.getLogger("test.passthrough")
        test_logger.setLevel(logging.DEBUG)
        test_logger.addHandler(handler)

        test_logger.info("should still work")
        # No exception means the original callHandlers worked
        test_logger.removeHandler(handler)

    @patch("smello.patches.patch_logging.transport")
    def test_captures_extra_attributes(self, mock_transport):
        config = _make_config()
        patch_logging_mod.patch_logging(config)

        test_logger = logging.getLogger("test.extra")
        test_logger.setLevel(logging.DEBUG)
        test_logger.warning("with extra", extra={"user_id": 42})

        data = mock_transport.send_event.call_args[0][1]
        assert data["extra"]["user_id"] == 42
