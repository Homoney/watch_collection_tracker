from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def to_naive_utc(value: Optional[datetime]) -> Optional[datetime]:
    """Return a naive UTC datetime.

    The database stores naive UTC times. A client time with an offset (for
    example the web app's "...Z" ISO strings) is converted to UTC and the
    offset dropped, so it can be compared with stored values.
    """
    if value is None or value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


class MarketValueBase(BaseModel):
    """Base schema for market value"""

    value: Decimal = Field(..., ge=0, description="Market value amount")
    currency: str = Field(
        default="USD", max_length=3, description="Three-letter currency code"
    )
    source: str = Field(
        default="manual", description="Source of value: manual, chrono24, api"
    )
    notes: Optional[str] = Field(
        None, description="Optional notes about this valuation"
    )
    recorded_at: datetime = Field(
        default_factory=datetime.utcnow, description="When this value was recorded"
    )


class MarketValueCreate(BaseModel):
    """Schema for creating market value"""

    value: Decimal = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=3)
    source: str = Field(default="manual")
    notes: Optional[str] = None
    recorded_at: Optional[datetime] = None  # Optional, defaults to now if not provided

    @field_validator("recorded_at")
    @classmethod
    def _recorded_at_naive_utc(cls, value: Optional[datetime]) -> Optional[datetime]:
        return to_naive_utc(value)


class MarketValueUpdate(BaseModel):
    """Schema for updating market value"""

    value: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    source: Optional[str] = None
    notes: Optional[str] = None
    recorded_at: Optional[datetime] = None

    @field_validator("recorded_at")
    @classmethod
    def _recorded_at_naive_utc(cls, value: Optional[datetime]) -> Optional[datetime]:
        return to_naive_utc(value)


class MarketValueResponse(BaseModel):
    """Schema for market value response"""

    id: UUID
    watch_id: UUID
    value: Decimal
    currency: str
    source: str
    notes: Optional[str]
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WatchAnalytics(BaseModel):
    """Analytics for a single watch"""

    watch_id: UUID
    current_value: Optional[Decimal]
    current_currency: str
    purchase_price: Optional[Decimal]
    purchase_currency: str
    total_return: Optional[
        Decimal
    ]  # Current value - purchase price (in purchase currency)
    roi_percentage: Optional[float]  # Return on investment as percentage
    annualized_return: Optional[float]  # Annualized ROI percentage
    value_change_30d: Optional[Decimal]  # Change in last 30 days
    value_change_90d: Optional[Decimal]  # Change in last 90 days
    value_change_1y: Optional[Decimal]  # Change in last year
    total_valuations: int  # Number of recorded valuations
    first_valuation_date: Optional[datetime]
    latest_valuation_date: Optional[datetime]


class CollectionAnalytics(BaseModel):
    """Analytics for entire collection"""

    total_watches: int
    total_current_value: Decimal
    total_purchase_price: Decimal
    currency: str  # Base currency for totals
    total_return: Decimal
    average_roi: float  # Average ROI across all watches
    top_performers: list[dict]  # Top 5 watches by ROI
    worst_performers: list[dict]  # Bottom 5 watches by ROI
    value_by_brand: dict[str, Decimal]  # Value breakdown by brand
    value_by_collection: dict[str, Decimal]  # Value breakdown by collection
    total_valuations: int  # Total number of valuations recorded
