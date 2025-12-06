"""
Fix existing invitation context by adding invitee_id
"""
import asyncio
from sqlalchemy import text, select
from database.db import engine
from models.message import Message, RoomContext
from models.room import RoomMember


async def fix_invitation_contexts():
    async with engine.begin() as conn:
        # Get all plan_invitation messages
        result = await conn.execute(text("""
            SELECT id, sender_id, room_id, content 
            FROM messages 
            WHERE message_type = 'plan_invitation'
        """))
        
        messages = result.fetchall()
        print(f"Found {len(messages)} invitation messages")
        
        for msg_id, sender_id, room_id, content in messages:
            # Get room members
            members_result = await conn.execute(text(f"""
                SELECT user_id FROM room_members WHERE room_id = {room_id}
            """))
            members = [row[0] for row in members_result.fetchall()]
            
            # Find invitee (the other person)
            invitee_id = None
            for member_id in members:
                if member_id != sender_id:
                    invitee_id = member_id
                    break
            
            if not invitee_id:
                print(f"  ⚠️  Message {msg_id}: Could not find invitee in room {room_id}")
                continue
            
            # Update context
            context_key = f"invitation_{msg_id}"
            
            # Check if context exists
            context_result = await conn.execute(text(f"""
                SELECT value FROM room_contexts 
                WHERE room_id = {room_id} AND key = '{context_key}'
            """))
            context_row = context_result.fetchone()
            
            if context_row:
                import json
                context_value = context_row[0]
                if isinstance(context_value, str):
                    context_value = json.loads(context_value)
                
                context_value['invitee_id'] = invitee_id
                
                await conn.execute(text(f"""
                    UPDATE room_contexts 
                    SET value = '{json.dumps(context_value)}'::jsonb
                    WHERE room_id = {room_id} AND key = '{context_key}'
                """))
                print(f"  ✅ Updated context for message {msg_id}: invitee_id={invitee_id}")
            else:
                print(f"  ⚠️  No context found for message {msg_id}")
        
        print("\n✅ All invitation contexts updated!")


if __name__ == "__main__":
    asyncio.run(fix_invitation_contexts())
