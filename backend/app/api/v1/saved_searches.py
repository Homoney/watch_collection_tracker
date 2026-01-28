from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.saved_search import SavedSearch
from app.schemas.saved_search import (
    SavedSearchCreate,
    SavedSearchUpdate,
    SavedSearchResponse
)

router = APIRouter()


@router.get("/", response_model=List[SavedSearchResponse])
def list_saved_searches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all saved searches for the current user"""
    searches = db.query(SavedSearch).filter(
        SavedSearch.user_id == current_user.id
    ).order_by(SavedSearch.name).all()

    return searches


@router.post("/", response_model=SavedSearchResponse, status_code=201)
def create_saved_search(
    search_data: SavedSearchCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new saved search"""
    # Check if name already exists for this user
    existing = db.query(SavedSearch).filter(
        SavedSearch.user_id == current_user.id,
        SavedSearch.name == search_data.name
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="A saved search with this name already exists"
        )

    saved_search = SavedSearch(
        user_id=current_user.id,
        name=search_data.name,
        filters=search_data.filters
    )

    db.add(saved_search)
    db.commit()
    db.refresh(saved_search)

    return saved_search


@router.get("/{search_id}", response_model=SavedSearchResponse)
def get_saved_search(
    search_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific saved search"""
    saved_search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user.id
    ).first()

    if not saved_search:
        raise HTTPException(status_code=404, detail="Saved search not found")

    return saved_search


@router.put("/{search_id}", response_model=SavedSearchResponse)
def update_saved_search(
    search_id: UUID,
    search_data: SavedSearchUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a saved search"""
    saved_search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user.id
    ).first()

    if not saved_search:
        raise HTTPException(status_code=404, detail="Saved search not found")

    # Check if new name conflicts with existing
    if search_data.name and search_data.name != saved_search.name:
        existing = db.query(SavedSearch).filter(
            SavedSearch.user_id == current_user.id,
            SavedSearch.name == search_data.name
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail="A saved search with this name already exists"
            )

    # Update fields
    if search_data.name is not None:
        saved_search.name = search_data.name
    if search_data.filters is not None:
        saved_search.filters = search_data.filters

    db.commit()
    db.refresh(saved_search)

    return saved_search


@router.delete("/{search_id}", status_code=204)
def delete_saved_search(
    search_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a saved search"""
    saved_search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user.id
    ).first()

    if not saved_search:
        raise HTTPException(status_code=404, detail="Saved search not found")

    db.delete(saved_search)
    db.commit()

    return None
