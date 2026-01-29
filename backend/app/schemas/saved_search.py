from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SavedSearchBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    filters: dict


class SavedSearchCreate(SavedSearchBase):
    pass


class SavedSearchUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    filters: Optional[dict] = None


class SavedSearchResponse(SavedSearchBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
