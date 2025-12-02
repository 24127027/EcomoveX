from typing import List
from models.plan import PlanDestination, DestinationType


class PlanValidator:
    @staticmethod
    def validate_plan(destinations: List[PlanDestination]) -> List[str]:
        warnings = []

        if not destinations:
            return ["Lịch trình của bạn đang trống trơn, hãy thêm vài địa điểm nhé."]

        # 1. Kiểm tra số lượng địa điểm (Quá ít điểm đi chơi)
        # Lọc ra những điểm là chỗ chơi (attraction) để đếm
        attractions = [d for d in destinations if d.type == DestinationType.attraction]
        if len(attractions) < 2:
            warnings.append(
                "Lịch trình có vẻ hơi ít chỗ chơi, bạn có muốn mình gợi ý thêm vài địa điểm thú vị gần đó không?"
            )

        # 2. Kiểm tra chỗ ăn uống (Quên chọn chỗ ăn)
        has_food = any(d.type == DestinationType.restaurant for d in destinations)
        if not has_food:
            warnings.append(
                "Mình chưa thấy bạn chọn nhà hàng hay quán cafe nào. Đi chơi nhớ phải nạp năng lượng nhé!"
            )

        # 3. Kiểm tra logic sắp xếp (Ví dụ: Ăn xong mới đi chơi hay đi chơi rồi mới ăn?)
        # (Optional) Logic này tùy biến

        return warnings
