"""FastAPI application setup with Tortoise ORM."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from starlette.types import Receive, Scope, Send
from tortoise.contrib.fastapi import register_tortoise

from smello_server.routes.api import router as api_router


class SPAStaticFiles(StaticFiles):
    """StaticFiles subclass that falls back to index.html for SPA routing."""

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            await super().__call__(scope, receive, send)
        except HTTPException as exc:
            if exc.status_code == 404:
                scope["path"] = "/index.html"
                await super().__call__(scope, receive, send)
            else:
                raise


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
    # Bundled frontend shipped inside the wheel
    bundled = Path(__file__).parent / "_frontend"
    if bundled.is_dir() and (bundled / "index.html").is_file():
        return bundled
    return None


def create_app(db_url: str | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""

    application = FastAPI(title="Smello")

    application.include_router(api_router)

    frontend_dir = _get_frontend_dir()
    if frontend_dir:
        application.mount(
            "/", SPAStaticFiles(directory=str(frontend_dir), html=True), name="spa"
        )

    register_tortoise(
        application,
        db_url=db_url or _get_db_url(),
        modules={"models": ["smello_server.models"]},
        generate_schemas=True,
        add_exception_handlers=True,
    )

    return application
