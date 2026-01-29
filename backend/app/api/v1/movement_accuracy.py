import logging
from datetime import datetime, timedelta, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.movement_accuracy import MovementAccuracyReading
from app.models.user import User
from app.models.watch import Watch
from app.schemas.movement_accuracy import (
    AccuracyAnalytics,
    AtomicTimeResponse,
    MovementAccuracyReadingCreate,
    MovementAccuracyReadingResponse,
    MovementAccuracyReadingUpdate,
    MovementAccuracyReadingWithDrift,
)
from app.utils.atomic_time import (
    calculate_drift_spd,
    get_atomic_time,
    validate_reading_pair,
)

logger = logging.getLogger(__name__)

router = APIRouter()
atomic_time_router = APIRouter()  # Public router for atomic time


@atomic_time_router.get("/atomic-time", response_model=AtomicTimeResponse)
async def get_current_atomic_time(
    tz: str = Query(
        "UTC", description="Timezone for atomic time (e.g., UTC, America/New_York)"
    )
):
    """
    Get current atomic time from WorldTimeAPI with fallback to server time.
    Used by frontend to display real-time clock.
    """
    current_time, is_atomic = await get_atomic_time(tz)

    return AtomicTimeResponse(
        current_time=current_time,
        is_atomic_source=is_atomic,
        timezone=tz,
        unix_timestamp=current_time.timestamp(),
    )


def _verify_watch_ownership(watch_id: UUID, user_id: UUID, db: Session) -> Watch:
    """Helper to verify watch exists and belongs to current user."""
    watch = (
        db.query(Watch).filter(Watch.id == watch_id, Watch.user_id == user_id).first()
    )

    if not watch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Watch not found"
        )

    return watch


