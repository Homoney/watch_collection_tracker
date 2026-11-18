"""Tests for session revocation, the refresh cookie and login throttling."""
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.core.security import create_access_token, get_password_hash

LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
ME = "/api/v1/auth/me"
CREDS = {"email": "test@example.com", "password": "testpass123"}


def login(client):
    r = client.post(LOGIN, json=CREDS)
    assert r.status_code == 200, r.text
    return r


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


class TestRefreshCookie:
    def test_login_sets_httponly_cookie(self, client: TestClient, test_user):
        r = login(client)
        cookie = r.headers["set-cookie"].lower()
        assert "refresh_token=" in cookie
        assert "httponly" in cookie
        assert "path=/api/v1/auth" in cookie
        assert "samesite=strict" in cookie

    def test_secure_flag_behind_https_proxy(self, client, test_user):
        r = client.post(LOGIN, json=CREDS, headers={"X-Forwarded-Proto": "https"})
        assert "secure" in r.headers["set-cookie"].lower()

    def test_refresh_with_cookie_omits_token_in_body(self, client, test_user):
        login(client)
        r = client.post(REFRESH)
        assert r.status_code == 200
        assert r.json()["refresh_token"] is None
        assert client.get(ME, headers=bearer(r.json()["access_token"])).status_code == 200

    def test_refresh_with_body_still_supported(self, client, test_user):
        token = login(client).json()["refresh_token"]
        client.cookies.clear()
        r = client.post(REFRESH, json={"refresh_token": token})
        assert r.status_code == 200
        assert r.json()["refresh_token"]

    def test_refresh_without_token(self, client, test_user):
        assert client.post(REFRESH).status_code == 401

    def test_refresh_for_deleted_user(self, client, test_user, test_db: Session):
        token = login(client).json()["refresh_token"]
        test_db.delete(test_user)
        test_db.commit()
        client.cookies.clear()
        assert client.post(REFRESH, json={"refresh_token": token}).status_code == 401


class TestRevocation:
    def test_change_password_ends_old_sessions(self, client, test_user):
        old = login(client).json()
        r = client.post(
            "/api/v1/auth/change-password",
            headers=bearer(old["access_token"]),
            json={"current_password": "testpass123", "new_password": "newpass12345"},
        )
        assert r.status_code == 204
        assert client.get(ME, headers=bearer(old["access_token"])).status_code == 401
        jar_after_change = dict(client.cookies)
        client.cookies.clear()
        assert (
            client.post(REFRESH, json={"refresh_token": old["refresh_token"]}).status_code
            == 401
        )
        # The browser that changed the password stays signed in via its new cookie
        for k, v in jar_after_change.items():
            client.cookies.set(k, v, path="/api/v1/auth")
        assert client.post(REFRESH).status_code == 200

    def test_logout_ends_sessions(self, client, test_user):
        tokens = login(client).json()
        r = client.post("/api/v1/auth/logout", headers=bearer(tokens["access_token"]))
        assert r.status_code == 204
        assert client.get(ME, headers=bearer(tokens["access_token"])).status_code == 401
        client.cookies.clear()
        assert (
            client.post(REFRESH, json={"refresh_token": tokens["refresh_token"]}).status_code
            == 401
        )

    def test_admin_reset_ends_sessions(self, client, test_user, test_db):
        admin = User(
            email="admin@example.com",
            hashed_password=get_password_hash("adminpass123"),
            role=UserRole.admin,
        )
        test_db.add(admin)
        test_db.commit()
        tokens = login(client).json()
        r = client.post(
            f"/api/v1/users/{test_user.id}/reset-password",
            headers=bearer(create_access_token({"sub": str(admin.id)})),
            json={"new_password": "resetpass123"},
        )
        assert r.status_code == 204
        assert client.get(ME, headers=bearer(tokens["access_token"])).status_code == 401


class TestLoginThrottling:
    def test_lockout_after_repeated_failures(self, client, test_user, test_db):
        for _ in range(5):
            r = client.post(LOGIN, json={**CREDS, "password": "wrong-password"})
            assert r.status_code == 401
        # Locked: even the right password is refused for now
        assert client.post(LOGIN, json=CREDS).status_code == 429
        test_db.refresh(test_user)
        assert test_user.locked_until > datetime.utcnow()

    def test_lock_expires(self, client, test_user, test_db):
        test_user.locked_until = datetime.utcnow() - timedelta(minutes=1)
        test_db.commit()
        assert client.post(LOGIN, json=CREDS).status_code == 200
        test_db.refresh(test_user)
        assert test_user.locked_until is None

    def test_success_resets_counter(self, client, test_user, test_db):
        for _ in range(3):
            client.post(LOGIN, json={**CREDS, "password": "wrong-password"})
        login(client)
        test_db.refresh(test_user)
        assert test_user.failed_login_count == 0

    def test_wrong_current_password_counts(self, client, test_user, auth_headers, test_db):
        for _ in range(5):
            client.post(
                "/api/v1/auth/change-password",
                headers=auth_headers,
                json={"current_password": "nope-nope", "new_password": "newpass12345"},
            )
        r = client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={"current_password": "testpass123", "new_password": "newpass12345"},
        )
        assert r.status_code == 429
