"""Serve uploaded files, only with a valid signed URL (see core/file_urls.py)."""

from pathlib import Path
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from app.config import settings
from app.core.file_urls import verify_upload_uri

router = APIRouter()

FILE_HEADERS = {
    "Cache-Control": "private, max-age=3600",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}


@router.get("/uploads/{file_path:path}", include_in_schema=False)
def serve_upload(file_path: str, request: Request):
    # Check the signature against the URI exactly as the browser sent it
    raw_path = request.scope.get("raw_path", b"").decode("latin-1")
    query = request.scope.get("query_string", b"").decode("latin-1")
    if not verify_upload_uri(f"{raw_path}?{query}"):
        raise HTTPException(status_code=403, detail="Forbidden")

    root = Path(settings.UPLOAD_DIR).resolve()
    target = (root / unquote(raw_path[len("/uploads/") :])).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise HTTPException(status_code=404, detail="Not Found")
    return FileResponse(target, headers=FILE_HEADERS)
