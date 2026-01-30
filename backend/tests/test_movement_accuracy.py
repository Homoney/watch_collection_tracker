"""
Tests for movement accuracy tracking endpoints
"""
from datetime import datetime, timedelta
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.watch import Watch
from app.models.movement_accuracy import MovementAccuracyReading


class TestAtomicTime:
    """Test atomic time endpoint"""

    @patch('app.utils.atomic_time.get_atomic_time')
    async def test_get_atomic_time_success(self, mock_get_time, client: TestClient):
        """Test getting atomic time"""
        test_time = datetime.utcnow()
        mock_get_time.return_value = AsyncMock(return_value=(test_time, True))

        response = client.get("/api/v1/atomic-time")

        assert response.status_code == 200
        data = response.json()
        assert "current_time" in data
        assert "is_atomic_source" in data
        assert "timezone" in data
        assert "unix_timestamp" in data

    def test_get_atomic_time_with_timezone(self, client: TestClient):
        """Test atomic time with specific timezone"""
        response = client.get("/api/v1/atomic-time?tz=America/New_York")

        assert response.status_code == 200
        data = response.json()
        assert data["timezone"] == "America/New_York"


class TestCreateAccuracyReading:
    """Test accuracy reading creation"""

    def test_create_initial_reading_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test creating first (initial) reading"""
        response = client.post(
            f"/api/v1/watches/{test_watch.id}/accuracy-readings",
            headers=auth_headers,
            json={
                "watch_seconds_position": 0,
                "is_initial_reading": True,
                "timezone": "UTC",
                "notes": "After regulation"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["watch_id"] == str(test_watch.id)
        assert data["watch_seconds_position"] == 0
        assert data["is_initial_reading"] is True
        assert data["notes"] == "After regulation"

    def test_create_initial_reading_first_must_be_initial(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch
    ):
        """Test that first reading must be marked as initial"""
        response = client.post(
            f"/api/v1/watches/{test_watch.id}/accuracy-readings",
            headers=auth_headers,
            json={
                "watch_seconds_position": 0,
                "is_initial_reading": False,  # Wrong!
                "timezone": "UTC"
            }
        )

        assert response.status_code == 400
        assert "must be marked as initial" in response.json()["detail"]

    def test_create_subsequent_reading_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test creating subsequent reading after initial"""
        # Create initial reading
        initial_time = datetime.utcnow() - timedelta(hours=24)
        initial = MovementAccuracyReading(
            watch_id=test_watch.id,
            reference_time=initial_time,
            watch_seconds_position=0,
            is_initial_reading=True,
            timezone="UTC"
        )
        test_db.add(initial)
        test_db.commit()

        # Create subsequent reading (24 hours later)
        response = client.post(
            f"/api/v1/watches/{test_watch.id}/accuracy-readings",
            headers=auth_headers,
            json={
                "watch_seconds_position": 15,  # Watch is at 15 seconds position
                "is_initial_reading": False,
                "timezone": "UTC",
                "notes": "Daily check"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["is_initial_reading"] is False
        assert data["watch_seconds_position"] == 15

    def test_create_subsequent_reading_requires_prior_initial(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test that subsequent reading requires an initial reading"""
        # Create a subsequent reading (not initial) as first reading
        # But first create a non-initial reading in the past to bypass first check
        old_reading = MovementAccuracyReading(
            watch_id=test_watch.id,
            reference_time=datetime.utcnow() - timedelta(days=200),
            watch_seconds_position=0,
            is_initial_reading=True,
            timezone="UTC"
        )
        test_db.add(old_reading)
        test_db.commit()

        # Try to create subsequent without recent initial
        response = client.post(
            f"/api/v1/watches/{test_watch.id}/accuracy-readings",
            headers=auth_headers,
            json={
                "watch_seconds_position": 15,
                "is_initial_reading": False,
                "timezone": "UTC"
            }
        )

        # Should fail because initial is too old (>90 days)
        assert response.status_code == 400

    def test_create_subsequent_reading_minimum_6_hours(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test minimum 6 hour gap between initial and subsequent"""
        # Create initial reading
        initial_time = datetime.utcnow() - timedelta(hours=3)  # Only 3 hours ago
        initial = MovementAccuracyReading(
            watch_id=test_watch.id,
            reference_time=initial_time,
            watch_seconds_position=0,
            is_initial_reading=True,
            timezone="UTC"
        )
        test_db.add(initial)
        test_db.commit()

        # Try to create subsequent too soon
        response = client.post(
            f"/api/v1/watches/{test_watch.id}/accuracy-readings",
            headers=auth_headers,
            json={
                "watch_seconds_position": 15,  # Valid: must be 0, 15, 30, or 45
                "is_initial_reading": False,
                "timezone": "UTC"
            }
        )

        assert response.status_code == 400
        # Check for the actual error message format
        detail = response.json()["detail"].lower()
        assert ("6" in detail and "hours" in detail) or "minimum" in detail

    def test_create_subsequent_reading_maximum_90_days(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test maximum 90 day gap validation"""
        # Create initial reading 100 days ago
        initial_time = datetime.utcnow() - timedelta(days=100)
        initial = MovementAccuracyReading(
            watch_id=test_watch.id,
            reference_time=initial_time,
            watch_seconds_position=0,
            is_initial_reading=True,
            timezone="UTC"
        )
        test_db.add(initial)
        test_db.commit()

        # Try to create subsequent beyond 90 days
        response = client.post(
            f"/api/v1/watches/{test_watch.id}/accuracy-readings",
            headers=auth_headers,
            json={
                "watch_seconds_position": 30,  # Valid: must be 0, 15, 30, or 45
                "is_initial_reading": False,
                "timezone": "UTC"
            }
        )

        assert response.status_code == 400
        assert "90 days" in response.json()["detail"].lower()

    def test_create_reading_unauthorized(
        self,
        client: TestClient,
        test_watch: Watch
    ):
        """Test creating reading without authentication"""
        response = client.post(
            f"/api/v1/watches/{test_watch.id}/accuracy-readings",
            json={
                "watch_seconds_position": 0,
                "is_initial_reading": True,
                "timezone": "UTC"
            }
        )

        assert response.status_code == 401


class TestListAccuracyReadings:
    """Test listing accuracy readings"""

    def test_list_accuracy_readings_with_drift(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test listing readings includes drift calculation"""
        # Create initial and subsequent readings
        initial_time = datetime.utcnow() - timedelta(hours=24)
        initial = MovementAccuracyReading(
            watch_id=test_watch.id,
            reference_time=initial_time,
            watch_seconds_position=0,
            is_initial_reading=True,
            timezone="UTC"
        )
        test_db.add(initial)
        test_db.commit()

        subsequent_time = datetime.utcnow()
        subsequent = MovementAccuracyReading(
            watch_id=test_watch.id,
            reference_time=subsequent_time,
            watch_seconds_position=15,  # Valid positions: 0, 15, 30, or 45
            is_initial_reading=False,
            timezone="UTC"
        )
        test_db.add(subsequent)
        test_db.commit()

        # List readings
        response = client.get(
            f"/api/v1/watches/{test_watch.id}/accuracy-readings",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Check that subsequent reading has drift calculated
        subsequent_data = next(r for r in data if not r["is_initial_reading"])
        assert "drift_seconds_per_day" in subsequent_data
        assert subsequent_data["drift_seconds_per_day"] is not None
        assert "hours_since_initial" in subsequent_data
        assert "paired_initial_id" in subsequent_data

    def test_list_accuracy_readings_sorted_by_date(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test readings are sorted by date (most recent first)"""
        # Create multiple readings
        base_time = datetime.utcnow() - timedelta(days=10)

        valid_positions = [0, 15, 30]
        for i in range(3):
            reading = MovementAccuracyReading(
                watch_id=test_watch.id,
                reference_time=base_time + timedelta(days=i * 3),
                watch_seconds_position=valid_positions[i],
                is_initial_reading=(i == 0),
                timezone="UTC"
            )
            test_db.add(reading)
        test_db.commit()

        response = client.get(
            f"/api/v1/watches/{test_watch.id}/accuracy-readings",
            headers=auth_headers
        )

        data = response.json()
        # Should be sorted descending (most recent first)
        assert data[0]["watch_seconds_position"] == 30  # Most recent
        assert data[2]["watch_seconds_position"] == 0   # Oldest

    def test_list_accuracy_readings_pairs_with_initials(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test that subsequent readings pair with correct initial"""
        # Create first initial
        initial1_time = datetime.utcnow() - timedelta(days=50)
        initial1 = MovementAccuracyReading(
            watch_id=test_watch.id,
            reference_time=initial1_time,
            watch_seconds_position=0,
            is_initial_reading=True,
            timezone="UTC"
        )
        test_db.add(initial1)

        # Create subsequent after first initial
        sub1_time = initial1_time + timedelta(days=10)
        sub1 = MovementAccuracyReading(
            watch_id=test_watch.id,
            reference_time=sub1_time,
            watch_seconds_position=45,  # Must be 0, 15, 30, or 45
            is_initial_reading=False,
            timezone="UTC"
        )
        test_db.add(sub1)

        # Create second initial (after regulation)
        initial2_time = datetime.utcnow() - timedelta(days=20)
        initial2 = MovementAccuracyReading(
            watch_id=test_watch.id,
            reference_time=initial2_time,
            watch_seconds_position=0,
            is_initial_reading=True,
            timezone="UTC"
        )
        test_db.add(initial2)

        # Create subsequent after second initial
        sub2_time = datetime.utcnow()
        sub2 = MovementAccuracyReading(
            watch_id=test_watch.id,
            reference_time=sub2_time,
            watch_seconds_position=30,  # Must be 0, 15, 30, or 45
            is_initial_reading=False,
            timezone="UTC"
        )
        test_db.add(sub2)
        test_db.commit()

        response = client.get(
            f"/api/v1/watches/{test_watch.id}/accuracy-readings",
            headers=auth_headers
        )

        data = response.json()
        # Find the most recent subsequent reading
        most_recent_sub = data[0]
        assert not most_recent_sub["is_initial_reading"]
        # It should be paired with initial2
        assert str(most_recent_sub["paired_initial_id"]) == str(initial2.id)

    def test_list_accuracy_readings_empty(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch
    ):
        """Test listing when no readings exist"""
        response = client.get(
            f"/api/v1/watches/{test_watch.id}/accuracy-readings",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json() == []


class TestGetAccuracyReading:
    """Test getting individual accuracy reading"""

    def test_get_accuracy_reading_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test getting a specific reading"""
        reading = MovementAccuracyReading(
            watch_id=test_watch.id,
            reference_time=datetime.utcnow(),
            watch_seconds_position=0,
            is_initial_reading=True,
            timezone="UTC",
            notes="Test reading"
        )
        test_db.add(reading)
        test_db.commit()
        test_db.refresh(reading)

        response = client.get(
            f"/api/v1/watches/{test_watch.id}/accuracy-readings/{reading.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(reading.id)
        assert data["notes"] == "Test reading"

    def test_get_accuracy_reading_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch
    ):
        """Test getting non-existent reading"""
        response = client.get(
            f"/api/v1/watches/{test_watch.id}/accuracy-readings/00000000-0000-0000-0000-000000000000",
            headers=auth_headers
        )

        assert response.status_code == 404


class TestUpdateAccuracyReading:
    """Test updating accuracy readings"""

    def test_update_accuracy_reading_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test updating reading notes"""
        reading = MovementAccuracyReading(
            watch_id=test_watch.id,
            reference_time=datetime.utcnow(),
            watch_seconds_position=0,
            is_initial_reading=True,
            timezone="UTC",
            notes="Original notes"
        )
        test_db.add(reading)
        test_db.commit()
        test_db.refresh(reading)

        response = client.put(
            f"/api/v1/watches/{test_watch.id}/accuracy-readings/{reading.id}",
            headers=auth_headers,
            json={"notes": "Updated notes"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Updated notes"

    def test_update_accuracy_reading_unauthorized(
        self,
        client: TestClient,
        auth_headers2: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test updating another user's reading"""
        reading = MovementAccuracyReading(
            watch_id=test_watch.id,
            reference_time=datetime.utcnow(),
            watch_seconds_position=0,
            is_initial_reading=True,
            timezone="UTC"
        )
        test_db.add(reading)
        test_db.commit()
        test_db.refresh(reading)

        response = client.put(
            f"/api/v1/watches/{test_watch.id}/accuracy-readings/{reading.id}",
            headers=auth_headers2,
            json={"notes": "Hacked"}
        )

        assert response.status_code == 404


class TestDeleteAccuracyReading:
    """Test deleting accuracy readings"""

    def test_delete_accuracy_reading_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test successful deletion"""
        reading = MovementAccuracyReading(
            watch_id=test_watch.id,
            reference_time=datetime.utcnow(),
            watch_seconds_position=0,
            is_initial_reading=True,
            timezone="UTC"
        )
        test_db.add(reading)
        test_db.commit()
        reading_id = reading.id

        response = client.delete(
            f"/api/v1/watches/{test_watch.id}/accuracy-readings/{reading_id}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify deletion
        deleted = test_db.query(MovementAccuracyReading).filter(
            MovementAccuracyReading.id == reading_id
        ).first()
        assert deleted is None

    def test_delete_accuracy_reading_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch
    ):
        """Test deleting non-existent reading"""
        response = client.delete(
            f"/api/v1/watches/{test_watch.id}/accuracy-readings/00000000-0000-0000-0000-000000000000",
            headers=auth_headers
        )

        assert response.status_code == 404


class TestAccuracyAnalytics:
    """Test accuracy analytics endpoint"""

    def test_accuracy_analytics_single_reading(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test analytics with single initial reading"""
        reading = MovementAccuracyReading(
            watch_id=test_watch.id,
            reference_time=datetime.utcnow(),
            watch_seconds_position=0,
            is_initial_reading=True,
            timezone="UTC"
        )
        test_db.add(reading)
        test_db.commit()

        response = client.get(
            f"/api/v1/watches/{test_watch.id}/accuracy-analytics",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_readings"] == 1
        assert data["current_drift_spd"] is None  # No subsequent yet

    def test_accuracy_analytics_multiple_readings(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test analytics with multiple readings"""
        base_time = datetime.utcnow() - timedelta(days=30)

        # Create initial
        initial = MovementAccuracyReading(
            watch_id=test_watch.id,
            reference_time=base_time,
            watch_seconds_position=0,
            is_initial_reading=True,
            timezone="UTC"
        )
        test_db.add(initial)

        # Create subsequents with varying positions
        positions = [15, 30, 45]  # Valid positions only
        for i in range(1, 4):
            reading = MovementAccuracyReading(
                watch_id=test_watch.id,
                reference_time=base_time + timedelta(days=i * 7),
                watch_seconds_position=positions[i-1],
                is_initial_reading=False,
                timezone="UTC"
            )
            test_db.add(reading)

        test_db.commit()

        response = client.get(
            f"/api/v1/watches/{test_watch.id}/accuracy-analytics",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_readings"] == 4
        assert data["current_drift_spd"] is not None
        assert data["average_drift_spd"] is not None

    def test_accuracy_analytics_calculates_average_drift(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch,
        test_db: Session
    ):
        """Test average drift calculation"""
        base_time = datetime.utcnow() - timedelta(days=20)

        # Initial
        initial = MovementAccuracyReading(
            watch_id=test_watch.id,
            reference_time=base_time,
            watch_seconds_position=0,
            is_initial_reading=True,
            timezone="UTC"
        )
        test_db.add(initial)

        # Multiple subsequents
        positions = [15, 30]  # Valid positions only: 0, 15, 30, or 45
        for i, days in enumerate([7, 14]):
            reading = MovementAccuracyReading(
                watch_id=test_watch.id,
                reference_time=base_time + timedelta(days=days),
                watch_seconds_position=positions[i],
                is_initial_reading=False,
                timezone="UTC"
            )
            test_db.add(reading)

        test_db.commit()

        response = client.get(
            f"/api/v1/watches/{test_watch.id}/accuracy-analytics",
            headers=auth_headers
        )

        data = response.json()
        assert data["average_drift_spd"] is not None

    def test_accuracy_analytics_no_readings(
        self,
        client: TestClient,
        auth_headers: dict,
        test_watch: Watch
    ):
        """Test analytics with no readings"""
        response = client.get(
            f"/api/v1/watches/{test_watch.id}/accuracy-analytics",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_readings"] == 0
        assert data["current_drift_spd"] is None

    def test_accuracy_analytics_unauthorized(
        self,
        client: TestClient,
        test_watch: Watch
    ):
        """Test analytics without authentication"""
        response = client.get(
            f"/api/v1/watches/{test_watch.id}/accuracy-analytics"
        )

        assert response.status_code == 401
