from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.reference import Brand, Complication, MovementType
from app.schemas.reference import (
    BrandResponse,
    ComplicationResponse,
    MovementTypeResponse,
)

router = APIRouter()


@router.get("/brands", response_model=List[BrandResponse])
def list_brands(db: Session = Depends(get_db)):
    """Get all watch brands ordered by sort_order"""
    return db.query(Brand).order_by(Brand.sort_order, Brand.name).all()


@router.get("/movement-types", response_model=List[MovementTypeResponse])
def list_movement_types(db: Session = Depends(get_db)):
    """Get all movement types ordered by sort_order"""
    return (
        db.query(MovementType)
        .order_by(MovementType.sort_order, MovementType.name)
        .all()
    )


@router.get("/complications", response_model=List[ComplicationResponse])
def list_complications(db: Session = Depends(get_db)):
    """Get all complications ordered by sort_order"""
    return (
        db.query(Complication)
        .order_by(Complication.sort_order, Complication.name)
        .all()
    )
