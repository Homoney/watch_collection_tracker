"""Save a picture from a URL as a watch image file.

Downloads through safe_fetch (public hosts only, size cap), checks it is a
real image of at least 200 x 200 pixels, and stores it as JPEG under
UPLOAD_DIR/<watch_id>/. Returns the file's metadata, or None.
"""

import logging
import uuid
from io import BytesIO
from pathlib import Path
from typing import Callable, Optional

from PIL import Image

from app.config import settings
from app.utils.safe_fetch import fetch_bytes

logger = logging.getLogger(__name__)

MIN_SIDE = 200


def save_image_from_url(
    url: str,
    watch_id: str,
    name_prefix: str,
    upload_root: Optional[str] = None,
    fetch: Callable = fetch_bytes,
    headers: Optional[dict] = None,
) -> Optional[dict]:
    try:
        content_type, body = fetch(url, headers=headers)
    except Exception as exc:
        logger.info("Image download failed (%s)", type(exc).__name__)
        return None
    if "image" not in (content_type or ""):
        logger.info("Not an image: %s", content_type)
        return None

    upload_dir = Path(upload_root or settings.UPLOAD_DIR) / watch_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{name_prefix}_{uuid.uuid4().hex[:8]}.jpg"
    dest = upload_dir / file_name
    try:
        with Image.open(BytesIO(body)) as img:
            if img.width < MIN_SIDE or img.height < MIN_SIDE:
                logger.info("Image too small: %sx%s", img.width, img.height)
                return None
            if img.mode != "RGB":
                rgba = img.convert("RGBA")
                img = Image.new("RGB", rgba.size, (255, 255, 255))
                img.paste(rgba, mask=rgba.split()[-1])
            img.save(dest, "JPEG", quality=85, optimize=True)
            width, height = img.size
    except Exception as exc:
        logger.info("Not a usable image (%s)", type(exc).__name__)
        dest.unlink(missing_ok=True)
        return None
    return {
        "file_path": f"{watch_id}/{file_name}",
        "file_name": file_name,
        "file_size": dest.stat().st_size,
        "mime_type": "image/jpeg",
        "width": width,
        "height": height,
    }
