"""
AutoWorth AI — Auth Service (Full Implementation)

Business logic for the full authentication lifecycle:
  - Email/password registration with email verification
  - Email/password login with single-session enforcement
  - Google OAuth login (ID token verification via Google tokeninfo)
  - JWT access + HTTP-only refresh token issuance
  - Token refresh with session rotation
  - Logout (session invalidation)
  - Email verification confirmation
  - Profile read + update

Layer: Business Logic Layer
Dependencies: UserRepository, SessionRepository, SecurityUtils, EmailService
"""

import logging
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import httpx
from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    GoogleOAuthRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.models.user import User
from app.models.role import Role
from sqlalchemy import select
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)
settings = get_settings()

# ──────────────────────────────────────────────
# Role name constants
# ──────────────────────────────────────────────
ROLE_USER = "user"
ROLE_ADMIN = "admin"
ROLE_GUEST = "guest"


class AuthService:
    """
    Handles full authentication business logic.

    Responsibilities:
    - User registration with email verification
    - Email/password login with session management
    - Google OAuth token validation and login
    - JWT token generation and refresh (with session rotation)
    - Password reset workflow
    - Profile management

    Note: Database access is delegated to repositories.
    No SQLAlchemy queries are written directly in this service.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._user_repo = UserRepository(db)
        self._session_repo = SessionRepository(db)

    # ──────────────────────────────────────────────
    # Registration
    # ──────────────────────────────────────────────
    async def register(self, data: UserRegisterRequest) -> dict:
        """
        Create a new user account.

        Returns:
            Dict with 'user' (UserResponse) and optionally 'verification_token' (dev only).

        Raises:
            409 if email already registered.
        """
        # 1. Check for duplicate email
        if await self._user_repo.email_exists(data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "message": "An account with this email address already exists.",
                    "error_code": "EMAIL_ALREADY_EXISTS",
                },
            )

        # 2. Resolve the "user" role
        user_role = await self._get_role_by_name(ROLE_USER)

        # 3. Generate email verification token
        verification_token = secrets.token_urlsafe(32)

        # 4. Create user
        new_user = await self._user_repo.create(
            first_name=data.first_name.strip(),
            last_name=data.last_name.strip(),
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            role_id=user_role.id,
            is_active=True,
            is_verified=False,
            email_verification_token=verification_token,
        )

        # Reload with role relationship
        new_user = await self._user_repo.get_by_id_with_role(new_user.id)

        # 5. Send verification email (async, non-blocking on failure)
        try:
            from app.services.email_service import EmailService
            email_svc = EmailService()
            await email_svc.send_verification_email(
                to_email=new_user.email,
                first_name=new_user.first_name,
                token=verification_token,
            )
        except Exception as exc:
            logger.warning(f"Failed to send verification email: {exc}")

        await self._db.commit()

        result: dict = {"user": UserResponse.model_validate(new_user)}
        # Return token in debug mode for easy testing without email setup
        if settings.DEBUG:
            result["verification_token"] = verification_token
        return result

    # ──────────────────────────────────────────────
    # Email/Password Login
    # ──────────────────────────────────────────────
    async def login(
        self,
        data: UserLoginRequest,
        request: Request | None = None,
    ) -> tuple[TokenResponse, str]:
        """
        Authenticate a user and issue JWT tokens.

        Returns:
            Tuple of (TokenResponse, refresh_token_string).
            Caller is responsible for setting refresh token as HTTP-only cookie.

        Raises:
            401 if credentials are invalid.
            403 if account is inactive or email not verified.
        """
        # 1. Fetch user
        user = await self._user_repo.get_by_email(data.email)
        if not user or not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "Invalid email or password.",
                    "error_code": "INVALID_CREDENTIALS",
                },
            )

        # 2. Verify password
        if not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "Invalid email or password.",
                    "error_code": "INVALID_CREDENTIALS",
                },
            )

        # 3. Account status checks
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "message": "Your account has been deactivated. Please contact support.",
                    "error_code": "ACCOUNT_INACTIVE",
                },
            )

        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "message": "Please verify your email address before logging in.",
                    "error_code": "EMAIL_NOT_VERIFIED",
                },
            )

        return await self._issue_tokens(user=user, request=request)

    # ──────────────────────────────────────────────
    # Google OAuth Login
    # ──────────────────────────────────────────────
    async def google_login(
        self,
        data: GoogleOAuthRequest,
        request: Request | None = None,
    ) -> tuple[TokenResponse, str]:
        """
        Validate a Google ID token and log the user in (or register them).

        Strategy:
        - Verify token via Google's tokeninfo endpoint
        - Look up existing user by oauth_sub → email fallback
        - Create new user if not found (pre-verified, no password)
        - Issue platform JWT tokens

        Returns:
            Tuple of (TokenResponse, refresh_token_string).

        Raises:
            401 if Google token is invalid.
        """
        # 1. Verify Google ID token
        google_profile = await self._verify_google_token(data.id_token)
        google_sub: str = google_profile["sub"]
        email: str = google_profile["email"].lower()
        first_name: str = google_profile.get("given_name", "")
        last_name: str = google_profile.get("family_name", "")
        picture: str | None = google_profile.get("picture")

        # 2. Look up user by OAuth sub first, then email
        user = await self._user_repo.get_by_oauth_sub("google", google_sub)

        if not user:
            # Check if user registered with same email via password
            user = await self._user_repo.get_by_email(email)
            if user:
                # Link Google OAuth to existing account
                user = await self._user_repo.update(
                    user,
                    oauth_provider="google",
                    oauth_sub=google_sub,
                    is_verified=True,
                    profile_image_url=picture or user.profile_image_url,
                )
            else:
                # New Google user — create account
                user_role = await self._get_role_by_name(ROLE_USER)
                user = await self._user_repo.create(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    password_hash=None,
                    oauth_provider="google",
                    oauth_sub=google_sub,
                    profile_image_url=picture,
                    role_id=user_role.id,
                    is_active=True,
                    is_verified=True,  # Google already verified the email
                )

        # Reload with role
        user = await self._user_repo.get_by_id_with_role(user.id)

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "message": "Your account has been deactivated.",
                    "error_code": "ACCOUNT_INACTIVE",
                },
            )

        return await self._issue_tokens(user=user, request=request)

    # ──────────────────────────────────────────────
    # Token Refresh
    # ──────────────────────────────────────────────
    async def refresh_access_token(self, refresh_token: str) -> tuple[TokenResponse, str]:
        """
        Validate the refresh token, rotate it, and return a new access token.

        Raises:
            401 if token is invalid, expired, or session not found.
        """
        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "Invalid or expired refresh token.",
                    "error_code": "INVALID_REFRESH_TOKEN",
                },
            )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "Invalid token type.",
                    "error_code": "INVALID_TOKEN_TYPE",
                },
            )

        # Validate session still active
        token_hash = SessionRepository.hash_token(refresh_token)
        session = await self._session_repo.get_active_session_by_hash(token_hash)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "Session expired or invalidated. Please log in again.",
                    "error_code": "SESSION_EXPIRED",
                },
            )

        user_id = uuid.UUID(payload["sub"])
        user = await self._user_repo.get_by_id_with_role(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "User not found or inactive.",
                    "error_code": "USER_NOT_FOUND",
                },
            )

        # Invalidate old session and issue new tokens
        await self._session_repo.invalidate_session_by_hash(token_hash)
        token_response, new_refresh = await self._issue_tokens(user=user)
        await self._db.commit()
        return token_response, new_refresh

    # ──────────────────────────────────────────────
    # Logout
    # ──────────────────────────────────────────────
    async def logout(self, refresh_token: str | None) -> None:
        """
        Invalidate the current session.
        Safe to call even if session doesn't exist.
        """
        if not refresh_token:
            return
        token_hash = SessionRepository.hash_token(refresh_token)
        await self._session_repo.invalidate_session_by_hash(token_hash)
        await self._db.commit()

    # ──────────────────────────────────────────────
    # Email Verification
    # ──────────────────────────────────────────────
    async def verify_email(self, token: str) -> UserResponse:
        """
        Confirm email using the verification token.

        Raises:
            400 if token is invalid or already used.
        """
        from sqlalchemy import select
        result = await self._db.execute(
            select(User).where(User.email_verification_token == token)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Invalid or expired verification token.",
                    "error_code": "INVALID_VERIFICATION_TOKEN",
                },
            )

        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "This email address has already been verified.",
                    "error_code": "ALREADY_VERIFIED",
                },
            )

        user = await self._user_repo.update(
            user,
            is_verified=True,
            email_verification_token=None,
        )
        user = await self._user_repo.get_by_id_with_role(user.id)
        await self._db.commit()
        return UserResponse.model_validate(user)

    # ──────────────────────────────────────────────
    # Profile
    # ──────────────────────────────────────────────
    async def get_me(self, user: User) -> UserResponse:
        """Return the current user's profile."""
        # Reload to ensure role is loaded
        fresh = await self._user_repo.get_by_id_with_role(user.id)
        return UserResponse.model_validate(fresh)

    async def update_me(self, user: User, data: UserUpdateRequest) -> UserResponse:
        """Update current user's profile (name, avatar URL)."""
        update_fields = data.model_dump(exclude_none=True)
        if not update_fields:
            return await self.get_me(user)

        updated = await self._user_repo.update(user, **update_fields)
        fresh = await self._user_repo.get_by_id_with_role(updated.id)
        await self._db.commit()
        return UserResponse.model_validate(fresh)

    # ──────────────────────────────────────────────
    # Private Helpers
    # ──────────────────────────────────────────────
    async def _issue_tokens(
        self,
        *,
        user: User,
        request: Request | None = None,
    ) -> tuple[TokenResponse, str]:
        """
        Issue access + refresh tokens and persist session.
        Invalidates all prior sessions (single-session policy).
        """
        # Invalidate existing sessions
        await self._session_repo.invalidate_all_user_sessions(user.id)

        # Create tokens
        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"role": user.role.name, "email": user.email},
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        # Persist session using refresh token hash
        token_hash = SessionRepository.hash_token(refresh_token)
        expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        device_info: str | None = None
        ip_address: str | None = None
        if request:
            device_info = request.headers.get("user-agent")
            ip_address = (
                request.headers.get("x-forwarded-for", "").split(",")[0].strip()
                or request.client.host
                if request.client
                else None
            )

        await self._session_repo.create_session(
            user_id=user.id,
            jwt_token_hash=token_hash,
            expires_at=expires_at,
            device_info=device_info,
            ip_address=ip_address,
        )

        await self._db.commit()

        user_resp = UserResponse.model_validate(user)
        token_response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_resp,
        )
        return token_response, refresh_token

    async def _get_role_by_name(self, name: str) -> Role:
        """Fetch a role by name. Raises 500 if roles are not seeded."""
        result = await self._db.execute(select(Role).where(Role.name == name))
        role = result.scalar_one_or_none()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": f"Role '{name}' not found. Please run the DB seed script.",
                    "error_code": "ROLE_NOT_SEEDED",
                },
            )
        return role

    async def _verify_google_token(self, id_token: str) -> dict:
        """
        Verify a Google ID token using the tokeninfo endpoint.

        Returns the decoded token payload (sub, email, given_name, etc.)

        Raises:
            401 if the token is invalid or the audience doesn't match.
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    "https://oauth2.googleapis.com/tokeninfo",
                    params={"id_token": id_token},
                )
            except httpx.RequestError as exc:
                logger.error(f"Google tokeninfo request failed: {exc}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={
                        "success": False,
                        "message": "Could not reach Google OAuth servers. Try again.",
                        "error_code": "GOOGLE_OAUTH_UNAVAILABLE",
                    },
                )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "Invalid or expired Google ID token.",
                    "error_code": "INVALID_GOOGLE_TOKEN",
                },
            )

        payload = response.json()

        # Validate audience matches our app
        if settings.GOOGLE_CLIENT_ID and payload.get("aud") != settings.GOOGLE_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "Google token audience mismatch.",
                    "error_code": "GOOGLE_TOKEN_AUDIENCE_MISMATCH",
                },
            )

        if not payload.get("email_verified", "false") in (True, "true"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Google account email is not verified.",
                    "error_code": "GOOGLE_EMAIL_NOT_VERIFIED",
                },
            )

        return payload
