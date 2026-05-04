"""Tests for the `smello` CLI (`smello run` wrapper)."""

from __future__ import annotations

import argparse
import importlib
import os
import subprocess
import sys
from unittest.mock import patch

import pytest
from smello import cli


@pytest.fixture
def sitecustomize():
    """Import the bootstrap sitecustomize with a cleared env.

    Its top-level ``_activate()`` runs once, on first import. If ``SMELLO_URL``
    is set in the developer's shell or in CI, that first import would call the
    real ``smello.init()`` and patch HTTP libraries globally. Importing inside
    a cleared env makes the activation a no-op; subsequent tests inspect the
    cached module safely.
    """
    with patch.dict(os.environ, {}, clear=True):
        return importlib.import_module("smello.bootstrap.sitecustomize")


def _make_args(**overrides) -> argparse.Namespace:
    defaults = {
        "subcommand": "run",
        "server": None,
        "capture_host": None,
        "ignore_host": None,
        "capture_all": None,
        "redact_header": None,
        "redact_query_param": None,
        "capture_exceptions": None,
        "capture_logs": None,
        "log_level": None,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def _capture_execvpe(argv: list[str]) -> dict:
    captured: dict = {}

    def fake_execvpe(executable, command, env):
        captured["executable"] = executable
        captured["command"] = command
        captured["env"] = env

    with patch.object(cli.os, "execvpe", side_effect=fake_execvpe):
        cli.main(argv)
    return captured


# --- _smello_env_overrides (pure CLI-flag translation) ---


def test_overrides_default_empty():
    """Without any flags, no SMELLO_* overrides are produced."""
    assert cli._smello_env_overrides(_make_args()) == {}


def test_overrides_server():
    overrides = cli._smello_env_overrides(_make_args(server="http://x:5110"))
    assert overrides == {"SMELLO_URL": "http://x:5110"}


def test_overrides_capture_hosts():
    overrides = cli._smello_env_overrides(_make_args(capture_host=["a.com", "b.com"]))
    assert overrides == {
        "SMELLO_CAPTURE_HOSTS": "a.com,b.com",
        "SMELLO_CAPTURE_ALL": "false",  # auto-disabled
    }


def test_overrides_ignore_hosts():
    overrides = cli._smello_env_overrides(_make_args(ignore_host=["internal.svc"]))
    assert overrides == {"SMELLO_IGNORE_HOSTS": "internal.svc"}


@pytest.mark.parametrize("flag,expected", [(True, "true"), (False, "false")])
def test_overrides_capture_all(flag, expected):
    overrides = cli._smello_env_overrides(_make_args(capture_all=flag))
    assert overrides["SMELLO_CAPTURE_ALL"] == expected


def test_overrides_capture_all_unset():
    """No `--capture-all` flag and no `--capture-host` -> no SMELLO_CAPTURE_ALL."""
    assert "SMELLO_CAPTURE_ALL" not in cli._smello_env_overrides(_make_args())


def test_overrides_capture_host_plus_explicit_capture_all():
    """An explicit `--capture-all` is preserved alongside `--capture-host`."""
    overrides = cli._smello_env_overrides(
        _make_args(capture_host=["api.stripe.com"], capture_all=True)
    )
    assert overrides["SMELLO_CAPTURE_ALL"] == "true"


def test_overrides_redact_headers():
    overrides = cli._smello_env_overrides(_make_args(redact_header=["X-Secret"]))
    assert overrides == {"SMELLO_REDACT_HEADERS": "X-Secret"}


def test_overrides_redact_query_params():
    overrides = cli._smello_env_overrides(_make_args(redact_query_param=["api_key"]))
    assert overrides == {"SMELLO_REDACT_QUERY_PARAMS": "api_key"}


@pytest.mark.parametrize("flag,expected", [(True, "true"), (False, "false")])
def test_overrides_capture_exceptions(flag, expected):
    overrides = cli._smello_env_overrides(_make_args(capture_exceptions=flag))
    assert overrides == {"SMELLO_CAPTURE_EXCEPTIONS": expected}


@pytest.mark.parametrize("flag,expected", [(True, "true"), (False, "false")])
def test_overrides_capture_logs(flag, expected):
    overrides = cli._smello_env_overrides(_make_args(capture_logs=flag))
    assert overrides == {"SMELLO_CAPTURE_LOGS": expected}


def test_overrides_log_level():
    overrides = cli._smello_env_overrides(_make_args(log_level=20))
    assert overrides == {"SMELLO_LOG_LEVEL": "20"}


def test_overrides_capture_logs_with_level():
    overrides = cli._smello_env_overrides(_make_args(capture_logs=True, log_level=10))
    assert overrides == {"SMELLO_CAPTURE_LOGS": "true", "SMELLO_LOG_LEVEL": "10"}


# --- _build_child_env (composes os.environ + overrides + PYTHONPATH + URL default) ---


def test_pythonpath_prepends_bootstrap():
    with patch.dict(os.environ, {"PYTHONPATH": "/foo"}, clear=True):
        env = cli._build_child_env(_make_args())
    assert env["PYTHONPATH"] == f"{cli._bootstrap_dir()}{os.pathsep}/foo"


def test_pythonpath_when_unset():
    with patch.dict(os.environ, {}, clear=True):
        env = cli._build_child_env(_make_args())
    assert env["PYTHONPATH"] == cli._bootstrap_dir()


def test_default_server_url_when_nothing_set():
    with patch.dict(os.environ, {}, clear=True):
        env = cli._build_child_env(_make_args())
    assert env["SMELLO_URL"] == cli.DEFAULT_SERVER_URL


def test_explicit_server_overrides_parent_env():
    with patch.dict(os.environ, {"SMELLO_URL": "http://parent:9999"}, clear=True):
        env = cli._build_child_env(_make_args(server="http://explicit:5000"))
    assert env["SMELLO_URL"] == "http://explicit:5000"


def test_inherits_smello_url_from_parent():
    with patch.dict(os.environ, {"SMELLO_URL": "http://parent:9999"}, clear=True):
        env = cli._build_child_env(_make_args())
    assert env["SMELLO_URL"] == "http://parent:9999"


# --- main entry point ---


def test_no_command_returns_2(capsys):
    rc = cli.main(["run"])

    assert rc == 2
    assert "no command specified" in capsys.readouterr().err


def test_no_subcommand_prints_help(capsys):
    rc = cli.main([])

    assert rc == 2
    assert "smello" in capsys.readouterr().err  # argparse prints program name in help


def test_run_passes_command_and_env():
    c = _capture_execvpe(["run", "--server", "http://x:5110", "--", "echo", "hi"])

    assert c["command"] == ["echo", "hi"]
    assert c["env"]["SMELLO_URL"] == "http://x:5110"
    assert c["env"]["PYTHONPATH"].startswith(cli._bootstrap_dir())


def test_explicit_dash_dash_optional():
    """`smello run pytest tests/` works without `--`."""
    c = _capture_execvpe(["run", "pytest", "tests/"])

    assert c["command"] == ["pytest", "tests/"]


def test_dash_dash_inside_command_preserved():
    """`smello run pytest -- tests/` keeps pytest's own `--`."""
    c = _capture_execvpe(["run", "pytest", "--", "tests/"])

    assert c["command"] == ["pytest", "--", "tests/"]


def test_command_flags_pass_through():
    """Flags after the command name belong to the wrapped command."""
    c = _capture_execvpe(["run", "uvicorn", "--reload", "app:app"])

    assert c["command"] == ["uvicorn", "--reload", "app:app"]


def test_repeated_smello_flags():
    c = _capture_execvpe(
        [
            "run",
            "--capture-host",
            "a.com",
            "--capture-host",
            "b.com",
            "pytest",
        ]
    )

    assert c["command"] == ["pytest"]
    assert c["env"]["SMELLO_CAPTURE_HOSTS"] == "a.com,b.com"


def test_command_not_found_returns_127(capsys):
    with patch.object(cli.os, "execvpe", side_effect=FileNotFoundError):
        rc = cli.main(["run", "--", "definitely-not-a-real-cmd-xyz"])

    assert rc == 127
    assert "not found" in capsys.readouterr().err


def test_permission_denied_returns_126(capsys):
    with patch.object(cli.os, "execvpe", side_effect=PermissionError):
        rc = cli.main(["run", "--", "/tmp/no-exec-bit"])

    assert rc == 126
    err = capsys.readouterr().err
    assert "permission denied" in err
    assert "smello run -- python" in err  # hint shown


def test_py_script_gets_python_prepended():
    c = _capture_execvpe(["run", "--", "examples/wrapper_demo.py", "arg1"])

    assert c["executable"] == sys.executable
    assert c["command"] == [sys.executable, "examples/wrapper_demo.py", "arg1"]


def test_py_script_without_dash_dash():
    """`smello run script.py` (no `--`) should also work."""
    c = _capture_execvpe(["run", "examples/wrapper_demo.py"])

    assert c["command"] == [sys.executable, "examples/wrapper_demo.py"]


# --- _resolve_executable ---


@pytest.mark.parametrize(
    "argv",
    [
        ["script.py"],
        ["script.pyw", "arg"],
        ["path/to/nested.py"],
    ],
)
def test_resolve_executable_python_script(argv):
    executable, command = cli._resolve_executable(argv)

    assert executable == sys.executable
    assert command == [sys.executable, *argv]


def test_resolve_executable_path_lookup():
    executable, command = cli._resolve_executable(["echo", "hi"])

    assert os.path.basename(executable) == "echo"
    assert command == ["echo", "hi"]


def test_resolve_executable_unknown_command():
    """If neither `.py` nor on PATH, return the bare argv0 for execvpe to fail."""
    executable, command = cli._resolve_executable(["definitely-not-a-real-cmd-xyz"])

    assert executable == "definitely-not-a-real-cmd-xyz"
    assert command == ["definitely-not-a-real-cmd-xyz"]


# --- bootstrap module ---


def test_bootstrap_dir_contains_sitecustomize():
    path = os.path.join(cli._bootstrap_dir(), "sitecustomize.py")

    assert os.path.isfile(path), f"missing: {path}"


def test_bootstrap_skips_without_smello_url(sitecustomize):
    """sitecustomize should be a no-op if SMELLO_URL is not set."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("smello.init") as mock_init:
            sitecustomize._activate()

            mock_init.assert_not_called()


def test_bootstrap_calls_init_when_url_set(sitecustomize):
    with patch.dict(os.environ, {"SMELLO_URL": "http://x:5110"}, clear=True):
        with patch("smello.init") as mock_init:
            sitecustomize._activate()

            mock_init.assert_called_once()


# --- end-to-end subprocess test ---


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX exec semantics only")
def test_wrapped_python_inits_smello(tmp_path):
    """End-to-end: launching smello via subprocess activates smello in the child."""
    script = tmp_path / "probe.py"
    script.write_text(
        "import os, sys\n"
        "import smello\n"
        "sys.stdout.write(os.environ.get('SMELLO_URL', '') + '|')\n"
        "sys.stdout.write('config' if smello._config else 'no-config')\n"
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "smello.cli",
            "run",
            "--server",
            "http://localhost:65530",
            "--",
            sys.executable,
            str(script),
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == "http://localhost:65530|config"
