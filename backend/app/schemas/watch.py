from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.watch import ConditionEnum
from app.schemas.watch_image import WatchImageResponse


class WatchBase(BaseModel):
    brand_id: UUID
    model: str = Field(..., min_length=1, max_length=200)
    reference_number: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    collection_id: Optional[UUID] = None
    movement_type_id: Optional[UUID] = None

    # Purchase information
    purchase_date: Optional[datetime] = None
    retailer: Optional[str] = Field(None, max_length=200)
    purchase_price: Optional[Decimal] = Field(None, ge=0)
    purchase_currency: str = Field(default="USD", max_length=3)

    # Specifications
    case_diameter: Optional[Decimal] = Field(None, ge=0, le=999.99)
    case_thickness: Optional[Decimal] = Field(None, ge=0, le=999.99)
    lug_width: Optional[Decimal] = Field(None, ge=0, le=999.99)
    water_resistance: Optional[int] = Field(None, ge=0)
    power_reserve: Optional[int] = Field(None, ge=0)

    # Complications
    complications: List[str] = Field(default_factory=list)

    # Condition
    condition: Optional[ConditionEnum] = None

    # Market value
    current_market_value: Optional[Decimal] = Field(None, ge=0)
    current_market_currency: str = Field(default="USD", max_length=3)
    last_value_update: Optional[datetime] = None

    # Notes
    notes: Optional[str] = None


class WatchCreate(WatchBase):
    pass


class WatchUpdate(BaseModel):
    brand_id: Optional[UUID] = None
    model: Optional[str] = Field(None, min_length=1, max_length=200)
    reference_number: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    collection_id: Optional[UUID] = None
    movement_type_id: Optional[UUID] = None

    # Purchase information
    purchase_date: Optional[datetime] = None
    retailer: Optional[str] = Field(None, max_length=200)
    purchase_price: Optional[Decimal] = Field(None, ge=0)
    purchase_currency: Optional[str] = Field(None, max_length=3)

    # Specifications
    case_diameter: Optional[Decimal] = Field(None, ge=0, le=999.99)
    case_thickness: Optional[Decimal] = Field(None, ge=0, le=999.99)
    lug_width: Optional[Decimal] = Field(None, ge=0, le=999.99)
    water_resistance: Optional[int] = Field(None, ge=0)
    power_reserve: Optional[int] = Field(None, ge=0)

    # Complications
    complications: Optional[List[str]] = None

    # Condition
    condition: Optional[ConditionEnum] = None

    # Market value
    current_market_value: Optional[Decimal] = Field(None, ge=0)
    current_market_currency: Optional[str] = Field(None, max_length=3)
    last_value_update: Optional[datetime] = None

    # Notes
    notes: Optional[str] = None


class BrandInWatch(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True


class MovementTypeInWatch(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True


class CollectionInWatch(BaseModel):
    id: UUID
    name: str
    color: str

    class Config:
        from_attributes = True


class WatchResponse(WatchBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    brand: Optional[BrandInWatch] = None
    movement_type: Optional[MovementTypeInWatch] = None
    collection: Optional[CollectionInWatch] = None
    images: List[WatchImageResponse] = []

    class Config:
        from_attributes = True


class WatchListResponse(BaseModel):
    id: UUID
    brand_id: UUID
    model: str
    reference_number: Optional[str]
    collection_id: Optional[UUID]
    purchase_date: Optional[datetime]
    purchase_price: Optional[Decimal]
    purchase_currency: str
    condition: Optional[ConditionEnum]
    created_at: datetime
    brand: Optional[BrandInWatch] = None
    collection: Optional[CollectionInWatch] = None
    primary_image: Optional[WatchImageResponse] = None

    class Config:
        from_attributes = True


class PaginatedWatchResponse(BaseModel):
    items: List[WatchListResponse]
    total: int
    limit: int
    offset: int
