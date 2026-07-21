"""
AutoWorth AI — FastAPI Dependencies

Reusable dependency functions injected into route handlers via Depends().

Provides:
  - get_db: Yields a scoped AsyncSession
  - get_current_user: Decodes Bearer JWT, returns User ORM object
  - get_current_active_user: Also checks is_active
  - require_verified: Also checks is_verified
  - require_admin: Also checks role == "admin"
"""

import uuid
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import decode_token
from app.models.user import User
from app.repositories.user_repository import UserRepository

# ──────────────────────────────────────────────
# DB Session Dependency
# ──────────────────────────────────────────────
bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncSession:  # type: ignore[override]
    """Yield a scoped async database session."""
    async with AsyncSessionLocal() as session:
        yield session


# ──────────────────────────────────────────────
# Current User Extraction
# ──────────────────────────────────────────────
async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Security(bearer_scheme),
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Decode the Bearer JWT and return the corresponding User ORM object.

    Raises:
        401 if token is missing, malformed, expired, or user does not exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "success": False,
            "message": "Authentication required. Please provide a valid access token.",
            "error_code": "NOT_AUTHENTICATED",
        },
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    try:
        payload = decode_token(credentials.credentials)
        user_id_str: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")

        if user_id_str is None or token_type != "access":
            raise credentials_exception

        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id_with_role(user_id)

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Returns the current user only if their account is active.

    Raises:
        403 if the account is deactivated.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "Your account has been deactivated. Please contact support.",
                "error_code": "ACCOUNT_INACTIVE",
            },
        )
    return current_user


async def require_verified(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """
    Returns the current user only if their email is verified.

    Raises:
        403 if the email has not been verified yet.
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "Please verify your email address to access this resource.",
                "error_code": "EMAIL_NOT_VERIFIED",
            },
        )
    return current_user


async def require_admin(
    current_user: Annotated[User, Depends(require_verified)],
) -> User:
    """
    Returns the current user only if they have the admin role.

    Raises:
        403 if the user is not an admin.
    """
    if not current_user.role or current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "Administrator access required.",
                "error_code": "INSUFFICIENT_PERMISSIONS",
            },
        )
    return current_user


# ──────────────────────────────────────────────
# Type Aliases (convenience)
# ──────────────────────────────────────────────
CurrentUser = Annotated[User, Depends(get_current_user)]
ActiveUser = Annotated[User, Depends(get_current_active_user)]
VerifiedUser = Annotated[User, Depends(require_verified)]
AdminUser = Annotated[User, Depends(require_admin)]
DBSession = Annotated[AsyncSession, Depends(get_db)]
