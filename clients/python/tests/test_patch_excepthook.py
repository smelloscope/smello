"""Tests for the exception hook patch."""

import linecache
import sys
import threading
from unittest.mock import patch

from smello.config import SmelloConfig
from smello.patches import patch_excepthook


def _make_config(**kwargs):
    return SmelloConfig(server_url="http://localhost:5110", **kwargs)


class TestPatchExcepthook:
    def setup_method(self):
        # Reset the patched flag so each test can re-apply
        patch_excepthook._patched = False

    def test_installs_excepthook(self):
        original = sys.excepthook
        config = _make_config(capture_exceptions=True)
        patch_excepthook.patch_excepthook(config)
        assert sys.excepthook is not original
        # Restore
        sys.excepthook = original

    def test_skips_when_disabled(self):
        original = sys.excepthook
        config = _make_config(capture_exceptions=False)
        patch_excepthook.patch_excepthook(config)
        assert sys.excepthook is original

    @patch("smello.patches.patch_excepthook.transport")
    def test_calls_original_excepthook(self, mock_transport):
        original_called = []
        original = sys.excepthook

        def fake_original(exc_type, exc_value, exc_tb):
            original_called.append((exc_type, exc_value))

        sys.excepthook = fake_original
        config = _make_config(capture_exceptions=True)
        patch_excepthook.patch_excepthook(config)

        try:
            raise ValueError("test error")
        except ValueError:
            exc_type, exc_value, exc_tb = sys.exc_info()
            sys.excepthook(exc_type, exc_value, exc_tb)

        assert len(original_called) == 1
        assert original_called[0][0] is ValueError
        # Restore
        sys.excepthook = original

    @patch("smello.patches.patch_excepthook.transport")
    def test_sends_exception_event(self, mock_transport):
        original = sys.excepthook

        def noop_original(exc_type, exc_value, exc_tb):
            pass

        sys.excepthook = noop_original
        config = _make_config(capture_exceptions=True)
        patch_excepthook.patch_excepthook(config)

        try:
            raise ValueError("test capture")
        except ValueError:
            exc_type, exc_value, exc_tb = sys.exc_info()
            sys.excepthook(exc_type, exc_value, exc_tb)

        mock_transport.send_event.assert_called_once()
        call_args = mock_transport.send_event.call_args
        assert call_args[0][0] == "exception"
        data = call_args[0][1]
        assert data["exc_type"] == "ValueError"
        assert "test capture" in data["exc_value"]
        assert "Traceback" in data["traceback_text"]
        assert len(data["frames"]) > 0
        assert data["frames"][-1]["function"] == "test_sends_exception_event"
        mock_transport.flush.assert_called_once()
        # Restore
        sys.excepthook = original


class TestCaptureException:
    def setup_method(self):
        patch_excepthook._patched = False

    @patch("smello.patches.patch_excepthook.transport")
    def test_capture_exception_serializes_frames(self, mock_transport):
        try:
            raise RuntimeError("frame test")
        except RuntimeError:
            exc_type, exc_value, exc_tb = sys.exc_info()
            patch_excepthook._capture_exception(exc_type, exc_value, exc_tb)

        data = mock_transport.send_event.call_args[0][1]
        assert data["exc_type"] == "RuntimeError"
        assert data["exc_value"] == "frame test"
        assert data["exc_module"] == "builtins"
        assert any(
            f["function"] == "test_capture_exception_serializes_frames"
            for f in data["frames"]
        )

    @patch("smello.patches.patch_excepthook.transport")
    def test_capture_exception_skips_none(self, mock_transport):
        patch_excepthook._capture_exception(None, None, None)
        mock_transport.send_event.assert_not_called()

    @patch("smello.patches.patch_excepthook.transport")
    def test_capture_exception_includes_pre_post_context(self, mock_transport):
        try:
            raise RuntimeError("context test")
        except RuntimeError:
            exc_type, exc_value, exc_tb = sys.exc_info()
            patch_excepthook._capture_exception(exc_type, exc_value, exc_tb)

        data = mock_transport.send_event.call_args[0][1]
        # The frame raising the error is this test file — it has surrounding lines.
        last_frame = data["frames"][-1]
        assert (
            last_frame["function"] == "test_capture_exception_includes_pre_post_context"
        )
        assert last_frame["pre_context"], "expected pre_context to be populated"
        assert last_frame["post_context"], "expected post_context to be populated"
        # The raise line itself is the context_line, not in pre/post.
        assert "raise RuntimeError" not in "\n".join(last_frame["pre_context"])
        assert "raise RuntimeError" not in "\n".join(last_frame["post_context"])


class TestGetFrameSource:
    def test_returns_empty_for_missing_file(self):
        pre, line, post = patch_excepthook._get_frame_source("/nonexistent/path.py", 5)
        assert pre == []
        assert line is None
        assert post == []

    def test_returns_empty_for_synthetic_filename(self):
        pre, line, post = patch_excepthook._get_frame_source("<string>", 1)
        assert pre == []
        assert line is None
        assert post == []

    def test_returns_empty_for_invalid_lineno(self):
        pre, line, post = patch_excepthook._get_frame_source(__file__, 0)
        assert pre == []
        assert line is None
        assert post == []

    def test_returns_lines_for_real_file(self, tmp_path):
        src = tmp_path / "sample.py"
        src.write_text("line 1\nline 2\nline 3\nline 4\nline 5\nline 6\nline 7\n")
        # linecache may have stale data from another test; refresh.
        linecache.checkcache(str(src))
        pre, line, post = patch_excepthook._get_frame_source(
            str(src), lineno=4, count=2
        )
        assert pre == ["line 2", "line 3"]
        assert line == "line 4"
        assert post == ["line 5", "line 6"]

    def test_preserves_indentation_on_error_line(self, tmp_path):
        src = tmp_path / "indented.py"
        src.write_text(
            "def f():\n"
            "    if True:\n"
            "        raise RuntimeError('boom')\n"
            "    return None\n"
        )
        linecache.checkcache(str(src))
        pre, line, post = patch_excepthook._get_frame_source(
            str(src), lineno=3, count=2
        )
        assert pre == ["def f():", "    if True:"]
        assert line == "        raise RuntimeError('boom')"
        assert post == ["    return None"]


class TestThreadingExcepthook:
    def setup_method(self):
        patch_excepthook._patched = False

    @patch("smello.patches.patch_excepthook.transport")
    def test_installs_threading_excepthook(self, mock_transport):
        original = threading.excepthook
        config = _make_config(capture_exceptions=True)
        patch_excepthook.patch_excepthook(config)
        assert threading.excepthook is not original
        threading.excepthook = original
