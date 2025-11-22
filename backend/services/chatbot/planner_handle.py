# services/planner_handler.py
from repository.planning_repository import PlanningRepository
from services.chatbot.rule_engine import RuleEngine, Intent
from services.recommendation_service import recommend_for_cluster_hybrid
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional

class PlannerHandler:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PlanningRepository()
        self.rule = RuleEngine()

    async def handle(self, user_id: int, session_id: int, user_text: str) -> Dict[str, Any]:
        parse = self.rule.classify(user_text)
        intent = parse.intent
        ent = parse.entities

        plan = await self.repo.get_active_plan(self.db, user_id)
        if not plan:
            return {"ok": False, "message": "Không có plan active để chỉnh sửa."}

        if intent == Intent.ADD:
            # require day or default append to last day
            day = ent.get("day") or 1
            item = {
                "day_index": day,
                "time": ent.get("time"),
                "title": ent.get("title") or "Hoạt động mới",
                "type": "activity",
                "meta": {}
            }
            new_item = await self.repo.add_plan_item(self.db, plan.id, item)
            return {"ok": True, "action": "add", "item": {"id": new_item.id, "title": new_item.title, "day": new_item.day_index}}

        if intent == Intent.REMOVE:
            # try by item_id, else by matching title on that day
            item_id = ent.get("item_id")
            if item_id:
                ok = await self.repo.delete_plan_item(self.db, item_id, user_id)
                return {"ok": ok, "action": "remove", "item_id": item_id}
            # fallback: search by title
            title = ent.get("title")
            if title:
                # naive search
                items = await self.repo.get_plan_items(self.db, plan.id)
                cand = [it for it in items if title.lower() in it.title.lower()]
                if not cand:
                    return {"ok": False, "message": f"Không tìm thấy activity chứa '{title}'"}
                # delete first match
                ok = await self.repo.delete_plan_item(self.db, cand[0].id, user_id)
                return {"ok": ok, "action": "remove", "item_id": cand[0].id}
            return {"ok": False, "message": "Cần id hoặc tên activity để xóa."}

        if intent == Intent.MODIFY_TIME:
            item_id = ent.get("item_id")
            time = ent.get("time")
            if not item_id:
                # if no id, try to match by day and last item
                day = ent.get("day") or 1
                items = await self.repo.get_plan_items(self.db, plan.id)
                # pick first item on that day (may need better disambiguation)
                cand = [it for it in items if it.day_index == day]
                if not cand:
                    return {"ok": False, "message": f"Không tìm thấy hoạt động ngày {day} để đổi giờ."}
                item_id = cand[0].id
            updated = await self.repo.update_plan_item(self.db, item_id, {"time": time})
            if not updated:
                return {"ok": False, "message": "Không cập nhật được activity."}
            return {"ok": True, "action": "modify_time", "item": {"id": updated.id, "time": updated.time}}

        if intent == Intent.CHANGE_BUDGET:
            budget = ent.get("budget")
            plan.meta = plan.meta or {}
            plan.meta["budget"] = budget
            await self.db.commit()
            return {"ok": True, "action": "change_budget", "budget": budget}

        if intent == Intent.VIEW_PLAN:
            items = await self.repo.get_plan_items(self.db, plan.id)
            # convert items to simple dict
            out = [{"id": it.id, "day": it.day_index, "time": it.time, "title": it.title} for it in items]
            return {"ok": True, "action": "view_plan", "plan": {"id": plan.id, "title": plan.title, "items": out}}

        if intent == Intent.SUGGEST:
            # call recommend_for_cluster_hybrid or fallback LLM suggestion
            suggestions = await recommend_for_cluster_hybrid(user_id)
            return {"ok": True, "action": "suggest", "suggestions": suggestions}

        return {"ok": False, "message": "Mình không hiểu yêu cầu, bạn nói lại được không?"}
