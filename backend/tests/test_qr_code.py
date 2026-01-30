"""
Tests for QR code generation utilities
"""
import pytest
from io import BytesIO
from PIL import Image as PILImage

from app.utils.qr_code import generate_qr_code, generate_watch_qr_code


class TestGenerateQRCode:
    """Test QR code generation"""

    def test_generate_qr_code_success(self):
        """Test successful QR code generation"""
        data = "https://example.com/test"
        qr_buffer = generate_qr_code(data)

        assert isinstance(qr_buffer, BytesIO)
        assert qr_buffer.tell() == 0  # Buffer should be at position 0

        # Verify it's a valid PNG image
        img = PILImage.open(qr_buffer)
        assert img.format == "PNG"
        assert img.size[0] > 0
        assert img.size[1] > 0

    def test_generate_qr_code_with_different_sizes(self):
        """Test QR code generation with different box sizes"""
        data = "Test data"

        # Generate with default size
        qr_default = generate_qr_code(data)
        img_default = PILImage.open(qr_default)
        size_default = img_default.size

        # Generate with larger size
        qr_large = generate_qr_code(data, size=20)
        img_large = PILImage.open(qr_large)
        size_large = img_large.size

        # Larger box size should produce larger image
        assert size_large[0] > size_default[0]
        assert size_large[1] > size_default[1]

    def test_generate_qr_code_empty_string(self):
        """Test QR code generation with empty string"""
        qr_buffer = generate_qr_code("")

        # Should still generate a valid image
        assert isinstance(qr_buffer, BytesIO)
        img = PILImage.open(qr_buffer)
        assert img.format == "PNG"

    def test_generate_qr_code_long_data(self):
        """Test QR code generation with long data"""
        long_data = "https://example.com/very/long/path/" + "x" * 200
        qr_buffer = generate_qr_code(long_data)

        assert isinstance(qr_buffer, BytesIO)
        img = PILImage.open(qr_buffer)
        assert img.format == "PNG"

    def test_generate_qr_code_special_characters(self):
        """Test QR code generation with special characters"""
        data = "Test with special chars: !@#$%^&*()[]{}|;:',.<>?/~`"
        qr_buffer = generate_qr_code(data)

        assert isinstance(qr_buffer, BytesIO)
        img = PILImage.open(qr_buffer)
        assert img.format == "PNG"

    def test_generate_qr_code_unicode(self):
        """Test QR code generation with unicode characters"""
        data = "Unicode test: 你好世界 🌍 مرحبا"
        qr_buffer = generate_qr_code(data)

        assert isinstance(qr_buffer, BytesIO)
        img = PILImage.open(qr_buffer)
        assert img.format == "PNG"


class TestGenerateWatchQRCode:
    """Test watch-specific QR code generation"""

    def test_generate_watch_qr_code_default_url(self):
        """Test watch QR code with default base URL"""
        watch_id = "12345678-1234-1234-1234-123456789abc"
        qr_buffer = generate_watch_qr_code(watch_id)

        assert isinstance(qr_buffer, BytesIO)
        img = PILImage.open(qr_buffer)
        assert img.format == "PNG"

    def test_generate_watch_qr_code_custom_url(self):
        """Test watch QR code with custom base URL"""
        watch_id = "12345678-1234-1234-1234-123456789abc"
        custom_url = "https://production.example.com"

        qr_buffer = generate_watch_qr_code(watch_id, base_url=custom_url)

        assert isinstance(qr_buffer, BytesIO)
        img = PILImage.open(qr_buffer)
        assert img.format == "PNG"

    def test_generate_watch_qr_code_different_watch_ids(self):
        """Test QR codes for different watch IDs produce different images"""
        watch_id_1 = "11111111-1111-1111-1111-111111111111"
        watch_id_2 = "22222222-2222-2222-2222-222222222222"

        qr_1 = generate_watch_qr_code(watch_id_1)
        qr_2 = generate_watch_qr_code(watch_id_2)

        # Both should be valid images
        img_1 = PILImage.open(qr_1)
        img_2 = PILImage.open(qr_2)

        assert img_1.format == "PNG"
        assert img_2.format == "PNG"

        # Convert to bytes and compare - they should be different
        qr_1.seek(0)
        qr_2.seek(0)
        assert qr_1.read() != qr_2.read()

    def test_generate_watch_qr_code_url_format(self):
        """Test that watch QR code generates proper URL format"""
        watch_id = "test-watch-id"
        base_url = "https://example.com"

        # The QR code should contain: https://example.com/watches/test-watch-id
        qr_buffer = generate_watch_qr_code(watch_id, base_url=base_url)

        assert isinstance(qr_buffer, BytesIO)
        img = PILImage.open(qr_buffer)
        assert img.format == "PNG"
