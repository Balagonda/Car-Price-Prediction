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

import csv
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User
from app.models.brand import Brand
from app.models.car_model import CarModel
from app.models.variant import Variant
from app.models.city import City

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


async def seed_vehicles(session) -> None:
    """Parse docs/2026-05-22.csv and seed Brand, CarModel, Variant, and City tables."""
    csv_path = Path(__file__).parent.parent.parent.parent / "docs" / "2026-05-22.csv"
    if not csv_path.exists():
        print(f"  ⚠️ CSV file not found at {csv_path}")
        return

    print(f"  🚗 Parsing vehicle data from {csv_path.name}...")
    brands_map: dict[str, Brand] = {}
    models_map: dict[tuple[int, str], CarModel] = {}
    cities_map: dict[tuple[str, str], City] = {}

    with open(csv_path, mode="r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            make_name = (row.get("make") or "").strip()
            model_name = (row.get("model") or "").strip()
            trim_name = (row.get("trim") or "").strip()
            city_name = (row.get("sellerCity") or "").strip()
            state_name = (row.get("sellerState") or "").strip()

            if not make_name or not model_name:
                continue

            # 1. Brand
            if make_name not in brands_map:
                res = await session.execute(select(Brand).where(Brand.name == make_name))
                brand = res.scalar_one_or_none()
                if not brand:
                    brand = Brand(name=make_name, is_active=True)
                    session.add(brand)
                    await session.flush()
                brands_map[make_name] = brand

            brand = brands_map[make_name]

            # 2. CarModel
            model_key = (brand.id, model_name)
            if model_key not in models_map:
                res = await session.execute(
                    select(CarModel).where(CarModel.brand_id == brand.id, CarModel.name == model_name)
                )
                car_model = res.scalar_one_or_none()
                if not car_model:
                    car_model = CarModel(name=model_name, brand_id=brand.id, is_active=True)
                    session.add(car_model)
                    await session.flush()
                models_map[model_key] = car_model

            car_model = models_map[model_key]

            # 3. Variant
            if trim_name:
                res = await session.execute(
                    select(Variant).where(Variant.car_model_id == car_model.id, Variant.name == trim_name)
                )
                if not res.scalar_one_or_none():
                    variant = Variant(name=trim_name, car_model_id=car_model.id, is_active=True)
                    session.add(variant)

            # 4. City
            if city_name and state_name:
                city_key = (city_name, state_name)
                if city_key not in cities_map:
                    res = await session.execute(
                        select(City).where(City.name == city_name, City.state == state_name)
                    )
                    if not res.scalar_one_or_none():
                        city = City(name=city_name, state=state_name, is_active=True)
                        session.add(city)
                        await session.flush()
                        cities_map[city_key] = city

            count += 1
            if count >= 500:  # Seed top 500 records for performance
                break

    print(f"  ✅ Seeded {len(brands_map)} brands and {len(models_map)} models!")


async def main() -> None:
    print("🌱 Seeding AutoWorth AI database...")
    async with AsyncSessionLocal() as session:
        try:
            print("\n📋 Seeding roles...")
            roles = await seed_roles(session)

            print("\n👤 Seeding admin user...")
            await seed_admin_user(session, roles["admin"])

            print("\n🚘 Seeding vehicle catalog...")
            await seed_vehicles(session)

            await session.commit()
            print("\n✅ Database seeding complete!")
        except Exception as exc:
            await session.rollback()
            print(f"\n❌ Seeding failed: {exc}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
