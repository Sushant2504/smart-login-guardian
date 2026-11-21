"""
Authentication API endpoints
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import (
    Token, TokenRefresh, UserLogin, UserRegister,
    PasswordChange, PasswordReset, PasswordResetConfirm
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.api.deps import get_current_user, get_current_active_user
from app.models import User
from app.core import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account
    """
    auth_service = AuthService(db)

    try:
        user = await auth_service.register_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )
        logger.info("User registered", user_id=str(user.id), email=user.email)
        return user

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password to get access token
    """
    auth_service = AuthService(db)

    user = await auth_service.authenticate_user(
        credentials.email,
        credentials.password
    )

    if not user:
        logger.warning("Failed login attempt", email=credentials.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = await auth_service.create_access_token(
        subject=str(user.id)
    )

    refresh_token = await auth_service.create_refresh_token(
        subject=str(user.id)
    )

    logger.info("User logged in", user_id=str(user.id), email=user.email)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/login/oauth2", response_model=Token)
async def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth2 compatible login endpoint (for Swagger UI)
    """
    auth_service = AuthService(db)

    user = await auth_service.authenticate_user(
        form_data.username,  # OAuth2 uses username field
        form_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = await auth_service.create_access_token(
        subject=str(user.id)
    )

    return Token(
        access_token=access_token,
        refresh_token="",  # OAuth2 endpoint doesn't return refresh token
        token_type="bearer"
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    auth_service = AuthService(db)

    try:
        new_access_token = await auth_service.refresh_access_token(
            token_data.refresh_token
        )

        return Token(
            access_token=new_access_token,
            refresh_token=token_data.refresh_token,
            token_type="bearer"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information
    """
    return current_user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change current user's password
    """
    auth_service = AuthService(db)

    # Verify old password
    is_valid = await auth_service.verify_password(
        password_data.old_password,
        current_user.password_hash
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )

    # Update password
    await auth_service.update_password(
        user_id=current_user.id,
        new_password=password_data.new_password
    )

    logger.info("Password changed", user_id=str(current_user.id))


@router.post("/password-reset", status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(
    reset_data: PasswordReset,
    db: AsyncSession = Depends(get_db)
):
    """
    Request password reset email
    """
    auth_service = AuthService(db)

    # Send reset email (don't reveal if email exists)
    await auth_service.request_password_reset(reset_data.email)

    logger.info("Password reset requested", email=reset_data.email)

    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """
    Confirm password reset with token
    """
    auth_service = AuthService(db)

    try:
        await auth_service.reset_password_with_token(
            token=reset_data.token,
            new_password=reset_data.new_password
        )
        logger.info("Password reset confirmed")

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout current user (invalidate tokens)
    """
    # In a real implementation, you would:
    # 1. Add tokens to a blacklist in Redis
    # 2. Clear any user sessions
    logger.info("User logged out", user_id=str(current_user.id))


@router.post("/api-key/generate", status_code=status.HTTP_201_CREATED)
async def generate_api_key(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a new API key for programmatic access
    """
    auth_service = AuthService(db)

    api_key = await auth_service.generate_api_key(current_user.id)

    logger.info("API key generated", user_id=str(current_user.id))

    return {
        "api_key": api_key,
        "note": "Store this key securely. It won't be shown again."
    }


@router.delete("/api-key/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Revoke current API key
    """
    auth_service = AuthService(db)

    await auth_service.revoke_api_key(current_user.id)

    logger.info("API key revoked", user_id=str(current_user.id))
