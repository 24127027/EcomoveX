from typing import Any, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession


class BudgetCheckAgent:
    """Agent kiểm tra ngân sách của plan."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process(self, plan: Any, action: str = "validate") -> Dict[str, Any]:
        """Kiểm tra tổng estimated_cost so với budget_limit."""
        modifications: List[Dict] = []
        warnings: List[str] = []

        if isinstance(plan, dict):
            plan_data = plan
        elif hasattr(plan, "model_dump"):
            plan_data = plan.model_dump()
        else:
            plan_data = {"budget_limit": getattr(plan, "budget_limit", 0), "destinations": []}
            if getattr(plan, "destinations", None):
                for d in plan.destinations:
                    plan_data["destinations"].append({"estimated_cost": getattr(d, "estimated_cost", None)})

        budget = plan_data.get("budget_limit") or 0
        destinations = plan_data.get("destinations", [])

        if budget is None or budget <= 0:
            return {"success": True, "message": "Không có giới hạn ngân sách", "modifications": []}

        total_cost = 0
        missing_cost_count = 0
        
        for d in destinations:
            cost = d.get("estimated_cost") if isinstance(d, dict) else getattr(d, "estimated_cost", 0)
            if cost and cost > 0:
                total_cost += cost
            else:
                missing_cost_count += 1

        if total_cost > budget:
            over_amount = total_cost - budget
            warnings.append(f"Tổng chi phí ({total_cost:,.0f} VND) vượt ngân sách ({budget:,.0f} VND) khoảng {over_amount:,.0f} VND")
            modifications.append({
                "issue": "over_budget",
                "total_cost": total_cost,
                "budget_limit": budget,
                "over_by": over_amount,
                "suggestion": "Giảm bớt điểm đến hoặc tăng ngân sách"
            })
        
        if missing_cost_count > 0:
            warnings.append(f"Có {missing_cost_count} điểm đến chưa có thông tin chi phí")
            modifications.append({"issue": "missing_cost", "count": missing_cost_count, "suggestion": "Bổ sung chi phí ước tính"})
        
        usage_percent = (total_cost / budget * 100) if budget > 0 else 0

        return {
            "success": len(warnings) == 0 or usage_percent < 100,
            "message": "\n".join(warnings) if warnings else f"Ngân sách: {total_cost:,.0f}/{budget:,.0f} VND ({usage_percent:.1f}%)",
            "modifications": modifications,
            "budget_usage": {"total_cost": total_cost, "budget_limit": budget, "usage_percent": usage_percent, "remaining": budget - total_cost}
        }
