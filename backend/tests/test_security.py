"""
Security-focused tests
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.core.security import create_access_token, create_refresh_token


class TestTokenValidation:
    """Test JWT token validation"""

    def test_valid_token(self, client: TestClient, test_user):
        """Test that valid token is accepted"""
        token = create_access_token(data={"sub": str(test_user.id)})
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

    def test_expired_token(self, client: TestClient, test_user):
        """Test that expired token is rejected"""
        # Create token that expired 1 hour ago
        token = create_access_token(
            data={"sub": str(test_user.id)},
            expires_delta=timedelta(hours=-1)
        )
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401

    def test_malformed_token(self, client: TestClient):
        """Test that malformed token is rejected"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer malformed.token.here"}
        )
        assert response.status_code == 401

    def test_missing_token(self, client: TestClient):
        """Test that missing token is rejected"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401


class TestAuthorizationChecks:
    """Test authorization and ownership checks"""

    def test_cannot_access_other_users_watch(
        self,
        client: TestClient,
        auth_headers2: dict,
        test_watch
    ):
        """Test that user cannot access another user's watch"""
        response = client.get(
            f"/api/v1/watches/{test_watch.id}",
            headers=auth_headers2
        )
        assert response.status_code == 404  # Not found for security

    def test_cannot_update_other_users_watch(
        self,
        client: TestClient,
        auth_headers2: dict,
        test_watch
    ):
        """Test that user cannot update another user's watch"""
        response = client.put(
            f"/api/v1/watches/{test_watch.id}",
            headers=auth_headers2,
            json={"model": "Hacked"}
        )
        assert response.status_code == 404

    def test_cannot_delete_other_users_watch(
        self,
        client: TestClient,
        auth_headers2: dict,
        test_watch
    ):
        """Test that user cannot delete another user's watch"""
        response = client.delete(
            f"/api/v1/watches/{test_watch.id}",
            headers=auth_headers2
        )
        assert response.status_code == 404

    def test_cannot_access_other_users_collection(
        self,
        client: TestClient,
        auth_headers2: dict,
        test_collection
    ):
        """Test that user cannot access another user's collection"""
        response = client.get(
            f"/api/v1/collections/{test_collection.id}",
            headers=auth_headers2
        )
        assert response.status_code == 404


class TestInputValidation:
    """Test input validation and sanitization"""

    def test_sql_injection_attempt_email(self, client: TestClient):
        """Test that SQL injection in email is rejected"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com'; DROP TABLE users; --",
                "password": "testpass123"
            }
        )
        # Should fail validation, not execute SQL
        assert response.status_code == 422

    def test_xss_attempt_watch_model(
        self,
        client: TestClient,
        auth_headers: dict,
        test_brand
    ):
        """Test that XSS attempt in watch model is handled"""
        response = client.post(
            "/api/v1/watches/",
            headers=auth_headers,
            json={
                "model": "<script>alert('XSS')</script>",
                "brand_id": str(test_brand.id)
            }
        )
        # Should accept but sanitize/escape
        assert response.status_code == 201
        data = response.json()
        # The value should be stored but will be escaped when rendered
        assert "script" in data["model"]

    def test_negative_price_rejected(
        self,
        client: TestClient,
        auth_headers: dict,
        test_brand
    ):
        """Test that negative price is rejected"""
        response = client.post(
            "/api/v1/watches/",
            headers=auth_headers,
            json={
                "model": "Test Watch",
                "brand_id": str(test_brand.id),
                "purchase_price": -1000.00
            }
        )
        assert response.status_code == 422

    def test_invalid_uuid_rejected(self, client: TestClient, auth_headers: dict):
        """Test that invalid UUID is rejected"""
        response = client.get(
            "/api/v1/watches/not-a-valid-uuid",
            headers=auth_headers
        )
        assert response.status_code == 422


class TestPasswordSecurity:
    """Test password security"""

    def test_password_not_returned_in_response(self, client: TestClient):
        """Test that password is never returned in API responses"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepass123"
            }
        )
        data = response.json()
        assert "password" not in data
        assert "hashed_password" not in data

    def test_password_is_hashed(self, client: TestClient, test_user, test_db):
        """Test that passwords are stored hashed"""
        # Password should not be stored in plain text
        assert test_user.hashed_password != "testpass123"
        # Hashed password should start with bcrypt prefix
        assert test_user.hashed_password.startswith("$2")
