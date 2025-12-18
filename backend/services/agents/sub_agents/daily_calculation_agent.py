from typing import Any, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime, timedelta


class DailyCalculationAgent:
    """Agent validate daily schedule của plan."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _parse_date(self, val: Any):
        if val is None:
            return None
        if isinstance(val, date) and not isinstance(val, datetime):
            return val
        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, str):
            try:
                return datetime.strptime(val.split("T")[0], "%Y-%m-%d").date()
            except:
                pass
        return None

    async def process(self, plan: Any, action: str = "validate") -> Dict[str, Any]:
        """Validate visit_date, order_in_day và kiểm tra ngày trống."""
        modifications: List[Dict] = []
        warnings: List[str] = []

        if isinstance(plan, dict):
            destinations = plan.get("destinations", [])
            start_date = self._parse_date(plan.get("start_date"))
            end_date = self._parse_date(plan.get("end_date"))
        else:
            destinations = getattr(plan, "destinations", []) or []
            start_date = self._parse_date(getattr(plan, "start_date", None))
            end_date = self._parse_date(getattr(plan, "end_date", None))

        if not destinations:
            return {
                "success": False,
                "message": "Kế hoạch chưa có điểm đến nào",
                "modifications": [{"issue": "no_destinations", "suggestion": "Thêm các điểm đến vào kế hoạch"}]
            }

        day_map: Dict[str, List] = {}
        missing_date_count = 0
        missing_order_count = 0

        for idx, d in enumerate(destinations):
            visit_date = d.get("visit_date") if isinstance(d, dict) else getattr(d, "visit_date", None)
            order_in_day = d.get("order_in_day") if isinstance(d, dict) else getattr(d, "order_in_day", None)

            if not visit_date:
                missing_date_count += 1
                modifications.append({
                    "destination_index": idx,
                    "field": "visit_date",
                    "issue": "missing",
                    "suggestion": "Cần chọn ngày tham quan"
                })
                continue

            if order_in_day is None:
                missing_order_count += 1
                modifications.append({
                    "destination_index": idx,
                    "field": "order_in_day",
                    "issue": "missing",
                    "suggestion": "Cần xác định thứ tự tham quan trong ngày"
                })

            day_key = str(visit_date)
            if day_key not in day_map:
                day_map[day_key] = []
            day_map[day_key].append({"index": idx, "dest": d, "order": order_in_day})

        if missing_date_count > 0:
            warnings.append(f"Có {missing_date_count} điểm đến chưa có ngày tham quan")
        if missing_order_count > 0:
            warnings.append(f"Có {missing_order_count} điểm đến chưa có thứ tự trong ngày")

        for day, items in day_map.items():
            seen_orders: Dict[int, int] = {}
            for item in items:
                order = item["order"]
                if order is None:
                    continue
                if order in seen_orders:
                    warnings.append(f"Trùng thứ tự {order} trong ngày {day}")
                    modifications.append({
                        "visit_date": day,
                        "order_in_day": order,
                        "issue": "duplicate_order",
                        "suggestion": "Sắp xếp lại thứ tự tham quan"
                    })
                else:
                    seen_orders[order] = 1

        if start_date and end_date:
            empty_days = []
            cur = start_date
            while cur <= end_date:
                if str(cur) not in day_map:
                    empty_days.append(str(cur))
                cur = cur + timedelta(days=1)

            if empty_days:
                if len(empty_days) <= 3:
                    for day in empty_days:
                        warnings.append(f"Ngày {day} chưa có lịch trình")
                else:
                    warnings.append(f"Có {len(empty_days)} ngày chưa có lịch trình")
                modifications.append({
                    "issue": "empty_days",
                    "days": empty_days,
                    "suggestion": "Thêm hoạt động cho các ngày trống"
                })

        schedule_summary = [
            {"date": day, "count": len(items), "destinations": sorted(items, key=lambda x: x["order"] or 0)}
            for day, items in sorted(day_map.items())
        ]

        return {
            "success": len(warnings) == 0,
            "message": "Lịch trình hợp lệ" if not warnings else "\n".join(warnings),
            "modifications": modifications,
            "schedule_summary": schedule_summary
        }