@router.post(
    "/{watch_id}/accuracy-readings",
    response_model=MovementAccuracyReadingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_accuracy_reading(
    watch_id: UUID,
    reading: MovementAccuracyReadingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new accuracy reading for a watch.

    Validation rules:
    - First reading for a watch must be marked as initial
    - Subsequent readings require a prior initial within 90 days
    - Subsequent readings must be at least 6 hours after the paired initial
    """
    # Verify watch ownership
    watch = _verify_watch_ownership(watch_id, current_user.id, db)

    # Get atomic time for reference
    reference_time, is_atomic = await get_atomic_time(reading.timezone)

    # Check if this is the first reading
    existing_count = (
        db.query(func.count(MovementAccuracyReading.id))
        .filter(MovementAccuracyReading.watch_id == watch_id)
        .scalar()
    )

    if existing_count == 0:
        # First reading must be initial
        if not reading.is_initial_reading:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="First reading for a watch must be marked as initial (baseline)",
            )
    elif not reading.is_initial_reading:
        # For subsequent readings, find the most recent initial reading
        most_recent_initial = (
            db.query(MovementAccuracyReading)
            .filter(
                MovementAccuracyReading.watch_id == watch_id,
                MovementAccuracyReading.is_initial_reading == True,
                MovementAccuracyReading.reference_time < reference_time,
            )
            .order_by(desc(MovementAccuracyReading.reference_time))
            .first()
        )

        if not most_recent_initial:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No initial reading found. Please create an initial reading first.",
            )

        # Validate the reading pair
        is_valid, error_msg = validate_reading_pair(
            most_recent_initial.reference_time,
            reference_time,
            min_hours=6.0,
            max_days=90,
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg
            )

    # Create the reading
    db_reading = MovementAccuracyReading(
        watch_id=watch_id,
        reference_time=reference_time,
        watch_seconds_position=reading.watch_seconds_position,
        is_initial_reading=reading.is_initial_reading,
        is_atomic_source=is_atomic,
        notes=reading.notes,
        timezone=reading.timezone,
    )

    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)

    logger.info(
        f"Created accuracy reading for watch {watch_id}: "
        f"initial={reading.is_initial_reading}, position={reading.watch_seconds_position}, "
        f"atomic={is_atomic}"
    )

    return db_reading


@router.get(
    "/{watch_id}/accuracy-readings",
    response_model=List[MovementAccuracyReadingWithDrift],
)
def list_accuracy_readings(
    watch_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all accuracy readings for a watch, sorted by date descending.
    Includes calculated drift for subsequent readings.
    """
    # Verify watch ownership
    _verify_watch_ownership(watch_id, current_user.id, db)

    # Get all readings sorted by date descending
    readings = (
        db.query(MovementAccuracyReading)
        .filter(MovementAccuracyReading.watch_id == watch_id)
        .order_by(desc(MovementAccuracyReading.reference_time))
        .all()
    )

    # Calculate drift for subsequent readings
    result = []
    for reading in readings:
        reading_dict = MovementAccuracyReadingWithDrift.model_validate(
            reading
        ).model_dump()

        if not reading.is_initial_reading:
            # Find the most recent initial before this reading
            paired_initial = (
                db.query(MovementAccuracyReading)
                .filter(
                    MovementAccuracyReading.watch_id == watch_id,
                    MovementAccuracyReading.is_initial_reading == True,
                    MovementAccuracyReading.reference_time < reading.reference_time,
                )
                .order_by(desc(MovementAccuracyReading.reference_time))
                .first()
            )

            if paired_initial:
                try:
                    drift = calculate_drift_spd(
                        paired_initial.reference_time,
                        paired_initial.watch_seconds_position,
                        reading.reference_time,
                        reading.watch_seconds_position,
                    )

                    hours_elapsed = (
                        reading.reference_time - paired_initial.reference_time
                    ).total_seconds() / 3600

                    reading_dict["drift_seconds_per_day"] = drift
                    reading_dict["hours_since_initial"] = round(hours_elapsed, 2)
                    reading_dict["paired_initial_id"] = paired_initial.id
                except Exception as e:
                    logger.error(
                        f"Error calculating drift for reading {reading.id}: {e}"
                    )

        result.append(MovementAccuracyReadingWithDrift(**reading_dict))

    return result


@router.get(
    "/{watch_id}/accuracy-readings/{reading_id}",
    response_model=MovementAccuracyReadingWithDrift,
)
def get_accuracy_reading(
    watch_id: UUID,
    reading_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single accuracy reading by ID."""
    # Verify watch ownership
    _verify_watch_ownership(watch_id, current_user.id, db)

    # Get the reading
    reading = (
        db.query(MovementAccuracyReading)
        .filter(
            MovementAccuracyReading.id == reading_id,
            MovementAccuracyReading.watch_id == watch_id,
        )
        .first()
    )

    if not reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Accuracy reading not found"
        )

    # Build response with drift calculation
    reading_dict = MovementAccuracyReadingWithDrift.model_validate(reading).model_dump()

    if not reading.is_initial_reading:
        # Find the most recent initial before this reading
        paired_initial = (
            db.query(MovementAccuracyReading)
            .filter(
                MovementAccuracyReading.watch_id == watch_id,
                MovementAccuracyReading.is_initial_reading == True,
                MovementAccuracyReading.reference_time < reading.reference_time,
            )
            .order_by(desc(MovementAccuracyReading.reference_time))
            .first()
        )

        if paired_initial:
            try:
                drift = calculate_drift_spd(
                    paired_initial.reference_time,
                    paired_initial.watch_seconds_position,
                    reading.reference_time,
                    reading.watch_seconds_position,
                )

                hours_elapsed = (
                    reading.reference_time - paired_initial.reference_time
                ).total_seconds() / 3600

                reading_dict["drift_seconds_per_day"] = drift
                reading_dict["hours_since_initial"] = round(hours_elapsed, 2)
                reading_dict["paired_initial_id"] = paired_initial.id
            except Exception as e:
                logger.error(f"Error calculating drift for reading {reading.id}: {e}")

    return MovementAccuracyReadingWithDrift(**reading_dict)


@router.put(
    "/{watch_id}/accuracy-readings/{reading_id}",
    response_model=MovementAccuracyReadingResponse,
)
def update_accuracy_reading(
    watch_id: UUID,
    reading_id: UUID,
    reading_update: MovementAccuracyReadingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing accuracy reading."""
    # Verify watch ownership
    _verify_watch_ownership(watch_id, current_user.id, db)

    # Get the reading
    db_reading = (
        db.query(MovementAccuracyReading)
        .filter(
            MovementAccuracyReading.id == reading_id,
            MovementAccuracyReading.watch_id == watch_id,
        )
        .first()
    )

    if not db_reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Accuracy reading not found"
        )

    # Update fields
    update_data = reading_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_reading, field, value)

    db_reading.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_reading)

    logger.info(f"Updated accuracy reading {reading_id} for watch {watch_id}")

    return db_reading


