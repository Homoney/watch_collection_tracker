from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    default_currency: Optional[str] = Field(None, pattern="^(USD|EUR|GBP|CHF)$")
    theme: Optional[str] = Field(None, pattern="^(light|dark)$")


class UserChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class UserResponse(UserBase):
    id: UUID
    role: str
    default_currency: str
    theme: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class UserAdminUpdate(BaseModel):
    """Admin-only user update schema"""
    role: Optional[str] = Field(None, pattern="^(user|admin)$")


class UserAdminPasswordReset(BaseModel):
    """Admin-only password reset schema"""
    new_password: str = Field(..., min_length=8, max_length=100)
