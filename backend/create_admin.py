"""
Script to promote a user to Admin role
Usage: python create_admin.py <email>
Example: python create_admin.py admin@example.com
"""
import asyncio
import sys
from sqlalchemy import select
from database.db import async_session
from models.user import User, Role


async def promote_to_admin(email: str):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User with email '{email}' not found")
            return False
        
        user.role = Role.admin
        await session.commit()
        print(f"✅ User '{user.username}' (ID: {user.id}) has been promoted to Admin!")
        return True


async def list_users():
    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            print("No users found in database")
            return
        
        print("\nExisting users:")
        print("-" * 60)
        for user in users:
            print(f"ID: {user.id} | Email: {user.email} | Username: {user.username} | Role: {user.role}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_admin.py <email>")
        print("\nOr list all users: python create_admin.py --list")
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        asyncio.run(list_users())
    else:
        email = sys.argv[1]
        asyncio.run(promote_to_admin(email))
