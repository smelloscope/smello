"""CLI entry point: `smello-server run` or `python -m smello_server`."""

import argparse
import logging
import os
from pathlib import Path

import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

logger = logging.getLogger("smello_server")

_DEFAULT_DB_DIR = Path.home() / ".smello"
_DEFAULT_DB_PATH = _DEFAULT_DB_DIR / "smello.db"


def _print_banner(host: str, port: int):
    console = Console()
    url = f"http://localhost:{port}" if host == "0.0.0.0" else f"http://{host}:{port}"

    body = Text()
    body.append("Smello is running at ", style="bold")
    body.append(url, style="bold #FFA600")
    body.append("\n\n")
    body.append(
        "If Smello's been useful, a GitHub star helps others find it too:\n",
        style="dim",
    )
    body.append("https://github.com/smelloscope/smello\n\n", style="dim")
    body.append("Got feedback or found a bug? Drop a note:\n", style="dim")
    body.append("https://github.com/smelloscope/smello/discussions", style="dim")

    console.print()
    console.print(Panel(body, border_style="#FFA600", expand=False, padding=(1, 2)))
    console.print()


def main():
    parser = argparse.ArgumentParser(
        prog="smello-server", description="Smello HTTP request inspector"
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Start the Smello server")
    run_parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    run_parser.add_argument(
        "--port", type=int, default=5110, help="Port to bind to (default: 5110)"
    )
    run_parser.add_argument(
        "--db-path",
        default=None,
        help=f"Path to SQLite database file (default: {_DEFAULT_DB_PATH})",
    )
    run_parser.add_argument(
        "--reload",
        action="store_true",
        default=False,
        help="Enable auto-reload on code changes (for development)",
    )

    args = parser.parse_args()

    if args.command is None:
        args.command = "run"
        args.host = "0.0.0.0"
        args.port = 5110
        args.db_path = None
        args.reload = False

    if args.command == "run":
        if args.db_path:
            os.environ["SMELLO_DB_PATH"] = args.db_path

        db_path = args.db_path or os.environ.get("SMELLO_DB_PATH") or _DEFAULT_DB_PATH
        logging.basicConfig(level=logging.INFO)
        logger.info("Database: %s", db_path)

        _print_banner(args.host, args.port)

        uvicorn.run(
            "smello_server.app:create_app",
            factory=True,
            host=args.host,
            port=args.port,
            log_level="info",
            reload=args.reload,
        )


if __name__ == "__main__":
    main()
