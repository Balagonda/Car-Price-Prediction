"""
AutoWorth AI — Common Schemas

Reusable Pydantic v2 response models used across all endpoints.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with shared configuration."""

    model_config = ConfigDict(
        from_attributes=True,      # Enable ORM mode (SQLAlchemy → Pydantic)
        populate_by_name=True,
        use_enum_values=True,
    )


class APIResponse(BaseSchema, Generic[T]):
    """
    Standard API response envelope.

    All API responses should be wrapped in this model for consistency.
    """

    success: bool = True
    message: str = "OK"
    data: T | None = None


class PaginatedResponse(BaseSchema, Generic[T]):
    """Paginated list response."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorDetail(BaseSchema):
    """Single field validation error detail."""

    field: str
    message: str


class ErrorResponse(BaseSchema):
    """Standard error response body."""

    success: bool = False
    message: str
    errors: list[ErrorDetail] | None = None
    error_code: str | None = None
