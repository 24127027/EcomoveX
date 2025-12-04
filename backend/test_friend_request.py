#!/usr/bin/env python3
"""
Script để test friend request by username
Kiểm tra database và debug 404 error
"""

import asyncio
from sqlalchemy import select
from database.db import UserAsyncSessionLocal
from models.user import User


async def check_users():
    """Kiểm tra tất cả users trong database"""
    print("=" * 80)
    print("📊 CHECKING ALL USERS IN DATABASE")
    print("=" * 80)
    
    async with UserAsyncSessionLocal() as db:
        try:
            # Lấy tất cả users
            result = await db.execute(select(User))
            users = result.scalars().all()
            
            if not users:
                print("\n⚠️  WARNING: No users found in database!")
                print("   Make sure you have created test accounts.")
                return
            
            print(f"\n✅ Found {len(users)} users:\n")
            print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Created':<25}")
            print("-" * 80)
            
            for user in users:
                print(f"{user.id:<5} {user.username:<20} {user.email:<30} {str(user.created_at)[:19]}")
            
            print("\n" + "=" * 80)
            print("💡 TO TEST FRIEND REQUEST:")
            print("=" * 80)
            
            if len(users) >= 2:
                user1 = users[0]
                user2 = users[1]
                
                print(f"\n1. Login as: {user1.username}")
                print(f"2. Send friend request to username: {user2.username}")
                print(f"\nExample API call:")
                print(f"""
curl -X POST http://localhost:8000/friends/request/by-username \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{{"username": "{user2.username}"}}'
                """)
                
                # Test search
                print("\n" + "=" * 80)
                print("🔍 TESTING SEARCH FUNCTION")
                print("=" * 80)
                
                from repository.user_repository import UserRepository
                
                # Test search với username exact
                print(f"\nTest 1: Search for exact username '{user2.username}'")
                results = await UserRepository.search_users(db, user2.username)
                print(f"Results: {len(results)} found")
                for r in results:
                    print(f"  - {r.username} (exact match: {r.username.lower() == user2.username.lower()})")
                
                # Test search với partial
                partial = user2.username[:3] if len(user2.username) >= 3 else user2.username
                print(f"\nTest 2: Search for partial username '{partial}'")
                results = await UserRepository.search_users(db, partial)
                print(f"Results: {len(results)} found")
                for r in results:
                    print(f"  - {r.username}")
                
                # Test case sensitivity
                print(f"\nTest 3: Search with different case '{user2.username.upper()}'")
                results = await UserRepository.search_users(db, user2.username.upper())
                print(f"Results: {len(results)} found")
                for r in results:
                    print(f"  - {r.username}")
            else:
                print("\n⚠️  Need at least 2 users to test friend request")
                print("   Create another account first!")
        
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()


async def test_specific_username(username: str):
    """Test search với username cụ thể"""
    print("=" * 80)
    print(f"🔍 TESTING SEARCH FOR USERNAME: '{username}'")
    print("=" * 80)
    
    async with UserAsyncSessionLocal() as db:
        try:
            from repository.user_repository import UserRepository
            
            print(f"\nSearching for: '{username}'")
            results = await UserRepository.search_users(db, username, limit=10)
            
            print(f"\n✅ Found {len(results)} results:")
            if results:
                for idx, user in enumerate(results, 1):
                    is_exact = user.username.lower() == username.lower()
                    match_type = "EXACT MATCH ✓" if is_exact else "partial match"
                    print(f"\n{idx}. User ID: {user.id}")
                    print(f"   Username: '{user.username}' ({match_type})")
                    print(f"   Email: {user.email}")
            else:
                print("\n⚠️  No users found!")
                print("\nPossible reasons:")
                print("  1. Username does not exist in database")
                print("  2. Typo in username")
                print("  3. Username is case-sensitive (should not be with ILIKE)")
                
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()


async def main():
    import sys
    
    if len(sys.argv) > 1:
        # Test với username cụ thể
        username = sys.argv[1]
        await test_specific_username(username)
    else:
        # Check tất cả users
        await check_users()
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
