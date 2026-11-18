from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BrandResponse(BaseModel):
    id: UUID
    name: str
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class MovementTypeResponse(BaseModel):
    id: UUID
    name: str
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class ComplicationResponse(BaseModel):
    id: UUID
    name: str
    sort_order: int

    model_config = ConfigDict(from_attributes=True)
