"""
Tests for authentication endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User


class TestRegister:
    """Test user registration"""

    def test_register_success(self, client: TestClient, test_db: Session):
        """Test successful user registration"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepass123"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "hashed_password" not in data  # Should not return password

        # Verify user in database
        user = test_db.query(User).filter(User.email == "newuser@example.com").first()
        assert user is not None
        assert user.is_active is True

    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """Test registration with duplicate email fails"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "anotherpass123"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email format"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "notanemail",
                "password": "securepass123"
            }
        )
        assert response.status_code == 422  # Validation error

    def test_register_weak_password(self, client: TestClient):
        """Test registration with weak password"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "123"  # Too short
            }
        )
        assert response.status_code == 422


class TestLogin:
    """Test user login"""

    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful login"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpass123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """Test login with incorrect password"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "somepassword"
            }
        )
        assert response.status_code == 401

    def test_login_missing_credentials(self, client: TestClient):
        """Test login without credentials"""
        response = client.post("/api/v1/auth/login", data={})
        assert response.status_code == 422


class TestTokenRefresh:
    """Test token refresh"""

    def test_refresh_token_success(self, client: TestClient, test_user: User):
        """Test successful token refresh"""
        # First login to get tokens
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpass123"
            }
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh the token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_invalid(self, client: TestClient):
        """Test refresh with invalid token"""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )
        assert response.status_code == 401


class TestGetCurrentUser:
    """Test getting current user"""

    def test_get_current_user_success(self, client: TestClient, auth_headers: dict, test_user: User):
        """Test getting current user with valid token"""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == str(test_user.id)

    def test_get_current_user_unauthorized(self, client: TestClient):
        """Test getting current user without token"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
