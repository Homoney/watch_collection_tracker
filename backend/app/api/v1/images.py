from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.watch import Watch
from app.models.watch_image import ImageSourceEnum, WatchImage
from app.schemas.watch_image import UpdateImageRequest, WatchImageResponse
from app.utils.file_upload import delete_file, save_uploaded_file, validate_image_file

router = APIRouter()


def verify_watch_ownership(watch_id: UUID, current_user: User, db: Session) -> Watch:
    """
    Verify that the watch exists and belongs to the current user.

    Args:
        watch_id: The watch UUID
        current_user: The authenticated user
        db: Database session

    Returns:
        The Watch object if found and owned by user

    Raises:
        HTTPException: If watch not found or not owned by user
    """
    watch = (
        db.query(Watch)
        .filter(Watch.id == watch_id, Watch.user_id == current_user.id)
        .first()
    )

    if not watch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Watch not found"
        )

    return watch


@router.post(
    "/{watch_id}/images",
    response_model=WatchImageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_image(
    watch_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload an image for a watch.

    - Validates file type and size
    - Saves file to storage
    - Creates database record
    - Returns image metadata with URL
    """
    # Verify watch ownership
    watch = verify_watch_ownership(watch_id, current_user, db)

    # Validate the uploaded file
    is_valid, error_msg = validate_image_file(file)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if file_size > settings.MAX_UPLOAD_SIZE:
        max_size_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {max_size_mb}MB",
        )

    # Save file to disk
    try:
        file_metadata = save_uploaded_file(file, watch_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}",
        )

    # Check if this is the first image for this watch
    existing_images_count = (
        db.query(WatchImage).filter(WatchImage.watch_id == watch_id).count()
    )

    is_primary = existing_images_count == 0  # First image is primary by default

    # Create database record
    watch_image = WatchImage(
        watch_id=watch_id,
        file_path=file_metadata["file_path"],
        file_name=file_metadata["file_name"],
        file_size=file_metadata["file_size"],
        mime_type=file_metadata["mime_type"],
        width=file_metadata["width"],
        height=file_metadata["height"],
        is_primary=is_primary,
        sort_order=existing_images_count,
        source=ImageSourceEnum.USER_UPLOAD,
    )

    db.add(watch_image)
    db.commit()
    db.refresh(watch_image)

    return watch_image


@router.get("/{watch_id}/images", response_model=List[WatchImageResponse])
def list_images(
    watch_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all images for a watch, ordered by sort_order.
    """
    # Verify watch ownership
    watch = verify_watch_ownership(watch_id, current_user, db)

    # Query images
    images = (
        db.query(WatchImage)
        .filter(WatchImage.watch_id == watch_id)
        .order_by(WatchImage.sort_order)
        .all()
    )

    return images


@router.patch("/{watch_id}/images/{image_id}", response_model=WatchImageResponse)
def update_image(
    watch_id: UUID,
    image_id: UUID,
    update_data: UpdateImageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update image metadata (set as primary or change sort order).

    - If setting is_primary=True, unsets all other images for this watch
    """
    # Verify watch ownership
    watch = verify_watch_ownership(watch_id, current_user, db)

    # Find the image
    image = (
        db.query(WatchImage)
        .filter(WatchImage.id == image_id, WatchImage.watch_id == watch_id)
        .first()
    )

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )

    # Handle primary image logic
    if update_data.is_primary is True:
        # Unset all other images as primary
        db.query(WatchImage).filter(
            WatchImage.watch_id == watch_id, WatchImage.id != image_id
        ).update({"is_primary": False})

        image.is_primary = True

    elif update_data.is_primary is False:
        # Prevent unsetting primary if this is the only image
        total_images = (
            db.query(WatchImage).filter(WatchImage.watch_id == watch_id).count()
        )

        if total_images > 1:
            image.is_primary = False
            # Auto-promote the next image by sort_order
            next_image = (
                db.query(WatchImage)
                .filter(WatchImage.watch_id == watch_id, WatchImage.id != image_id)
                .order_by(WatchImage.sort_order)
                .first()
            )

            if next_image:
                next_image.is_primary = True

    # Update sort order
    if update_data.sort_order is not None:
        image.sort_order = update_data.sort_order

    db.commit()
    db.refresh(image)

    return image


@router.delete("/{watch_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(
    watch_id: UUID,
    image_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete an image (both database record and physical file).

    - If deleting the primary image, auto-promotes the next image by sort_order
    """
    # Verify watch ownership
    watch = verify_watch_ownership(watch_id, current_user, db)

    # Find the image
    image = (
        db.query(WatchImage)
        .filter(WatchImage.id == image_id, WatchImage.watch_id == watch_id)
        .first()
    )

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )

    was_primary = image.is_primary
    file_path = image.file_path

    # Delete database record
    db.delete(image)
    db.commit()

    # Delete physical file
    delete_file(file_path)

    # If this was the primary image, promote the next one
    if was_primary:
        next_image = (
            db.query(WatchImage)
            .filter(WatchImage.watch_id == watch_id)
            .order_by(WatchImage.sort_order)
            .first()
        )

        if next_image:
            next_image.is_primary = True
            db.commit()

    return None
