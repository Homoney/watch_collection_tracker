"""
Tests for saved searches endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.saved_search import SavedSearch
from app.models.user import User


class TestListSavedSearches:
    """Test listing saved searches"""

    def test_list_saved_searches_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        test_db: Session
    ):
        """Test listing user's saved searches"""
        # Create saved searches
        search1 = SavedSearch(
            user_id=test_user.id,
            name="Rolex Only",
            filters={"brand_id": "some-uuid"}
        )
        search2 = SavedSearch(
            user_id=test_user.id,
            name="Vintage Watches",
            filters={"min_year": 1970, "max_year": 1990}
        )
        test_db.add_all([search1, search2])
        test_db.commit()

        response = client.get("/api/v1/saved-searches/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Should be sorted by name
        assert data[0]["name"] == "Rolex Only"
        assert data[1]["name"] == "Vintage Watches"

    def test_list_saved_searches_user_isolation(
        self,
        client: TestClient,
        auth_headers: dict,
        auth_headers2: dict,
        test_user: User,
        test_user2: User,
        test_db: Session
    ):
        """Test that users only see their own searches"""
        # Create search for user 1
        search1 = SavedSearch(
            user_id=test_user.id,
            name="My Search",
            filters={}
        )
        # Create search for user 2
        search2 = SavedSearch(
            user_id=test_user2.id,
            name="Other Search",
            filters={}
        )
        test_db.add_all([search1, search2])
        test_db.commit()

        # User 1 should only see their search
        response = client.get("/api/v1/saved-searches/", headers=auth_headers)
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "My Search"

    def test_list_saved_searches_empty(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test listing when no searches exist"""
        response = client.get("/api/v1/saved-searches/", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_list_saved_searches_unauthorized(self, client: TestClient):
        """Test listing without authentication"""
        response = client.get("/api/v1/saved-searches/")

        assert response.status_code == 403


class TestCreateSavedSearch:
    """Test saved search creation"""

    def test_create_saved_search_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_db: Session
    ):
        """Test successful saved search creation"""
        response = client.post(
            "/api/v1/saved-searches/",
            headers=auth_headers,
            json={
                "name": "Luxury Brands",
                "filters": {
                    "brand_id": ["brand-1", "brand-2"],
                    "min_price": 10000
                }
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Luxury Brands"
        assert data["filters"]["min_price"] == 10000
        assert "id" in data

    def test_create_saved_search_duplicate_name(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        test_db: Session
    ):
        """Test that duplicate names are rejected"""
        # Create first search
        search = SavedSearch(
            user_id=test_user.id,
            name="My Search",
            filters={}
        )
        test_db.add(search)
        test_db.commit()

        # Try to create another with same name
        response = client.post(
            "/api/v1/saved-searches/",
            headers=auth_headers,
            json={"name": "My Search", "filters": {}}
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_create_saved_search_allows_same_name_different_user(
        self,
        client: TestClient,
        auth_headers: dict,
        auth_headers2: dict,
        test_user: User,
        test_db: Session
    ):
        """Test that different users can have same search name"""
        # Create search for user 1
        search = SavedSearch(
            user_id=test_user.id,
            name="Common Name",
            filters={}
        )
        test_db.add(search)
        test_db.commit()

        # User 2 should be able to use same name
        response = client.post(
            "/api/v1/saved-searches/",
            headers=auth_headers2,
            json={"name": "Common Name", "filters": {}}
        )

        assert response.status_code == 201

    def test_create_saved_search_complex_filters(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test creating search with complex filter object"""
        response = client.post(
            "/api/v1/saved-searches/",
            headers=auth_headers,
            json={
                "name": "Complex Search",
                "filters": {
                    "brand_ids": ["id1", "id2"],
                    "movement_type": "automatic",
                    "min_price": 5000,
                    "max_price": 50000,
                    "case_diameter_min": 38,
                    "case_diameter_max": 42,
                    "complications": ["chronograph", "date"]
                }
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["filters"]) == 7

    def test_create_saved_search_unauthorized(self, client: TestClient):
        """Test creating without authentication"""
        response = client.post(
            "/api/v1/saved-searches/",
            json={"name": "Test", "filters": {}}
        )

        assert response.status_code == 403


class TestGetSavedSearch:
    """Test getting individual saved search"""

    def test_get_saved_search_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        test_db: Session
    ):
        """Test getting a specific saved search"""
        search = SavedSearch(
            user_id=test_user.id,
            name="Test Search",
            filters={"brand": "Omega"}
        )
        test_db.add(search)
        test_db.commit()
        test_db.refresh(search)

        response = client.get(
            f"/api/v1/saved-searches/{search.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(search.id)
        assert data["name"] == "Test Search"

    def test_get_saved_search_not_found(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test getting non-existent search"""
        response = client.get(
            "/api/v1/saved-searches/00000000-0000-0000-0000-000000000000",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_get_saved_search_wrong_owner(
        self,
        client: TestClient,
        auth_headers2: dict,
        test_user: User,
        test_db: Session
    ):
        """Test getting another user's search"""
        search = SavedSearch(
            user_id=test_user.id,
            name="Private Search",
            filters={}
        )
        test_db.add(search)
        test_db.commit()
        test_db.refresh(search)

        response = client.get(
            f"/api/v1/saved-searches/{search.id}",
            headers=auth_headers2
        )

        assert response.status_code == 404


class TestUpdateSavedSearch:
    """Test updating saved searches"""

    def test_update_saved_search_name(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        test_db: Session
    ):
        """Test updating search name"""
        search = SavedSearch(
            user_id=test_user.id,
            name="Old Name",
            filters={}
        )
        test_db.add(search)
        test_db.commit()
        test_db.refresh(search)

        response = client.put(
            f"/api/v1/saved-searches/{search.id}",
            headers=auth_headers,
            json={"name": "New Name"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"

    def test_update_saved_search_filters(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        test_db: Session
    ):
        """Test updating search filters"""
        search = SavedSearch(
            user_id=test_user.id,
            name="Test",
            filters={"brand": "Rolex"}
        )
        test_db.add(search)
        test_db.commit()
        test_db.refresh(search)

        response = client.put(
            f"/api/v1/saved-searches/{search.id}",
            headers=auth_headers,
            json={"filters": {"brand": "Omega", "min_price": 3000}}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filters"]["brand"] == "Omega"
        assert data["filters"]["min_price"] == 3000

    def test_update_saved_search_duplicate_name(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        test_db: Session
    ):
        """Test that updating to duplicate name is rejected"""
        search1 = SavedSearch(user_id=test_user.id, name="Search 1", filters={})
        search2 = SavedSearch(user_id=test_user.id, name="Search 2", filters={})
        test_db.add_all([search1, search2])
        test_db.commit()
        test_db.refresh(search2)

        # Try to rename search2 to search1's name
        response = client.put(
            f"/api/v1/saved-searches/{search2.id}",
            headers=auth_headers,
            json={"name": "Search 1"}
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_update_saved_search_partial(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        test_db: Session
    ):
        """Test partial update (only some fields)"""
        search = SavedSearch(
            user_id=test_user.id,
            name="Original",
            filters={"brand": "Rolex"}
        )
        test_db.add(search)
        test_db.commit()
        test_db.refresh(search)

        # Update only filters, not name
        response = client.put(
            f"/api/v1/saved-searches/{search.id}",
            headers=auth_headers,
            json={"filters": {"brand": "Omega"}}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Original"  # Unchanged
        assert data["filters"]["brand"] == "Omega"  # Changed

    def test_update_saved_search_unauthorized(
        self,
        client: TestClient,
        auth_headers2: dict,
        test_user: User,
        test_db: Session
    ):
        """Test updating another user's search"""
        search = SavedSearch(
            user_id=test_user.id,
            name="Test",
            filters={}
        )
        test_db.add(search)
        test_db.commit()
        test_db.refresh(search)

        response = client.put(
            f"/api/v1/saved-searches/{search.id}",
            headers=auth_headers2,
            json={"name": "Hacked"}
        )

        assert response.status_code == 404


class TestDeleteSavedSearch:
    """Test deleting saved searches"""

    def test_delete_saved_search_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        test_db: Session
    ):
        """Test successful deletion"""
        search = SavedSearch(
            user_id=test_user.id,
            name="To Delete",
            filters={}
        )
        test_db.add(search)
        test_db.commit()
        search_id = search.id

        response = client.delete(
            f"/api/v1/saved-searches/{search_id}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify deletion
        deleted = test_db.query(SavedSearch).filter(
            SavedSearch.id == search_id
        ).first()
        assert deleted is None

    def test_delete_saved_search_not_found(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test deleting non-existent search"""
        response = client.delete(
            "/api/v1/saved-searches/00000000-0000-0000-0000-000000000000",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_delete_saved_search_unauthorized(
        self,
        client: TestClient,
        auth_headers2: dict,
        test_user: User,
        test_db: Session
    ):
        """Test deleting another user's search"""
        search = SavedSearch(
            user_id=test_user.id,
            name="Protected",
            filters={}
        )
        test_db.add(search)
        test_db.commit()
        test_db.refresh(search)

        response = client.delete(
            f"/api/v1/saved-searches/{search.id}",
            headers=auth_headers2
        )

        assert response.status_code == 404
