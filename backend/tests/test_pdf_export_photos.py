"""PDF export includes the watch photo stored under settings.UPLOAD_DIR (#201).

Uses the real UPLOAD_DIR (the test DATA_DIR), where the upload endpoint writes."""

import io

from PIL import Image as PILImage


def _jpeg(width=400, height=300) -> bytes:
    buf = io.BytesIO()
    PILImage.new("RGB", (width, height), color="blue").save(buf, format="JPEG")
    return buf.getvalue()


def _upload_photo(client, auth_headers, watch_id):
    response = client.post(
        f"/api/v1/watches/{watch_id}/images",
        headers=auth_headers,
        files={"file": ("photo.jpg", io.BytesIO(_jpeg()), "image/jpeg")},
    )
    assert response.status_code == 201


def _pdf_has_image(pdf: bytes) -> bool:
    return b"/Subtype /Image" in pdf


class TestPdfExportPhotos:
    def test_watch_pdf_includes_uploaded_photo(self, client, auth_headers, test_watch):
        _upload_photo(client, auth_headers, test_watch.id)

        response = client.get(
            f"/api/v1/watches/{test_watch.id}/export/pdf", headers=auth_headers
        )

        assert response.status_code == 200
        assert _pdf_has_image(response.content)

    def test_collection_pdf_includes_uploaded_photo(
        self, client, auth_headers, test_watch
    ):
        _upload_photo(client, auth_headers, test_watch.id)

        response = client.get("/api/v1/watches/export/pdf", headers=auth_headers)

        assert response.status_code == 200
        assert _pdf_has_image(response.content)

    def test_watch_pdf_without_photo_has_no_image(
        self, client, auth_headers, test_watch
    ):
        response = client.get(
            f"/api/v1/watches/{test_watch.id}/export/pdf", headers=auth_headers
        )

        assert response.status_code == 200
        assert not _pdf_has_image(response.content)
