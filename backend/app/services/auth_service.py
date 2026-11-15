"""
Authentication service
"""
from typing import Optional
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.auth import TokenResponse
from app.schemas.user import User as UserSchema
from app.repositories.user_repository import UserRepository
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import UnauthorizedException, ConflictException
from app.config import settings


class AuthService:
    """Authentication service"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def login(self, email: str, password: str) -> TokenResponse:
        """
        Authenticate user and return tokens
        """
        # Get user by email
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise UnauthorizedException("Invalid email or password")

        # Verify password
        if not verify_password(password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")

        # Check if user is active
        if not user.is_active:
            raise UnauthorizedException("User account is inactive")

        # Create tokens
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserSchema.model_validate(user)
        )

    async def register(self, email: str, password: str, full_name: str) -> User:
        """
        Register a new user
        """
        # Check if user already exists
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise ConflictException("User with this email already exists")

        # Hash password
        password_hash = get_password_hash(password)

        # Create user
        user = await self.user_repo.create(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            is_active=True,
            is_superuser=False
        )

        return user

    async def refresh_access_token(self, refresh_token: str) -> str:
        """
        Generate new access token from refresh token
        """
        # Decode refresh token
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid refresh token")

        # Get user
        user_id = payload.get("sub")
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedException("User not found or inactive")

        # Create new access token
        access_token = create_access_token({"sub": str(user.id)})
        return access_token

    async def get_current_user(self, token: str) -> Optional[User]:
        """
        Get current user from access token
        """
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            return None

        user_id = payload.get("sub")
        return await self.user_repo.get_by_id(user_id)
