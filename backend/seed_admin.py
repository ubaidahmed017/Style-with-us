import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import User, UserRole

async def seed_admin(email: str, firebase_uid: str, name: str):
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
