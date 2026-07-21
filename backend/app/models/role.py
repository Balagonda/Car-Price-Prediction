"""
AutoWorth AI — Role Model

Stores user roles: Guest, Registered User, Admin.
Seeded once at application initialisation.
"""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ────────────────────────────────────────
    users: Mapped[list["User"]] = relationship("User", back_populates="role")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Role id={self.id} name={self.name!r}>"
