"""App-served /uploads/ (signed URLs) and in-app rate limits."""

from urllib.parse import quote

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import settings
from app.core.file_urls import sign_upload_url
from app.middleware.rate_limit import RULES, RateLimiter, RateLimitMiddleware


@pytest.fixture
def stored_file(mock_upload_dir):
    folder = mock_upload_dir / "w1"
    folder.mkdir()
    (folder / "photo one.jpg").write_bytes(b"jpegbytes")
    (mock_upload_dir.parent / "outside.txt").write_text("secret")
    return "w1/photo one.jpg"


class TestUploads:
    def test_signed_url_serves_file_with_headers(self, client, stored_file):
        r = client.get(sign_upload_url(stored_file))
        assert r.status_code == 200
        assert r.content == b"jpegbytes"
        assert r.headers["cache-control"] == "private, max-age=3600"
        assert r.headers["referrer-policy"] == "no-referrer"
        assert r.headers["x-content-type-options"] == "nosniff"
        assert "content-security-policy" not in r.headers

    def test_unsigned_or_tampered_is_403(self, client, stored_file):
        url = sign_upload_url(stored_file)
        assert client.get("/uploads/" + quote(stored_file)).status_code == 403
        assert client.get(url[:-1] + ("0" if url[-1] != "0" else "1")).status_code == 403
        other = url.replace("w1/", "w2/")
        assert client.get(other).status_code == 403

    def test_expired_is_403(self, client, stored_file):
        url = sign_upload_url(stored_file, now=0)
        assert client.get(url).status_code == 403

    def test_missing_file_is_404(self, client, mock_upload_dir):
        assert client.get(sign_upload_url("w1/none.jpg")).status_code == 404

    def test_no_escape_from_upload_dir(self, client, stored_file):
        url = sign_upload_url("../outside.txt")
        r = client.get(url)
        assert r.status_code in (403, 404)
        assert b"secret" not in r.content

    def test_verify_route_still_works(self, client, stored_file):
        url = sign_upload_url(stored_file)
        r = client.get("/api/v1/files/verify", headers={"X-Original-URI": url})
        assert r.status_code == 204


def _rule(name):
    return next(r for r in RULES if r.name == name)


class TestRateLimiter:
    def test_bucket_allows_burst_then_waits(self):
        now = [0.0]
        limiter = RateLimiter(clock=lambda: now[0])
        auth = _rule("auth")
        assert [limiter.hit(auth, "a") for _ in range(4)] == [0, 0, 0, 0]
        wait = limiter.hit(auth, "a")
        assert 11 < wait <= 12
        assert limiter.hit(auth, "b") == 0  # other clients unaffected
        now[0] += 12
        assert limiter.hit(auth, "a") == 0

    def test_upload_rule_only_counts_posts(self):
        upload = _rule("upload")
        path = "/api/v1/watches/abc/images"
        assert upload.matches("POST", path)
        assert not upload.matches("GET", path)


class TestRateLimitMiddleware:
    @pytest.fixture
    def limited_client(self, monkeypatch):
        monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
        app = FastAPI()

        @app.post("/api/v1/auth/login")
        def login():
            return {"ok": True}

        @app.get("/health")
        def health():
            return {"ok": True}

        app.add_middleware(RateLimitMiddleware, limiter=RateLimiter())
        return TestClient(app)

    def test_login_limited_with_retry_after(self, limited_client):
        codes = [limited_client.post("/api/v1/auth/login").status_code for _ in range(5)]
        assert codes == [200, 200, 200, 200, 429]
        r = limited_client.post("/api/v1/auth/login")
        assert r.json() == {"detail": "Too many requests"}
        assert int(r.headers["retry-after"]) >= 1

    def test_non_api_paths_not_limited(self, limited_client):
        assert all(limited_client.get("/health").status_code == 200 for _ in range(50))

    def test_switch_off(self, limited_client, monkeypatch):
        monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", False)
        assert all(
            limited_client.post("/api/v1/auth/login").status_code == 200 for _ in range(10)
        )
