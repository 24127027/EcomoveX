# sub_agents/budget_check_agent.py
from typing import Any, Dict, List

class BudgetCheckAgent:
    def __init__(self, db):
        self.db = db

    async def process(self, plan: Any, action: str) -> Dict[str, Any]:
        """
        Check tổng estimated_cost against budget_limit.
        """
        modifications: List[Dict] = []
        warnings: List[str] = []

        budget = getattr(plan, "budget_limit", None)
        destinations = getattr(plan, "destinations", [])

        # Nếu không set budget thì khỏi check
        if not budget:
            return {
                "success": True,
                "message": "No budget limit set",
                "modifications": []
            }

        total_cost = 0
        for d in destinations:
            cost = getattr(d, "estimated_cost", 0)
            if cost:
                total_cost += cost

        # Check over budget
        if total_cost > budget:
            warnings.append(f"Total cost {total_cost} exceeds budget {budget}")
            modifications.append({
                "suggestion": "Reduce destinations, lower estimated_cost, or increase budget_limit"
            })

        return {
            "success": len(warnings) == 0,
            "message": "\n".join(warnings) if warnings else "Budget OK",
            "modifications": modifications
        }
