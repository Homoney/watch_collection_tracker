import os
import uuid
from typing import List, Optional
from pathlib import Path
import httpx
from google_images_download import google_images_download
from PIL import Image
from io import BytesIO


def fetch_watch_images(
    brand: str,
    model: str,
    watch_id: str,
    limit: int = 3,
    storage_path: str = "/app/storage"
) -> List[dict]:
    """
    Fetch watch images from Google Images.

    Args:
        brand: Watch brand name
        model: Watch model name
        watch_id: UUID of the watch
        limit: Number of images to fetch (default: 3)
        storage_path: Base storage path

    Returns:
        List of image metadata dicts with file info

    Raises:
        Exception: If image fetching fails
    """
    # Create search query
    search_query = f"{brand} {model} watch"

    # Create upload directory for this watch
    upload_dir = Path(storage_path) / "uploads" / watch_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Temporary download directory
    temp_dir = Path(storage_path) / "temp" / str(uuid.uuid4())
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Configure google_images_download
        response = google_images_download.googleimagesdownload()

        arguments = {
            "keywords": search_query,
            "limit": limit,
            "print_urls": False,
            "no_directory": True,
            "silent_mode": True,
            "output_directory": str(temp_dir),
            "image_directory": "",
            "format": "jpg",
            "type": "photo",
            "size": "medium",  # Medium sized images
            "aspect_ratio": "square",  # Prefer square images for watches
        }

        # Download images
        paths = response.download(arguments)

        # Process downloaded images
        image_metadata = []

        # Get the downloaded files
        downloaded_files = list(temp_dir.glob("*"))

        for idx, source_path in enumerate(downloaded_files[:limit]):
            if not source_path.is_file():
                continue

            try:
                # Generate unique filename
                file_ext = source_path.suffix or '.jpg'
                file_name = f"google_{idx + 1}_{uuid.uuid4().hex[:8]}{file_ext}"
                dest_path = upload_dir / file_name

                # Open and validate image
                with Image.open(source_path) as img:
                    # Convert RGBA to RGB if necessary
                    if img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background

                    # Save to final location
                    img.save(dest_path, 'JPEG', quality=85)

                    # Get image dimensions and file size
                    width, height = img.size
                    file_size = dest_path.stat().st_size

                # Create metadata
                image_metadata.append({
                    'file_path': f"{watch_id}/{file_name}",
                    'file_name': file_name,
                    'file_size': file_size,
                    'mime_type': 'image/jpeg',
                    'width': width,
                    'height': height,
                    'source': 'google_images',
                    'is_primary': idx == 0,  # First image is primary
                    'sort_order': idx
                })

            except Exception as e:
                print(f"Failed to process image {source_path}: {e}")
                continue

        return image_metadata

    except Exception as e:
        raise Exception(f"Failed to fetch images from Google: {str(e)}")

    finally:
        # Clean up temp directory
        try:
            for file in temp_dir.glob("*"):
                file.unlink()
            temp_dir.rmdir()
        except:
            pass


async def fetch_watch_images_from_urls(
    urls: List[str],
    watch_id: str,
    storage_path: str = "/app/storage"
) -> List[dict]:
    """
    Download watch images from provided URLs.

    Args:
        urls: List of image URLs to download
        watch_id: UUID of the watch
        storage_path: Base storage path

    Returns:
        List of image metadata dicts with file info
    """
    upload_dir = Path(storage_path) / "uploads" / watch_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    image_metadata = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for idx, url in enumerate(urls):
            try:
                # Download image
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()

                # Load image
                img_data = BytesIO(response.content)

                with Image.open(img_data) as img:
                    # Generate filename
                    file_name = f"url_{idx + 1}_{uuid.uuid4().hex[:8]}.jpg"
                    dest_path = upload_dir / file_name

                    # Convert RGBA to RGB if necessary
                    if img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background

                    # Save image
                    img.save(dest_path, 'JPEG', quality=85)

                    # Get metadata
                    width, height = img.size
                    file_size = dest_path.stat().st_size

                # Create metadata
                image_metadata.append({
                    'file_path': f"{watch_id}/{file_name}",
                    'file_name': file_name,
                    'file_size': file_size,
                    'mime_type': 'image/jpeg',
                    'width': width,
                    'height': height,
                    'source': 'url_import',
                    'is_primary': idx == 0,
                    'sort_order': idx
                })

            except Exception as e:
                print(f"Failed to download image from {url}: {e}")
                continue

    return image_metadata
