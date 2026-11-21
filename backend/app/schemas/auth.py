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
    sub: Optional[str] = None


class Token(BaseSchema):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseSchema):
    """Token refresh request"""
    refresh_token: str


class UserLogin(BaseSchema):
    """User login request"""
    email: str
    password: str


class UserRegister(BaseSchema):
    """User registration request"""
    email: str
    password: str = Field(..., min_length=8)
    full_name: str


class PasswordChange(BaseSchema):
    """Password change request"""
    old_password: str
    new_password: str = Field(..., min_length=8)


class PasswordReset(BaseSchema):
    """Password reset request"""
    email: str


class PasswordResetConfirm(BaseSchema):
    """Password reset confirmation"""
    token: str
    new_password: str = Field(..., min_length=8)


class TokenPayloadOld(BaseSchema):
    """JWT token payload (old)"""
    sub: str  # user_id
    exp: int
    type: str
