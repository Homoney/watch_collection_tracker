from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.schemas.user import UserResponse, UserAdminUpdate, UserAdminPasswordReset
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from app.core.deps import get_current_admin
from app.utils.logging import log_security_event

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """List all users (admin only)"""
    users = db.query(User).order_by(User.created_at.desc()).all()

    log_security_event(
        "admin_list_users",
        user_id=str(current_admin.id),
        details={"user_count": len(users)}
    )

    return users


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Get a specific user by ID (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user_role(
    user_id: UUID,
    user_data: UserAdminUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Update user role (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent admin from demoting themselves
    if user.id == current_admin.id and user_data.role == "user":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote yourself from admin"
        )

    old_role = user.role.value

    if user_data.role is not None:
        user.role = UserRole.admin if user_data.role == "admin" else UserRole.user

    db.commit()
    db.refresh(user)

    log_security_event(
        "admin_update_user_role",
        user_id=str(current_admin.id),
        details={
            "target_user_id": str(user.id),
            "old_role": old_role,
            "new_role": user.role.value
        }
    )

    return user


@router.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_user_password(
    user_id: UUID,
    password_data: UserAdminPasswordReset,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Reset a user's password (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()

    log_security_event(
        "admin_reset_user_password",
        user_id=str(current_admin.id),
        details={"target_user_id": str(user.id)}
    )

    return None


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Delete a user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent admin from deleting themselves
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )

    log_security_event(
        "admin_delete_user",
        user_id=str(current_admin.id),
        details={
            "target_user_id": str(user.id),
            "target_email": user.email
        }
    )

    db.delete(user)
    db.commit()

    return None
