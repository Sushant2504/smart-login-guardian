"""
API route dependencies for authentication and authorization
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from redis import Redis

from app.core import get_logger, AppException
from app.config import settings
from app.database import get_db
from app.models import User
from app.repositories import UserRepository
from app.core.cache import get_redis

logger = get_logger(__name__)

# Security schemes
security = HTTPBearer()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class UnauthorizedException(AppException):
    """Raised when user is not authorized"""
    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(AppException):
    """Raised when user lacks permissions"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to get current authenticated user from JWT token
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException("Invalid authentication credentials")

    except JWTError as e:
        logger.warning("JWT decode error", error=str(e))
        raise UnauthorizedException("Invalid authentication credentials")

    # Get user from database
    user_repo = UserRepository(db)
    user = await user_repo.get(user_id)

    if user is None:
        raise UnauthorizedException("User not found")

    if not user.is_active:
        raise ForbiddenException("User account is disabled")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to ensure user is active
    """
    if not current_user.is_active:
        raise ForbiddenException("Inactive user")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to ensure user has admin role
    """
    if current_user.role != "admin":
        raise ForbiddenException("Admin access required")
    return current_user


async def get_current_analyst_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to ensure user has analyst or admin role
    """
    if current_user.role not in ["admin", "analyst"]:
        raise ForbiddenException("Analyst access required")
    return current_user


async def verify_api_key(
    api_key: Optional[str] = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to verify API key authentication
    """
    if not api_key:
        raise UnauthorizedException("API key required")

    # In production, store hashed API keys in database
    # For now, verify against user's api_key field
    user_repo = UserRepository(db)
    user = await user_repo.get_by_api_key(api_key)

    if not user:
        raise UnauthorizedException("Invalid API key")

    if not user.is_active:
        raise ForbiddenException("User account is disabled")

    return user


async def get_redis_client() -> Generator[Redis, None, None]:
    """
    Dependency to get Redis client
    """
    redis = get_redis()
    try:
        yield redis
    finally:
        pass  # Connection pool handles cleanup


class RateLimiter:
    """
    Rate limiting dependency
    """
    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period

    async def __call__(
        self,
        request,
        redis: Redis = Depends(get_redis_client),
        current_user: Optional[User] = Depends(get_current_user)
    ):
        """Check rate limit for user or IP"""
        import time

        # Use user ID if authenticated, otherwise IP address
        identifier = current_user.id if current_user else request.client.host
        key = f"rate_limit:{identifier}:{request.url.path}"

        # Get current count
        current = redis.get(key)

        if current is None:
            # First request in period
            redis.setex(key, self.period, 1)
        else:
            current = int(current)
            if current >= self.calls:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again in {self.period} seconds."
                )
            redis.incr(key)


def require_permission(permission: str):
    """
    Dependency factory to check user permissions
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        # Simple role-based permissions
        permissions_map = {
            "admin": ["*"],  # Admin has all permissions
            "analyst": [
                "events:read", "events:write",
                "alerts:read", "alerts:manage",
                "reports:read"
            ],
            "viewer": ["events:read", "alerts:read", "reports:read"],
            "api": ["events:write"]
        }

        user_permissions = permissions_map.get(current_user.role, [])

        if "*" not in user_permissions and permission not in user_permissions:
            raise ForbiddenException(
                f"Permission '{permission}' required"
            )

        return current_user

    return permission_checker
