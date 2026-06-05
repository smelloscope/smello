"""Tests for _get_frontend_dir() auto-detection logic and SPA serving."""

import pytest
import smello_server.app as app_module
import tortoise.context
from fastapi.testclient import TestClient
from smello_server.app import _get_frontend_dir, create_app


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


# --- SPA path traversal protection ---


@pytest.fixture()
def spa_client(tmp_path, monkeypatch):
    """TestClient with a frontend directory and a secret file outside it."""
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "index.html").write_text("<html>index</html>")
    (frontend / "legit.txt").write_text("legit file")
    monkeypatch.setenv("SMELLO_FRONTEND_DIR", str(frontend))

    (tmp_path / "secret.txt").write_text("SECRET")

    tortoise.context._global_context = None
    app = create_app(db_url=f"sqlite://{tmp_path / 'test.db'}")
    with TestClient(app) as tc:
        yield tc
    tortoise.context._global_context = None


def test_spa_serves_legit_file(spa_client):
    """Files inside the frontend directory are served normally."""
    resp = spa_client.get("/legit.txt")
    assert resp.status_code == 200
    assert resp.text == "legit file"


def test_spa_path_traversal_percent_encoded(spa_client):
    """%2e%2e path traversal is blocked."""
    resp = spa_client.get("/%2e%2e/secret.txt")
    assert resp.status_code == 200
    assert "SECRET" not in resp.text
    assert "index" in resp.text


def test_spa_path_traversal_dot_dot(spa_client):
    """Literal ../ path traversal is blocked."""
    resp = spa_client.get("/../secret.txt")
    assert resp.status_code == 200
    assert "SECRET" not in resp.text


def test_spa_unknown_path_returns_index(spa_client):
    """Unknown paths return index.html (SPA fallback)."""
    resp = spa_client.get("/nonexistent/page")
    assert resp.status_code == 200
    assert "index" in resp.text
