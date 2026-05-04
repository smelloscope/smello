"""Tests for the exception hook patch."""

import linecache
import sys
import threading

import pytest
from smello.config import SmelloConfig
from smello.patches import patch_excepthook


def _make_config(**kwargs):
    return SmelloConfig(server_url="http://localhost:5110", **kwargs)


@pytest.fixture(autouse=True)
def _reset_patched_flag():
    patch_excepthook._patched = False
    yield
    patch_excepthook._patched = False


def test_installs_excepthook():
    # Arrange
    original = sys.excepthook
    config = _make_config(capture_exceptions=True)

    # Act
    patch_excepthook.patch_excepthook(config)

    # Assert
    try:
        assert sys.excepthook is not original
    finally:
        sys.excepthook = original


def test_skips_when_disabled():
    # Arrange
    original = sys.excepthook
    config = _make_config(capture_exceptions=False)

    # Act
    patch_excepthook.patch_excepthook(config)

    # Assert
    assert sys.excepthook is original


def test_calls_original_excepthook(mock_transport):
    # Arrange
    original = sys.excepthook
    original_called = []

    def fake_original(exc_type, exc_value, exc_tb):
        original_called.append((exc_type, exc_value))

    sys.excepthook = fake_original
    config = _make_config(capture_exceptions=True)
    patch_excepthook.patch_excepthook(config)

    # Act
    try:
        raise ValueError("test error")
    except ValueError:
        exc_type, exc_value, exc_tb = sys.exc_info()
        sys.excepthook(exc_type, exc_value, exc_tb)

    # Assert
    try:
        assert len(original_called) == 1
        assert original_called[0][0] is ValueError
    finally:
        sys.excepthook = original


def test_sends_exception_event(mock_transport):
    # Arrange
    original = sys.excepthook

    def noop_original(exc_type, exc_value, exc_tb):
        pass

    sys.excepthook = noop_original
    config = _make_config(capture_exceptions=True)
    patch_excepthook.patch_excepthook(config)

    # Act
    try:
        raise ValueError("test capture")
    except ValueError:
        exc_type, exc_value, exc_tb = sys.exc_info()
        sys.excepthook(exc_type, exc_value, exc_tb)

    # Assert
    try:
        assert len(mock_transport.send_exception_calls) == 1
        payload = mock_transport.send_exception_calls[0]
        assert payload["id"]
        assert payload["timestamp"]
        data = payload["data"]
        assert data["exc_type"] == "ValueError"
        assert "test capture" in data["exc_value"]
        assert "Traceback" in data["traceback_text"]
        assert len(data["frames"]) > 0
        assert data["frames"][-1]["function"] == "test_sends_exception_event"
        assert mock_transport.flush_calls == 1
    finally:
        sys.excepthook = original


def test_capture_exception_serializes_frames(mock_transport):
    # Act
    try:
        raise RuntimeError("frame test")
    except RuntimeError:
        exc_type, exc_value, exc_tb = sys.exc_info()
        patch_excepthook._capture_exception(exc_type, exc_value, exc_tb)

    # Assert
    data = mock_transport.send_exception_calls[0]["data"]
    assert data["exc_type"] == "RuntimeError"
    assert data["exc_value"] == "frame test"
    assert data["exc_module"] == "builtins"
    assert any(
        f["function"] == "test_capture_exception_serializes_frames"
        for f in data["frames"]
    )


def test_capture_exception_skips_none(mock_transport):
    # Act
    patch_excepthook._capture_exception(None, None, None)

    # Assert
    assert mock_transport.send_exception_calls == []


def test_capture_exception_includes_pre_post_context(mock_transport):
    # Act
    try:
        raise RuntimeError("context test")
    except RuntimeError:
        exc_type, exc_value, exc_tb = sys.exc_info()
        patch_excepthook._capture_exception(exc_type, exc_value, exc_tb)

    # Assert
    data = mock_transport.send_exception_calls[0]["data"]
    last_frame = data["frames"][-1]
    assert last_frame["function"] == "test_capture_exception_includes_pre_post_context"
    assert last_frame["pre_context"], "expected pre_context to be populated"
    assert last_frame["post_context"], "expected post_context to be populated"
    # The raise line itself is the context_line, not in pre/post.
    assert "raise RuntimeError" not in "\n".join(last_frame["pre_context"])
    assert "raise RuntimeError" not in "\n".join(last_frame["post_context"])


def test_get_frame_source_returns_empty_for_missing_file():
    # Act
    pre, line, post = patch_excepthook._get_frame_source("/nonexistent/path.py", 5)

    # Assert
    assert pre == []
    assert line is None
    assert post == []


def test_get_frame_source_returns_empty_for_synthetic_filename():
    # Act
    pre, line, post = patch_excepthook._get_frame_source("<string>", 1)

    # Assert
    assert pre == []
    assert line is None
    assert post == []


def test_get_frame_source_returns_empty_for_invalid_lineno():
    # Act
    pre, line, post = patch_excepthook._get_frame_source(__file__, 0)

    # Assert
    assert pre == []
    assert line is None
    assert post == []


def test_get_frame_source_returns_lines_for_real_file(tmp_path):
    # Arrange
    src = tmp_path / "sample.py"
    src.write_text("line 1\nline 2\nline 3\nline 4\nline 5\nline 6\nline 7\n")
    # linecache may have stale data from another test; refresh.
    linecache.checkcache(str(src))

    # Act
    pre, line, post = patch_excepthook._get_frame_source(str(src), lineno=4, count=2)

    # Assert
    assert pre == ["line 2", "line 3"]
    assert line == "line 4"
    assert post == ["line 5", "line 6"]


def test_get_frame_source_preserves_indentation_on_error_line(tmp_path):
    # Arrange
    src = tmp_path / "indented.py"
    src.write_text(
        "def f():\n    if True:\n        raise RuntimeError('boom')\n    return None\n"
    )
    linecache.checkcache(str(src))

    # Act
    pre, line, post = patch_excepthook._get_frame_source(str(src), lineno=3, count=2)

    # Assert
    assert pre == ["def f():", "    if True:"]
    assert line == "        raise RuntimeError('boom')"
    assert post == ["    return None"]


def test_installs_threading_excepthook(mock_transport):
    # Arrange
    original = threading.excepthook
    config = _make_config(capture_exceptions=True)

    # Act
    patch_excepthook.patch_excepthook(config)

    # Assert
    try:
        assert threading.excepthook is not original
    finally:
        threading.excepthook = original
