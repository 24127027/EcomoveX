"""
Check invitation context in database
"""
import asyncio
from sqlalchemy import text
from database.db import engine


async def check_contexts():
    async with engine.connect() as conn:
        # Check all plan_invitation messages
        print("=" * 60)
        print("PLAN INVITATION MESSAGES:")
        print("=" * 60)
        result = await conn.execute(text("""
            SELECT id, sender_id, room_id, content, created_at
            FROM messages 
            WHERE message_type = 'plan_invitation'
            ORDER BY id
        """))
        
        for row in result:
            print(f"\nMessage ID: {row[0]}")
            print(f"  Sender ID: {row[1]}")
            print(f"  Room ID: {row[2]}")
            print(f"  Content: {row[3]}")
            print(f"  Created: {row[4]}")
        
        print("\n" + "=" * 60)
        print("ROOM CONTEXTS:")
        print("=" * 60)
        
        # Check room_context table
        result = await conn.execute(text("""
            SELECT room_id, key, value
            FROM room_context
            WHERE key LIKE 'invitation_%'
            ORDER BY room_id, key
        """))
        
        contexts = result.fetchall()
        if contexts:
            for row in contexts:
                print(f"\nRoom ID: {row[0]}")
                print(f"  Key: {row[1]}")
                print(f"  Value: {row[2]}")
        else:
            print("NO CONTEXTS FOUND!")
        
        print("\n" + "=" * 60)
        print("ROOM MEMBERS:")
        print("=" * 60)
        
        # Check room members for room 2
        result = await conn.execute(text("""
            SELECT rm.room_id, rm.user_id, u.username
            FROM room_members rm
            LEFT JOIN users u ON u.id = rm.user_id
            WHERE rm.room_id = 2
            ORDER BY rm.user_id
        """))
        
        for row in result:
            print(f"Room {row[0]}: User {row[1]} ({row[2]})")
        
        print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(check_contexts())
