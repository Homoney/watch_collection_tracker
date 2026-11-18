"""Serve the built web app (Vite `dist/`) from FastAPI.

/assets/* are content-hashed files and are cached for a year. Any other GET
that is not an API, upload or docs path gets a real file from dist/ if one
exists, otherwise index.html so the browser router can handle it.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles

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

    @app.api_route(
        "/{full_path:path}", methods=["GET", "HEAD"], include_in_schema=False
    )
    async def web_app(full_path: str):
        if _is_reserved(full_path):
            raise HTTPException(status_code=404, detail="Not Found")
        found = files.get(full_path)
        if found is not None and found != index:
            return FileResponse(found)
        return FileResponse(index, headers={"Cache-Control": "no-cache"})

    return True
