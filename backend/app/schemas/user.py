"""
User schemas
"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import EmailStr, Field

from app.schemas.common import BaseSchema
from app.models.user import UserRole


class UserBase(BaseSchema):
    """Base user schema"""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.VIEWER


class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseSchema):
    """Schema for updating a user"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """User schema with database fields"""
    id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime


class User(UserInDB):
    """Public user schema"""
    pass


class UserWithPassword(UserInDB):
    """User schema with password hash (internal use)"""
    password_hash: str


class UserResponse(User):
    """User API response"""
    pass


class UserListResponse(BaseSchema):
    """User list response"""
    users: List[User]
    total: int
    skip: int
    limit: int
