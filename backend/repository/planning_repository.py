# repository/planning_repository.py
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models.chatbot.planning import TravelPlan, PlanItem, ChatSessionContext
from typing import Optional, List, Dict, Any

class PlanningRepository:
    @staticmethod
    async def get_active_plan(db: AsyncSession, user_id: int) -> Optional[TravelPlan]:
        q = await db.execute(
            select(TravelPlan).where(TravelPlan.user_id == user_id).order_by(TravelPlan.updated_at.desc()).limit(1)
        )
        return q.scalars().first()

    @staticmethod
    async def get_plan_by_id(db: AsyncSession, plan_id: int) -> Optional[TravelPlan]:
        q = await db.execute(select(TravelPlan).where(TravelPlan.id == plan_id))
        return q.scalars().first()

    @staticmethod
    async def get_plan_items(db: AsyncSession, plan_id: int) -> List[PlanItem]:
        q = await db.execute(select(PlanItem).where(PlanItem.plan_id == plan_id).order_by(PlanItem.day_index, PlanItem.time))
        return q.scalars().all()

    @staticmethod
    async def add_plan_item(db: AsyncSession, plan_id: int, item_data: Dict[str,Any]) -> PlanItem:
        item = PlanItem(plan_id=plan_id, **item_data)
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def delete_plan_item(db: AsyncSession, item_id: int, user_id: int) -> bool:
        # ensure plan belongs to user
        q = await db.execute(select(PlanItem).join(TravelPlan).where(PlanItem.id==item_id, TravelPlan.user_id==user_id))
        item = q.scalars().first()
        if not item:
            return False
        await db.delete(item)
        await db.commit()
        return True

    @staticmethod
    async def update_plan_item(db: AsyncSession, item_id: int, updates: Dict[str,Any]) -> Optional[PlanItem]:
        q = await db.execute(select(PlanItem).where(PlanItem.id == item_id))
        item = q.scalars().first()
        if not item:
            return None
        for k,v in updates.items():
            setattr(item, k, v)
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def save_session_context(db: AsyncSession, session_id: int, key: str, value: Any):
        # upsert
        q = await db.execute(select(ChatSessionContext).where(ChatSessionContext.session_id==session_id, ChatSessionContext.key==key))
        row = q.scalars().first()
        if row:
            row.value = value
            await db.commit()
            await db.refresh(row)
            return row
        new = ChatSessionContext(session_id=session_id, key=key, value=value)
        db.add(new)
        await db.commit()
        await db.refresh(new)
        return new

    @staticmethod
    async def load_session_context(db: AsyncSession, session_id: int) -> Dict[str,Any]:
        q = await db.execute(select(ChatSessionContext).where(ChatSessionContext.session_id==session_id))
        rows = q.scalars().all()
        return {r.key: r.value for r in rows}
