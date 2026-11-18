"""Time-limited signed URLs for files under /uploads/.

nginx serves the files, but only after asking the backend (auth_request) to
check the signature. Browsers load images with plain <img> tags that cannot
send a Bearer token, so the API hands out URLs that carry their own proof.

Expiry is rounded up to a window boundary so a URL stays identical for a
while, which keeps browser and React Query caching effective.
"""

import hashlib
import hmac
import time
from typing import Optional
from urllib.parse import parse_qs, quote, urlsplit

from app.config import settings

UPLOADS_PREFIX = "/uploads/"


def _key() -> bytes:
    # Derive a dedicated key so upload signatures can never be confused
    # with JWT signatures made from the same secret.
    return hmac.new(
        settings.SECRET_KEY.encode(), b"upload-url-v1", hashlib.sha256
    ).digest()


def _signature(path: str, expires: int) -> str:
    msg = f"{path}\n{expires}".encode()
    return hmac.new(_key(), msg, hashlib.sha256).hexdigest()


def sign_upload_url(relative_path: str, now: Optional[float] = None) -> str:
    """Return a signed URL for a file stored at UPLOAD_DIR/relative_path."""
    path = UPLOADS_PREFIX + quote(relative_path.lstrip("/"), safe="/")
    ttl = max(60, settings.UPLOAD_URL_TTL_SECONDS)
    now = time.time() if now is None else now
    # Valid for between one and two TTL windows.
    expires = (int(now) // ttl + 2) * ttl
    return f"{path}?expires={expires}&sig={_signature(path, expires)}"


def verify_upload_uri(uri: str, now: Optional[float] = None) -> bool:
    """Check a raw request URI (path + query) produced by sign_upload_url."""
    if not uri:
        return False
    parts = urlsplit(uri)
    path = parts.path
    if not path.startswith(UPLOADS_PREFIX) or ".." in path or "\\" in path:
        return False
    query = parse_qs(parts.query)
    try:
        expires = int(query["expires"][0])
        sig = query["sig"][0]
    except (KeyError, IndexError, ValueError):
        return False
    now = time.time() if now is None else now
    if expires < now:
        return False
    return hmac.compare_digest(sig, _signature(path, expires))
