from services.agents.planner_agent import PlannerAgent
from services.plan_service import PlanService
from repository.plan_repository import PlanRepository
from schemas.plan_schema import PlanDestinationCreate, PlanDestinationUpdate, PlanUpdate
from models.plan import DestinationType, TimeSlot
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from utils.nlp.rule_engine import Intent


class PlanEditAgent:
    """Agent xử lý các yêu cầu chỉnh sửa plan từ user."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _add_destination(self, user_id: int, plan: Any, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Thêm destination vào plan."""
        destination_id = entities.get("destination_id") or entities.get("location")
        if not destination_id:
            return {"ok": False, "message": "Vui lòng cung cấp địa điểm cần thêm."}
        
        visit_date = entities.get("visit_date") or entities.get("day") or plan.start_date
        dest_data = PlanDestinationCreate(
            destination_id=str(destination_id),
            destination_type=DestinationType.attraction,
            order_in_day=entities.get("order_in_day", 1),
            visit_date=visit_date,
            estimated_cost=entities.get("estimated_cost"),
            note=entities.get("title") or entities.get("note", ""),
            time_slot=entities.get("time_slot", TimeSlot.morning),
        )
        
        try:
            new_dest = await PlanService.add_destination_to_plan(self.db, user_id, plan.id, dest_data)
            return {"ok": True, "action": "add", "message": "Đã thêm địa điểm vào kế hoạch.", "item": {"id": new_dest.id, "destination_id": new_dest.destination_id}}
        except Exception as e:
            return {"ok": False, "message": f"Không thể thêm địa điểm: {str(e)}"}

    async def _remove_destination(self, user_id: int, plan: Any, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Xóa destination khỏi plan."""
        plan_dest_id = entities.get("item_id")
        destination_id = entities.get("destination_id")
        
        if not plan_dest_id and destination_id and plan.destinations:
            for dest in plan.destinations:
                if dest.destination_id == destination_id:
                    plan_dest_id = dest.id
                    break
        
        if not plan_dest_id:
            return {"ok": False, "message": "Vui lòng chỉ định địa điểm cần xóa."}
        
        try:
            success = await PlanRepository.remove_destination_from_plan(self.db, plan_dest_id)
            if success:
                return {"ok": True, "action": "remove", "message": "Đã xóa địa điểm khỏi kế hoạch.", "item_id": plan_dest_id}
            return {"ok": False, "message": "Không tìm thấy địa điểm cần xóa."}
        except Exception as e:
            return {"ok": False, "message": f"Không thể xóa địa điểm: {str(e)}"}

    async def _modify_time(self, user_id: int, plan: Any, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Cập nhật thời gian của destination."""
        destination_id = entities.get("destination_id")
        
        if not destination_id and entities.get("item_id") and plan.destinations:
            item_id = entities.get("item_id")
            for dest in plan.destinations:
                if dest.id == item_id:
                    destination_id = dest.destination_id
                    break
        
        if not destination_id:
            return {"ok": False, "message": "Vui lòng chỉ định địa điểm cần thay đổi thời gian."}
        
        update_data = PlanDestinationUpdate(
            visit_date=entities.get("visit_date") or entities.get("day"),
            order_in_day=entities.get("order_in_day"),
            time_slot=entities.get("time_slot"),
        )
        
        try:
            updated = await PlanRepository.update_plan_destination(self.db, plan.id, destination_id, update_data)
            if updated:
                return {"ok": True, "action": "modify_time", "message": "Đã cập nhật thời gian cho địa điểm."}
            return {"ok": False, "message": "Không thể cập nhật thời gian."}
        except Exception as e:
            return {"ok": False, "message": f"Lỗi khi cập nhật thời gian: {str(e)}"}

    async def _change_budget(self, user_id: int, plan: Any, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Thay đổi budget của plan."""
        budget_info = entities.get("budget")
        if not budget_info:
            return {"ok": False, "message": "Vui lòng cung cấp ngân sách mới."}
        
        budget_amount = budget_info.get("amount") if isinstance(budget_info, dict) else budget_info
        
        try:
            updated_plan = await PlanService.update_plan(self.db, user_id, plan.id, PlanUpdate(budget_limit=budget_amount))
            if updated_plan:
                return {"ok": True, "action": "change_budget", "message": f"Đã cập nhật ngân sách thành {budget_amount:,.0f} VND.", "budget": budget_amount}
            return {"ok": False, "message": "Không thể cập nhật ngân sách."}
        except Exception as e:
            return {"ok": False, "message": f"Lỗi khi cập nhật ngân sách: {str(e)}"}

    async def edit_plan(self, user_id: int, room_id: int, user_text: str, intent: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Xử lý yêu cầu chỉnh sửa plan."""
        plans = await PlanService.get_plans_by_user(self.db, user_id)
        plan = plans[0] if plans else None
        
        if not plan:
            return {"ok": False, "message": "Bạn chưa có kế hoạch nào. Hãy tạo kế hoạch mới trước."}
        
        if not await PlanService.is_member(self.db, user_id, plan.id):
            return {"ok": False, "message": "Bạn không có quyền chỉnh sửa kế hoạch này."}
        
        if intent == Intent.ADD:
            result = await self._add_destination(user_id, plan, entities)
        elif intent == Intent.REMOVE:
            result = await self._remove_destination(user_id, plan, entities)
        elif intent in [Intent.MODIFY_TIME, Intent.MODIFY_DAY]:
            result = await self._modify_time(user_id, plan, entities)
        elif intent == Intent.CHANGE_BUDGET:
            result = await self._change_budget(user_id, plan, entities)
        else:
            result = {"ok": False, "message": "Không hiểu yêu cầu."}
        
        if result.get("ok"):
            from services.agents.planner_agent import PlannerAgent
            result["validation"] = await PlannerAgent(self.db).validate_plan(user_id, plan.id)
            
            updated_plans = await PlanService.get_plans_by_user(self.db, user_id)
            current_plan = next((p for p in updated_plans if p.id == plan.id), None)
            if current_plan:
                result["plan"] = current_plan.model_dump(mode="json")
        
        return result
