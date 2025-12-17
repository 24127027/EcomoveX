from typing import Any, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime


class PlanValidatorAgent:
    """Agent validate toàn bộ kế hoạch du lịch."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process(self, plan: Any, action: str = "validate") -> Dict[str, Any]:
        """Validate place_name, dates, destinations."""
        modifications: List[Dict] = []
        warnings: List[str] = []

        if isinstance(plan, dict):
            place_name, start, end = plan.get("place_name"), plan.get("start_date"), plan.get("end_date")
            dests = plan.get("destinations", [])
        elif hasattr(plan, "model_dump"):
            pd = plan.model_dump()
            place_name, start, end = pd.get("place_name"), pd.get("start_date"), pd.get("end_date")
            dests = pd.get("destinations", [])
        else:
            place_name = getattr(plan, "place_name", None)
            start, end = getattr(plan, "start_date", None), getattr(plan, "end_date", None)
            dests = getattr(plan, "destinations", []) or []

        if not place_name:
            modifications.append({"field": "place_name", "issue": "missing", "suggestion": "Đặt tên cho kế hoạch"})
            warnings.append("Thiếu tên kế hoạch")

        if not start:
            modifications.append({"field": "start_date", "issue": "missing", "suggestion": "Chọn ngày bắt đầu"})
            warnings.append("Thiếu ngày bắt đầu")
        if not end:
            modifications.append({"field": "end_date", "issue": "missing", "suggestion": "Chọn ngày kết thúc"})
            warnings.append("Thiếu ngày kết thúc")

        if start and end:
            try:
                s_val = datetime.strptime(start.split("T")[0], "%Y-%m-%d").date() if isinstance(start, str) else (start if isinstance(start, date) else start)
                e_val = datetime.strptime(end.split("T")[0], "%Y-%m-%d").date() if isinstance(end, str) else (end if isinstance(end, date) else end)
                if s_val > e_val:
                    warnings.append("Ngày bắt đầu phải trước ngày kết thúc")
                    modifications.append({"field": "dates", "issue": "invalid_range", "suggestion": "Kiểm tra lại ngày"})
                elif (e_val - s_val).days + 1 > 30:
                    warnings.append(f"Chuyến đi kéo dài {(e_val - s_val).days + 1} ngày - khá dài")
            except:
                pass

        if not dests:
            warnings.append("Kế hoạch chưa có điểm đến nào")
            modifications.append({"field": "destinations", "issue": "empty", "suggestion": "Thêm điểm đến"})
        else:
            missing_id = missing_type = missing_date = 0
            for idx, d in enumerate(dests):
                dest_id = d.get("destination_id") if isinstance(d, dict) else getattr(d, "destination_id", None)
                dest_type = d.get("type") or d.get("destination_type") if isinstance(d, dict) else getattr(d, "type", None) or getattr(d, "destination_type", None)
                visit_date = d.get("visit_date") if isinstance(d, dict) else getattr(d, "visit_date", None)

                if not dest_id:
                    missing_id += 1
                    modifications.append({"destination_index": idx, "field": "destination_id", "issue": "missing"})
                if not dest_type:
                    missing_type += 1
                    modifications.append({"destination_index": idx, "field": "destination_type", "issue": "missing"})
                if not visit_date:
                    missing_date += 1
                    modifications.append({"destination_index": idx, "field": "visit_date", "issue": "missing"})

            if missing_id > 0:
                warnings.append(f"{missing_id} điểm đến thiếu destination_id")
            if missing_type > 0:
                warnings.append(f"{missing_type} điểm đến thiếu loại hình")
            if missing_date > 0:
                warnings.append(f"{missing_date} điểm đến thiếu ngày tham quan")

        is_valid = len(warnings) == 0
        message = f"Kế hoạch hợp lệ - {len(dests)} điểm đến" if is_valid else "\n".join(warnings)

        return {
            "success": is_valid,
            "message": message,
            "modifications": modifications,
            "summary": {
                "place_name": place_name,
                "start_date": str(start) if start else None,
                "end_date": str(end) if end else None,
                "destination_count": len(dests),
                "issue_count": len(warnings)
            }
        }
