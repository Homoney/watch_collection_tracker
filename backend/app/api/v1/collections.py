from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.collection import Collection
from app.models.user import User
from app.models.watch import Watch
from app.schemas.collection import (CollectionCreate, CollectionResponse,
                                    CollectionUpdate)

router = APIRouter()


@router.get("/", response_model=List[CollectionResponse])
def list_collections(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get all collections for the current user"""
    collections = (
        db.query(Collection, func.count(Watch.id).label("watch_count"))
        .outerjoin(Watch, Watch.collection_id == Collection.id)
        .filter(Collection.user_id == current_user.id)
        .group_by(Collection.id)
        .order_by(Collection.is_default.desc(), Collection.created_at)
        .all()
    )

    result = []
    for collection, watch_count in collections:
        collection_dict = {
            "id": collection.id,
            "user_id": collection.user_id,
            "name": collection.name,
            "description": collection.description,
            "color": collection.color,
            "is_default": collection.is_default,
            "created_at": collection.created_at,
            "updated_at": collection.updated_at,
            "watch_count": watch_count,
        }
        result.append(CollectionResponse(**collection_dict))

    return result


@router.post(
    "/", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED
)
def create_collection(
    collection_data: CollectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new collection"""
    # If this is set as default, unset all other defaults for this user
    if collection_data.is_default:
        db.query(Collection).filter(
            Collection.user_id == current_user.id, Collection.is_default == True
        ).update({"is_default": False})

    new_collection = Collection(user_id=current_user.id, **collection_data.model_dump())
    db.add(new_collection)
    db.commit()
    db.refresh(new_collection)

    # Get watch count (will be 0 for new collection)
    return CollectionResponse(
        **{
            "id": new_collection.id,
            "user_id": new_collection.user_id,
            "name": new_collection.name,
            "description": new_collection.description,
            "color": new_collection.color,
            "is_default": new_collection.is_default,
            "created_at": new_collection.created_at,
            "updated_at": new_collection.updated_at,
            "watch_count": 0,
        }
    )


@router.get("/{collection_id}", response_model=CollectionResponse)
def get_collection(
    collection_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific collection with watch count"""
    collection = (
        db.query(Collection)
        .filter(Collection.id == collection_id, Collection.user_id == current_user.id)
        .first()
    )

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
        )

    # Get watch count
    watch_count = (
        db.query(func.count(Watch.id))
        .filter(Watch.collection_id == collection_id)
        .scalar()
    )

    return CollectionResponse(
        **{
            "id": collection.id,
            "user_id": collection.user_id,
            "name": collection.name,
            "description": collection.description,
            "color": collection.color,
            "is_default": collection.is_default,
            "created_at": collection.created_at,
            "updated_at": collection.updated_at,
            "watch_count": watch_count or 0,
        }
    )


@router.put("/{collection_id}", response_model=CollectionResponse)
def update_collection(
    collection_id: UUID,
    collection_data: CollectionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a collection"""
    collection = (
        db.query(Collection)
        .filter(Collection.id == collection_id, Collection.user_id == current_user.id)
        .first()
    )

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
        )

    # If setting this as default, unset all other defaults for this user
    if collection_data.is_default and not collection.is_default:
        db.query(Collection).filter(
            Collection.user_id == current_user.id,
            Collection.id != collection_id,
            Collection.is_default == True,
        ).update({"is_default": False})

    # Update only provided fields
    update_data = collection_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(collection, key, value)

    db.commit()
    db.refresh(collection)

    # Get watch count
    watch_count = (
        db.query(func.count(Watch.id))
        .filter(Watch.collection_id == collection_id)
        .scalar()
    )

    return CollectionResponse(
        **{
            "id": collection.id,
            "user_id": collection.user_id,
            "name": collection.name,
            "description": collection.description,
            "color": collection.color,
            "is_default": collection.is_default,
            "created_at": collection.created_at,
            "updated_at": collection.updated_at,
            "watch_count": watch_count or 0,
        }
    )


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(
    collection_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a collection (sets watches' collection_id to NULL)"""
    collection = (
        db.query(Collection)
        .filter(Collection.id == collection_id, Collection.user_id == current_user.id)
        .first()
    )

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
        )

    # Set all watches in this collection to have NULL collection_id
    db.query(Watch).filter(Watch.collection_id == collection_id).update(
        {"collection_id": None}
    )

    # Delete the collection
    db.delete(collection)
    db.commit()

    return None
