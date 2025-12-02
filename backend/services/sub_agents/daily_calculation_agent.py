# sub_agents/daily_calculation_agent.py
from typing import Any, Dict, List

class DailyCalculationAgent:
    def __init__(self, db):
        self.db = db

    async def process(self, plan: Any, action: str) -> Dict[str, Any]:
        """
        Validate và tính sơ bộ daily schedule.
        Check:
        - mỗi destination phải có visit_date
        - mỗi destination phải có order_in_day
        - trong cùng 1 ngày không được trùng order_in_day
        - ngày nào không có điểm đến -> cảnh báo
        """
        modifications: List[Dict] = []
        warnings: List[str] = []

        destinations = getattr(plan, "destinations", [])
        if not destinations:
            return {
                "success": False,
                "message": "Plan has no destinations",
                "modifications": [{"issue": "no_destinations"}]
            }

        # Group theo ngày
        day_map = {}  # visit_date -> list of destinations

        for idx, d in enumerate(destinations):

            # Missing visit_date
            if not getattr(d, "visit_date", None):
                warnings.append(f"Destination {idx} missing visit_date")
                modifications.append({
                    "destination_index": idx,
                    "field": "visit_date",
                    "issue": "missing"
                })
                continue

            # Missing order_in_day
            if getattr(d, "order_in_day", None) is None:
                warnings.append(f"Destination {idx} missing order_in_day")
                modifications.append({
                    "destination_index": idx,
                    "field": "order_in_day",
                    "issue": "missing"
                })

            # Group for daily schedule
            day = d.visit_date
            if day not in day_map:
                day_map[day] = []
            day_map[day].append(d)

        # ---- Check trùng order trong cùng 1 ngày ----
        for day, items in day_map.items():
            seen_orders = {}
            for d in items:
                order = getattr(d, "order_in_day", None)
                if order is None:
                    continue
                if order in seen_orders:
                    warnings.append(
                        f"Duplicate order_in_day {order} on {day}"
                    )
                    modifications.append({
                        "visit_date": str(day),
                        "order_in_day": order,
                        "issue": "duplicate_order"
                    })
                else:
                    seen_orders[order] = True

        # ---- Check ngày không có destination ----
        if plan.start_date and plan.end_date:
            cur = plan.start_date
            while cur <= plan.end_date:
                if cur not in day_map:
                    warnings.append(f"No destinations scheduled for {cur}")
                    modifications.append({
                        "visit_date": str(cur),
                        "issue": "empty_day"
                    })
                cur = cur.fromordinal(cur.toordinal() + 1)

        return {
            "success": len(warnings) == 0,
            "message": "\n".join(warnings) if warnings else "Daily schedule valid",
            "modifications": modifications
        }
