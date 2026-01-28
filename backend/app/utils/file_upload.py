import os
import re
import uuid
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile
from PIL import Image
from app.config import settings


# Allowed MIME types for image uploads
ALLOWED_MIME_TYPES = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
]

# Allowed file extensions
ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp"]


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
            return False, f"Invalid file extension. Allowed extensions: {allowed_ext_str}"

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
    name = re.sub(r'[^\w\s-]', '', name)

    # Replace spaces with underscores
    name = re.sub(r'\s+', '_', name)

    # Remove leading/trailing underscores
    name = name.strip('_')

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
        with Image.open(file_path) as img:
            return img.width, img.height
    except Exception as e:
        print(f"Failed to extract image dimensions: {e}")
        return None, None


def save_uploaded_file(
    file: UploadFile,
    watch_id: uuid.UUID,
    upload_dir: str = settings.UPLOAD_DIR
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

    # Save file to disk
    with open(file_path, "wb") as buffer:
        content = file.file.read()
        buffer.write(content)

    # Get file size
    file_size = file_path.stat().st_size

    # Extract image dimensions
    width, height = get_image_dimensions(str(file_path))

    # Build relative path (watch_id/filename)
    relative_path = f"{watch_id}/{sanitized_name}"

    return {
        "file_path": relative_path,
        "file_name": sanitized_name,
        "file_size": file_size,
        "mime_type": file.content_type or "image/jpeg",
        "width": width,
        "height": height,
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

        if not str(resolved_path).startswith(str(upload_dir_resolved)):
            print(f"Security warning: Attempted to delete file outside upload directory: {file_path}")
            return False

        # Delete the file if it exists
        if resolved_path.exists() and resolved_path.is_file():
            resolved_path.unlink()
            return True

        return False
    except Exception as e:
        print(f"Failed to delete file {file_path}: {e}")
        return False
