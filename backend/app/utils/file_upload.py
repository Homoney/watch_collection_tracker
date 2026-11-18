import logging
import re
import uuid
from pathlib import Path
from typing import Optional, Tuple

from fastapi import UploadFile
from PIL import Image as PILImage

from app.config import settings

logger = logging.getLogger(__name__)

# Allowed MIME types for image uploads
ALLOWED_MIME_TYPES = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
]

# Allowed file extensions
ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp"]

# Allowed MIME types for document uploads (receipts, certificates, etc.)
ALLOWED_DOCUMENT_MIME_TYPES = [
    "application/pdf",
    "image/jpeg",
    "image/png",
]

# Allowed document extensions
ALLOWED_DOCUMENT_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png"]

# Formats Pillow must detect in the bytes (not just the declared type)
IMAGE_FORMAT_MIME = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "GIF": "image/gif",
    "WEBP": "image/webp",
}
DOCUMENT_IMAGE_FORMATS = {"JPEG", "PNG"}

# Refuse images that decode to more pixels than this (decompression bombs).
MAX_IMAGE_PIXELS = 100_000_000
PILImage.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS

CHUNK_SIZE = 1024 * 1024


class InvalidUploadError(ValueError):
    """The uploaded bytes are not an allowed file, or are too large."""


def _write_limited(file: UploadFile, dest: Path, max_bytes: int) -> int:
    """Copy the upload to dest in chunks, stopping once it passes max_bytes."""
    file.file.seek(0)
    written = 0
    try:
        with open(dest, "wb") as buffer:
            while True:
                chunk = file.file.read(CHUNK_SIZE)
                if not chunk:
                    break
                written += len(chunk)
                if written > max_bytes:
                    raise InvalidUploadError(
                        f"File size exceeds maximum allowed size of "
                        f"{max_bytes / (1024 * 1024):g}MB"
                    )
                buffer.write(chunk)
    except BaseException:
        dest.unlink(missing_ok=True)
        raise
    return written


def inspect_image(path: Path, allowed_formats=IMAGE_FORMAT_MIME.keys()) -> tuple:
    """Check the file really is an allowed image. Returns (mime, width, height)."""
    try:
        with PILImage.open(path) as img:
            fmt = img.format
            width, height = img.size
            img.verify()
    except (PILImage.DecompressionBombError, PILImage.DecompressionBombWarning):
        raise InvalidUploadError("Image dimensions are too large")
    except Exception:
        raise InvalidUploadError("File is not a valid image")
    if fmt not in allowed_formats:
        raise InvalidUploadError("File is not an allowed image type")
    if width * height > MAX_IMAGE_PIXELS:
        raise InvalidUploadError("Image dimensions are too large")
    return IMAGE_FORMAT_MIME[fmt], width, height


def inspect_document(path: Path) -> str:
    """Check a service document is a real PDF or JPEG/PNG. Returns its MIME type."""
    with open(path, "rb") as fh:
        head = fh.read(5)
    if head == b"%PDF-":
        return "application/pdf"
    mime, _, _ = inspect_image(path, DOCUMENT_IMAGE_FORMATS)
    return mime


def validate_image_file(file: UploadFile) -> Tuple[bool, str]:
    """
    Validate that the uploaded file is a valid image.

    Args:
        file: The uploaded file to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        allowed_types_str = ", ".join(ALLOWED_MIME_TYPES)
        return False, f"Invalid file type. Allowed types: {allowed_types_str}"

    # Check file extension
    if file.filename:
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            allowed_ext_str = ", ".join(ALLOWED_EXTENSIONS)
            return (
                False,
                f"Invalid file extension. Allowed extensions: {allowed_ext_str}",
            )

    return True, ""


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent directory traversal and other attacks.

    Args:
        filename: The original filename

    Returns:
        A sanitized filename
    """
    # Get the file extension
    name = Path(filename).stem
    ext = Path(filename).suffix.lower()

    # Remove any non-alphanumeric characters except hyphens and underscores
    name = re.sub(r"[^\w\s-]", "", name)

    # Replace spaces with underscores
    name = re.sub(r"\s+", "_", name)

    # Remove leading/trailing underscores
    name = name.strip("_")

    # Limit length to 100 characters
    if len(name) > 100:
        name = name[:100]

    # If name is empty after sanitization, generate a random name
    if not name:
        name = f"image_{uuid.uuid4().hex[:8]}"

    return f"{name}{ext}"


