from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession


class OpeningHoursAgent:
    """Agent kiểm tra giờ mở cửa của các destination trong plan."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process(self, plan: Any, action: str = "validate") -> Dict[str, Any]:
        """Kiểm tra giờ mở cửa của từng destination."""
        if isinstance(plan, dict):
            plan_data = plan
        elif hasattr(plan, "model_dump"):
            plan_data = plan.model_dump()
        else:
            plan_data = {"destinations": []}
            if getattr(plan, "destinations", None):
                for d in plan.destinations:
                    plan_data["destinations"].append({
                        "id": getattr(d, "id", None),
                        "destination_id": getattr(d, "destination_id", None),
                        "name": getattr(d, "name", None),
                        "opening_hours": getattr(d, "opening_hours", None),
                    })

        destinations = plan_data.get("destinations", [])
        if not destinations:
            return {"success": True, "message": "Không có điểm đến để kiểm tra", "modifications": []}

        modifications = []
        checked_count = 0
        missing_count = 0

        for dest in destinations:
            dest_id = dest.get("destination_id") or dest.get("id")
            dest_name = dest.get("name") or dest_id or "Unknown"
            checked_count += 1

            if not dest.get("opening_hours"):
                missing_count += 1
                modifications.append({
                    "destination_id": dest_id,
                    "destination_name": dest_name,
                    "issue": "missing_opening_hours",
                    "suggestion": f"Kiểm tra giờ mở cửa của '{dest_name}'"
                })

        warnings = []
        if missing_count > 0:
            warnings.append(f"Có {missing_count}/{checked_count} điểm đến chưa có thông tin giờ mở cửa")

        return {
            "success": len(warnings) == 0,
            "message": "\n".join(warnings) if warnings else "Tất cả điểm đến đều có giờ mở cửa",
            "modifications": modifications,
            "stats": {"checked": checked_count, "missing_hours": missing_count}
        }
