"""
Tests for watch CRUD endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.watch import Watch
from app.models.brand import Brand
from app.models.collection import Collection


class TestCreateWatch:
    """Test watch creation"""

    def test_create_watch_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_brand: Brand,
        test_collection: Collection,
        test_movement_type,
        test_db: Session
    ):
        """Test successful watch creation"""
        response = client.post(
            "/api/v1/watches/",
            headers=auth_headers,
            json={
                "model": "Daytona",
                "brand_id": str(test_brand.id),
                "collection_id": str(test_collection.id),
                "reference_number": "116500LN",
                "movement_type_id": str(test_movement_type.id),
                "purchase_price": 15000.00,
                "purchase_currency": "USD"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["model"] == "Daytona"
        assert data["brand"]["name"] == "Rolex"
        assert "id" in data

    def test_create_watch_missing_required_fields(self, client: TestClient, auth_headers: dict):
        """Test watch creation without required fields"""
        response = client.post(
            "/api/v1/watches/",
            headers=auth_headers,
            json={"model": "Test Watch"}  # Missing brand_id
        )
        assert response.status_code == 422

    def test_create_watch_unauthorized(self, client: TestClient, test_brand: Brand):
        """Test watch creation without authentication"""
        response = client.post(
            "/api/v1/watches/",
            json={
                "model": "Daytona",
                "brand_id": str(test_brand.id)
            }
        )
        assert response.status_code == 401

    def test_create_watch_invalid_brand(self, client: TestClient, auth_headers: dict):
        """Test watch creation with non-existent brand"""
        response = client.post(
            "/api/v1/watches/",
            headers=auth_headers,
            json={
                "model": "Test Watch",
                "brand_id": "00000000-0000-0000-0000-000000000000"
            }
        )
        assert response.status_code == 404


class TestListWatches:
    """Test watch listing"""

    def test_list_watches_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch
    ):
        """Test listing user's watches"""
        response = client.get("/api/v1/watches/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0
        assert data["items"][0]["model"] == "Submariner Date"

    def test_list_watches_pagination(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session,
        test_user,
        test_brand
    ):
        """Test watch list pagination"""
        # Create additional watches
        for i in range(5):
            watch = Watch(
                model=f"Watch {i}",
                brand_id=test_brand.id,
                user_id=test_user.id
            )
            test_db.add(watch)
        test_db.commit()

        # Test pagination
        response = client.get(
            "/api/v1/watches/?skip=0&limit=3",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3

    def test_list_watches_filter_by_brand(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_brand: Brand
    ):
        """Test filtering watches by brand"""
        response = client.get(
            f"/api/v1/watches/?brand_id={test_brand.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert all(item["brand"]["id"] == str(test_brand.id) for item in data["items"])

    def test_list_watches_search(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch
    ):
        """Test searching watches by model"""
        response = client.get(
            "/api/v1/watches/?search=Submariner",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0
        assert "Submariner" in data["items"][0]["model"]

    def test_list_watches_only_users_watches(
        self,
        client: TestClient,
        auth_headers: dict,
        auth_headers2: dict,
        test_watch: Watch,
        test_user2,
        test_brand,
        test_db: Session
    ):
        """Test that users only see their own watches"""
        # Create watch for user2
        watch2 = Watch(
            model="User 2 Watch",
            brand_id=test_brand.id,
            user_id=test_user2.id
        )
        test_db.add(watch2)
        test_db.commit()

        # User 1 should only see their watch
        response = client.get("/api/v1/watches/", headers=auth_headers)
        data = response.json()
        assert all(item["model"] != "User 2 Watch" for item in data["items"])


class TestGetWatch:
    """Test getting watch detail"""

    def test_get_watch_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch
    ):
        """Test getting watch detail"""
        response = client.get(
            f"/api/v1/watches/{test_watch.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_watch.id)
        assert data["model"] == "Submariner Date"

    def test_get_watch_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent watch"""
        response = client.get(
            "/api/v1/watches/00000000-0000-0000-0000-000000000000",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_get_watch_unauthorized(
        self,
        client: TestClient,
        auth_headers2: dict,
        test_watch: Watch
    ):
        """Test getting another user's watch"""
        response = client.get(
            f"/api/v1/watches/{test_watch.id}",
            headers=auth_headers2
        )
        assert response.status_code == 404  # Not found for security


class TestUpdateWatch:
    """Test watch updates"""

    def test_update_watch_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch
    ):
        """Test successful watch update"""
        response = client.put(
            f"/api/v1/watches/{test_watch.id}",
            headers=auth_headers,
            json={"model": "Submariner Date Updated"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "Submariner Date Updated"

    def test_update_watch_unauthorized(
        self,
        client: TestClient,
        auth_headers2: dict,
        test_watch: Watch
    ):
        """Test updating another user's watch"""
        response = client.put(
            f"/api/v1/watches/{test_watch.id}",
            headers=auth_headers2,
            json={"model": "Hacked"}
        )
        assert response.status_code == 404

    def test_update_watch_invalid_brand(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch
    ):
        """Test updating watch with invalid brand"""
        response = client.put(
            f"/api/v1/watches/{test_watch.id}",
            headers=auth_headers,
            json={"brand_id": "00000000-0000-0000-0000-000000000000"}
        )
        assert response.status_code == 404


class TestDeleteWatch:
    """Test watch deletion"""

    def test_delete_watch_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test successful watch deletion"""
        watch_id = test_watch.id
        response = client.delete(
            f"/api/v1/watches/{watch_id}",
            headers=auth_headers
        )
        assert response.status_code == 204

        # Verify watch is deleted
        watch = test_db.query(Watch).filter(Watch.id == watch_id).first()
        assert watch is None

    def test_delete_watch_unauthorized(
        self,
        client: TestClient,
        auth_headers2: dict,
        test_watch: Watch
    ):
        """Test deleting another user's watch"""
        response = client.delete(
            f"/api/v1/watches/{test_watch.id}",
            headers=auth_headers2
        )
        assert response.status_code == 404