def get_image_dimensions(file_path: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Extract image dimensions using Pillow.

    Args:
        file_path: Path to the image file

    Returns:
        Tuple of (width, height) or (None, None) if extraction fails
    """
    try:
        with PILImage.open(file_path) as img:
            return img.width, img.height
    except Exception as e:
        logger.warning(f"Failed to extract image dimensions: {e}")
        return None, None


def save_uploaded_file(
    file: UploadFile, watch_id: uuid.UUID, upload_dir: str = settings.UPLOAD_DIR
) -> dict:
    """
    Save an uploaded file to disk and return metadata.

    Args:
        file: The uploaded file
        watch_id: The UUID of the watch this image belongs to
        upload_dir: Base directory for uploads

    Returns:
        Dictionary containing file metadata:
        {
            'file_path': str,      # Relative path from upload_dir
            'file_name': str,      # Sanitized filename
            'file_size': int,      # File size in bytes
            'mime_type': str,      # MIME type
            'width': int | None,   # Image width in pixels
            'height': int | None   # Image height in pixels
        }
    """
    # Create watch-specific directory
    watch_dir = Path(upload_dir) / str(watch_id)
    watch_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename
    sanitized_name = sanitize_filename(file.filename or "image.jpg")

    # Handle duplicate filenames by appending a counter
    file_path = watch_dir / sanitized_name
    counter = 1
    name_stem = Path(sanitized_name).stem
    name_ext = Path(sanitized_name).suffix
    while file_path.exists():
        sanitized_name = f"{name_stem}_{counter}{name_ext}"
        file_path = watch_dir / sanitized_name
        counter += 1

    # Save file to disk (size-capped), then check the bytes are an image
    file_size = _write_limited(file, file_path, settings.MAX_UPLOAD_SIZE)
    try:
        mime_type, width, height = inspect_image(file_path)
    except InvalidUploadError:
        file_path.unlink(missing_ok=True)
        raise

    # Build relative path (watch_id/filename)
    relative_path = f"{watch_id}/{sanitized_name}"

    return {
        "file_path": relative_path,
        "file_name": sanitized_name,
        "file_size": file_size,
        "mime_type": mime_type,
        "width": width,
        "height": height,
    }


def validate_document_file(file: UploadFile) -> Tuple[bool, str]:
    """
    Validate that the uploaded file is a valid document (PDF or image).

    Args:
        file: The uploaded file to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check MIME type
    if file.content_type not in ALLOWED_DOCUMENT_MIME_TYPES:
        allowed_types_str = ", ".join(ALLOWED_DOCUMENT_MIME_TYPES)
        return False, f"Invalid file type. Allowed types: {allowed_types_str}"

    # Check file extension
    if file.filename:
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_DOCUMENT_EXTENSIONS:
            allowed_ext_str = ", ".join(ALLOWED_DOCUMENT_EXTENSIONS)
            return (
                False,
                f"Invalid file extension. Allowed extensions: {allowed_ext_str}",
            )

    return True, ""


def save_service_document(
    file: UploadFile,
    watch_id: uuid.UUID,
    service_id: uuid.UUID,
    upload_dir: str = settings.UPLOAD_DIR,
) -> dict:
    """
    Save a service document to disk and return metadata.

    Args:
        file: The uploaded file
        watch_id: The UUID of the watch
        service_id: The UUID of the service history record
        upload_dir: Base directory for uploads

    Returns:
        Dictionary containing file metadata:
        {
            'file_path': str,      # Relative path from upload_dir
            'file_name': str,      # Sanitized filename
            'file_size': int,      # File size in bytes
            'mime_type': str       # MIME type
        }
    """
    # Create service-specific directory
    service_dir = Path(upload_dir) / "service-docs" / str(watch_id) / str(service_id)
    service_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename
    sanitized_name = sanitize_filename(file.filename or "document.pdf")

    # Handle duplicate filenames by appending a counter
    file_path = service_dir / sanitized_name
    counter = 1
    name_stem = Path(sanitized_name).stem
    name_ext = Path(sanitized_name).suffix
    while file_path.exists():
        sanitized_name = f"{name_stem}_{counter}{name_ext}"
        file_path = service_dir / sanitized_name
        counter += 1

    # Save file to disk (size-capped), then check the bytes match the type
    file_size = _write_limited(file, file_path, settings.MAX_DOCUMENT_SIZE)
    try:
        mime_type = inspect_document(file_path)
    except InvalidUploadError:
        file_path.unlink(missing_ok=True)
        raise

    # Build relative path (watch_id/service_id/filename)
    relative_path = f"{watch_id}/{service_id}/{sanitized_name}"

    return {
        "file_path": relative_path,
        "file_name": sanitized_name,
        "file_size": file_size,
        "mime_type": mime_type,
    }


def delete_file(file_path: str, upload_dir: str = settings.UPLOAD_DIR) -> bool:
    """
    Safely delete a file from storage.

    Args:
        file_path: Relative path to the file (e.g., "watch_id/filename.jpg")
        upload_dir: Base directory for uploads

    Returns:
        True if file was deleted, False otherwise
    """
    try:
        full_path = Path(upload_dir) / file_path

        # Security check: ensure the path is within upload_dir
        resolved_path = full_path.resolve()
        upload_dir_resolved = Path(upload_dir).resolve()

        if not resolved_path.is_relative_to(upload_dir_resolved):
            logger.warning(
                f"Security warning: Attempted to delete file outside upload directory: {file_path}"
            )
            return False

        # Delete the file if it exists
        if resolved_path.exists() and resolved_path.is_file():
            resolved_path.unlink()
            return True

        return False
    except Exception as e:
        logger.warning(f"Failed to delete file {file_path}: {e}")
        return False
