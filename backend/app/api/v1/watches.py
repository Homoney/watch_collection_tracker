from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import asc, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user
from app.database import get_db
from app.models.collection import Collection
from app.models.reference import Brand, MovementType
from app.models.user import User
from app.models.watch import ConditionEnum, Watch
from app.models.watch_image import ImageSourceEnum, WatchImage
from app.schemas.watch import (
    PaginatedWatchResponse,
    WatchCreate,
    WatchListResponse,
    WatchResponse,
    WatchUpdate,
)
from app.utils.google_images import fetch_watch_images
from app.utils.pdf_export import generate_collection_pdf, generate_watch_pdf
from app.utils.qr_code import generate_watch_qr_code

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
    sort_by: str = Query(
        default="created_at", regex="^(created_at|purchase_date|purchase_price|model)$"
    ),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List watches with advanced filtering, search, sorting, and pagination"""
    # Base query with relationships loaded
    query = (
        db.query(Watch)
        .options(
            joinedload(Watch.brand),
            joinedload(Watch.collection),
            joinedload(Watch.images),
        )
        .filter(Watch.user_id == current_user.id)
    )

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

    # Enhanced search with PostgreSQL full-text search for better performance
    if search:
        # Use full-text search for model field (indexed)
        # Fall back to ILIKE for other fields (less common searches)
        query = query.join(Brand).filter(
            or_(
                func.to_tsvector("english", Watch.model).op("@@")(
                    func.plainto_tsquery("english", search)
                ),
                func.to_tsvector("english", Brand.name).op("@@")(
                    func.plainto_tsquery("english", search)
                ),
                Watch.reference_number.ilike(f"%{search}%"),
                Watch.serial_number.ilike(f"%{search}%"),
                Watch.notes.ilike(f"%{search}%"),
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
        watch_dict["primary_image"] = primary_image
        items.append(WatchListResponse(**watch_dict))

    return PaginatedWatchResponse(items=items, total=total, limit=limit, offset=offset)


@router.post("/", response_model=WatchResponse, status_code=status.HTTP_201_CREATED)
def create_watch(
    watch_data: WatchCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new watch"""
    # Verify brand exists
    brand = db.query(Brand).filter(Brand.id == watch_data.brand_id).first()
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found"
        )

    # Verify movement type exists if provided
    if watch_data.movement_type_id:
        movement_type = (
            db.query(MovementType)
            .filter(MovementType.id == watch_data.movement_type_id)
            .first()
        )
        if not movement_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Movement type not found"
            )

    # Verify collection exists and belongs to user if provided
    if watch_data.collection_id:
        collection = (
            db.query(Collection)
            .filter(
                Collection.id == watch_data.collection_id,
                Collection.user_id == current_user.id,
            )
            .first()
        )
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
            )

    new_watch = Watch(user_id=current_user.id, **watch_data.model_dump())
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
    db: Session = Depends(get_db),
):
    """Get a specific watch with all details"""
    watch = (
        db.query(Watch)
        .options(
            joinedload(Watch.brand),
            joinedload(Watch.movement_type),
            joinedload(Watch.collection),
            joinedload(Watch.images),
        )
        .filter(Watch.id == watch_id, Watch.user_id == current_user.id)
        .first()
    )

    if not watch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Watch not found"
        )

    return WatchResponse.model_validate(watch)


@router.put("/{watch_id}", response_model=WatchResponse)
def update_watch(
    watch_id: UUID,
    watch_data: WatchUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a watch"""
    watch = (
        db.query(Watch)
        .filter(Watch.id == watch_id, Watch.user_id == current_user.id)
        .first()
    )

    if not watch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Watch not found"
        )

    # Verify brand exists if being updated
    if watch_data.brand_id:
        brand = db.query(Brand).filter(Brand.id == watch_data.brand_id).first()
        if not brand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found"
            )

    # Verify movement type exists if being updated
    if watch_data.movement_type_id:
        movement_type = (
            db.query(MovementType)
            .filter(MovementType.id == watch_data.movement_type_id)
            .first()
        )
        if not movement_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Movement type not found"
            )

    # Verify collection exists and belongs to user if being updated
    if watch_data.collection_id:
        collection = (
            db.query(Collection)
            .filter(
                Collection.id == watch_data.collection_id,
                Collection.user_id == current_user.id,
            )
            .first()
        )
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
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
    db: Session = Depends(get_db),
):
    """Delete a watch (cascades to images and service history)"""
    watch = (
        db.query(Watch)
        .filter(Watch.id == watch_id, Watch.user_id == current_user.id)
        .first()
    )

    if not watch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Watch not found"
        )

    db.delete(watch)
    db.commit()

    return None


@router.get("/{watch_id}/qr-code")
def get_watch_qr_code(
    watch_id: UUID,
    base_url: str = Query(
        default="http://localhost:8080",
        description="Base URL for the watch detail page",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate a QR code for a watch that links to its detail page.
    Returns a PNG image that can be downloaded, printed, or displayed.
    """
    # Verify watch exists and belongs to current user
    watch = (
        db.query(Watch)
        .filter(Watch.id == watch_id, Watch.user_id == current_user.id)
        .first()
    )

    if not watch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Watch not found"
        )

    # Generate QR code
    qr_buffer = generate_watch_qr_code(str(watch_id), base_url)

    # Return as streaming response
    return StreamingResponse(
        qr_buffer,
        media_type="image/png",
        headers={"Content-Disposition": f'inline; filename="watch-{watch_id}-qr.png"'},
    )


