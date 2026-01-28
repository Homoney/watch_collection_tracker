"""
Tests for collection CRUD endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.collection import Collection


class TestCreateCollection:
    """Test collection creation"""

    def test_create_collection_success(self, client: TestClient, auth_headers: dict):
        """Test successful collection creation"""
        response = client.post(
            "/api/v1/collections/",
            headers=auth_headers,
            json={
                "name": "Vintage Watches",
                "description": "My vintage collection",
                "color": "#FF5733"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Vintage Watches"
        assert data["color"] == "#FF5733"

    def test_create_collection_minimal(self, client: TestClient, auth_headers: dict):
        """Test collection creation with minimal fields"""
        response = client.post(
            "/api/v1/collections/",
            headers=auth_headers,
            json={"name": "Simple Collection"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Simple Collection"

    def test_create_collection_unauthorized(self, client: TestClient):
        """Test collection creation without authentication"""
        response = client.post(
            "/api/v1/collections/",
            json={"name": "Test Collection"}
        )
        assert response.status_code == 401


class TestListCollections:
    """Test collection listing"""

    def test_list_collections_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_collection: Collection
    ):
        """Test listing user's collections"""
        response = client.get("/api/v1/collections/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["name"] == "Test Collection"

    def test_list_collections_only_users_collections(
        self,
        client: TestClient,
        auth_headers: dict,
        auth_headers2: dict,
        test_collection: Collection,
        test_user2,
        test_db: Session
    ):
        """Test that users only see their own collections"""
        # Create collection for user2
        collection2 = Collection(
            name="User 2 Collection",
            user_id=test_user2.id
        )
        test_db.add(collection2)
        test_db.commit()

        # User 1 should only see their collection
        response = client.get("/api/v1/collections/", headers=auth_headers)
        data = response.json()
        assert all(item["name"] != "User 2 Collection" for item in data)


class TestGetCollection:
    """Test getting collection detail"""

    def test_get_collection_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_collection: Collection
    ):
        """Test getting collection detail"""
        response = client.get(
            f"/api/v1/collections/{test_collection.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_collection.id)
        assert data["name"] == "Test Collection"

    def test_get_collection_unauthorized(
        self,
        client: TestClient,
        auth_headers2: dict,
        test_collection: Collection
    ):
        """Test getting another user's collection"""
        response = client.get(
            f"/api/v1/collections/{test_collection.id}",
            headers=auth_headers2
        )
        assert response.status_code == 404


class TestUpdateCollection:
    """Test collection updates"""

    def test_update_collection_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_collection: Collection
    ):
        """Test successful collection update"""
        response = client.put(
            f"/api/v1/collections/{test_collection.id}",
            headers=auth_headers,
            json={
                "name": "Updated Collection",
                "description": "New description",
                "color": "#00FF00"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Collection"
        assert data["color"] == "#00FF00"

    def test_update_collection_unauthorized(
        self,
        client: TestClient,
        auth_headers2: dict,
        test_collection: Collection
    ):
        """Test updating another user's collection"""
        response = client.put(
            f"/api/v1/collections/{test_collection.id}",
            headers=auth_headers2,
            json={"name": "Hacked"}
        )
        assert response.status_code == 404


class TestDeleteCollection:
    """Test collection deletion"""

    def test_delete_collection_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_collection: Collection,
        test_db: Session
    ):
        """Test successful collection deletion"""
        collection_id = test_collection.id
        response = client.delete(
            f"/api/v1/collections/{collection_id}",
            headers=auth_headers
        )
        assert response.status_code == 204

        # Verify collection is deleted
        collection = test_db.query(Collection).filter(
            Collection.id == collection_id
        ).first()
        assert collection is None

    def test_delete_collection_unauthorized(
        self,
        client: TestClient,
        auth_headers2: dict,
        test_collection: Collection
    ):
        """Test deleting another user's collection"""
        response = client.delete(
            f"/api/v1/collections/{test_collection.id}",
            headers=auth_headers2
        )
        assert response.status_code == 404
