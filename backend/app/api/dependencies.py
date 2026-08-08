"""
FastAPI dependencies for dependency injection.

Provides:
- get_current_user: Validates JWT and returns the authenticated User.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.user_repository import UserRepository

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency that extracts and validates the JWT from the Authorization header.

    Returns:
        The authenticated User ORM object.

    Raises:
        HTTPException 401: If token is missing, invalid, or expired.
        HTTPException 401: If the user in the token no longer exists.
    """
    _unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "success": False,
            "error": {
                "code": "UNAUTHORIZED",
                "message": "Authentication required.",
            },
        },
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise _unauthorized

    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise _unauthorized

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise _unauthorized

    repo = UserRepository(session)
    import uuid
    try:
        user = await repo.get_by_id(uuid.UUID(user_id))
    except (ValueError, Exception):
        raise _unauthorized

    if not user:
        raise _unauthorized

    return user
