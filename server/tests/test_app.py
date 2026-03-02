"""Tests for _get_frontend_dir() auto-detection logic."""

import smello_server.app as app_module
from smello_server.app import _get_frontend_dir


def test_env_var_with_valid_dir(tmp_path, monkeypatch):
    """SMELLO_FRONTEND_DIR pointing to a dir with index.html is returned."""
    (tmp_path / "index.html").write_text("<html></html>")
    monkeypatch.setenv("SMELLO_FRONTEND_DIR", str(tmp_path))
    assert _get_frontend_dir() == tmp_path


def test_env_var_missing_index_html(tmp_path, monkeypatch):
    """Env var dir without index.html falls through."""
    monkeypatch.setenv("SMELLO_FRONTEND_DIR", str(tmp_path))
    # No index.html in tmp_path, should fall through to bundled check
    assert _get_frontend_dir() is None


def test_bundled_frontend_detected(tmp_path, monkeypatch):
    """Bundled _frontend/ next to app.py is detected when no env var."""
    monkeypatch.delenv("SMELLO_FRONTEND_DIR", raising=False)

    # Create a fake _frontend dir next to a fake __file__
    fake_package = tmp_path / "smello_server"
    fake_package.mkdir()
    bundled = fake_package / "_frontend"
    bundled.mkdir()
    (bundled / "index.html").write_text("<html></html>")

    monkeypatch.setattr(app_module, "__file__", str(fake_package / "app.py"))
    assert _get_frontend_dir() == bundled


def test_env_var_takes_precedence_over_bundled(tmp_path, monkeypatch):
    """SMELLO_FRONTEND_DIR takes precedence over bundled _frontend/."""
    env_dir = tmp_path / "env_frontend"
    env_dir.mkdir()
    (env_dir / "index.html").write_text("<html></html>")
    monkeypatch.setenv("SMELLO_FRONTEND_DIR", str(env_dir))

    # Also set up bundled dir
    fake_package = tmp_path / "smello_server"
    fake_package.mkdir()
    bundled = fake_package / "_frontend"
    bundled.mkdir()
    (bundled / "index.html").write_text("<html></html>")

    monkeypatch.setattr(app_module, "__file__", str(fake_package / "app.py"))
    assert _get_frontend_dir() == env_dir


def test_no_frontend_returns_none(monkeypatch):
    """Neither env var nor bundled → returns None."""
    monkeypatch.delenv("SMELLO_FRONTEND_DIR", raising=False)
    result = _get_frontend_dir()
    # The real package doesn't ship _frontend/ in development
    assert result is None
