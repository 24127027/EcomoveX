"""
Update invitee_id for existing invitation contexts
"""
import asyncio
from sqlalchemy import text
from database.db import engine


async def update_contexts():
    async with engine.begin() as conn:
        print("Updating invitation contexts...")
        
        # Get all invitation messages
        result = await conn.execute(text("""
            SELECT m.id, m.sender_id, m.room_id
            FROM messages m
            WHERE m.message_type = 'plan_invitation'
        """))
        
        messages = result.fetchall()
        
        for msg_id, sender_id, room_id in messages:
            # Get room members
            members_result = await conn.execute(text(f"""
                SELECT user_id FROM room_members WHERE room_id = {room_id}
            """))
            members = [row[0] for row in members_result.fetchall()]
            
            # Find invitee (not the sender)
            invitee_id = None
            for member_id in members:
                if member_id != sender_id:
                    invitee_id = member_id
                    break
            
            if not invitee_id:
                print(f"  ⚠️  Message {msg_id}: No invitee found!")
                continue
            
            # Update context
            context_key = f"invitation_{msg_id}"
            
            # Get current context
            context_result = await conn.execute(text("""
                SELECT value FROM room_context 
                WHERE room_id = :room_id AND key = :key
            """), {"room_id": room_id, "key": context_key})
            
            context_row = context_result.fetchone()
            
            if context_row:
                import json
                context_value = context_row[0]
                
                # Update invitee_id
                context_value['invitee_id'] = invitee_id
                
                # Update in database
                await conn.execute(text("""
                    UPDATE room_context 
                    SET value = :value
                    WHERE room_id = :room_id AND key = :key
                """), {
                    "value": json.dumps(context_value),
                    "room_id": room_id,
                    "key": context_key
                })
                
                print(f"  ✅ Message {msg_id}: Updated invitee_id to {invitee_id}")
            else:
                print(f"  ⚠️  Message {msg_id}: Context not found!")
        
        print("\n✅ All contexts updated!")


if __name__ == "__main__":
    asyncio.run(update_contexts())
