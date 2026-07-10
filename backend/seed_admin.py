import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

sys.path.append(str(Path(__file__).resolve().parent))

from sqlalchemy import select
from app.core.database import engine, AsyncSessionLocal
from app.models.base import Base
from app.models import User, UserRole

async def seed_admin(email: str, firebase_uid: str, name: str):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            print(f"User {email} already exists. Setting role to ADMIN.")
            user.role = UserRole.ADMIN
            user.firebase_uid = firebase_uid
            user.name = name
        else:
            print(f"Seeding new admin: {name} ({email})")
            user = User(
                email=email,
                firebase_uid=firebase_uid,
                name=name,
                role=UserRole.ADMIN
            )
            session.add(user)

        await session.commit()
        print("Admin user successfully seeded!")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python seed_admin.py <email> <firebase_uid> <name>")
        sys.exit(1)
    asyncio.run(seed_admin(sys.argv[1], sys.argv[2], sys.argv[3]))
