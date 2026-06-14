import asyncio
from datetime import datetime, timezone
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal, engine
from app.models import Base, User, Group, GroupMembership
from app.routers.auth import get_password_hash

async def seed_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSessionLocal() as db:
        users_data = [
            {"name": "Aisha", "email": "aisha@example.com"},
            {"name": "Rohan", "email": "rohan@example.com"},
            {"name": "Priya", "email": "priya@example.com"},
            {"name": "Meera", "email": "meera@example.com"},
            {"name": "Sam", "email": "sam@example.com"},
            {"name": "Dev", "email": "dev@example.com"}
        ]
        
        users = []
        for u in users_data:
            db_user = User(name=u["name"], email=u["email"], hashed_password=get_password_hash("pass123"))
            db.add(db_user)
            users.append(db_user)
            
        await db.commit()
        for u in users:
            await db.refresh(u)
            
        group = Group(name="Flatmates")
        db.add(group)
        await db.commit()
        await db.refresh(group)
        
        feb_date = datetime(2026, 2, 1, tzinfo=timezone.utc)
        mid_april_date = datetime(2026, 4, 15, tzinfo=timezone.utc)
        end_march_date = datetime(2026, 3, 31, tzinfo=timezone.utc)
        
        for u in users:
            m = GroupMembership(group_id=group.id, user_id=u.id, joined_at=feb_date)
            if u.name == "Meera":
                m.left_at = end_march_date
            if u.name == "Sam":
                m.joined_at = mid_april_date
            db.add(m)
            
        await db.commit()
        print("Database seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed_db())