@router.delete(
    "/{watch_id}/accuracy-readings/{reading_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_accuracy_reading(
    watch_id: UUID,
    reading_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an accuracy reading."""
    # Verify watch ownership
    _verify_watch_ownership(watch_id, current_user.id, db)

    # Get the reading
    db_reading = (
        db.query(MovementAccuracyReading)
        .filter(
            MovementAccuracyReading.id == reading_id,
            MovementAccuracyReading.watch_id == watch_id,
        )
        .first()
    )

    if not db_reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Accuracy reading not found"
        )

    db.delete(db_reading)
    db.commit()

    logger.info(f"Deleted accuracy reading {reading_id} for watch {watch_id}")

    return None


@router.get("/{watch_id}/accuracy-analytics", response_model=AccuracyAnalytics)
def get_accuracy_analytics(
    watch_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get analytics and statistics for watch movement accuracy.
    Calculates drift metrics, trends, and statistics.
    """
    # Verify watch ownership
    _verify_watch_ownership(watch_id, current_user.id, db)

    # Get all readings
    all_readings = (
        db.query(MovementAccuracyReading)
        .filter(MovementAccuracyReading.watch_id == watch_id)
        .order_by(MovementAccuracyReading.reference_time)
        .all()
    )

    # Count readings
    total_readings = len(all_readings)
    initial_readings = [r for r in all_readings if r.is_initial_reading]
    subsequent_readings = [r for r in all_readings if not r.is_initial_reading]

    # Initialize analytics
    analytics = AccuracyAnalytics(
        watch_id=watch_id,
        total_readings=total_readings,
        total_initial_readings=len(initial_readings),
        total_subsequent_readings=len(subsequent_readings),
    )

    if not all_readings:
        return analytics

    # Set date ranges
    analytics.first_reading_date = all_readings[0].reference_time
    analytics.last_reading_date = all_readings[-1].reference_time

    if len(all_readings) >= 2:
        days_range = (
            all_readings[-1].reference_time - all_readings[0].reference_time
        ).days
        analytics.date_range_days = days_range

    # Calculate drift for all subsequent readings
    drift_values = []

    for reading in subsequent_readings:
        # Find the most recent initial before this reading
        paired_initial = None
        for initial in reversed(initial_readings):
            if initial.reference_time < reading.reference_time:
                paired_initial = initial
                break

        if paired_initial:
            try:
                drift = calculate_drift_spd(
                    paired_initial.reference_time,
                    paired_initial.watch_seconds_position,
                    reading.reference_time,
                    reading.watch_seconds_position,
                )
                drift_values.append({"drift": drift, "date": reading.reference_time})
            except Exception as e:
                logger.error(f"Error calculating drift for analytics: {e}")

    if not drift_values:
        return analytics

    # Calculate statistics
    drifts = [d["drift"] for d in drift_values]

    # Current drift (most recent)
    analytics.current_drift_spd = drifts[-1]

    # Average drift
    analytics.average_drift_spd = round(sum(drifts) / len(drifts), 2)

    # Best/worst accuracy (closest/furthest from zero)
    abs_drifts = [(abs(d), d) for d in drifts]
    abs_drifts.sort()
    analytics.best_accuracy_spd = abs_drifts[0][1]
    analytics.worst_accuracy_spd = abs_drifts[-1][1]

    # Time-based trends
    now = datetime.now(timezone.utc)

    # 7-day average
    recent_7d = [d["drift"] for d in drift_values if (now - d["date"]).days <= 7]
    if recent_7d:
        analytics.drift_7d_avg = round(sum(recent_7d) / len(recent_7d), 2)

    # 30-day average
    recent_30d = [d["drift"] for d in drift_values if (now - d["date"]).days <= 30]
    if recent_30d:
        analytics.drift_30d_avg = round(sum(recent_30d) / len(recent_30d), 2)

    # 90-day average
    recent_90d = [d["drift"] for d in drift_values if (now - d["date"]).days <= 90]
    if recent_90d:
        analytics.drift_90d_avg = round(sum(recent_90d) / len(recent_90d), 2)

    return analytics
