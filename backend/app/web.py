"""Serve the built web app (Vite `dist/`) from FastAPI.

/assets/* are content-hashed files and are cached for a year. Any other GET
that is not an API, upload or docs path gets a real file from dist/ if one
exists, otherwise index.html so the browser router can handle it.

This runs as the router's fallback, after every route and the usual
trailing-slash redirect have been tried, so `/api/v1/saved-searches` still
redirects to `/api/v1/saved-searches/` as it does without the web app.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles
from starlette.types import Receive, Scope, Send

RESERVED_PREFIXES = ("api", "uploads", "docs", "redoc", "openapi.json", "health")


class _ImmutableStaticFiles(StaticFiles):
    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response


def _is_reserved(path: str) -> bool:
    first = path.split("/", 1)[0]
    return first in RESERVED_PREFIXES


def mount_web_app(app: FastAPI, dist_dir: str) -> bool:
    """Add the web app routes. Returns False when there is no build to serve."""
    dist = Path(dist_dir).resolve()
    index = dist / "index.html"
    if not index.is_file():
        return False

    if (dist / "assets").is_dir():
        app.mount(
            "/assets", _ImmutableStaticFiles(directory=dist / "assets"), name="assets"
        )

    # The build is fixed for the life of the process, so list its files once.
    # A request path is only ever used as a key into this map, never joined
    # onto the file system.
    files = {
        f.relative_to(dist).as_posix(): f
        for f in dist.rglob("*")
        if f.is_file() and not f.is_symlink()
    }

    not_found = app.router.default

    async def web_app(scope: Scope, receive: Receive, send: Send) -> None:
        full_path = scope["path"].lstrip("/")
        if (
            scope["type"] != "http"
            or scope["method"] not in ("GET", "HEAD")
            or _is_reserved(full_path)
        ):
            await not_found(scope, receive, send)
            return
        found = files.get(full_path)
        if found is not None and found != index:
            response = FileResponse(found)
        else:
            response = FileResponse(index, headers={"Cache-Control": "no-cache"})
        await response(scope, receive, send)

    app.router.default = web_app
    return True
