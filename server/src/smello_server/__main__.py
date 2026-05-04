"""CLI entry point: `smello-server run` or `python -m smello_server`."""

import json
import logging
import os
import threading
import webbrowser
from pathlib import Path
from typing import Annotated

import typer
import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

logger = logging.getLogger("smello_server")

_DEFAULT_DB_DIR = Path.home() / ".smello"
_DEFAULT_DB_PATH = _DEFAULT_DB_DIR / "smello.db"

app = typer.Typer(add_completion=False)


def _get_url(host: str, port: int) -> str:
    if host in ("0.0.0.0", "127.0.0.1", "localhost"):
        return f"http://localhost:{port}"
    return f"http://{host}:{port}"


def _print_banner(host: str, port: int):
    console = Console()
    url = _get_url(host, port)

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


@app.command()
def run(
    host: Annotated[str, typer.Option(help="Host to bind to.")] = "0.0.0.0",
    port: Annotated[int, typer.Option(help="Port to bind to.")] = 5110,
    db_path: Annotated[
        str | None,
        typer.Option(
            help=f"Path to SQLite database file (default: {_DEFAULT_DB_PATH})."
        ),
    ] = None,
    reload: Annotated[
        bool, typer.Option(help="Enable auto-reload on code changes.")
    ] = False,
    open_browser: Annotated[
        bool, typer.Option("--open/--no-open", help="Open the dashboard in a browser.")
    ] = True,
):
    """Start the Smello server."""
    if db_path:
        os.environ["SMELLO_DB_PATH"] = db_path

    resolved_db = db_path or os.environ.get("SMELLO_DB_PATH") or str(_DEFAULT_DB_PATH)
    logging.basicConfig(level=logging.INFO)
    logger.info("Database: %s", resolved_db)

    _print_banner(host, port)

    if open_browser:
        url = _get_url(host, port)
        threading.Timer(1.5, webbrowser.open, args=(url,)).start()

    uvicorn.run(
        "smello_server.app:create_app",
        factory=True,
        host=host,
        port=port,
        log_level="info",
        reload=reload,
    )


@app.command("openapi-export")
def openapi_export(
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Where to write the OpenAPI schema."),
    ] = Path("frontend/openapi.json"),
):
    """Export the FastAPI OpenAPI schema to a JSON file.

    Used by the frontend's `openapi-typescript` step to generate TS types.
    """
    # Imported lazily so unrelated CLI invocations (e.g. `--help`) don't pay
    # the cost of loading FastAPI + Tortoise.
    from smello_server.app import create_app  # noqa: PLC0415

    schema = create_app().openapi()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(schema, indent=2) + "\n")
    typer.echo(f"Wrote OpenAPI schema → {output}")


def main():
    app()


if __name__ == "__main__":
    main()
