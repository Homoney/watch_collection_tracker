from uuid import UUID

from pydantic import BaseModel


class BrandResponse(BaseModel):
    id: UUID
    name: str
    sort_order: int

    class Config:
        from_attributes = True


class MovementTypeResponse(BaseModel):
    id: UUID
    name: str
    sort_order: int

    class Config:
        from_attributes = True


class ComplicationResponse(BaseModel):
    id: UUID
    name: str
    sort_order: int

    class Config:
        from_attributes = True
