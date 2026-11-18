"""Internal check used by nginx before it serves a file under /uploads/."""

from fastapi import APIRouter, Header, Response, status

from app.core.file_urls import verify_upload_uri

router = APIRouter()


@router.get("/verify", include_in_schema=False)
def verify_upload(x_original_uri: str = Header(default="")):
    """Return 204 if the signed upload URL is valid, otherwise 403."""
    if verify_upload_uri(x_original_uri):
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return Response(status_code=status.HTTP_403_FORBIDDEN)
