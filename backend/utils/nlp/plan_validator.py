from typing import List
from datetime import datetime, timedelta

from models.plan import PlanDestination, DestinationType
from services.route_service import RouteService  # yêu cầu có sẵn
from integration.weather_api import WeatherAPI   # yêu cầu bạn phải có module weather
from services.map_service import MapService  # dùng để check open/close hours (Google Map API)
from schemas.map_schema import PlaceDetailsResponse, PlaceDetailsRequest
from repository.plan_repository import PlanRepository

class PlanValidator:
    """
    Trình kiểm tra lịch trình du lịch.
    Tất cả các bước đều chỉ return LIST cảnh báo, không tự ý sửa dữ liệu.
    """

    @staticmethod
    async def validate_plan(destinations: List[PlanDestination], user_id: int) -> List[str]:
        warnings = []

        if not destinations:
            return ["Lịch trình của bạn đang trống, hãy thêm vài địa điểm nhé!"]

        # ------------------------------------------------------------
        # 1. Kiểm tra số lượng attraction
        # ------------------------------------------------------------
        attractions = [d for d in destinations if d.type == DestinationType.attraction]
        if len(attractions) < 2:
            warnings.append(
                
                "Lịch trình hơi ít điểm vui chơi. Bạn muốn mình đề xuất thêm địa điểm gần đó không?"
            
            )

        # ------------------------------------------------------------
        # 2. Kiểm tra có chọn nơi ăn uống chưa
        # ------------------------------------------------------------
        has_food = any(d.type == DestinationType.restaurant for d in destinations)
        if not has_food:
            warnings.append(
                "Bạn chưa chọn nhà hàng/quán cafe nào. Đi chơi nhớ nạp năng lượng nhé!"
            )

        # ------------------------------------------------------------
        # 3. Kiểm tra thời lượng ước tính
        # (Giả lập rule đơn giản – attraction cần 2–4 giờ, ăn uống cần 1 giờ)
        # ------------------------------------------------------------
        for d in destinations:
            if d.type == DestinationType.attraction:
                if d.estimated_cost is None:
                    pass  # skip
            # (Bạn có thể bổ sung thêm logic duration sau)

        # ------------------------------------------------------------
        # 4. Kiểm tra giờ mở cửa / đóng cửa (Google Maps API), kiểm tra thêm SerpAPI busy hours
        # ------------------------------------------------------------
        for d in destinations:
            try:
                details: PlaceDetailsResponse = await MapService.get_location_details(
                    PlaceDetailsRequest(place_id=d.destination_id)
                )
                if details.opening_hours and hasattr(details.opening_hours, "open_now"):
                    if not details.opening_hours.open_now:
                        warnings.append(
                            f"⚠ Địa điểm {details.name} có thể đang đóng cửa vào thời điểm bạn dự định đi."
                        )
            except Exception:
                pass  # im lặng, không làm bể luồng

        # ------------------------------------------------------------
        # 5. Kiểm tra thời tiết (Weather API)
        # ------------------------------------------------------------
        try:
            first_day = destinations[0].visit_date
            weather = await WeatherAPI.get_weather_forecast(first_day)

            if weather.get("rain_probability", 0) > 60:
                warnings.append(
                    "Dự báo có mưa vào ngày bạn đi. Bạn có muốn điều chỉnh lịch trình hoặc thêm hoạt động trong nhà?"
                )
        except Exception:
            pass

        # ------------------------------------------------------------
        # 6. Kiểm tra khoảng cách di chuyển
        # ------------------------------------------------------------
        try:
            metrics = await RouteService.calculate_trip_metrics(destinations)
            if metrics["total_distance_km"] > 30:
                warnings.append(
                    "Khoảng cách giữa các địa điểm khá xa, bạn có muốn mình tối ưu lại đường đi không?"
                )
        except Exception:
            pass

        # ------------------------------------------------------------
        # 7. Gợi ý sắp xếp các điểm đến hợp lý trong ngày
        # (Gợi ý, không thay đổi thứ tự thực tế)
        # ------------------------------------------------------------
        if len(destinations) > 3:
            warnings.append(
                "Bạn có muốn mình đề xuất thứ tự thăm địa điểm tối ưu theo khoảng cách và thời gian không?"
            )
            
        # ------------------------------------------------------------
        # 8. Kiểm tra budget có đủ không
        # ------------------------------------------------------------
        total_estimated = 0
        for dest in destinations:
            if dest.estimated_cost is not None:
                total_estimated += dest.estimated_cost
            else:
                # nếu dest.estimated_cost = None, cố gắng lấy từ MapService nếu cần
                try:
                    place_details: PlaceDetailsResponse = await MapService.get_location_details(
                        PlaceDetailsRequest(place_id=dest.destination_id)
                    )
                    if place_details.price_level:
                        # giả lập cost theo price_level * 200_000 VNĐ
                        total_estimated += place_details.price_level * 200_000
                except Exception:
                    pass  # nếu lỗi, bỏ qua

        # Lấy budget từ PlanRepository (giả sử có hàm get_user_budget)
        user_budget = await PlanRepository.get_user_budget(user_id)
        if total_estimated > user_budget:
            warnings.append(
                f"Tổng chi phí dự kiến khoảng {total_estimated:,} VNĐ, có thể vượt ngân sách. Bạn muốn tối ưu lại lịch trình?"
            )

        return warnings
