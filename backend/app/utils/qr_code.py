from io import BytesIO

import qrcode
from PIL import Image


def generate_qr_code(data: str, size: int = 10) -> BytesIO:
    """
    Generate a QR code image from the given data.

    Args:
        data: The data to encode in the QR code
        size: The size of each box in the QR code (default: 10)

    Returns:
        BytesIO: A buffer containing the QR code image in PNG format
    """
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,  # Controls the size (1 is smallest, 40 is largest)
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=4,
    )

    # Add data and generate the QR code
    qr.add_data(data)
    qr.make(fit=True)

    # Create an image from the QR code
    img = qr.make_image(fill_color="black", back_color="white")

    # Save to BytesIO buffer
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer


def generate_watch_qr_code(
    watch_id: str, base_url: str = "http://localhost:8080"
) -> BytesIO:
    """
    Generate a QR code for a specific watch that links to its detail page.

    Args:
        watch_id: The UUID of the watch
        base_url: The base URL of the application

    Returns:
        BytesIO: A buffer containing the QR code image in PNG format
    """
    watch_url = f"{base_url}/watches/{watch_id}"
    return generate_qr_code(watch_url)
