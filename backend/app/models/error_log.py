"""
AutoWorth AI — ErrorLog Model

Captures unhandled exceptions and system errors.
Severity levels align with Python's logging module.
"""

import enum
import uuid

from sqlalchemy import Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ErrorSeverity(str, enum.Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorLog(Base, TimestampMixin):
    __tablename__ = "error_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    service: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
        # e.g. "prediction_service", "cv_engine", "auth_service"
    )
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    stack_trace: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[ErrorSeverity] = mapped_column(
        Enum(ErrorSeverity, name="error_severity_enum"),
        default=ErrorSeverity.ERROR,
        nullable=False,
        index=True,
    )
    request_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    request_method: Mapped[str | None] = mapped_column(String(10), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ErrorLog id={self.id} "
            f"service={self.service!r} "
            f"severity={self.severity}>"
        )
