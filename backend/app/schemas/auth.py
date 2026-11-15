"""
Authentication schemas
"""
from pydantic import EmailStr, Field

from app.schemas.common import BaseSchema
from app.schemas.user import User


class LoginRequest(BaseSchema):
    """Login request"""
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseSchema):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: User


class RefreshTokenRequest(BaseSchema):
    """Refresh token request"""
    refresh_token: str


class TokenPayload(BaseSchema):
    """JWT token payload"""
    sub: str  # user_id
    exp: int
    type: str
