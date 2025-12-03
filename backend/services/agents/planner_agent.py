from services.agents.sub_agents.opening_hours_agent import OpeningHoursAgent
from services.agents.sub_agents.budget_check_agent import BudgetCheckAgent
from services.agents.sub_agents.daily_calculation_agent import DailyCalculationAgent
from services.agents.sub_agents.plan_validator_agent import PlanValidatorAgent
from integration.text_generator_api import TextGeneratorAPI
from services.plan_service import PlanService
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import json


class PlannerAgent:
    """Agent chính xử lý các yêu cầu liên quan đến plan."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.model = TextGeneratorAPI()
        instruction_path = Path(__file__).parent.parent / "instructions" / "main_agent.txt"
        self.instruction = self._load_instruction(str(instruction_path))
    
    def _load_instruction(self, filepath: str) -> str:
        path = Path(filepath)
        if not path.exists():
            return "You are a travel planning assistant. Help users plan trips efficiently."
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()

    async def _run_sub_agents(self, plan: Union[Any, Dict[str, Any]], action: str = "validate") -> Dict[str, Any]:
        """Chạy tất cả sub-agents để validate plan."""
        warnings, modifications = [], []
        plan_data = self._plan_to_dict(plan)
        
        sub_agents = [
            ("opening_hours", OpeningHoursAgent),
            ("budget", BudgetCheckAgent),
            ("daily_schedule", DailyCalculationAgent),
            ("validator", PlanValidatorAgent),
        ]
        
        for agent_name, agent_cls in sub_agents:
            try:
                res = await agent_cls(self.db).process(plan_data, action)
                if not res.get("success", True):
                    warnings.append({"agent": agent_name, "message": res.get("message", "Unknown issue")})
                if res.get("modifications"):
                    for mod in res["modifications"]:
                        mod["source"] = agent_name
                        modifications.append(mod)
            except Exception as e:
                warnings.append({"agent": agent_name, "message": f"Agent error: {str(e)}"})
        
        return {"warnings": warnings, "modifications": modifications}

    def _plan_to_dict(self, plan: Union[Any, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Convert plan object thành dict."""
        if not plan:
            return None
        if isinstance(plan, dict):
            return plan
        if hasattr(plan, "model_dump"):
            data = plan.model_dump()
            if data.get("destinations"):
                for d in data["destinations"]:
                    if hasattr(d.get("type"), "value"):
                        d["type"] = d["type"].value
                    if hasattr(d.get("time_slot"), "value"):
                        d["time_slot"] = d["time_slot"].value
                    if d.get("visit_date"):
                        d["visit_date"] = str(d["visit_date"])
            if data.get("start_date"):
                data["start_date"] = str(data["start_date"])
            if data.get("end_date"):
                data["end_date"] = str(data["end_date"])
            return data
        
        destinations = []
        if hasattr(plan, "destinations") and plan.destinations:
            for d in plan.destinations:
                dest_dict = {
                    "id": getattr(d, "id", None),
                    "destination_id": getattr(d, "destination_id", None),
                    "type": getattr(d, "type", None),
                    "visit_date": str(getattr(d, "visit_date", "")) if getattr(d, "visit_date", None) else None,
                    "order_in_day": getattr(d, "order_in_day", None),
                    "time_slot": getattr(d, "time_slot", None),
                    "estimated_cost": getattr(d, "estimated_cost", None),
                    "note": getattr(d, "note", None),
                }
                if hasattr(dest_dict["type"], "value"):
                    dest_dict["type"] = dest_dict["type"].value
                if hasattr(dest_dict["time_slot"], "value"):
                    dest_dict["time_slot"] = dest_dict["time_slot"].value
                destinations.append(dest_dict)
        
        return {
            "id": getattr(plan, "id", None),
            "place_name": getattr(plan, "place_name", None),
            "start_date": str(plan.start_date) if getattr(plan, "start_date", None) else None,
            "end_date": str(plan.end_date) if getattr(plan, "end_date", None) else None,
            "budget_limit": getattr(plan, "budget_limit", None),
            "destinations": destinations
        }

    async def validate_plan(self, user_id: int, plan_id: int) -> Dict[str, Any]:
        """Validate một plan cụ thể."""
        plans = await PlanService.get_plans_by_user(self.db, user_id)
        plan = next((p for p in plans if p.id == plan_id), None) if plans else None
        
        if not plan:
            return {"valid": False, "message": "Plan not found"}
        
        result = await self._run_sub_agents(plan, "validate")
        return {"valid": len(result["warnings"]) == 0, "warnings": result["warnings"], "suggestions": result["modifications"]}
    
    async def process_plan(self, user_id: int, room_id: int, user_text: str, action: str = "view") -> Dict[str, Any]:
        """Xử lý yêu cầu liên quan đến plan."""
        plans = await PlanService.get_plans_by_user(self.db, user_id)
        plan = plans[0] if plans else None
        
        if not plan:
            return {"ok": False, "message": "Bạn chưa có kế hoạch du lịch nào. Hãy tạo một kế hoạch mới!"}
        
        agent_results = await self._run_sub_agents(plan, action)
        warnings, modifications = agent_results["warnings"], agent_results["modifications"]
        plan_dict = self._plan_to_dict(plan)
        
        context_messages = [
            {"role": "system", "content": self.instruction},
            {"role": "user", "content": f"User request: {user_text}\n\nCurrent plan: {json.dumps(plan_dict, ensure_ascii=False, indent=2)}"},
        ]
        
        if warnings:
            context_messages.append({"role": "system", "content": f"Warnings:\n" + "\n".join([f"- {w['agent']}: {w['message']}" for w in warnings])})
        if modifications:
            context_messages.append({"role": "system", "content": f"Suggestions:\n{json.dumps(modifications, ensure_ascii=False, indent=2)}"})
        
        try:
            reply = await self.model.generate_reply(context_messages)
        except:
            reply = self._generate_fallback_reply(plan_dict, warnings, modifications)
        
        return {"ok": True, "message": reply, "plan": plan_dict, "warnings": warnings, "modifications": modifications, "intent": "plan_query"}

    def _generate_fallback_reply(self, plan: Dict, warnings: List[Dict], modifications: List[Dict]) -> str:
        """Tạo reply fallback khi LLM không khả dụng."""
        parts = []
        if plan:
            parts.append(f"📍 Kế hoạch: {plan.get('place_name', 'N/A')}")
            parts.append(f"📅 Từ {plan.get('start_date', '?')} đến {plan.get('end_date', '?')}")
            if plan.get('budget_limit'):
                parts.append(f"💰 Ngân sách: {plan['budget_limit']:,.0f} VND")
            if plan.get('destinations'):
                parts.append(f"\n📌 Có {len(plan['destinations'])} điểm đến.")
        if warnings:
            parts.append("\n⚠️ Lưu ý:")
            for w in warnings:
                parts.append(f"  - {w['message']}")
        if modifications:
            parts.append("\n💡 Gợi ý:")
            for m in modifications[:3]:
                parts.append(f"  - {m.get('suggestion') or m.get('issue', '')}")
        return "\n".join(parts) if parts else "Đã xem xét kế hoạch của bạn."
