"""FastAPI application setup with Tortoise ORM."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from tortoise.contrib.fastapi import register_tortoise

from smello_server.routes.api import router as api_router


def _get_db_url() -> str:
    db_path = os.environ.get("SMELLO_DB_PATH")
    if db_path:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite://{db_path}"
    default_dir = Path.home() / ".smello"
    default_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite://{default_dir / 'smello.db'}"


def _get_frontend_dir() -> Path | None:
    frontend_dir = os.environ.get("SMELLO_FRONTEND_DIR")
    if frontend_dir:
        p = Path(frontend_dir)
        if p.is_dir() and (p / "index.html").is_file():
            return p
    return None


def create_app(db_url: str | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(title="Smello")

    application.include_router(api_router)

    frontend_dir = _get_frontend_dir()
    if frontend_dir:
        assets_dir = frontend_dir / "assets"
        if assets_dir.is_dir():
            application.mount(
                "/assets", StaticFiles(directory=str(assets_dir)), name="assets"
            )

        index_html = frontend_dir / "index.html"

        @application.get("/{path:path}", include_in_schema=False)
        async def _serve_spa(path: str) -> FileResponse:
            # Serve the file if it exists in the frontend dir, otherwise index.html
            file_path = frontend_dir / path
            if path and file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(index_html)

    register_tortoise(
        application,
        db_url=db_url or _get_db_url(),
        modules={"models": ["smello_server.models"]},
        generate_schemas=True,
        add_exception_handlers=True,
    )

    return application
