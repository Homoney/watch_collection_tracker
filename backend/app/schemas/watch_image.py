from pydantic import BaseModel, Field, computed_field
from uuid import UUID
from datetime import datetime
from typing import Optional


class WatchImageResponse(BaseModel):
    """Response schema for watch images"""
    id: UUID
    watch_id: UUID
    file_path: str
    file_name: str
    file_size: int
    mime_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    is_primary: bool
    sort_order: int
    source: str
    created_at: datetime

    @computed_field
    @property
    def url(self) -> str:
        """Generate the public URL for the image"""
        return f"/uploads/{self.file_path}"

    class Config:
        from_attributes = True


class UpdateImageRequest(BaseModel):
    """Request schema for updating image metadata"""
    is_primary: Optional[bool] = Field(None, description="Set this image as primary")
    sort_order: Optional[int] = Field(None, description="Display order of the image")
