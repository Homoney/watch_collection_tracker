"""Reference-number look-up and its admin setting (the WatchBase API key)."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin, get_current_user
from app.database import get_db
from app.models.reference import Brand
from app.models.user import User
from app.spec_lookup import keys, service
from app.utils.logging import log_security_event

router = APIRouter()
settings_router = APIRouter()


@router.get("")
def look_up_reference(
    reference: str = Query(..., min_length=2, max_length=100),
    brand_id: Optional[UUID] = None,
    caliber: Optional[str] = Query(None, max_length=100),
    watchbase_id: Optional[int] = Query(None, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Find specs for a reference number. Always 200; see `status`.

    Fills nothing by itself: the web app puts the answer into the form's
    empty fields. Pass `watchbase_id` after the user picked one of `choices`.
    """
    brand = None
    if brand_id:
        row = db.query(Brand).filter(Brand.id == brand_id).first()
        brand = row.name if row else None
    return service.lookup(
        db, reference, brand=brand, caliber=caliber, watchbase_id=watchbase_id
    )


class KeyStatus(BaseModel):
    configured: bool
    from_environment: bool


class KeyUpdate(BaseModel):
    api_key: str = Field(..., min_length=8, max_length=200)

    @field_validator("api_key")
    @classmethod
    def no_spaces(cls, v: str) -> str:
        v = v.strip()
        if not v or any(ch.isspace() for ch in v):
            raise ValueError("The key cannot contain spaces")
        return v


@settings_router.get("/watchbase-key", response_model=KeyStatus)
def watchbase_key_status(current_admin: User = Depends(get_current_admin)):
    """Whether a WatchBase key is set. The key itself is never returned."""
    return keys.key_status()


@settings_router.put("/watchbase-key", response_model=KeyStatus)
def set_watchbase_key(
    body: KeyUpdate, current_admin: User = Depends(get_current_admin)
):
    keys.save_watchbase_key(body.api_key)
    log_security_event("watchbase_key_set", user_id=str(current_admin.id))
    return keys.key_status()


@settings_router.delete("/watchbase-key", response_model=KeyStatus)
def clear_watchbase_key(current_admin: User = Depends(get_current_admin)):
    keys.clear_watchbase_key()
    log_security_event("watchbase_key_cleared", user_id=str(current_admin.id))
    return keys.key_status()
