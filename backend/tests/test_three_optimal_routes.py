"""
Test tìm 3 tuyến đường tối ưu:
1. Tuyến nhanh nhất (shortest time)
2. Tuyến ít carbon nhất (lowest emission)
3. Tuyến thông minh (smart combination: walking + public transport)
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from services.map_service import MapService


def print_route_summary(route: dict, route_name: str):
    """Print route information in a formatted way"""
    print(f"\n{'='*80}")
    print(f"📍 {route_name.upper()}")
    print(f"{'='*80}")
    print(f"Loại tuyến: {route['display_name']}")
    print(f"Lý do: {route['reason']}")
    print(f"\n📊 Thông tin chi tiết:")
    print(f"  • Khoảng cách: {route['distance_km']:.2f} km")
    print(f"  • Thời gian: {route['duration_text']} ({route['duration_min']:.1f} phút)")
    print(f"  • Carbon: {route['carbon_kg']:.3f} kg CO2 ({route['emission_factor']:.0f} g/km)")
    print(f"  • Phương thức: {route['mode']}")
    
    # If transit, show transit details
    if route.get("transit_info"):
        transit_info = route["transit_info"]
        print(f"\n🚌 Chi tiết phương tiện công cộng:")
        print(f"  • Số chặng xe: {transit_info['total_transit_steps']}")
        print(f"  • Số đoạn đi bộ: {transit_info['total_walking_steps']}")
        
        if transit_info["transit_steps"]:
            print(f"\n  Các chặng xe:")
            for i, step in enumerate(transit_info["transit_steps"], 1):
                print(f"    {i}. {step['line']} ({step['vehicle']})")
                print(f"       Từ: {step['departure_stop']}")
                print(f"       Đến: {step['arrival_stop']}")
                print(f"       {step['num_stops']} trạm - {step['duration']}")
    
    # If smart route, show time comparison
    if route.get("time_comparison"):
        comp = route["time_comparison"]
        print(f"\n⏱️  So sánh với tuyến nhanh nhất:")
        print(f"  • Chậm hơn: {comp['vs_fastest_min']:.1f} phút ({comp['vs_fastest_percent']:+.1f}%)")


async def test_three_optimal_routes():
    """Test finding 3 optimal routes"""
    
    print("="*80)
    print("🧪 TEST: TÌM 3 TUYẾN ĐƯỜNG TỐI ƯU")
    print("="*80)
    print()
    
    # Test cases with different distances
    test_cases = [
        {
            "name": "TEST 1: Quãng ngắn trong thành phố (~1km)",
            "origin": "Chợ Bến Thành, Hồ Chí Minh",
            "destination": "Bitexco Financial Tower, Hồ Chí Minh"
        },
        {
            "name": "TEST 2: Quãng trung bình (~5km)",
            "origin": "Sân bay Tân Sơn Nhất, Hồ Chí Minh",
            "destination": "Landmark 81, Hồ Chí Minh"
        },
        {
            "name": "TEST 3: Quãng dài (~15km)",
            "origin": "Trung tâm Hà Nội",
            "destination": "Sân bay Nội Bài, Hà Nội"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{'#'*80}")
        print(f"# {test_case['name']}")
        print(f"# Từ: {test_case['origin']}")
        print(f"# Đến: {test_case['destination']}")
        print(f"{'#'*80}")
        
        try:
            result = await MapService.find_three_optimal_routes(
                origin=test_case["origin"],
                destination=test_case["destination"],
                max_time_ratio=1.3  # Smart route can be max 30% slower than fastest
            )
            
            if result.get("status") != "OK":
                print(f"\n❌ Lỗi: {result.get('message', 'Unknown error')}")
                continue
            
            routes = result.get("routes", {})
            
            # Display all 3 routes
            if "fastest" in routes:
                print_route_summary(routes["fastest"], "1️⃣ TUYẾN NHANH NHẤT")
            
            if "lowest_carbon" in routes:
                print_route_summary(routes["lowest_carbon"], "2️⃣ TUYẾN ÍT CARBON NHẤT")
            
            if "smart_combination" in routes:
                print_route_summary(routes["smart_combination"], "3️⃣ TUYẾN THÔNG MINH")
            else:
                print(f"\n{'='*80}")
                print(f"📍 3️⃣ TUYẾN THÔNG MINH")
                print(f"{'='*80}")
                print("⚠️  Không tìm thấy tuyến thông minh phù hợp")
                print("(Không có xe công cộng hoặc thời gian quá lâu)")
            
            # Show comparison table
            print(f"\n{'='*80}")
            print(f"📊 BẢNG SO SÁNH")
            print(f"{'='*80}")
            print(f"{'Tuyến':<25} {'Thời gian':<15} {'Khoảng cách':<15} {'Carbon':<15}")
            print(f"{'-'*80}")
            
            for route_type, route_name in [
                ("fastest", "Nhanh nhất"),
                ("lowest_carbon", "Ít carbon nhất"),
                ("smart_combination", "Thông minh")
            ]:
                if route_type in routes:
                    route = routes[route_type]
                    print(f"{route_name:<25} {route['duration_text']:<15} {route['distance_km']:.2f} km{'':<8} {route['carbon_kg']:.3f} kg")
            
            # Show recommendation
            print(f"\n{'='*80}")
            print(f"💡 KHUYẾN NGHỊ")
            print(f"{'='*80}")
            recommendation = result.get("recommendation", {})
            rec_route = recommendation.get("route", "fastest") if isinstance(recommendation, dict) else "fastest"
            rec_reason = recommendation.get("reason", "") if isinstance(recommendation, dict) else ""
            
            route_names = {
                "fastest": "Tuyến nhanh nhất",
                "lowest_carbon": "Tuyến ít carbon nhất",
                "smart_combination": "Tuyến thông minh"
            }
            
            print(f"✅ Khuyến nghị: {route_names.get(rec_route, rec_route)}")
            print(f"📝 Lý do: {rec_reason}")
            
            # Show carbon savings
            if "fastest" in routes and "lowest_carbon" in routes:
                fastest = routes["fastest"]
                lowest_carbon = routes["lowest_carbon"]
                
                carbon_saved = fastest["carbon_kg"] - lowest_carbon["carbon_kg"]
                carbon_saved_percent = (carbon_saved / fastest["carbon_kg"] * 100) if fastest["carbon_kg"] > 0 else 0
                time_diff = lowest_carbon["duration_min"] - fastest["duration_min"]
                
                print(f"\n🌱 Tiết kiệm carbon:")
                print(f"  • Nếu chọn tuyến ít carbon: tiết kiệm {carbon_saved:.3f} kg CO2 ({carbon_saved_percent:.1f}%)")
                print(f"  • Tốn thêm thời gian: {time_diff:.1f} phút")
                
                if carbon_saved > 0:
                    print(f"  • Tương đương: {carbon_saved*365:.1f} kg CO2/năm nếu đi hàng ngày")
            
            print(f"\n📈 Tổng số tuyến phân tích: {result.get('total_routes_analyzed', 0)}")
        
        except Exception as e:
            print(f"\n❌ Lỗi khi xử lý: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*80}")
    print("✅ HOÀN THÀNH TEST")
    print(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(test_three_optimal_routes())
