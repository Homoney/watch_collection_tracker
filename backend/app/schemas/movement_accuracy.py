from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID


# Request schemas
class MovementAccuracyReadingCreate(BaseModel):
    """Schema for creating a new accuracy reading."""
    watch_seconds_position: int = Field(
        ...,
        ge=0,
        le=45,
        description="Watch second hand position: 0, 15, 30, or 45"
    )
    is_initial_reading: bool = Field(
        ...,
        description="True if this is a baseline reading (watch perfectly synced)"
    )
    notes: Optional[str] = Field(None, max_length=5000)
    timezone: str = Field(default="UTC", max_length=50)

    @field_validator('watch_seconds_position')
    @classmethod
    def validate_seconds_position(cls, v: int) -> int:
        if v not in [0, 15, 30, 45]:
            raise ValueError('watch_seconds_position must be 0, 15, 30, or 45')
        return v


class MovementAccuracyReadingUpdate(BaseModel):
    """Schema for updating an existing accuracy reading."""
    watch_seconds_position: Optional[int] = Field(
        None,
        ge=0,
        le=45,
        description="Watch second hand position: 0, 15, 30, or 45"
    )
    is_initial_reading: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=5000)
    timezone: Optional[str] = Field(None, max_length=50)

    @field_validator('watch_seconds_position')
    @classmethod
    def validate_seconds_position(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v not in [0, 15, 30, 45]:
            raise ValueError('watch_seconds_position must be 0, 15, 30, or 45')
        return v


# Response schemas
class MovementAccuracyReadingResponse(BaseModel):
    """Schema for returning an accuracy reading."""
    id: UUID
    watch_id: UUID
    reference_time: datetime
    watch_seconds_position: int
    is_initial_reading: bool
    is_atomic_source: bool
    notes: Optional[str]
    timezone: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MovementAccuracyReadingWithDrift(MovementAccuracyReadingResponse):
    """Accuracy reading with calculated drift (for subsequent readings only)."""
    drift_seconds_per_day: Optional[float] = Field(
        None,
        description="Positive = watch running fast, negative = slow, null for initial readings"
    )
    hours_since_initial: Optional[float] = Field(
        None,
        description="Hours elapsed since the paired initial reading"
    )
    paired_initial_id: Optional[UUID] = Field(
        None,
        description="ID of the initial reading this was paired with for drift calculation"
    )


class AccuracyAnalytics(BaseModel):
    """Analytics and statistics for watch movement accuracy."""
    watch_id: UUID
    total_readings: int
    total_initial_readings: int
    total_subsequent_readings: int

    # Current state
    current_drift_spd: Optional[float] = Field(
        None,
        description="Most recent drift calculation in seconds per day"
    )
    last_reading_date: Optional[datetime] = None

    # All-time statistics
    average_drift_spd: Optional[float] = Field(
        None,
        description="Mean drift across all subsequent readings"
    )
    best_accuracy_spd: Optional[float] = Field(
        None,
        description="Closest drift to zero (best performance)"
    )
    worst_accuracy_spd: Optional[float] = Field(
        None,
        description="Furthest drift from zero (worst performance)"
    )

    # Time-based trends
    drift_7d_avg: Optional[float] = Field(
        None,
        description="Average drift over last 7 days"
    )
    drift_30d_avg: Optional[float] = Field(
        None,
        description="Average drift over last 30 days"
    )
    drift_90d_avg: Optional[float] = Field(
        None,
        description="Average drift over last 90 days"
    )

    # Date ranges
    first_reading_date: Optional[datetime] = None
    date_range_days: Optional[int] = Field(
        None,
        description="Days between first and last reading"
    )


class AtomicTimeResponse(BaseModel):
    """Response from atomic time endpoint."""
    current_time: datetime = Field(
        ...,
        description="Current time from WorldTimeAPI or server fallback"
    )
    is_atomic_source: bool = Field(
        ...,
        description="False if WorldTimeAPI failed and server time was used"
    )
    timezone: str = Field(default="UTC")
    unix_timestamp: float = Field(
        ...,
        description="Unix timestamp for precise calculations"
    )
