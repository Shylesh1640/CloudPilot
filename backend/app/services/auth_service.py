"""
Authentication service — registration, login, and JWT issuance.

Route → AuthService → UserRepository → SQLAlchemy
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserRead


class AuthService:
    """Handles user registration, login, and JWT token management."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = UserRepository(session)

    async def register(self, data: UserCreate) -> UserRead:
        """
        Register a new user.

        Raises:
            HTTPException 409: If email is already registered.
        """
        existing = await self._repo.get_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "error": {
                        "code": "EMAIL_ALREADY_EXISTS",
                        "message": "An account with this email already exists.",
                    },
                },
            )
        user = await self._repo.create(
            name=data.name,
            email=data.email,
            password_hash=hash_password(data.password),
        )
        return UserRead.model_validate(user)

    async def login(self, data: LoginRequest) -> TokenResponse:
        """
        Authenticate a user and return a JWT access token.

        Raises:
            HTTPException 401: If credentials are invalid.
        """
        user = await self._repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Invalid email or password.",
                    },
                },
            )
        token = create_access_token(subject=str(user.id))
        return TokenResponse(access_token=token)

    async def get_current_user(self, user: User) -> UserRead:
        """Return the authenticated user's public profile."""
        return UserRead.model_validate(user)