@router.get("/{watch_id}/export/pdf")
def export_watch_pdf(
    watch_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Export a single watch as a PDF document.
    Includes all watch details, images, service history, and analytics.
    """
    # Load watch with all relationships
    watch = (
        db.query(Watch)
        .options(
            joinedload(Watch.brand),
            joinedload(Watch.movement_type),
            joinedload(Watch.collection),
            joinedload(Watch.images),
            joinedload(Watch.service_history),
        )
        .filter(Watch.id == watch_id, Watch.user_id == current_user.id)
        .first()
    )

    if not watch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Watch not found"
        )

    # Convert to dict for PDF generation
    from app.schemas.watch import WatchResponse

    watch_data = WatchResponse.model_validate(watch).model_dump()

    # Generate PDF
    pdf_buffer = generate_watch_pdf(watch_data)

    # Safe filename
    brand_name = watch.brand.name if watch.brand else "Unknown"
    model = watch.model.replace("/", "-").replace(" ", "_")
    filename = f"{brand_name}_{model}.pdf".replace(" ", "_")

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/pdf")
def export_all_watches_pdf(
    collection_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Export all user watches (or watches in a specific collection) as a PDF document.
    """
    # Build query
    query = (
        db.query(Watch)
        .options(
            joinedload(Watch.brand),
            joinedload(Watch.collection),
            joinedload(Watch.images),
        )
        .filter(Watch.user_id == current_user.id)
    )

    # Filter by collection if specified
    if collection_id:
        query = query.filter(Watch.collection_id == collection_id)

    watches = query.order_by(Watch.brand_id, Watch.model).all()

    if not watches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No watches found"
        )

    # Convert to list of dicts
    from app.schemas.watch import WatchListResponse

    watches_data = [WatchListResponse.model_validate(w).model_dump() for w in watches]

    # Determine collection name
    if collection_id:
        collection = (
            db.query(Collection)
            .filter(
                Collection.id == collection_id, Collection.user_id == current_user.id
            )
            .first()
        )
        collection_name = collection.name if collection else "Watch Collection"
    else:
        collection_name = "My Watch Collection"

    # Generate PDF
    pdf_buffer = generate_collection_pdf(watches_data, collection_name)

    # Safe filename
    filename = f"{collection_name.replace(' ', '_')}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{watch_id}/fetch-images", status_code=status.HTTP_201_CREATED)
def fetch_google_images(
    watch_id: UUID,
    limit: int = Query(default=3, ge=1, le=5, description="Number of images to fetch"),
    offset: int = Query(
        default=0, ge=0, description="Number of images to skip (for pagination)"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Fetch watch images from Google Images.
    Supports fetching multiple batches via offset parameter.
    Uses brand + reference number for more accurate search.
    """
    # Verify watch exists and belongs to user
    watch = (
        db.query(Watch)
        .options(joinedload(Watch.brand), joinedload(Watch.images))
        .filter(Watch.id == watch_id, Watch.user_id == current_user.id)
        .first()
    )

    if not watch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Watch not found"
        )

    # Get brand, model, and reference number
    brand_name = watch.brand.name if watch.brand else "watch"
    model = watch.model
    reference_number = watch.reference_number

    # Get current max sort_order for this watch to append new images
    max_sort_order = (
        db.query(func.max(WatchImage.sort_order))
        .filter(WatchImage.watch_id == watch_id)
        .scalar()
        or -1
    )

    try:
        # Fetch images from Google
        image_metadata_list = fetch_watch_images(
            brand=brand_name,
            model=model,
            watch_id=str(watch_id),
            limit=limit,
            reference_number=reference_number,
            offset=offset,
        )

        if not image_metadata_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No images found for this watch",
            )

        # Create database records for each image
        created_images = []
        for idx, metadata in enumerate(image_metadata_list):
            # Adjust sort_order to append after existing images
            # Only set first image as primary if watch has no images yet
            image = WatchImage(
                watch_id=watch_id,
                file_path=metadata["file_path"],
                file_name=metadata["file_name"],
                file_size=metadata["file_size"],
                mime_type=metadata["mime_type"],
                width=metadata.get("width"),
                height=metadata.get("height"),
                is_primary=(
                    max_sort_order == -1 and idx == 0
                ),  # Only first if no existing images
                sort_order=max_sort_order + 1 + idx,
                source=ImageSourceEnum.GOOGLE_IMAGES,
            )
            db.add(image)
            created_images.append(image)

        db.commit()

        # Refresh to get IDs
        for image in created_images:
            db.refresh(image)

        # Return image schemas
        from app.schemas.watch_image import WatchImageResponse

        return {
            "message": f"Successfully fetched {len(created_images)} images",
            "images": [
                WatchImageResponse.model_validate(img).model_dump()
                for img in created_images
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch images: {str(e)}",
        )
