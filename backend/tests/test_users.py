"""
Tests for user management endpoints (admin only)
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.core.security import get_password_hash, create_access_token


@pytest.fixture(scope="function")
def admin_user(test_db: Session) -> User:
    """Create an admin user for testing"""
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass123"),
        role=UserRole.admin
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_headers(admin_user: User) -> dict:
    """Generate JWT token for admin user"""
    access_token = create_access_token(data={"sub": str(admin_user.id)})
    return {"Authorization": f"Bearer {access_token}"}


class TestListUsers:
    """Test listing all users"""

    def test_list_users_as_admin(
        self,
        client: TestClient,
        admin_headers: dict,
        test_user: User,
        test_user2: User,
        admin_user: User
    ):
        """Test admin can list all users"""
        response = client.get("/api/v1/users/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3  # At least admin, test_user, test_user2

    def test_list_users_as_regular_user_forbidden(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test regular users cannot list users"""
        response = client.get("/api/v1/users/", headers=auth_headers)

        assert response.status_code == 403

    def test_list_users_unauthorized(self, client: TestClient):
        """Test listing users without authentication"""
        response = client.get("/api/v1/users/")

        assert response.status_code == 401


class TestGetUser:
    """Test getting specific user"""

    def test_get_user_as_admin(
        self,
        client: TestClient,
        admin_headers: dict,
        test_user: User
    ):
        """Test admin can get any user"""
        response = client.get(
            f"/api/v1/users/{test_user.id}",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["role"] == "user"

    def test_get_user_not_found(
        self,
        client: TestClient,
        admin_headers: dict
    ):
        """Test getting non-existent user"""
        response = client.get(
            "/api/v1/users/00000000-0000-0000-0000-000000000000",
            headers=admin_headers
        )

        assert response.status_code == 404

    def test_get_user_as_regular_user_forbidden(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user2: User
    ):
        """Test regular users cannot get other users"""
        response = client.get(
            f"/api/v1/users/{test_user2.id}",
            headers=auth_headers
        )

        assert response.status_code == 403


class TestUpdateUserRole:
    """Test updating user roles"""

    def test_update_user_promote_to_admin(
        self,
        client: TestClient,
        admin_headers: dict,
        test_user: User,
        test_db: Session
    ):
        """Test promoting user to admin"""
        response = client.patch(
            f"/api/v1/users/{test_user.id}",
            headers=admin_headers,
            json={"role": "admin"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"

        # Verify in database
        test_db.refresh(test_user)
        assert test_user.role == UserRole.admin

    def test_update_user_demote_to_user(
        self,
        client: TestClient,
        admin_headers: dict,
        test_db: Session
    ):
        """Test demoting admin to user"""
        # Create another admin to demote
        temp_admin = User(
            email="temp_admin@example.com",
            hashed_password=get_password_hash("pass123"),
            role=UserRole.admin
        )
        test_db.add(temp_admin)
        test_db.commit()
        test_db.refresh(temp_admin)

        response = client.patch(
            f"/api/v1/users/{temp_admin.id}",
            headers=admin_headers,
            json={"role": "user"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "user"

    def test_update_user_cannot_demote_self(
        self,
        client: TestClient,
        admin_headers: dict,
        admin_user: User
    ):
        """Test admin cannot demote themselves"""
        response = client.patch(
            f"/api/v1/users/{admin_user.id}",
            headers=admin_headers,
            json={"role": "user"}
        )

        assert response.status_code == 400
        assert "Cannot demote yourself" in response.json()["detail"]

    def test_update_user_role_not_found(
        self,
        client: TestClient,
        admin_headers: dict
    ):
        """Test updating non-existent user"""
        response = client.patch(
            "/api/v1/users/00000000-0000-0000-0000-000000000000",
            headers=admin_headers,
            json={"role": "admin"}
        )

        assert response.status_code == 404

    def test_update_user_role_as_regular_user_forbidden(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user2: User
    ):
        """Test regular users cannot update roles"""
        response = client.patch(
            f"/api/v1/users/{test_user2.id}",
            headers=auth_headers,
            json={"role": "admin"}
        )

        assert response.status_code == 403


class TestResetUserPassword:
    """Test admin password reset"""

    def test_reset_user_password_success(
        self,
        client: TestClient,
        admin_headers: dict,
        test_user: User,
        test_db: Session
    ):
        """Test admin can reset user password"""
        old_hash = test_user.hashed_password

        response = client.post(
            f"/api/v1/users/{test_user.id}/reset-password",
            headers=admin_headers,
            json={"new_password": "newpassword123"}
        )

        assert response.status_code == 204

        # Verify password was changed
        test_db.refresh(test_user)
        assert test_user.hashed_password != old_hash

    def test_reset_user_password_can_login_with_new(
        self,
        client: TestClient,
        admin_headers: dict,
        test_user: User,
        test_db: Session
    ):
        """Test user can login with new password after reset"""
        # Reset password
        client.post(
            f"/api/v1/users/{test_user.id}/reset-password",
            headers=admin_headers,
            json={"new_password": "brandnewpass"}
        )

        # Try to login with new password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "brandnewpass"
            }
        )

        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_reset_user_password_not_found(
        self,
        client: TestClient,
        admin_headers: dict
    ):
        """Test resetting password for non-existent user"""
        response = client.post(
            "/api/v1/users/00000000-0000-0000-0000-000000000000/reset-password",
            headers=admin_headers,
            json={"new_password": "newpass123"}
        )

        assert response.status_code == 404

    def test_reset_user_password_as_regular_user_forbidden(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user2: User
    ):
        """Test regular users cannot reset passwords"""
        response = client.post(
            f"/api/v1/users/{test_user2.id}/reset-password",
            headers=auth_headers,
            json={"new_password": "hacked"}
        )

        assert response.status_code == 403

    def test_reset_user_password_validation(
        self,
        client: TestClient,
        admin_headers: dict,
        test_user: User
    ):
        """Test password validation requirements"""
        # Try with too short password
        response = client.post(
            f"/api/v1/users/{test_user.id}/reset-password",
            headers=admin_headers,
            json={"new_password": "short"}
        )

        # Should fail validation (assuming min length requirement)
        assert response.status_code in [400, 422]


class TestDeleteUser:
    """Test user deletion"""

    def test_delete_user_success(
        self,
        client: TestClient,
        admin_headers: dict,
        test_user: User,
        test_db: Session
    ):
        """Test admin can delete users"""
        user_id = test_user.id

        response = client.delete(
            f"/api/v1/users/{user_id}",
            headers=admin_headers
        )

        assert response.status_code == 204

        # Verify deletion
        deleted = test_db.query(User).filter(User.id == user_id).first()
        assert deleted is None

    def test_delete_user_cannot_delete_self(
        self,
        client: TestClient,
        admin_headers: dict,
        admin_user: User
    ):
        """Test admin cannot delete themselves"""
        response = client.delete(
            f"/api/v1/users/{admin_user.id}",
            headers=admin_headers
        )

        assert response.status_code == 400
        assert "Cannot delete yourself" in response.json()["detail"]

    def test_delete_user_cascades_to_watches(
        self,
        client: TestClient,
        admin_headers: dict,
        test_user: User,
        test_watch,  # This watch belongs to test_user
        test_db: Session
    ):
        """Test deleting user cascades to their watches"""
        from app.models.watch import Watch

        # Verify watch exists
        assert test_db.query(Watch).filter(
            Watch.user_id == test_user.id
        ).first() is not None

        # Delete user
        client.delete(
            f"/api/v1/users/{test_user.id}",
            headers=admin_headers
        )

        # Verify watches are deleted (cascade)
        watches = test_db.query(Watch).filter(
            Watch.user_id == test_user.id
        ).all()
        assert len(watches) == 0

    def test_delete_user_not_found(
        self,
        client: TestClient,
        admin_headers: dict
    ):
        """Test deleting non-existent user"""
        response = client.delete(
            "/api/v1/users/00000000-0000-0000-0000-000000000000",
            headers=admin_headers
        )

        assert response.status_code == 404

    def test_delete_user_as_regular_user_forbidden(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user2: User
    ):
        """Test regular users cannot delete users"""
        response = client.delete(
            f"/api/v1/users/{test_user2.id}",
            headers=auth_headers
        )

        assert response.status_code == 403


class TestAdminAccessControl:
    """Test admin access control across all endpoints"""

    def test_all_endpoints_require_admin(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user2: User
    ):
        """Test that all user management endpoints require admin role"""
        endpoints = [
            ("GET", "/api/v1/users/"),
            ("GET", f"/api/v1/users/{test_user2.id}"),
            ("PATCH", f"/api/v1/users/{test_user2.id}", {"role": "admin"}),
            ("POST", f"/api/v1/users/{test_user2.id}/reset-password", {"new_password": "test"}),
            ("DELETE", f"/api/v1/users/{test_user2.id}"),
        ]

        for method, url, *body in endpoints:
            if method == "GET":
                response = client.get(url, headers=auth_headers)
            elif method == "PATCH":
                response = client.patch(url, headers=auth_headers, json=body[0])
            elif method == "POST":
                response = client.post(url, headers=auth_headers, json=body[0])
            elif method == "DELETE":
                response = client.delete(url, headers=auth_headers)

            assert response.status_code == 403, f"{method} {url} should return 403 for non-admin"

    def test_first_user_becomes_admin(
        self,
        client: TestClient,
        test_db: Session
    ):
        """Test that first registered user automatically becomes admin"""
        # Clear all users
        test_db.query(User).delete()
        test_db.commit()

        # Register first user
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "first@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 201

        # Check if user is admin
        user = test_db.query(User).filter(User.email == "first@example.com").first()
        assert user is not None
        assert user.role == UserRole.admin
