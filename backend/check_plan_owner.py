import asyncio
from database.db import get_db
from models.plan import PlanMember, PlanRole
from sqlalchemy import select

async def check_plan():
    async for db in get_db():
        # Check plan 4 members
        result = await db.execute(
            select(PlanMember).where(PlanMember.plan_id == 4)
        )
        members = result.scalars().all()
        print('\n=== PLAN 4 MEMBERS ===')
        for m in members:
            print(f'User ID: {m.user_id}, Role: {m.role.value}, Joined: {m.joined_at}')
        
        # Check who owns this plan
        owner_result = await db.execute(
            select(PlanMember).where(
                PlanMember.plan_id == 4,
                PlanMember.role == PlanRole.owner
            )
        )
        owner = owner_result.scalar_one_or_none()
        if owner:
            print(f'\n✅ Owner of Plan 4: User ID {owner.user_id}')
        else:
            print('\n❌ No owner found for Plan 4!')
        break

if __name__ == "__main__":
    asyncio.run(check_plan())
