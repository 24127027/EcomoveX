"""
Test chi tiết hơn với các kịch bản đặc biệt:
- Khoảng cách cực ngắn (chỉ nên đi bộ)
- Khoảng cách vừa phải (nên dùng xe công cộng)
- So sánh chi tiết 3 tuyến
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from services.map_service import MapService


async def test_special_cases():
    """Test các trường hợp đặc biệt"""
    
    print("="*100)
    print("🧪 TEST: CÁC KỊCH BẢN ĐẶC BIỆT - TÌM 3 TUYẾN TỐI ƯU")
    print("="*100)
    print()
    
    # Test case: Quãng đường ngắn (~2km) - đủ xa để có transit nhưng đủ gần để đi bộ
    print("█" * 100)
    print("█ TEST CASE: Quãng đường 2-3km (Đủ gần để đi bộ, nhưng transit cũng khả thi)")
    print("█ Mục tiêu: Kiểm tra sự cân bằng giữa 3 lựa chọn")
    print("█" * 100)
    print()
    
    origin = "Nhà hát Thành phố, Hồ Chí Minh"
    destination = "Chợ Bến Thành, Hồ Chí Minh"
    
    print(f"🚩 Điểm xuất phát: {origin}")
    print(f"🎯 Điểm đến: {destination}")
    print()
    
    result = await MapService.find_three_optimal_routes(
        origin=origin,
        destination=destination,
        max_time_ratio=2.0  # Cho phép smart route chậm hơn 2x
    )
    
    if result.get("status") == "OK":
        routes = result.get("routes", {})
        
        # Summary table
        print("┏" + "━" * 98 + "┓")
        print("┃" + " " * 38 + "📊 TỔNG QUAN 3 TUYẾN" + " " * 39 + "┃")
        print("┣" + "━" * 98 + "┫")
        print(f"┃ {'Tuyến':<20} │ {'Phương thức':<20} │ {'Thời gian':<15} │ {'Khoảng cách':<12} │ {'Carbon':<12} ┃")
        print("┣" + "━" * 98 + "┫")
        
        for route_key, route_label in [
            ("fastest", "1️⃣  Nhanh nhất"),
            ("lowest_carbon", "2️⃣  Ít carbon"),
            ("smart_combination", "3️⃣  Thông minh")
        ]:
            if route_key in routes:
                r = routes[route_key]
                mode_display = {
                    "driving": "🚗 Lái xe",
                    "walking": "🚶 Đi bộ",
                    "transit": "🚌 Xe công cộng",
                    "bicycling": "🚴 Đạp xe"
                }.get(r["mode"], r["mode"])
                
                print(f"┃ {route_label:<20} │ {mode_display:<20} │ {r['duration_text']:<15} │ {r['distance_km']:>6.2f} km    │ {r['carbon_kg']:>6.3f} kg  ┃")
        
        print("┗" + "━" * 98 + "┛")
        print()
        
        # Detailed comparison
        print("╔" + "═" * 98 + "╗")
        print("║" + " " * 35 + "📈 PHÂN TÍCH CHI TIẾT" + " " * 42 + "║")
        print("╚" + "═" * 98 + "╝")
        print()
        
        fastest = routes.get("fastest")
        lowest_carbon = routes.get("lowest_carbon")
        smart = routes.get("smart_combination")
        
        if fastest and lowest_carbon:
            print("┌─ So sánh: Nhanh nhất vs Ít carbon ─────────────────────────────────────────┐")
            time_diff = lowest_carbon["duration_min"] - fastest["duration_min"]
            carbon_saved = fastest["carbon_kg"] - lowest_carbon["carbon_kg"]
            carbon_saved_pct = (carbon_saved / fastest["carbon_kg"] * 100) if fastest["carbon_kg"] > 0 else 0
            
            print(f"│ ⏱️  Chênh lệch thời gian: {time_diff:+.1f} phút ({time_diff/fastest['duration_min']*100:+.1f}%)")
            print(f"│ 🌱 Tiết kiệm carbon: {carbon_saved:.3f} kg ({carbon_saved_pct:.1f}%)")
            
            if carbon_saved > 0:
                print(f"│ 📊 Trong 1 năm (365 ngày): {carbon_saved*365:.1f} kg CO2")
                print(f"│ 🌳 Tương đương trồng: {carbon_saved*365/21:.1f} cây xanh/năm")
            
            print("└─────────────────────────────────────────────────────────────────────────────┘")
            print()
        
        if smart:
            print("┌─ Tuyến thông minh ──────────────────────────────────────────────────────────┐")
            print(f"│ Lý do: {smart['reason']}")
            
            if smart.get("time_comparison"):
                tc = smart["time_comparison"]
                print(f"│ ⏱️  So với nhanh nhất: {tc['vs_fastest_min']:+.1f} phút ({tc['vs_fastest_percent']:+.1f}%)")
            
            if smart.get("carbon_comparison"):
                cc = smart["carbon_comparison"]
                print(f"│ 🌱 Tiết kiệm vs lái xe: {cc['vs_driving_kg']:.3f} kg ({cc['vs_driving_percent']:.1f}%)")
            
            # Show transit details if available
            if smart.get("transit_info"):
                ti = smart["transit_info"]
                print(f"│ 🚌 Số chặng xe công cộng: {ti['total_transit_steps']}")
                print(f"│ 🚶 Số đoạn đi bộ: {ti['total_walking_steps']}")
                
                if ti["transit_steps"]:
                    print("│")
                    print("│ Chi tiết các chặng xe:")
                    for i, step in enumerate(ti["transit_steps"], 1):
                        print(f"│   {i}. {step['line']} ({step['vehicle']}) - {step['num_stops']} trạm - {step['duration']}")
            
            print("└─────────────────────────────────────────────────────────────────────────────┘")
            print()
        
        # Recommendation
        print("╔" + "═" * 98 + "╗")
        print("║" + " " * 42 + "💡 KHUYẾN NGHỊ" + " " * 43 + "║")
        print("╚" + "═" * 98 + "╝")
        
        recommendation = result.get("recommendation", {})
        rec_route = recommendation.get("route", "fastest") if isinstance(recommendation, dict) else "fastest"
        rec_reason = recommendation.get("reason", "") if isinstance(recommendation, dict) else ""
        
        rec_names = {
            "fastest": "1️⃣  Tuyến nhanh nhất",
            "lowest_carbon": "2️⃣  Tuyến ít carbon nhất",
            "smart_combination": "3️⃣  Tuyến thông minh"
        }
        
        print()
        print(f"✅ Khuyến nghị: {rec_names.get(rec_route, rec_route)}")
        print(f"📝 Lý do: {rec_reason}")
        print()
        
        # Environmental impact
        if fastest and fastest["carbon_kg"] > 0:
            print("┌─ Tác động môi trường (nếu đi hàng ngày) ────────────────────────────────────┐")
            print(f"│ 🚗 Lái xe mỗi ngày: {fastest['carbon_kg']*365:.1f} kg CO2/năm")
            
            if lowest_carbon:
                print(f"│ 🌱 Tuyến ít carbon: {lowest_carbon['carbon_kg']*365:.1f} kg CO2/năm")
                saved_yearly = (fastest["carbon_kg"] - lowest_carbon["carbon_kg"]) * 365
                print(f"│ 💰 Tiết kiệm: {saved_yearly:.1f} kg CO2/năm ({saved_yearly/1000:.2f} tấn)")
                
                # Real-world comparisons
                trees = saved_yearly / 21  # 1 cây hấp thụ ~21kg CO2/năm
                km_car = saved_yearly / 0.192  # 1km xe hơi ~192g CO2
                
                print(f"│")
                print(f"│ 📊 Tương đương:")
                print(f"│    🌳 Trồng {trees:.1f} cây xanh")
                print(f"│    🚗 Giảm {km_car:.0f} km lái xe")
            
            print("└─────────────────────────────────────────────────────────────────────────────┘")
        
    else:
        print(f"❌ Lỗi: {result.get('message', 'Unknown error')}")
    
    # MapService uses static methods, no need to close
    
    print()
    print("=" * 100)
    print("✅ HOÀN THÀNH TEST")
    print("=" * 100)


if __name__ == "__main__":
    asyncio.run(test_special_cases())
