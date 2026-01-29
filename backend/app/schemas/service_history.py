from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, computed_field


class ServiceHistoryBase(BaseModel):
    """Base schema for service history"""

    service_date: datetime
    provider: str = Field(..., min_length=1, max_length=200)
    service_type: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    cost: Optional[Decimal] = Field(None, ge=0)
    cost_currency: str = Field(default="USD", max_length=3)
    next_service_due: Optional[datetime] = None


class ServiceHistoryCreate(ServiceHistoryBase):
    """Schema for creating service history"""

    pass


class ServiceHistoryUpdate(BaseModel):
    """Schema for updating service history"""

    service_date: Optional[datetime] = None
    provider: Optional[str] = Field(None, min_length=1, max_length=200)
    service_type: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    cost: Optional[Decimal] = Field(None, ge=0)
    cost_currency: Optional[str] = Field(None, max_length=3)
    next_service_due: Optional[datetime] = None


class ServiceDocumentResponse(BaseModel):
    """Schema for service document response"""

    id: UUID
    service_history_id: UUID
    file_path: str
    file_name: str
    file_size: int
    mime_type: str
    created_at: datetime

    @computed_field
    @property
    def url(self) -> str:
        """Generate URL for accessing the document"""
        return f"/uploads/service-docs/{self.file_path}"

    class Config:
        from_attributes = True


class ServiceHistoryResponse(ServiceHistoryBase):
    """Schema for service history response"""

    id: UUID
    watch_id: UUID
    created_at: datetime
    updated_at: datetime
    documents: List[ServiceDocumentResponse] = []

    class Config:
        from_attributes = True
