"""
AutoWorth AI — Auth Endpoints

Routes:
  POST   /auth/register         — Create account (triggers email verification)
  POST   /auth/login            — Email/password login → access token + refresh cookie
  POST   /auth/google-login     — Google ID token → access token + refresh cookie
  POST   /auth/refresh          — Rotate refresh token → new access token
  POST   /auth/logout           — Invalidate session
  GET    /auth/verify-email     — Confirm email with token query param
  GET    /auth/me               — Current user profile (requires verified)
  PATCH  /auth/me               — Update current user profile

All responses follow the standard APIResponse envelope.
"""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status

from app.api.v1.dependencies import DBSession, VerifiedUser, get_current_active_user
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.user import (
    GoogleOAuthRequest,
    TokenResponse,
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.services.auth_service import AuthService
from app.core.config import get_settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()

# Cookie name for the refresh token
REFRESH_COOKIE_NAME = "refresh_token"

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Set an HTTP-only secure cookie carrying the refresh token."""
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.is_production,  # HTTPS only in production
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/v1/auth",  # Scope cookie to auth routes only
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Clear the refresh token cookie."""
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/api/v1/auth",
    )


# ──────────────────────────────────────────────
# Register
# ──────────────────────────────────────────────
@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    response_model=APIResponse,
)
async def register(
    data: UserRegisterRequest,
    db: DBSession,
) -> APIResponse:
    """
    Create a new user account and trigger email verification.

    - Password is hashed with bcrypt before storage.
    - Returns user object. In DEBUG mode, also returns the verification_token for testing.
    """
    auth_svc = AuthService(db)
    result = await auth_svc.register(data)
    return APIResponse(
        success=True,
        message=(
            "Account created successfully! Please check your email to verify your account."
        ),
        data=result,
    )


# ──────────────────────────────────────────────
# Login (Email/Password)
# ──────────────────────────────────────────────
@router.post(
    "/login",
    summary="Login with email and password",
    response_model=APIResponse[TokenResponse],
)
async def login(
    data: UserLoginRequest,
    request: Request,
    response: Response,
    db: DBSession,
) -> APIResponse[TokenResponse]:
    """
    Authenticate with email + password.

    - Returns JWT access token in response body.
    - Sets refresh token as an HTTP-only cookie.
    - Enforces single active session per user (previous sessions invalidated).
    - Requires email to be verified.
    """
    auth_svc = AuthService(db)
    token_response, refresh_token = await auth_svc.login(data, request)
    _set_refresh_cookie(response, refresh_token)
    return APIResponse(
        success=True,
        message="Login successful.",
        data=token_response,
    )


# ──────────────────────────────────────────────
# Google OAuth Login
# ──────────────────────────────────────────────
@router.post(
    "/google-login",
    summary="Login or register with Google OAuth",
    response_model=APIResponse[TokenResponse],
)
async def google_login(
    data: GoogleOAuthRequest,
    request: Request,
    response: Response,
    db: DBSession,
) -> APIResponse[TokenResponse]:
    """
    Validate a Google ID token and issue platform JWT tokens.

    - Creates account if the user doesn't exist (pre-verified).
    - Links Google OAuth to an existing email/password account if email matches.
    - Returns access token + refresh cookie.
    """
    auth_svc = AuthService(db)
    token_response, refresh_token = await auth_svc.google_login(data, request)
    _set_refresh_cookie(response, refresh_token)
    return APIResponse(
        success=True,
        message="Google login successful.",
        data=token_response,
    )


# ──────────────────────────────────────────────
# Token Refresh
# ──────────────────────────────────────────────
@router.post(
    "/refresh",
    summary="Refresh access token using refresh cookie",
    response_model=APIResponse[TokenResponse],
)
async def refresh_token(
    response: Response,
    db: DBSession,
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE_NAME)] = None,
) -> APIResponse[TokenResponse]:
    """
    Rotate the refresh token and return a new access token.

    - Reads the refresh token from the HTTP-only cookie.
    - Invalidates the old session and creates a new one.
    - Sets a new refresh cookie.
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "No refresh token found. Please log in again.",
                "error_code": "MISSING_REFRESH_TOKEN",
            },
        )
    auth_svc = AuthService(db)
    token_response, new_refresh = await auth_svc.refresh_access_token(refresh_token)
    _set_refresh_cookie(response, new_refresh)
    return APIResponse(
        success=True,
        message="Token refreshed successfully.",
        data=token_response,
    )


# ──────────────────────────────────────────────
# Logout
# ──────────────────────────────────────────────
@router.post(
    "/logout",
    summary="Logout — invalidate current session",
    response_model=APIResponse,
)
async def logout(
    response: Response,
    db: DBSession,
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE_NAME)] = None,
) -> APIResponse:
    """
    Invalidate the user's current session.

    - The refresh token cookie is cleared.
    - The session record is marked inactive.
    """
    auth_svc = AuthService(db)
    await auth_svc.logout(refresh_token)
    _clear_refresh_cookie(response)
    return APIResponse(success=True, message="Logged out successfully.")


# ──────────────────────────────────────────────
# Email Verification
# ──────────────────────────────────────────────
@router.get(
    "/verify-email",
    summary="Verify email address using token",
    response_model=APIResponse[UserResponse],
)
async def verify_email(
    token: str,
    db: DBSession,
) -> APIResponse[UserResponse]:
    """
    Confirm email address using the verification token sent via email.

    - Marks the user's email as verified.
    - Returns the updated user profile.
    """
    auth_svc = AuthService(db)
    user_resp = await auth_svc.verify_email(token)
    return APIResponse(
        success=True,
        message="Email verified successfully. You can now log in.",
        data=user_resp,
    )


# ──────────────────────────────────────────────
# Current User Profile
# ──────────────────────────────────────────────
@router.get(
    "/me",
    summary="Get current user profile",
    response_model=APIResponse[UserResponse],
)
async def get_me(
    current_user: VerifiedUser,
    db: DBSession,
) -> APIResponse[UserResponse]:
    """
    Return the currently authenticated user's profile.

    - Requires a valid JWT access token.
    - Requires email verification.
    - Never returns password hash.
    """
    auth_svc = AuthService(db)
    user_resp = await auth_svc.get_me(current_user)
    return APIResponse(success=True, message="OK", data=user_resp)


@router.patch(
    "/me",
    summary="Update current user profile",
    response_model=APIResponse[UserResponse],
)
async def update_me(
    data: UserUpdateRequest,
    current_user: VerifiedUser,
    db: DBSession,
) -> APIResponse[UserResponse]:
    """
    Update the current user's first name, last name, or profile image URL.

    - Requires a valid JWT access token and verified email.
    - Only provided fields are updated (partial update).
    """
    auth_svc = AuthService(db)
    user_resp = await auth_svc.update_me(current_user, data)
    return APIResponse(
        success=True,
        message="Profile updated successfully.",
        data=user_resp,
    )
