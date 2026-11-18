"""Tests for QR base_url checks, literal search wildcards, safe deletes and
generic error messages."""
import io

from PIL import Image as PILImage

from app.api.v1 import images as images_api
from app.utils.file_upload import delete_file


class TestQrBaseUrl:
    def url(self, watch, base):
        return f"/api/v1/watches/{watch.id}/qr-code?base_url={base}"

    def test_same_host_allowed(self, client, auth_headers, test_watch):
        r = client.get(self.url(test_watch, "http://testserver"), headers=auth_headers)
        assert r.status_code == 200
        assert r.headers["content-type"] == "image/png"

    def test_allowed_origin(self, client, auth_headers, test_watch):
        r = client.get(self.url(test_watch, "http://localhost"), headers=auth_headers)
        assert r.status_code == 200

    def test_other_site_rejected(self, client, auth_headers, test_watch):
        r = client.get(self.url(test_watch, "https://other.example"), headers=auth_headers)
        assert r.status_code == 400

    def test_path_or_query_rejected(self, client, auth_headers, test_watch):
        for base in ["http://testserver/x", "http://testserver%3Fa%3D1", "javascript:alert(1)"]:
            r = client.get(self.url(test_watch, base), headers=auth_headers)
            assert r.status_code == 400, base


class TestSearchWildcards:
    def test_percent_is_literal(self, client, auth_headers, test_watch):
        r = client.get("/api/v1/watches/?search=%25", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["items"] == []

    def test_normal_search_still_matches(self, client, auth_headers, test_watch):
        r = client.get("/api/v1/watches/?search=116610", headers=auth_headers)
        assert len(r.json()["items"]) == 1


class TestDeleteFile:
    def test_sibling_directory_refused(self, tmp_path):
        base = tmp_path / "uploads"
        base.mkdir()
        evil = tmp_path / "uploads_evil"
        evil.mkdir()
        target = evil / "x.jpg"
        target.write_bytes(b"x")
        assert delete_file("../uploads_evil/x.jpg", upload_dir=str(base)) is False
        assert target.exists()

    def test_inside_directory_deleted(self, tmp_path):
        (tmp_path / "w").mkdir()
        f = tmp_path / "w" / "a.jpg"
        f.write_bytes(b"x")
        assert delete_file("w/a.jpg", upload_dir=str(tmp_path)) is True


class TestErrorMessages:
    def test_save_failure_is_generic(
        self, client, auth_headers, test_watch, mock_upload_dir, monkeypatch
    ):
        def boom(*a, **k):
            raise OSError("/app/storage/uploads/secret-path: disk full")

        monkeypatch.setattr(images_api, "save_uploaded_file", boom)
        buf = io.BytesIO()
        PILImage.new("RGB", (300, 300)).save(buf, format="JPEG")
        buf.seek(0)
        r = client.post(
            f"/api/v1/watches/{test_watch.id}/images",
            headers=auth_headers,
            files={"file": ("a.jpg", buf, "image/jpeg")},
        )
        assert r.status_code == 500
        assert r.json()["detail"] == "Failed to save file"
