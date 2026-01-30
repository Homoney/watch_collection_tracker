import re
import uuid
from io import BytesIO
from pathlib import Path
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup
from PIL import Image


def fetch_watch_images(
    brand: str,
    model: str,
    watch_id: str,
    limit: int = 3,
    storage_path: str = "/app/storage",
    reference_number: Optional[str] = None,
    offset: int = 0,
) -> List[dict]:
    """
    Fetch watch images from Google Images using web scraping.

    Args:
        brand: Watch brand name
        model: Watch model name
        watch_id: UUID of the watch
        limit: Number of images to fetch (default: 3)
        storage_path: Base storage path
        reference_number: Optional reference number for more accurate search
        offset: Number of images to skip (for pagination)

    Returns:
        List of image metadata dicts with file info

    Raises:
        Exception: If image fetching fails
    """
    # Create search query - prefer reference number for accuracy
    if reference_number:
        search_query = f"{brand} {reference_number} watch"
    else:
        search_query = f"{brand} {model} watch"

    # Create upload directory for this watch
    upload_dir = Path(storage_path) / "uploads" / watch_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Fetch more image URLs than needed to account for offset and failures
        # Request double the needed amount to ensure we have enough after filtering
        fetch_count = offset + limit + 10
        image_urls = _scrape_google_images(search_query, fetch_count)

        if not image_urls:
            raise Exception("No images found in search results")

        # Skip offset images and take the next 'limit' images
        # Get extras in case some fail
        urls_to_fetch = image_urls[offset : offset + limit + 10]

        if not urls_to_fetch:
            raise Exception("No more images available at this offset")

        # Download and process images
        image_metadata = []

        for idx, url in enumerate(urls_to_fetch):
            # Stop once we have enough successful downloads
            if len(image_metadata) >= limit:
                break

            try:
                # Download image (use offset + idx for unique file naming)
                metadata = _download_and_process_image(
                    url, watch_id, offset + idx, upload_dir
                )
                if metadata:
                    image_metadata.append(metadata)

            except Exception as e:
                print(f"Failed to download image {offset + idx + 1} from {url}: {e}")
                continue

        if not image_metadata:
            raise Exception("Failed to download any images")

        return image_metadata

    except Exception as e:
        raise Exception(f"Failed to fetch images from Google: {str(e)}")


def _scrape_google_images(query: str, limit: int) -> List[str]:
    """
    Scrape Google Images search results for image URLs.

    Args:
        query: Search query
        limit: Maximum number of URLs to return

    Returns:
        List of image URLs
    """
    # URL encode the query
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&tbm=isch"

    # Headers to mimic a browser
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
    }

    try:
        # Make request to Google Images
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(search_url, headers=headers)
            response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.text, "lxml")

        # Extract image URLs from various possible locations
        image_urls = []

        # Method 1: Look for img tags with specific attributes
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if src and src.startswith("http") and "gstatic" not in src:
                image_urls.append(src)
                if len(image_urls) >= limit * 2:  # Get extras in case some fail
                    break

        # Method 2: Extract URLs from script tags (backup method)
        if len(image_urls) < limit:
            scripts = soup.find_all("script")
            for script in scripts:
                if script.string:
                    # Look for URLs in the format ["https://..."]
                    urls = re.findall(
                        r'https?://[^"\']+\.(?:jpg|jpeg|png|webp)', script.string
                    )
                    for url in urls:
                        if "encrypted" not in url and url not in image_urls:
                            image_urls.append(url)
                            if len(image_urls) >= limit * 2:
                                break

        # Filter and deduplicate
        filtered_urls = []
        seen = set()
        for url in image_urls:
            # Skip base64, very small images, and duplicates
            if url not in seen and not url.startswith("data:"):
                filtered_urls.append(url)
                seen.add(url)
                if len(filtered_urls) >= limit * 2:
                    break

        print(f"Found {len(filtered_urls)} image URLs for query: {query}")
        # Return extras in case some fail to download
        return filtered_urls[: limit * 2]

    except Exception as e:
        print(f"Error scraping Google Images: {e}")
        return []


def _download_and_process_image(
    url: str, watch_id: str, idx: int, upload_dir: Path
) -> Optional[dict]:
    """
    Download and process a single image.

    Args:
        url: Image URL
        watch_id: Watch UUID
        idx: Image index
        upload_dir: Upload directory path

    Returns:
        Image metadata dict or None if failed
    """
    try:
        # Download image with timeout
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get("content-type", "")
            if "image" not in content_type:
                print(f"URL does not point to an image: {content_type}")
                return None

            # Load image
            img_data = BytesIO(response.content)

            with Image.open(img_data) as img:
                # Skip very small images (likely icons or logos)
                if img.width < 200 or img.height < 200:
                    print(f"Image too small: {img.width}x{img.height}")
                    return None

                # Generate unique filename
                file_name = f"google_{idx + 1}_{uuid.uuid4().hex[:8]}.jpg"
                dest_path = upload_dir / file_name

                # Convert RGBA to RGB if necessary
                if img.mode in ("RGBA", "LA", "P"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(
                        img, mask=img.split()[-1] if img.mode == "RGBA" else None
                    )
                    img = background

                # Save to final location
                img.save(dest_path, "JPEG", quality=85, optimize=True)

                # Get image dimensions and file size
                width, height = img.size
                file_size = dest_path.stat().st_size

            # Create metadata
            return {
                "file_path": f"{watch_id}/{file_name}",
                "file_name": file_name,
                "file_size": file_size,
                "mime_type": "image/jpeg",
                "width": width,
                "height": height,
                "source": "google_images",
                "is_primary": idx == 0,  # First image is primary
                "sort_order": idx,
            }

    except Exception as e:
        print(f"Error downloading image from {url}: {e}")
        return None


async def fetch_watch_images_from_urls(
    urls: List[str], watch_id: str, storage_path: str = "/app/storage"
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
                    if img.mode in ("RGBA", "LA", "P"):
                        background = Image.new("RGB", img.size, (255, 255, 255))
                        if img.mode == "P":
                            img = img.convert("RGBA")
                        background.paste(
                            img, mask=img.split()[-1] if img.mode == "RGBA" else None
                        )
                        img = background

                    # Save image
                    img.save(dest_path, "JPEG", quality=85)

                    # Get metadata
                    width, height = img.size
                    file_size = dest_path.stat().st_size

                # Create metadata
                image_metadata.append(
                    {
                        "file_path": f"{watch_id}/{file_name}",
                        "file_name": file_name,
                        "file_size": file_size,
                        "mime_type": "image/jpeg",
                        "width": width,
                        "height": height,
                        "source": "url_import",
                        "is_primary": idx == 0,
                        "sort_order": idx,
                    }
                )

            except Exception as e:
                print(f"Failed to download image from {url}: {e}")
                continue

    return image_metadata
