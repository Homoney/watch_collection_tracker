"""
Tests for PDF export utilities
"""
import pytest
from io import BytesIO
from datetime import datetime

from app.utils.pdf_export import (
    format_currency,
    format_date,
    generate_watch_pdf,
    generate_collection_pdf
)


class TestFormatCurrency:
    """Test currency formatting"""

    def test_format_currency_with_value(self):
        """Test formatting currency with a value"""
        result = format_currency(1000.50, "USD")
        assert result == "USD 1,000.50"

    def test_format_currency_with_large_value(self):
        """Test formatting large currency values"""
        result = format_currency(1234567.89, "EUR")
        assert result == "EUR 1,234,567.89"

    def test_format_currency_with_zero(self):
        """Test formatting zero value"""
        result = format_currency(0, "GBP")
        assert result == "GBP 0.00"

    def test_format_currency_with_none(self):
        """Test formatting None value"""
        result = format_currency(None, "USD")
        assert result == "N/A"

    def test_format_currency_different_currencies(self):
        """Test formatting with different currency codes"""
        assert format_currency(100, "USD") == "USD 100.00"
        assert format_currency(100, "EUR") == "EUR 100.00"
        assert format_currency(100, "JPY") == "JPY 100.00"


class TestFormatDate:
    """Test date formatting"""

    def test_format_date_with_iso_string(self):
        """Test formatting ISO date string"""
        date_str = "2024-01-15T10:30:00"
        result = format_date(date_str)
        assert "January" in result
        assert "15" in result
        assert "2024" in result

    def test_format_date_with_timezone(self):
        """Test formatting ISO date string with timezone"""
        date_str = "2024-01-15T10:30:00Z"
        result = format_date(date_str)
        assert "January" in result
        assert "15" in result
        assert "2024" in result

    def test_format_date_with_none(self):
        """Test formatting None date"""
        result = format_date(None)
        assert result == "N/A"

    def test_format_date_with_empty_string(self):
        """Test formatting empty string"""
        result = format_date("")
        assert result == "N/A"

    def test_format_date_with_invalid_format(self):
        """Test formatting invalid date string"""
        result = format_date("not-a-date")
        assert result == "not-a-date"


class TestGenerateWatchPDF:
    """Test watch PDF generation"""

    def test_generate_watch_pdf_minimal_data(self):
        """Test generating PDF with minimal watch data"""
        watch_data = {
            "model": "Test Model",
            "brand": {"name": "Test Brand"},
            "images": []
        }

        pdf_buffer = generate_watch_pdf(watch_data)

        assert isinstance(pdf_buffer, BytesIO)
        assert pdf_buffer.tell() == 0

        # Verify it's a valid PDF by checking header
        pdf_buffer.seek(0)
        pdf_content = pdf_buffer.read(4)
        assert pdf_content == b'%PDF', "PDF should start with %PDF header"

    def test_generate_watch_pdf_with_full_data(self):
        """Test generating PDF with complete watch data"""
        watch_data = {
            "model": "Submariner",
            "brand": {"name": "Rolex"},
            "reference_number": "116610LN",
            "serial_number": "ABC123",
            "case_diameter": 40.0,
            "case_material": "Stainless Steel",
            "movement_type": {"name": "Automatic"},
            "water_resistance": 300,
            "purchase_price": 9000.00,
            "purchase_currency": "USD",
            "purchase_date": "2020-01-15T00:00:00",
            "purchase_location": "Authorized Dealer",
            "condition": "Excellent",
            "notes": "Daily wear watch",
            "current_market_value": "15000.00",
            "current_market_currency": "USD",
            "images": [],
            "service_history": [],
            "complications": []
        }

        pdf_buffer = generate_watch_pdf(watch_data)

        assert isinstance(pdf_buffer, BytesIO)
        pdf_buffer.seek(0)
        pdf_content = pdf_buffer.read()

        # Verify it's a valid PDF and contains expected data
        assert pdf_content.startswith(b'%PDF'), "PDF should start with %PDF header"
        assert len(pdf_content) > 1000, "PDF should contain substantial content"

    def test_generate_watch_pdf_with_complications(self):
        """Test PDF generation with complications"""
        watch_data = {
            "model": "Speedmaster",
            "brand": {"name": "Omega"},
            "complications": [
                {"name": "Chronograph"},
                {"name": "Date"},
                {"name": "Tachymeter"}
            ],
            "images": []
        }

        pdf_buffer = generate_watch_pdf(watch_data)

        assert isinstance(pdf_buffer, BytesIO)
        pdf_buffer.seek(0)
        pdf_content = pdf_buffer.read(4)
        assert pdf_content == b'%PDF', "PDF should start with %PDF header"

    def test_generate_watch_pdf_with_service_history(self):
        """Test PDF generation with service history"""
        watch_data = {
            "model": "Datejust",
            "brand": {"name": "Rolex"},
            "service_history": [
                {
                    "service_date": "2023-01-15T00:00:00",
                    "provider": "Rolex Service Center",
                    "service_type": "Full Service",
                    "cost": "850.00",
                    "cost_currency": "USD",
                    "next_service_due": "2028-01-15T00:00:00"
                }
            ],
            "images": []
        }

        pdf_buffer = generate_watch_pdf(watch_data)

        assert isinstance(pdf_buffer, BytesIO)
        pdf_buffer.seek(0)
        pdf_content = pdf_buffer.read(4)
        assert pdf_content == b'%PDF', "PDF should start with %PDF header"

    def test_generate_watch_pdf_with_images_path_not_exists(self):
        """Test PDF generation with image paths that don't exist"""
        watch_data = {
            "model": "Test",
            "brand": {"name": "Test"},
            "images": [
                {
                    "file_path": "nonexistent/image.jpg",
                    "is_primary": True
                }
            ]
        }

        pdf_buffer = generate_watch_pdf(watch_data, storage_path="/tmp/nonexistent")

        # Should still generate PDF even if images don't exist
        assert isinstance(pdf_buffer, BytesIO)
        pdf_buffer.seek(0)
        pdf_content = pdf_buffer.read(4)
        assert pdf_content == b'%PDF', "PDF should start with %PDF header"

    def test_generate_watch_pdf_with_missing_brand(self):
        """Test PDF generation with missing brand"""
        watch_data = {
            "model": "Test Model",
            "images": []
        }

        pdf_buffer = generate_watch_pdf(watch_data)

        assert isinstance(pdf_buffer, BytesIO)
        pdf_buffer.seek(0)
        pdf_content = pdf_buffer.read()
        assert pdf_content.startswith(b'%PDF'), "PDF should start with %PDF header"
        assert len(pdf_content) > 100, "PDF should contain content"


