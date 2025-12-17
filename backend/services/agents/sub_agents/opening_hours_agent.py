from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from services.map_service import MapService
from schemas.map_schema import PlaceDetailsRequest, PlaceDataCategory


class OpeningHoursAgent:
    """Agent kiểm tra giờ mở cửa của các destination trong plan."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process(self, plan: Any, action: str = "validate") -> Dict[str, Any]:
        """Kiểm tra giờ mở cửa của từng destination bằng cách gọi MapService."""
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
                    })

        destinations = plan_data.get("destinations", [])
        if not destinations:
            return {"success": True, "message": "Không có điểm đến để kiểm tra", "modifications": []}

        modifications = []
        checked_count = 0
        missing_count = 0
        closed_count = 0

        for dest in destinations:
            dest_id = dest.get("destination_id") or dest.get("id")
            if not dest_id:
                continue
            
            checked_count += 1
            
            try:
                # Fetch place details from Google Maps API
                import uuid
                place_details = await MapService.get_location_details(
                    PlaceDetailsRequest(
                        place_id=dest_id,
                        session_token=str(uuid.uuid4()),
                        categories=[PlaceDataCategory.BASIC]
                    ),
                    db=self.db
                )
                
                dest_name = place_details.name or dest_id
                
                if not place_details.opening_hours:
                    missing_count += 1
                    modifications.append({
                        "destination_id": dest_id,
                        "destination_name": dest_name,
                        "issue": "missing_opening_hours",
                        "suggestion": f"'{dest_name}' không có thông tin giờ mở cửa"
                    })
                elif not place_details.opening_hours.open_now:
                    closed_count += 1
                    modifications.append({
                        "destination_id": dest_id,
                        "destination_name": dest_name,
                        "issue": "currently_closed",
                        "suggestion": f"'{dest_name}' hiện đang đóng cửa"
                    })
            except Exception as e:
                print(f"Warning: Could not fetch opening hours for {dest_id}: {e}")
                missing_count += 1
                modifications.append({
                    "destination_id": dest_id,
                    "issue": "fetch_error",
                    "suggestion": f"Không thể lấy thông tin giờ mở cửa"
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
