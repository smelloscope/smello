"""``smello`` console script.

Today only one subcommand exists: ``smello run <command>``, a wrapper that
activates Smello in the wrapped process without code changes. Mechanism:
prepend a bootstrap directory containing a ``sitecustomize.py`` to
``PYTHONPATH``, then ``execvpe`` the user's command. Subprocess instrumentation
propagates automatically because PYTHONPATH is inherited.

Modeled on ``ddtrace-run`` and ``opentelemetry-instrument``.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from collections.abc import Sequence

import smello

DEFAULT_SERVER_URL = "http://localhost:5110"


def _bootstrap_dir() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(smello.__file__)), "bootstrap")


PYTHON_SCRIPT_SUFFIXES = (".py", ".pyw")


def _resolve_executable(command: list[str]) -> tuple[str, list[str]]:
    """Find the executable to invoke and return ``(executable, argv)``.

    If ``command[0]`` looks like a Python script (ends in ``.py``/``.pyw``),
    prepend ``sys.executable`` so the script runs even when it lacks an
    executable bit or shebang. This matches ``coverage run script.py`` UX.
    Otherwise, resolve via ``PATH``.
    """
    first = command[0]
    if first.endswith(PYTHON_SCRIPT_SUFFIXES):
        return sys.executable, [sys.executable, *command]
    return shutil.which(first) or first, command


def _smello_env_overrides(args: argparse.Namespace) -> dict[str, str]:
    """Translate parsed CLI flags into ``SMELLO_*`` env vars to set on the child.

    Pure function: depends only on ``args``. Returns the env vars the user
    asked for via flags. The caller merges these into the child's environment
    (see :func:`_build_child_env`).
    """
    overrides: dict[str, str] = {}

    if args.server:
        overrides["SMELLO_URL"] = args.server
    if args.capture_host:
        overrides["SMELLO_CAPTURE_HOSTS"] = ",".join(args.capture_host)
    if args.ignore_host:
        overrides["SMELLO_IGNORE_HOSTS"] = ",".join(args.ignore_host)
    if args.capture_all is not None:
        overrides["SMELLO_CAPTURE_ALL"] = "true" if args.capture_all else "false"
    elif args.capture_host:
        # `--capture-host` without an explicit `--capture-all` means "only these".
        # Match the help text ("Capture only this host") and the user's intuition.
        overrides["SMELLO_CAPTURE_ALL"] = "false"
    if args.redact_header:
        overrides["SMELLO_REDACT_HEADERS"] = ",".join(args.redact_header)
    if args.redact_query_param:
        overrides["SMELLO_REDACT_QUERY_PARAMS"] = ",".join(args.redact_query_param)
    if args.capture_exceptions is not None:
        overrides["SMELLO_CAPTURE_EXCEPTIONS"] = (
            "true" if args.capture_exceptions else "false"
        )
    if args.capture_logs is not None:
        overrides["SMELLO_CAPTURE_LOGS"] = "true" if args.capture_logs else "false"
    if args.log_level is not None:
        overrides["SMELLO_LOG_LEVEL"] = str(args.log_level)

    return overrides


def _build_child_env(args: argparse.Namespace) -> dict[str, str]:
    """Build the full environment for the wrapped child process.

    Starts from ``os.environ``, applies CLI-flag overrides, prepends the
    bootstrap directory to ``PYTHONPATH``, and defaults ``SMELLO_URL`` if
    neither flag nor env var supplied one.
    """
    env = os.environ.copy()
    env.update(_smello_env_overrides(args))

    bootstrap = _bootstrap_dir()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{bootstrap}{os.pathsep}{existing}" if existing else bootstrap

    env.setdefault("SMELLO_URL", DEFAULT_SERVER_URL)
    return env


def _build_parser() -> argparse.ArgumentParser:
    """Build the top-level argparse parser with the ``run`` subcommand."""
    parser = argparse.ArgumentParser(
        prog="smello",
        description="Capture outgoing HTTP requests and inspect them in a local web dashboard.",
    )
    parser.add_argument("--version", action="version", version=smello.__version__)
    sub = parser.add_subparsers(dest="subcommand", metavar="SUBCOMMAND")

    run = sub.add_parser(
        "run",
        help="Run a command with Smello capturing its HTTP traffic.",
        description=(
            "Wrap a command so Smello captures its outgoing HTTP traffic without "
            "modifying source. Use `--` to separate Smello flags from the wrapped "
            "command when needed."
        ),
    )
    run.add_argument(
        "--server",
        metavar="URL",
        help=f"Smello server URL (default: {DEFAULT_SERVER_URL}).",
    )
    run.add_argument(
        "--capture-host",
        action="append",
        metavar="HOST",
        help="Capture only this host (repeatable). Sets SMELLO_CAPTURE_HOSTS.",
    )
    run.add_argument(
        "--ignore-host",
        action="append",
        metavar="HOST",
        help="Ignore this host (repeatable). Sets SMELLO_IGNORE_HOSTS.",
    )
    run.add_argument(
        "--capture-all",
        dest="capture_all",
        action="store_true",
        default=None,
        help="Capture all hosts (default).",
    )
    run.add_argument(
        "--no-capture-all",
        dest="capture_all",
        action="store_false",
        help="Capture only hosts listed via --capture-host.",
    )
    run.add_argument(
        "--redact-header",
        action="append",
        metavar="HEADER",
        help="Redact this header value (repeatable).",
    )
    run.add_argument(
        "--redact-query-param",
        action="append",
        metavar="PARAM",
        help="Redact this query parameter value (repeatable).",
    )
    run.add_argument(
        "--capture-exceptions",
        dest="capture_exceptions",
        action="store_true",
        default=None,
        help="Capture unhandled exceptions (default).",
    )
    run.add_argument(
        "--no-capture-exceptions",
        dest="capture_exceptions",
        action="store_false",
        help="Disable unhandled-exception capture.",
    )
    run.add_argument(
        "--capture-logs",
        dest="capture_logs",
        action="store_true",
        default=None,
        help="Capture Python log records (off by default).",
    )
    run.add_argument(
        "--no-capture-logs",
        dest="capture_logs",
        action="store_false",
        help="Disable log capture.",
    )
    run.add_argument(
        "--log-level",
        type=int,
        metavar="LEVEL",
        default=None,
        help="Minimum log level to capture as an int (e.g. 20=INFO, 30=WARNING).",
    )
    run.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        metavar="COMMAND [ARGS...]",
        help="The command to wrap. Use `--` to disambiguate from Smello flags.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Console-script entry point. Returns a process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.subcommand != "run":
        parser.print_help(sys.stderr)
        return 2

    command = list(args.command)
    # argparse.REMAINDER preserves a leading `--` (it doesn't consume it the
    # way a normal positional would). Strip it so users can write
    # `smello run -- pytest tests/` for disambiguation.
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        print("smello run: no command specified", file=sys.stderr)
        print("usage: smello run [OPTIONS] [--] COMMAND [ARGS...]", file=sys.stderr)
        return 2

    env = _build_child_env(args)
    executable, command = _resolve_executable(command)

    try:
        os.execvpe(executable, command, env)
    except FileNotFoundError:
        print(f"smello run: command not found: {command[0]}", file=sys.stderr)
        return 127
    except PermissionError:
        print(
            f"smello run: permission denied: {command[0]}\n"
            "If this is a Python script, prefix the command with `python`:\n"
            f"  smello run -- python {command[0]}",
            file=sys.stderr,
        )
        return 126
    return 0  # unreachable on success (execvpe replaces the process)


if __name__ == "__main__":
    sys.exit(main())
