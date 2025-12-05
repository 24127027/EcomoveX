"""
Migration script to add 'plan_invitation' value to messagetype enum
"""
import asyncio
from sqlalchemy import text
from database.db import engine


async def migrate():
    async with engine.connect() as conn:
        # Check current enum values
        result = await conn.execute(text("""
            SELECT enumlabel 
            FROM pg_enum e
            JOIN pg_type t ON e.enumtypid = t.oid
            WHERE t.typname = 'messagetype'
            ORDER BY enumsortorder
        """))
        current_values = [row[0] for row in result]
        print(f'Current MessageType enum values: {current_values}')
        
        if 'plan_invitation' not in current_values:
            print('Adding plan_invitation to enum...')
            await conn.execute(text("""
                ALTER TYPE messagetype ADD VALUE 'plan_invitation'
            """))
            await conn.commit()
            print('✅ Successfully added plan_invitation to messagetype enum')
        else:
            print('✅ plan_invitation already exists in enum')


if __name__ == "__main__":
    asyncio.run(migrate())
