"""Tests for signed upload URLs, the safe image fetcher, registration rules
and the create-user command."""
import io
import time
from urllib.parse import urlsplit

import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image as PILImage
from sqlalchemy.orm import Session

from app.cli import create_user
from app.config import settings
from app.core.file_urls import sign_upload_url, verify_upload_uri
from app.models.user import User, UserRole
from app.utils.safe_fetch import (
    DownloadTooLargeError,
    UnsafeURLError,
    check_url,
    fetch_bytes,
)


# ---------------------------------------------------------------- signed URLs


class TestSignedUploadUrls:
    def test_signed_url_verifies(self):
        url = sign_upload_url("abc/photo.jpg")
        assert url.startswith("/uploads/abc/photo.jpg?expires=")
        assert verify_upload_uri(url)

    def test_service_doc_path(self):
        url = sign_upload_url("service-docs/w/s/receipt.pdf")
        assert urlsplit(url).path == "/uploads/service-docs/w/s/receipt.pdf"
        assert verify_upload_uri(url)

    def test_unsigned_rejected(self):
        assert not verify_upload_uri("/uploads/abc/photo.jpg")
        assert not verify_upload_uri("")

    def test_signature_bound_to_path(self):
        url = sign_upload_url("abc/photo.jpg")
        other = url.replace("/abc/photo.jpg", "/abc/other.jpg")
        assert not verify_upload_uri(other)

    def test_tampered_expiry_rejected(self):
        url = sign_upload_url("abc/photo.jpg")
        exp = urlsplit(url).query.split("&")[0].split("=")[1]
        assert not verify_upload_uri(url.replace(exp, str(int(exp) + 3600)))

    def test_expired_rejected(self):
        url = sign_upload_url("abc/photo.jpg", now=time.time() - 3 * 86400)
        assert not verify_upload_uri(url)

    def test_url_stable_within_window(self):
        now = (int(time.time()) // 3600) * 3600 + 10
        assert sign_upload_url("a/b.jpg", now=now) == sign_upload_url(
            "a/b.jpg", now=now + 60
        )

    def test_traversal_rejected(self):
        assert not verify_upload_uri("/uploads/../etc/passwd?expires=9999999999&sig=x")

    def test_verify_endpoint(self, client: TestClient):
        good = sign_upload_url("abc/photo.jpg")
        r = client.get("/api/v1/files/verify", headers={"X-Original-URI": good})
        assert r.status_code == 204
        r = client.get(
            "/api/v1/files/verify", headers={"X-Original-URI": "/uploads/abc/photo.jpg"}
        )
        assert r.status_code == 403
        r = client.get("/api/v1/files/verify")
        assert r.status_code == 403

    def test_image_response_carries_signed_url(
        self, client, auth_headers, test_watch, mock_upload_dir
    ):
        buf = io.BytesIO()
        PILImage.new("RGB", (300, 300), "red").save(buf, format="JPEG")
        buf.seek(0)
        r = client.post(
            f"/api/v1/watches/{test_watch.id}/images",
            headers=auth_headers,
            files={"file": ("t.jpg", buf, "image/jpeg")},
        )
        assert r.status_code == 201
        url = r.json()["url"]
        assert "sig=" in url and verify_upload_uri(url)


# ---------------------------------------------------------------- safe fetch


def resolver_for(mapping):
    def resolve(host, port):
        if host not in mapping:
            raise OSError("no such host")
        return mapping[host]

    return resolve


PUBLIC = resolver_for({"img.example.com": ["93.184.216.34"]})


class TestCheckUrl:
    @pytest.mark.parametrize(
        "url",
        [
            "file:///etc/passwd",
            "ftp://img.example.com/a.jpg",
            "gopher://img.example.com/",
            "http://img.example.com:8000/a.jpg",
            "http://user:pw@img.example.com/a.jpg",
            "http:///a.jpg",
        ],
    )
    def test_rejects_bad_url_shapes(self, url):
        with pytest.raises(UnsafeURLError):
            check_url(url, PUBLIC)

    @pytest.mark.parametrize(
        "ip",
        [
            "127.0.0.1",
            "10.0.0.5",
            "172.18.0.3",
            "192.168.1.1",
            "169.254.169.254",
            "100.64.0.1",
            "0.0.0.0",
            "::1",
            "fd00::1",
            "fe80::1",
            "::ffff:127.0.0.1",
        ],
    )
    def test_rejects_non_public_addresses(self, ip):
        with pytest.raises(UnsafeURLError):
            check_url("http://internal.test/a.jpg", resolver_for({"internal.test": [ip]}))

    def test_rejects_if_any_address_is_private(self):
        r = resolver_for({"mixed.test": ["93.184.216.34", "10.0.0.1"]})
        with pytest.raises(UnsafeURLError):
            check_url("https://mixed.test/a.jpg", r)

    def test_rejects_unresolvable(self):
        with pytest.raises(UnsafeURLError):
            check_url("https://nope.test/a.jpg", PUBLIC)

    def test_accepts_public(self):
        assert check_url("https://img.example.com/a.jpg", PUBLIC)[3] == "93.184.216.34"


class TestFetchBytes:
    def test_connects_to_checked_ip_with_host_header(self):
        seen = {}

        def handler(request):
            seen["host"] = request.url.host
            seen["header"] = request.headers["host"]
            return httpx.Response(200, headers={"content-type": "image/jpeg"}, content=b"x" * 10)

        ctype, body = fetch_bytes(
            "http://img.example.com/a.jpg?s=1",
            resolver=PUBLIC,
            transport=httpx.MockTransport(handler),
        )
        assert ctype == "image/jpeg" and body == b"x" * 10
        assert seen == {"host": "93.184.216.34", "header": "img.example.com"}

    def test_tries_each_checked_address_in_turn(self):
        # No IPv6 route: the first (IPv6) address fails to connect, IPv4 works
        r = resolver_for({"cdn.example.com": ["2606:4700::6810:1", "93.184.216.34"]})
        tried = []

        def handler(request):
            tried.append(request.url.host)
            if ":" in request.url.host:
                raise httpx.ConnectError("Network is unreachable")
            assert request.headers["host"] == "cdn.example.com"
            return httpx.Response(200, headers={"content-type": "image/jpeg"}, content=b"ok")

        ctype, body = fetch_bytes(
            "https://cdn.example.com/a.jpg", resolver=r, transport=httpx.MockTransport(handler)
        )
        assert body == b"ok"
        assert tried == ["2606:4700::6810:1", "93.184.216.34"]

    def test_every_address_still_checked(self):
        # A private address anywhere in the answer blocks the whole host
        r = resolver_for({"cdn.example.com": ["2606:4700::6810:1", "10.0.0.7"]})

        def handler(request):
            raise AssertionError("must not connect")

        with pytest.raises(UnsafeURLError):
            fetch_bytes(
                "https://cdn.example.com/a.jpg", resolver=r, transport=httpx.MockTransport(handler)
            )

    def test_all_addresses_unreachable_raises(self):
        r = resolver_for({"cdn.example.com": ["2606:4700::6810:1", "93.184.216.34"]})

        def handler(request):
            raise httpx.ConnectError("Network is unreachable")

        with pytest.raises(httpx.ConnectError):
            fetch_bytes(
                "https://cdn.example.com/a.jpg", resolver=r, transport=httpx.MockTransport(handler)
            )

    def test_redirect_to_internal_is_blocked(self):
        def handler(request):
            return httpx.Response(302, headers={"location": "http://metadata.test/latest"})

        r = resolver_for(
            {"img.example.com": ["93.184.216.34"], "metadata.test": ["169.254.169.254"]}
        )
        with pytest.raises(UnsafeURLError):
            fetch_bytes(
                "http://img.example.com/a.jpg",
                resolver=r,
                transport=httpx.MockTransport(handler),
            )

    def test_redirect_loop_is_capped(self):
        def handler(request):
            return httpx.Response(302, headers={"location": "/again"})

        with pytest.raises(UnsafeURLError):
            fetch_bytes(
                "http://img.example.com/a.jpg",
                resolver=PUBLIC,
                transport=httpx.MockTransport(handler),
            )

    def test_size_cap(self):
        def handler(request):
            return httpx.Response(200, content=b"x" * 2048)

        with pytest.raises(DownloadTooLargeError):
            fetch_bytes(
                "http://img.example.com/a.jpg",
                max_bytes=1024,
                resolver=PUBLIC,
                transport=httpx.MockTransport(handler),
            )


# ---------------------------------------------------------------- registration

REG = "/api/v1/auth/register"


class TestRegistration:
    def test_closed_by_default(self, client, test_db: Session, monkeypatch):
        monkeypatch.setattr(settings, "ALLOW_REGISTRATION", False)
        r = client.post(REG, json={"email": "a@example.com", "password": "watch-pass-123"})
        assert r.status_code == 403
        assert test_db.query(User).count() == 0

    def test_initial_admin_can_bootstrap(self, client, test_db, monkeypatch):
        monkeypatch.setattr(settings, "ALLOW_REGISTRATION", False)
        monkeypatch.setattr(settings, "INITIAL_ADMIN_EMAIL", "Owner@Example.com")
        r = client.post(REG, json={"email": "owner@example.com", "password": "watch-pass-123"})
        assert r.status_code == 201
        user = test_db.query(User).filter(User.email == "owner@example.com").one()
        assert user.role == UserRole.admin

    def test_bootstrap_only_on_empty_database(
        self, client, test_db, test_user, monkeypatch
    ):
        monkeypatch.setattr(settings, "ALLOW_REGISTRATION", False)
        monkeypatch.setattr(settings, "INITIAL_ADMIN_EMAIL", "owner@example.com")
        r = client.post(REG, json={"email": "owner@example.com", "password": "watch-pass-123"})
        assert r.status_code == 403

    def test_other_email_cannot_bootstrap(self, client, test_db, monkeypatch):
        monkeypatch.setattr(settings, "ALLOW_REGISTRATION", False)
        monkeypatch.setattr(settings, "INITIAL_ADMIN_EMAIL", "owner@example.com")
        r = client.post(REG, json={"email": "x@example.com", "password": "watch-pass-123"})
        assert r.status_code == 403
        assert "INITIAL_ADMIN_EMAIL" in r.json()["detail"]
        assert "owner@example.com" not in r.text

    def test_open_registration_never_grants_admin(self, client, test_db):
        r = client.post(REG, json={"email": "a@example.com", "password": "watch-pass-123"})
        assert r.status_code == 201
        assert test_db.query(User).one().role == UserRole.user


# ---------------------------------------------------------------- CLI


class TestCreateUserCommand:
    def test_create_admin(self, test_db):
        user, created = create_user(test_db, "boss@example.com", "watch-pass-123", admin=True)
        assert created and user.role == UserRole.admin

    def test_create_plain_user(self, test_db):
        user, created = create_user(test_db, "u@example.com", "watch-pass-123")
        assert created and user.role == UserRole.user

    def test_promote_existing(self, test_db, test_user):
        user, created = create_user(test_db, test_user.email, None, admin=True)
        assert not created and user.role == UserRole.admin

    def test_duplicate_without_admin_flag(self, test_db, test_user):
        with pytest.raises(ValueError):
            create_user(test_db, test_user.email, "watch-pass-123")

    def test_short_password(self, test_db):
        with pytest.raises(ValueError):
            create_user(test_db, "u@example.com", "short")


# ---------------------------------------------------------------- setup status

SETUP = "/api/v1/auth/setup-status"


class TestSetupStatus:
    def test_true_on_empty_database(self, client, test_db, monkeypatch):
        monkeypatch.setattr(settings, "INITIAL_ADMIN_EMAIL", "owner@example.com")
        r = client.get(SETUP)
        assert r.status_code == 200
        assert r.json() == {"setup_required": True, "admin_signup": True}
        assert "owner@example.com" not in r.text

    def test_false_when_users_exist(self, client, test_db, test_user, monkeypatch):
        monkeypatch.setattr(settings, "INITIAL_ADMIN_EMAIL", "owner@example.com")
        r = client.get(SETUP)
        assert r.status_code == 200
        assert r.json() == {"setup_required": False, "admin_signup": False}

    def test_no_admin_signup_without_initial_admin_email(
        self, client, test_db, monkeypatch
    ):
        # Open registration, no INITIAL_ADMIN_EMAIL: the first user is a plain
        # user, so the pages must not promise an admin account.
        monkeypatch.setattr(settings, "ALLOW_REGISTRATION", True)
        monkeypatch.setattr(settings, "INITIAL_ADMIN_EMAIL", "")
        assert client.get(SETUP).json() == {
            "setup_required": True,
            "admin_signup": False,
        }
        r = client.post(REG, json={"email": "a@example.com", "password": "watch-pass-123"})
        assert r.status_code == 201
        assert test_db.query(User).one().role == UserRole.user

    def test_turns_false_after_first_sign_up(self, client, test_db, monkeypatch):
        monkeypatch.setattr(settings, "ALLOW_REGISTRATION", False)
        monkeypatch.setattr(settings, "INITIAL_ADMIN_EMAIL", "owner@example.com")
        assert client.get(SETUP).json()["setup_required"] is True
        r = client.post(REG, json={"email": "owner@example.com", "password": "watch-pass-123"})
        assert r.status_code == 201
        assert client.get(SETUP).json() == {
            "setup_required": False,
            "admin_signup": False,
        }
