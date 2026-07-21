"""
AutoWorth AI — DB Seed Script

Seeds essential lookup data:
  - Roles (Guest, Registered User, Admin)
  - A default Admin user for first run

Run with:
    python -m app.core.seed
"""

import asyncio
import sys
from pathlib import Path

# Add backend root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User

settings = get_settings()

ROLES = [
    {"name": "guest", "description": "Unauthenticated user — browse only"},
    {"name": "user", "description": "Registered user — can make predictions"},
    {"name": "admin", "description": "Administrator — full system access"},
]


async def seed_roles(session) -> dict[str, Role]:
    """Insert roles if they don't exist. Returns role name → Role map."""
    roles: dict[str, Role] = {}
    for role_data in ROLES:
        result = await session.execute(
            select(Role).where(Role.name == role_data["name"])
        )
        role = result.scalar_one_or_none()
        if not role:
            role = Role(**role_data)
            session.add(role)
            await session.flush()
            print(f"  ✅ Created role: {role_data['name']}")
        else:
            print(f"  ⏭️  Role already exists: {role_data['name']}")
        roles[role_data["name"]] = role
    return roles


async def seed_admin_user(session, admin_role: Role) -> None:
    """Create a default admin user if none exists."""
    result = await session.execute(
        select(User).where(User.email == "admin@autoworth.ai")
    )
    admin = result.scalar_one_or_none()
    if not admin:
        admin = User(
            first_name="AutoWorth",
            last_name="Admin",
            email="admin@autoworth.ai",
            password_hash=hash_password("Admin@12345"),  # Change on first login!
            is_active=True,
            is_verified=True,
            role_id=admin_role.id,
        )
        session.add(admin)
        print("  ✅ Created default admin: admin@autoworth.ai / Admin@12345")
        print("  ⚠️  CHANGE THIS PASSWORD IMMEDIATELY IN PRODUCTION!")
    else:
        print("  ⏭️  Admin user already exists")


async def main() -> None:
    print("🌱 Seeding AutoWorth AI database...")
    async with AsyncSessionLocal() as session:
        try:
            print("\n📋 Seeding roles...")
            roles = await seed_roles(session)

            print("\n👤 Seeding admin user...")
            await seed_admin_user(session, roles["admin"])

            await session.commit()
            print("\n✅ Database seeding complete!")
        except Exception as exc:
            await session.rollback()
            print(f"\n❌ Seeding failed: {exc}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
