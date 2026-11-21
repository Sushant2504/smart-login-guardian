"""
User service for user management
"""
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserResponse, UserCreate, UserUpdate, UserListResponse


class UserService:
    """User management service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_users(
        self, skip: int, limit: int, role: Optional[str], is_active: Optional[bool]
    ) -> Tuple[List[UserResponse], int]:
        """List users"""
        # TODO: Implement
        return [], 0

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create new user"""
        # TODO: Implement
        raise NotImplementedError()

    async def get_user(self, user_id: UUID) -> Optional[UserResponse]:
        """Get user by ID"""
        # TODO: Implement
        return None

    async def update_user(
        self, user_id: UUID, user_data: UserUpdate
    ) -> Optional[UserResponse]:
        """Update user"""
        # TODO: Implement
        return None

    async def delete_user(self, user_id: UUID) -> bool:
        """Delete user"""
        # TODO: Implement
        return False

    async def deactivate_user(self, user_id: UUID) -> Optional[UserResponse]:
        """Deactivate user"""
        # TODO: Implement
        return None

    async def activate_user(self, user_id: UUID) -> Optional[UserResponse]:
        """Activate user"""
        # TODO: Implement
        return None
