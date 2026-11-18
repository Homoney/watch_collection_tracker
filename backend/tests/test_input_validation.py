"""Tests for upload content checks, upload caps, secret-key and password rules."""
import io
from datetime import datetime

import pytest
from PIL import Image as PILImage
from pydantic import ValidationError

from app.config import Settings, settings
from app.models.service_history import ServiceHistory
from app.utils import file_upload


def jpeg(w=300, h=300):
    buf = io.BytesIO()
    PILImage.new("RGB", (w, h), "blue").save(buf, format="JPEG")
    buf.seek(0)
    return buf


def upload_image(client, headers, watch, name, data, ctype):
    return client.post(
        f"/api/v1/watches/{watch.id}/images",
        headers=headers,
        files={"file": (name, data, ctype)},
    )


@pytest.fixture
def service(test_db, test_watch):
    record = ServiceHistory(
        watch_id=test_watch.id, service_date=datetime.utcnow(), provider="P"
    )
    test_db.add(record)
    test_db.commit()
    test_db.refresh(record)
    return record


def upload_doc(client, headers, watch, service, name, data, ctype):
    return client.post(
        f"/api/v1/watches/{watch.id}/service-history/{service.id}/documents",
        headers=headers,
        files={"file": (name, data, ctype)},
    )


class TestImageUploads:
    def test_non_image_bytes_rejected(self, client, auth_headers, test_watch, mock_upload_dir):
        r = upload_image(
            client, auth_headers, test_watch, "x.png", io.BytesIO(b"<html>hi</html>"), "image/png"
        )
        assert r.status_code == 400
        assert not any(mock_upload_dir.rglob("x*.png"))

    def test_mime_type_comes_from_content(self, client, auth_headers, test_watch, mock_upload_dir):
        r = upload_image(client, auth_headers, test_watch, "photo.png", jpeg(), "image/png")
        assert r.status_code == 201
        assert r.json()["mime_type"] == "image/jpeg"

    def test_size_cap_enforced_while_writing(
        self, client, auth_headers, test_watch, mock_upload_dir, monkeypatch
    ):
        monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE", 1000)
        r = upload_image(client, auth_headers, test_watch, "big.jpg", jpeg(600, 600), "image/jpeg")
        assert r.status_code == 400

    def test_pixel_limit(self, client, auth_headers, test_watch, mock_upload_dir, monkeypatch):
        monkeypatch.setattr(file_upload, "MAX_IMAGE_PIXELS", 100 * 100)
        r = upload_image(client, auth_headers, test_watch, "wide.jpg", jpeg(300, 300), "image/jpeg")
        assert r.status_code == 400
        assert "too large" in r.json()["detail"]

    def test_images_per_watch_cap(
        self, client, auth_headers, test_watch, mock_upload_dir, monkeypatch
    ):
        monkeypatch.setattr(settings, "MAX_IMAGES_PER_WATCH", 1)
        assert upload_image(client, auth_headers, test_watch, "a.jpg", jpeg(), "image/jpeg").status_code == 201
        assert upload_image(client, auth_headers, test_watch, "b.jpg", jpeg(), "image/jpeg").status_code == 400


class TestDocumentUploads:
    def test_fake_pdf_rejected(self, client, auth_headers, test_watch, service, mock_upload_dir):
        r = upload_doc(
            client, auth_headers, test_watch, service, "r.pdf", io.BytesIO(b"MZ\x90\x00 not a pdf"), "application/pdf"
        )
        assert r.status_code == 400

    def test_real_pdf_header_accepted(self, client, auth_headers, test_watch, service, mock_upload_dir):
        pdf = io.BytesIO(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n")
        r = upload_doc(client, auth_headers, test_watch, service, "r.pdf", pdf, "application/pdf")
        assert r.status_code == 201
        assert r.json()["mime_type"] == "application/pdf"

    def test_gif_not_allowed_as_document(self, client, auth_headers, test_watch, service, mock_upload_dir):
        buf = io.BytesIO()
        PILImage.new("RGB", (50, 50)).save(buf, format="GIF")
        buf.seek(0)
        r = upload_doc(client, auth_headers, test_watch, service, "r.png", buf, "image/png")
        assert r.status_code == 400

    def test_document_size_setting(
        self, client, auth_headers, test_watch, service, mock_upload_dir, monkeypatch
    ):
        monkeypatch.setattr(settings, "MAX_DOCUMENT_SIZE", 100)
        r = upload_doc(client, auth_headers, test_watch, service, "r.jpg", jpeg(), "image/jpeg")
        assert r.status_code == 400


BASE = dict(_env_file=None)


class TestSecretKeyRules:
    @pytest.mark.parametrize(
        "key", ["short", "CHANGE_ME_GENERATE_RANDOM_SECRET_KEY", "change_me" + "x" * 40]
    )
    def test_weak_keys_rejected(self, key):
        with pytest.raises(ValidationError):
            Settings(SECRET_KEY=key, **BASE)

    def test_algorithm_fixed(self):
        with pytest.raises(ValidationError):
            Settings(SECRET_KEY="k" * 40, ALGORITHM="none", **BASE)

    def test_strong_key_accepted(self):
        assert Settings(SECRET_KEY="k" * 40, **BASE).SECRET_KEY == "k" * 40


class TestPasswordRules:
    def test_common_password_refused_at_signup(self, client):
        r = client.post(
            "/api/v1/auth/register", json={"email": "c@example.com", "password": "Password123"}
        )
        assert r.status_code == 422

    def test_common_password_refused_on_change(self, client, auth_headers):
        r = client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={"current_password": "testpass123", "new_password": "qwerty123"},
        )
        assert r.status_code == 422
