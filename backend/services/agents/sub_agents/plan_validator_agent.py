# sub_agents/plan_validator_agent.py
from typing import Any, Dict, List

class PlanValidatorAgent:
    def __init__(self, db):
        self.db = db

    async def process(self, plan: Any, action: str) -> Dict[str, Any]:
        """
        Validate trip plan trước khi gửi cho main agent hoặc DB.

        Kiểm tra:
        - place_name
        - start/end date hợp lệ
        - danh sách destinations không rỗng
        - mỗi destination phải có id, type, visit_date
        """
        modifications: List[Dict] = []
        warnings: List[str] = []

        # ---- Validate place_name ----
        if not getattr(plan, "place_name", None):
            modifications.append({"field": "place_name", "issue": "missing"})
            warnings.append("Missing: place_name")

        # ---- Validate dates ----
        start = getattr(plan, "start_date", None)
        end = getattr(plan, "end_date", None)

        if not start:
            modifications.append({"field": "start_date", "issue": "missing"})
            warnings.append("Missing: start_date")

        if not end:
            modifications.append({"field": "end_date", "issue": "missing"})
            warnings.append("Missing: end_date")

        if start and end and start > end:
            warnings.append("start_date cannot be after end_date")
            modifications.append({"field": "start_date/end_date", "issue": "invalid_range"})

        # ---- Validate destinations ----
        dests = getattr(plan, "destinations", [])

        if not dests or len(dests) == 0:
            warnings.append("Trip has no destinations")
            modifications.append({"field": "destinations", "issue": "empty"})
        else:
            for idx, d in enumerate(dests):
                if not getattr(d, "destination_id", None):
                    modifications.append({"destination_index": idx, "field": "destination_id", "issue": "missing"})
                    warnings.append(f"Destination {idx} missing destination_id")

                if not getattr(d, "destination_type", None):
                    modifications.append({"destination_index": idx, "field": "destination_type", "issue": "missing"})
                    warnings.append(f"Destination {idx} missing destination_type")

                if not getattr(d, "visit_date", None):
                    modifications.append({"destination_index": idx, "field": "visit_date", "issue": "missing"})
                    warnings.append(f"Destination {idx} missing visit_date")

        return {
            "success": len(warnings) == 0,
            "message": "\n".join(warnings) if warnings else "Plan valid",
            "modifications": modifications
        }