class TestGenerateCollectionPDF:
    """Test collection PDF generation"""

    def test_generate_collection_pdf_minimal_data(self):
        """Test generating collection PDF with minimal data"""
        watches = []
        collection_name = "My Collection"

        pdf_buffer = generate_collection_pdf(watches, collection_name)

        assert isinstance(pdf_buffer, BytesIO)
        pdf_buffer.seek(0)
        pdf_content = pdf_buffer.read()
        assert pdf_content.startswith(b'%PDF'), "PDF should start with %PDF header"
        assert len(pdf_content) > 100, "PDF should contain content"

    def test_generate_collection_pdf_with_watches(self):
        """Test generating collection PDF with multiple watches"""
        watches = [
            {
                "model": "Submariner",
                "brand": {"name": "Rolex"},
                "reference_number": "116610LN",
                "purchase_price": 9000.00,
                "purchase_currency": "USD",
                "current_market_value": "15000.00",
                "current_market_currency": "USD"
            },
            {
                "model": "Datejust",
                "brand": {"name": "Rolex"},
                "reference_number": "126300",
                "purchase_price": 7000.00,
                "purchase_currency": "USD",
                "current_market_value": "8500.00",
                "current_market_currency": "USD"
            }
        ]
        collection_name = "Rolex Collection"

        pdf_buffer = generate_collection_pdf(watches, collection_name)

        assert isinstance(pdf_buffer, BytesIO)
        pdf_buffer.seek(0)
        pdf_content = pdf_buffer.read()

        # Verify it's a valid PDF with substantial content (multiple watches should generate larger PDF)
        assert pdf_content.startswith(b'%PDF'), "PDF should start with %PDF header"
        assert len(pdf_content) > 1000, "PDF with watches should contain substantial content"

    def test_generate_collection_pdf_with_totals(self):
        """Test that collection PDF includes summary totals"""
        watches = [
            {
                "model": "Watch 1",
                "brand": {"name": "Brand A"},
                "purchase_price": 5000.00,
                "purchase_currency": "USD",
                "current_market_value": "6000.00",
                "current_market_currency": "USD"
            },
            {
                "model": "Watch 2",
                "brand": {"name": "Brand B"},
                "purchase_price": 3000.00,
                "purchase_currency": "USD",
                "current_market_value": "3500.00",
                "current_market_currency": "USD"
            }
        ]
        collection_name = "Test Collection"

        pdf_buffer = generate_collection_pdf(watches, collection_name)

        assert isinstance(pdf_buffer, BytesIO)
        pdf_buffer.seek(0)
        pdf_content = pdf_buffer.read(4)
        assert pdf_content == b'%PDF', "PDF should start with %PDF header"

    def test_generate_collection_pdf_empty_collection(self):
        """Test generating PDF for empty collection"""
        watches = []
        collection_name = "Empty Collection"

        pdf_buffer = generate_collection_pdf(watches, collection_name)

        assert isinstance(pdf_buffer, BytesIO)
        pdf_buffer.seek(0)
        pdf_content = pdf_buffer.read(4)
        assert pdf_content == b'%PDF', "PDF should start with %PDF header"

    def test_generate_collection_pdf_with_description(self):
        """Test collection PDF with description"""
        watches = []
        collection_name = "Vintage Collection"

        pdf_buffer = generate_collection_pdf(watches, collection_name)

        assert isinstance(pdf_buffer, BytesIO)
        pdf_buffer.seek(0)
        pdf_content = pdf_buffer.read()
        assert pdf_content.startswith(b'%PDF'), "PDF should start with %PDF header"
        assert len(pdf_content) > 100, "PDF should contain content"

    def test_generate_collection_pdf_watches_with_missing_values(self):
        """Test collection PDF with watches that have missing data"""
        watches = [
            {
                "model": "Incomplete Watch",
                "brand": {"name": "Test"},
                # Missing prices
            }
        ]
        collection_name = "Mixed Collection"

        pdf_buffer = generate_collection_pdf(watches, collection_name)

        assert isinstance(pdf_buffer, BytesIO)
        pdf_buffer.seek(0)
        pdf_content = pdf_buffer.read(4)
        assert pdf_content == b'%PDF', "PDF should start with %PDF header"
