from typing import Dict, Any, List, Union


class OpeningHoursAgent:
    def __init__(self, db):
        self.db = db

    async def process(self, plan: Any, action: Any) -> Dict[str, Any]:
        """
        Kiểm tra giờ mở cửa của từng destination trong plan.

        Support:
        - ORM model (plan.destinations)
        - Pydantic model (plan.destinations)
        - Raw dict (plan["destinations"])
        """

        destinations = self._extract_destinations(plan)

        modifications = []
        warnings = []

        for dest in destinations:
            name = dest.get("destination_id", "Unknown")
            opening_hours = dest.get("opening_hours")  # field optional

            if not opening_hours:
                modifications.append({
                    "destination_id": dest.get("id"),
                    "destination_name": name,
                    "issue": "missing opening_hours"
                })
                warnings.append(f"Địa điểm '{name}' chưa có giờ mở cửa.")

        return {
            "success": len(warnings) == 0,
            "message": "\n".join(warnings),
            "modifications": modifications
        }

    # -----------------------------
    # INTERNAL HELPERS
    # -----------------------------
    def _extract_destinations(self, plan: Any) -> List[Dict[str, Any]]:
        """
        Trả về danh sách destination dưới dạng dict.
        Tự động xử lý 3 trường hợp:
        1. plan = ORM object (attribute)
        2. plan = Pydantic model
        3. plan = dict
        """

        # Case 1: dict JSON
        if isinstance(plan, dict):
            return plan.get("destinations", [])

        # Case 2: Pydantic model → convert to dict
        if hasattr(plan, "model_dump"):
            data = plan.model_dump()
            return data.get("destinations", [])

        # Case 3: ORM object
        if hasattr(plan, "destinations"):
            # convert ORM items to dict
            return [self._orm_to_dict(d) for d in plan.destinations]

        return []

    def _orm_to_dict(self, obj: Any) -> Dict[str, Any]:
        """
        Convert ORM to dict safely.
        """
        result = {}
        for field in dir(obj):
            if field.startswith("_"):
                continue
            try:
                value = getattr(obj, field)
                if isinstance(value, (str, int, float, type(None))):
                    result[field] = value
            except:
                pass
        return result
