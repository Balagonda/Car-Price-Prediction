"""
AutoWorth AI — User Schemas

Pydantic v2 schemas for user registration, login, and profile responses.
PASSWORD HASH IS NEVER INCLUDED IN ANY RESPONSE SCHEMA.
"""

import uuid
from datetime import datetime

from pydantic import EmailStr, Field, field_validator

from app.schemas.common import BaseSchema


# ──────────────────────────────────────────────
# Request Schemas
# ──────────────────────────────────────────────
class UserRegisterRequest(BaseSchema):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v


class UserLoginRequest(BaseSchema):
    email: EmailStr
    password: str
    remember_me: bool = False


class GoogleOAuthRequest(BaseSchema):
    id_token: str = Field(..., description="Google OAuth ID token from frontend")


class PasswordResetRequest(BaseSchema):
    email: EmailStr


class PasswordResetConfirmRequest(BaseSchema):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


# ──────────────────────────────────────────────
# Response Schemas
# ──────────────────────────────────────────────
class RoleResponse(BaseSchema):
    id: int
    name: str


class UserResponse(BaseSchema):
    """Safe user response — never includes password_hash."""

    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    profile_image_url: str | None = None
    is_active: bool
    is_verified: bool
    oauth_provider: str | None = None
    role: RoleResponse
    created_at: datetime


class TokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse


class UserUpdateRequest(BaseSchema):
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    profile_image_url: str | None = None
