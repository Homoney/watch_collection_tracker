"""
Tests for market value tracking and analytics endpoints
"""
from datetime import datetime, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.watch import Watch
from app.models.market_value import MarketValue
from app.models.collection import Collection


class TestCreateMarketValue:
    """Test market value creation"""

    def test_create_market_value_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test successful market value creation"""
        recorded_at = datetime.utcnow().isoformat()

        response = client.post(
            f"/api/v1/watches/{test_watch.id}/market-values",
            headers=auth_headers,
            json={
                "value": "15000.00",
                "currency": "USD",
                "source": "manual",
                "notes": "Current market estimate",
                "recorded_at": recorded_at
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["watch_id"] == str(test_watch.id)
        assert data["value"] == "15000.00"
        assert data["currency"] == "USD"
        assert data["source"] == "manual"
        assert data["notes"] == "Current market estimate"
        assert "id" in data

    def test_create_market_value_updates_watch_current_value(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test that creating a market value updates the watch's current value"""
        response = client.post(
            f"/api/v1/watches/{test_watch.id}/market-values",
            headers=auth_headers,
            json={
                "value": "16000.00",
                "currency": "USD",
                "source": "chrono24"
            }
        )

        assert response.status_code == 201

        # Verify watch current_market_value is updated
        test_db.refresh(test_watch)
        assert test_watch.current_market_value == Decimal("16000.00")
        assert test_watch.current_market_currency == "USD"
        assert test_watch.last_value_update is not None

    def test_create_market_value_only_updates_if_newer(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test that older values don't override newer current values"""
        # Create recent value
        recent_date = datetime.utcnow()
        client.post(
            f"/api/v1/watches/{test_watch.id}/market-values",
            headers=auth_headers,
            json={
                "value": "17000.00",
                "currency": "USD",
                "source": "manual",
                "recorded_at": recent_date.isoformat()
            }
        )

        test_db.refresh(test_watch)
        assert test_watch.current_market_value == Decimal("17000.00")

        # Try to add older value
        old_date = recent_date - timedelta(days=30)
        client.post(
            f"/api/v1/watches/{test_watch.id}/market-values",
            headers=auth_headers,
            json={
                "value": "14000.00",
                "currency": "USD",
                "source": "manual",
                "recorded_at": old_date.isoformat()
            }
        )

        # Current value should remain unchanged
        test_db.refresh(test_watch)
        assert test_watch.current_market_value == Decimal("17000.00")

    def test_create_market_value_validation(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch
    ):
        """Test validation of market value data"""
        # Missing required field
        response = client.post(
            f"/api/v1/watches/{test_watch.id}/market-values",
            headers=auth_headers,
            json={"currency": "USD"}  # Missing value
        )

        assert response.status_code == 422

    def test_create_market_value_unauthorized(
        self,
        client: TestClient,
        test_watch: Watch
    ):
        """Test creating market value without authentication"""
        response = client.post(
            f"/api/v1/watches/{test_watch.id}/market-values",
            json={"value": "15000", "currency": "USD", "source": "manual"}
        )

        assert response.status_code == 403

    def test_create_market_value_wrong_owner(
        self,
        client: TestClient,
        auth_headers2: dict,
        test_watch: Watch
    ):
        """Test creating market value for another user's watch"""
        response = client.post(
            f"/api/v1/watches/{test_watch.id}/market-values",
            headers=auth_headers2,
            json={"value": "15000", "currency": "USD", "source": "manual"}
        )

        assert response.status_code == 404


class TestListMarketValues:
    """Test market value listing"""

    def test_list_market_values_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test listing market values for a watch"""
        # Create multiple values
        for i in range(3):
            value = MarketValue(
                watch_id=test_watch.id,
                value=Decimal(f"{14000 + i * 1000}"),
                currency="USD",
                source="manual",
                recorded_at=datetime.utcnow() - timedelta(days=i * 30)
            )
            test_db.add(value)
        test_db.commit()

        response = client.get(
            f"/api/v1/watches/{test_watch.id}/market-values",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_list_market_values_date_range_filter(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test filtering market values by date range"""
        now = datetime.utcnow()

        # Create values at different dates
        dates = [
            now - timedelta(days=100),
            now - timedelta(days=50),
            now - timedelta(days=10)
        ]

        for i, date in enumerate(dates):
            value = MarketValue(
                watch_id=test_watch.id,
                value=Decimal(f"{15000 + i * 1000}"),
                currency="USD",
                source="manual",
                recorded_at=date
            )
            test_db.add(value)
        test_db.commit()

        # Filter for last 60 days
        start_date = (now - timedelta(days=60)).isoformat()
        response = client.get(
            f"/api/v1/watches/{test_watch.id}/market-values?start_date={start_date}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Should only return 2 most recent

    def test_list_market_values_sorted_by_date(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test that values are sorted by date (most recent first)"""
        now = datetime.utcnow()

        for i in range(3):
            value = MarketValue(
                watch_id=test_watch.id,
                value=Decimal(f"{14000 + i * 1000}"),
                currency="USD",
                source="manual",
                recorded_at=now - timedelta(days=i * 30)
            )
            test_db.add(value)
        test_db.commit()

        response = client.get(
            f"/api/v1/watches/{test_watch.id}/market-values",
            headers=auth_headers
        )

        data = response.json()
        # First item should be most recent (highest value)
        assert Decimal(data[0]["value"]) == Decimal("14000.00")
        assert Decimal(data[1]["value"]) == Decimal("15000.00")
        assert Decimal(data[2]["value"]) == Decimal("16000.00")

    def test_list_market_values_empty(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch
    ):
        """Test listing when no values exist"""
        response = client.get(
            f"/api/v1/watches/{test_watch.id}/market-values",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json() == []


class TestGetMarketValue:
    """Test getting individual market value"""

    def test_get_market_value_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test getting a specific market value"""
        value = MarketValue(
            watch_id=test_watch.id,
            value=Decimal("15000"),
            currency="USD",
            source="chrono24",
            notes="Test note"
        )
        test_db.add(value)
        test_db.commit()
        test_db.refresh(value)

        response = client.get(
            f"/api/v1/watches/{test_watch.id}/market-values/{value.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(value.id)
        assert Decimal(data["value"]) == Decimal("15000")
        assert data["source"] == "chrono24"

    def test_get_market_value_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch
    ):
        """Test getting non-existent market value"""
        response = client.get(
            f"/api/v1/watches/{test_watch.id}/market-values/00000000-0000-0000-0000-000000000000",
            headers=auth_headers
        )

        assert response.status_code == 404


class TestUpdateMarketValue:
    """Test market value updates"""

    def test_update_market_value_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test successful market value update"""
        value = MarketValue(
            watch_id=test_watch.id,
            value=Decimal("15000"),
            currency="USD",
            source="manual"
        )
        test_db.add(value)
        test_db.commit()
        test_db.refresh(value)

        response = client.put(
            f"/api/v1/watches/{test_watch.id}/market-values/{value.id}",
            headers=auth_headers,
            json={"value": "16000", "notes": "Updated estimate"}
        )

        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["value"]) == Decimal("16000")
        assert data["notes"] == "Updated estimate"

    def test_update_market_value_recalculates_watch_value(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test that updating a market value recalculates watch current value"""
        # Create value
        value = MarketValue(
            watch_id=test_watch.id,
            value=Decimal("15000"),
            currency="USD",
            source="manual",
            recorded_at=datetime.utcnow()
        )
        test_db.add(value)
        test_db.commit()
        test_db.refresh(value)

        # Update value
        client.put(
            f"/api/v1/watches/{test_watch.id}/market-values/{value.id}",
            headers=auth_headers,
            json={"value": "18000"}
        )

        # Verify watch current value is updated
        test_db.refresh(test_watch)
        assert test_watch.current_market_value == Decimal("18000")

    def test_update_market_value_unauthorized(
        self,
        client: TestClient,
        auth_headers2: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test updating another user's market value"""
        value = MarketValue(
            watch_id=test_watch.id,
            value=Decimal("15000"),
            currency="USD",
            source="manual"
        )
        test_db.add(value)
        test_db.commit()
        test_db.refresh(value)

        response = client.put(
            f"/api/v1/watches/{test_watch.id}/market-values/{value.id}",
            headers=auth_headers2,
            json={"value": "1"}
        )

        assert response.status_code == 404


class TestDeleteMarketValue:
    """Test market value deletion"""

    def test_delete_market_value_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test successful market value deletion"""
        value = MarketValue(
            watch_id=test_watch.id,
            value=Decimal("15000"),
            currency="USD",
            source="manual"
        )
        test_db.add(value)
        test_db.commit()
        value_id = value.id

        response = client.delete(
            f"/api/v1/watches/{test_watch.id}/market-values/{value_id}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify deletion
        deleted = test_db.query(MarketValue).filter(
            MarketValue.id == value_id
        ).first()
        assert deleted is None

    def test_delete_market_value_recalculates_watch_value(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test that deleting recalculates to next most recent value"""
        now = datetime.utcnow()

        # Create two values
        value1 = MarketValue(
            watch_id=test_watch.id,
            value=Decimal("14000"),
            currency="USD",
            source="manual",
            recorded_at=now - timedelta(days=30)
        )
        value2 = MarketValue(
            watch_id=test_watch.id,
            value=Decimal("16000"),
            currency="USD",
            source="manual",
            recorded_at=now
        )
        test_db.add_all([value1, value2])

        # Update watch to reflect most recent value
        test_watch.current_market_value = value2.value
        test_watch.current_market_currency = value2.currency
        test_watch.last_value_update = value2.recorded_at

        test_db.commit()

        test_db.refresh(test_watch)
        assert test_watch.current_market_value == Decimal("16000")

        # Delete most recent value
        client.delete(
            f"/api/v1/watches/{test_watch.id}/market-values/{value2.id}",
            headers=auth_headers
        )

        # Verify watch value reverts to older value
        test_db.refresh(test_watch)
        assert test_watch.current_market_value == Decimal("14000")

    def test_delete_market_value_clears_watch_value_if_last(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test that deleting last value clears watch current value"""
        value = MarketValue(
            watch_id=test_watch.id,
            value=Decimal("15000"),
            currency="USD",
            source="manual"
        )
        test_db.add(value)
        test_db.commit()
        test_db.refresh(test_watch)

        # Delete the only value
        client.delete(
            f"/api/v1/watches/{test_watch.id}/market-values/{value.id}",
            headers=auth_headers
        )

        # Verify watch value is cleared
        test_db.refresh(test_watch)
        assert test_watch.current_market_value is None
        assert test_watch.last_value_update is None


class TestWatchAnalytics:
    """Test watch-level analytics"""

    def test_watch_analytics_with_single_value(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test analytics with one market value"""
        value = MarketValue(
            watch_id=test_watch.id,
            value=Decimal("15000"),
            currency="USD",
            source="manual",
            recorded_at=datetime.utcnow()
        )
        test_db.add(value)

        # Update watch's current value (this is done by API but not by direct DB insert)
        test_watch.current_market_value = value.value
        test_watch.current_market_currency = value.currency
        test_watch.last_value_update = value.recorded_at

        test_db.commit()

        response = client.get(
            f"/api/v1/watches/{test_watch.id}/analytics",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["watch_id"] == str(test_watch.id)
        assert Decimal(data["current_value"]) == Decimal("15000")
        assert data["total_valuations"] == 1

    def test_watch_analytics_with_multiple_values(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test analytics with multiple market values"""
        now = datetime.utcnow()

        for i in range(5):
            value = MarketValue(
                watch_id=test_watch.id,
                value=Decimal(f"{14000 + i * 500}"),
                currency="USD",
                source="manual",
                recorded_at=now - timedelta(days=i * 30)
            )
            test_db.add(value)
        test_db.commit()

        response = client.get(
            f"/api/v1/watches/{test_watch.id}/analytics",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_valuations"] == 5

    def test_watch_analytics_calculates_roi(
        self,
        client: TestClient,
        auth_headers: dict,
        test_db: Session,
        test_user,
        test_brand,
        test_collection
    ):
        """Test ROI calculation"""
        # Create watch with purchase price
        watch = Watch(
            model="Test",
            brand_id=test_brand.id,
            collection_id=test_collection.id,
            user_id=test_user.id,
            purchase_price=Decimal("10000"),
            purchase_currency="USD"
        )
        test_db.add(watch)
        test_db.commit()
        test_db.refresh(watch)

        # Add market value
        value = MarketValue(
            watch_id=watch.id,
            value=Decimal("15000"),
            currency="USD",
            source="manual"
        )
        test_db.add(value)

        # Update watch's current value
        watch.current_market_value = value.value
        watch.current_market_currency = value.currency
        watch.last_value_update = value.recorded_at

        test_db.commit()

        response = client.get(
            f"/api/v1/watches/{watch.id}/analytics",
            headers={"Authorization": f"Bearer {client.post('/api/v1/auth/login', json={'email': test_user.email, 'password': 'testpass123'}).json()['access_token']}"}
        )

        data = response.json()
        assert data["purchase_price"] == "10000.00"
        assert Decimal(data["current_value"]) == Decimal("15000")
        assert data["total_return"] == "5000.00"
        assert data["roi_percentage"] == 50.0  # 50% ROI

    def test_watch_analytics_calculates_annualized_return(
        self,
        client: TestClient,
        auth_headers: dict,
        test_db: Session,
        test_user,
        test_brand,
        test_collection
    ):
        """Test annualized return calculation"""
        # Create watch with purchase date 2 years ago
        watch = Watch(
            model="Test",
            brand_id=test_brand.id,
            collection_id=test_collection.id,
            user_id=test_user.id,
            purchase_price=Decimal("10000"),
            purchase_currency="USD",
            purchase_date=datetime.utcnow() - timedelta(days=730)
        )
        test_db.add(watch)
        test_db.commit()
        test_db.refresh(watch)

        # Add current market value
        value = MarketValue(
            watch_id=watch.id,
            value=Decimal("12100"),
            currency="USD",
            source="manual"
        )
        test_db.add(value)

        # Update watch's current value
        watch.current_market_value = value.value
        watch.current_market_currency = value.currency
        watch.last_value_update = value.recorded_at

        test_db.commit()

        response = client.get(
            f"/api/v1/watches/{watch.id}/analytics",
            headers={"Authorization": f"Bearer {client.post('/api/v1/auth/login', json={'email': test_user.email, 'password': 'testpass123'}).json()['access_token']}"}
        )

        data = response.json()
        assert data["annualized_return"] is not None
        # Should be roughly 10% annualized (21% total over 2 years)

    def test_watch_analytics_calculates_value_changes(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test value change calculations (30d, 90d, 1y)"""
        now = datetime.utcnow()

        # Create values at different time points
        values_data = [
            (now - timedelta(days=400), Decimal("12000")),  # Over 1 year ago
            (now - timedelta(days=100), Decimal("13000")),  # ~90 days
            (now - timedelta(days=35), Decimal("14000")),   # ~30 days
            (now, Decimal("15000"))                          # Current
        ]

        for date, val in values_data:
            value = MarketValue(
                watch_id=test_watch.id,
                value=val,
                currency="USD",
                source="manual",
                recorded_at=date
            )
            test_db.add(value)

        # Update watch to reflect most recent value
        test_watch.current_market_value = Decimal("15000")
        test_watch.current_market_currency = "USD"
        test_watch.last_value_update = now

        test_db.commit()

        response = client.get(
            f"/api/v1/watches/{test_watch.id}/analytics",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["value_change_30d"] == "1000.00"  # 15000 - 14000
        assert data["value_change_90d"] == "2000.00"  # 15000 - 13000
        assert data["value_change_1y"] == "3000.00"   # 15000 - 12000

    def test_watch_analytics_no_values(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch
    ):
        """Test analytics when watch has no market values"""
        response = client.get(
            f"/api/v1/watches/{test_watch.id}/analytics",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_valuations"] == 0
        assert data["current_value"] is None

    def test_watch_analytics_unauthorized(
        self,
        client: TestClient,
        test_watch: Watch
    ):
        """Test analytics without authentication"""
        response = client.get(
            f"/api/v1/watches/{test_watch.id}/analytics"
        )

        assert response.status_code == 403


class TestCollectionAnalytics:
    """Test collection-level analytics"""

    def test_collection_analytics_all_watches(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session,
        test_user,
        test_brand,
        test_collection
    ):
        """Test analytics across all user's watches"""
        # Add market values to test_watch
        value1 = MarketValue(
            watch_id=test_watch.id,
            value=Decimal("15000"),
            currency="USD",
            source="manual"
        )
        test_db.add(value1)

        # Create another watch with value
        watch2 = Watch(
            model="Test2",
            brand_id=test_brand.id,
            collection_id=test_collection.id,
            user_id=test_user.id,
            purchase_price=Decimal("5000"),
            purchase_currency="USD"
        )
        test_db.add(watch2)
        test_db.commit()
        test_db.refresh(watch2)

        value2 = MarketValue(
            watch_id=watch2.id,
            value=Decimal("8000"),
            currency="USD",
            source="manual"
        )
        test_db.add(value2)
        test_db.commit()

        # Update watches to reflect current values
        test_watch.current_market_value = Decimal("15000")
        test_watch.current_market_currency = "USD"
        watch2.current_market_value = Decimal("8000")
        watch2.current_market_currency = "USD"
        test_db.commit()

        response = client.get(
            "/api/v1/collection-analytics",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_watches"] == 2
        assert data["total_valuations"] == 2
        assert Decimal(data["total_current_value"]) == Decimal("23000")

    def test_collection_analytics_calculates_roi(
        self,
        client: TestClient,
        auth_headers: dict,
        test_db: Session,
        test_user,
        test_brand,
        test_collection
    ):
        """Test ROI calculation in collection analytics"""
        # Create watch with purchase and current value
        watch = Watch(
            model="Test",
            brand_id=test_brand.id,
            collection_id=test_collection.id,
            user_id=test_user.id,
            purchase_price=Decimal("10000"),
            purchase_currency="USD",
            current_market_value=Decimal("15000"),
            current_market_currency="USD"
        )
        test_db.add(watch)
        test_db.commit()

        response = client.get(
            "/api/v1/collection-analytics",
            headers=auth_headers
        )

        data = response.json()
        assert data["total_return"] == "5000.00"
        assert data["average_roi"] == 50.0

    def test_collection_analytics_by_brand(
        self,
        client: TestClient,
        auth_headers: dict,
        test_db: Session,
        test_user,
        test_brand,
        test_collection
    ):
        """Test brand breakdown in analytics"""
        # Create watch with market value
        watch = Watch(
            model="Test",
            brand_id=test_brand.id,
            collection_id=test_collection.id,
            user_id=test_user.id,
            current_market_value=Decimal("15000"),
            current_market_currency="USD"
        )
        test_db.add(watch)
        test_db.commit()

        response = client.get(
            "/api/v1/collection-analytics",
            headers=auth_headers
        )

        data = response.json()
        assert "value_by_brand" in data
        assert test_brand.name in data["value_by_brand"]
        # Value returned as string in some API responses
        assert float(data["value_by_brand"][test_brand.name]) == 15000.0

    def test_collection_analytics_top_performers(
        self,
        client: TestClient,
        auth_headers: dict,
        test_db: Session,
        test_user,
        test_brand,
        test_collection
    ):
        """Test top performers list"""
        # Create multiple watches with varying ROI
        watches = []
        rois = [10, 25, 50, 75, 100]  # Different ROI percentages

        for i, roi_pct in enumerate(rois):
            watch = Watch(
                model=f"Watch{i}",
                brand_id=test_brand.id,
                collection_id=test_collection.id,
                user_id=test_user.id,
                purchase_price=Decimal("10000"),
                purchase_currency="USD",
                current_market_value=Decimal(10000 * (1 + roi_pct / 100)),
                current_market_currency="USD"
            )
            test_db.add(watch)
            watches.append(watch)
        test_db.commit()

        response = client.get(
            "/api/v1/collection-analytics",
            headers=auth_headers
        )

        data = response.json()
        assert "top_performers" in data
        assert len(data["top_performers"]) <= 5
        # Top performer should have highest ROI
        if data["top_performers"]:
            assert data["top_performers"][0]["roi"] == 100.0

    def test_collection_analytics_with_currency_filter(
        self,
        client: TestClient,
        auth_headers: dict,
        test_db: Session,
        test_user,
        test_brand,
        test_collection
    ):
        """Test currency filtering in analytics"""
        # Create watches with different currencies
        usd_watch = Watch(
            model="USD Watch",
            brand_id=test_brand.id,
            collection_id=test_collection.id,
            user_id=test_user.id,
            purchase_price=Decimal("10000"),
            purchase_currency="USD",
            current_market_value=Decimal("15000"),
            current_market_currency="USD"
        )
        eur_watch = Watch(
            model="EUR Watch",
            brand_id=test_brand.id,
            collection_id=test_collection.id,
            user_id=test_user.id,
            purchase_price=Decimal("10000"),
            purchase_currency="EUR",
            current_market_value=Decimal("15000"),
            current_market_currency="EUR"
        )
        test_db.add_all([usd_watch, eur_watch])
        test_db.commit()

        # Filter by USD
        response = client.get(
            "/api/v1/collection-analytics?currency=USD",
            headers=auth_headers
        )

        data = response.json()
        assert data["currency"] == "USD"
        # Should only include USD watch
        assert Decimal(data["total_current_value"]) == Decimal("15000")

    def test_collection_analytics_no_watches(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test analytics when user has no watches"""
        response = client.get(
            "/api/v1/collection-analytics",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_watches"] == 0
        assert data["total_current_value"] == "0"
