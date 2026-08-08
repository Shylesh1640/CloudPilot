"""Authentication routes: register, login, me."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=201,
    summary="Register a new user",
    description="Create a new CloudPilot user account. Password is securely hashed before storage.",
    responses={
        201: {"description": "User created successfully"},
        409: {"description": "Email address is already registered"},
        422: {"description": "Validation error"},
    },
)
async def register(
    data: UserCreate,
    session: AsyncSession = Depends(get_db),
) -> UserRead:
    service = AuthService(session)
    return await service.register(data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and obtain JWT",
    description="Authenticate with email and password. Returns a JWT access token for use in the Authorization header.",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
    },
)
async def login(
    data: LoginRequest,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(session)
    return await service.login(data)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user",
    description="Return the profile of the currently authenticated user. Requires a valid JWT in the Authorization header.",
    responses={
        200: {"description": "Current user profile"},
        401: {"description": "Not authenticated"},
    },
)
async def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)
