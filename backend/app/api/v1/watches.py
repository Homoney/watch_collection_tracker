from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, desc, asc
from typing import Optional
from uuid import UUID
from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.watch import Watch, ConditionEnum
from app.models.collection import Collection
from app.models.reference import Brand, MovementType
from app.schemas.watch import (
    WatchCreate,
    WatchUpdate,
    WatchResponse,
    WatchListResponse,
    PaginatedWatchResponse
)

router = APIRouter()


@router.get("/", response_model=PaginatedWatchResponse)
def list_watches(
    collection_id: Optional[UUID] = None,
    brand_id: Optional[UUID] = None,
    movement_type_id: Optional[UUID] = None,
    condition: Optional[ConditionEnum] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    purchase_date_from: Optional[str] = None,
    purchase_date_to: Optional[str] = None,
    sort_by: str = Query(default="created_at", regex="^(created_at|purchase_date|purchase_price|model)$"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List watches with advanced filtering, search, sorting, and pagination"""
    # Base query with relationships loaded
    query = db.query(Watch).options(
        joinedload(Watch.brand),
        joinedload(Watch.collection),
        joinedload(Watch.images)
    ).filter(Watch.user_id == current_user.id)

    # Apply filters
    if collection_id:
        query = query.filter(Watch.collection_id == collection_id)

    if brand_id:
        query = query.filter(Watch.brand_id == brand_id)

    if movement_type_id:
        query = query.filter(Watch.movement_type_id == movement_type_id)

    if condition:
        query = query.filter(Watch.condition == condition)

    # Price range filters
    if min_price is not None:
        query = query.filter(Watch.purchase_price >= min_price)

    if max_price is not None:
        query = query.filter(Watch.purchase_price <= max_price)

    # Market value range filters
    if min_value is not None:
        query = query.filter(Watch.current_market_value >= min_value)

    if max_value is not None:
        query = query.filter(Watch.current_market_value <= max_value)

    # Date range filters
    if purchase_date_from:
        query = query.filter(Watch.purchase_date >= purchase_date_from)

    if purchase_date_to:
        query = query.filter(Watch.purchase_date <= purchase_date_to)

    # Enhanced search across multiple fields including brand name
    if search:
        search_term = f"%{search}%"
        query = query.join(Brand).filter(
            or_(
                Watch.model.ilike(search_term),
                Watch.reference_number.ilike(search_term),
                Watch.serial_number.ilike(search_term),
                Watch.notes.ilike(search_term),
                Brand.name.ilike(search_term)
            )
        )

    # Get total count before pagination
    total = query.count()

    # Apply sorting
    sort_column = getattr(Watch, sort_by)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # Apply pagination
    watches = query.offset(offset).limit(limit).all()

    # Convert to list response format with primary image
    items = []
    for watch in watches:
        watch_dict = WatchListResponse.model_validate(watch).model_dump()
        # Find and attach primary image
        primary_image = next((img for img in watch.images if img.is_primary), None)
        watch_dict['primary_image'] = primary_image
        items.append(WatchListResponse(**watch_dict))

    return PaginatedWatchResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset
    )


@router.post("/", response_model=WatchResponse, status_code=status.HTTP_201_CREATED)
def create_watch(
    watch_data: WatchCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new watch"""
    # Verify brand exists
    brand = db.query(Brand).filter(Brand.id == watch_data.brand_id).first()
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )

    # Verify movement type exists if provided
    if watch_data.movement_type_id:
        movement_type = db.query(MovementType).filter(
            MovementType.id == watch_data.movement_type_id
        ).first()
        if not movement_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movement type not found"
            )

    # Verify collection exists and belongs to user if provided
    if watch_data.collection_id:
        collection = db.query(Collection).filter(
            Collection.id == watch_data.collection_id,
            Collection.user_id == current_user.id
        ).first()
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found"
            )

    new_watch = Watch(
        user_id=current_user.id,
        **watch_data.model_dump()
    )
    db.add(new_watch)
    db.commit()
    db.refresh(new_watch)

    # Load relationships
    db.refresh(new_watch, ["brand", "movement_type", "collection", "images"])

    return WatchResponse.model_validate(new_watch)


@router.get("/{watch_id}", response_model=WatchResponse)
def get_watch(
    watch_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific watch with all details"""
    watch = db.query(Watch).options(
        joinedload(Watch.brand),
        joinedload(Watch.movement_type),
        joinedload(Watch.collection),
        joinedload(Watch.images)
    ).filter(
        Watch.id == watch_id,
        Watch.user_id == current_user.id
    ).first()

    if not watch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watch not found"
        )

    return WatchResponse.model_validate(watch)


@router.put("/{watch_id}", response_model=WatchResponse)
def update_watch(
    watch_id: UUID,
    watch_data: WatchUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a watch"""
    watch = db.query(Watch).filter(
        Watch.id == watch_id,
        Watch.user_id == current_user.id
    ).first()

    if not watch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watch not found"
        )

    # Verify brand exists if being updated
    if watch_data.brand_id:
        brand = db.query(Brand).filter(Brand.id == watch_data.brand_id).first()
        if not brand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brand not found"
            )

    # Verify movement type exists if being updated
    if watch_data.movement_type_id:
        movement_type = db.query(MovementType).filter(
            MovementType.id == watch_data.movement_type_id
        ).first()
        if not movement_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movement type not found"
            )

    # Verify collection exists and belongs to user if being updated
    if watch_data.collection_id:
        collection = db.query(Collection).filter(
            Collection.id == watch_data.collection_id,
            Collection.user_id == current_user.id
        ).first()
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found"
            )

    # Update only provided fields
    update_data = watch_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(watch, key, value)

    db.commit()
    db.refresh(watch)

    # Load relationships
    db.refresh(watch, ["brand", "movement_type", "collection", "images"])

    return WatchResponse.model_validate(watch)


@router.delete("/{watch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watch(
    watch_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a watch (cascades to images and service history)"""
    watch = db.query(Watch).filter(
        Watch.id == watch_id,
        Watch.user_id == current_user.id
    ).first()

    if not watch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watch not found"
        )

    db.delete(watch)
    db.commit()

    return None
