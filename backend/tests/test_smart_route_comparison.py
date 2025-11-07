"""
Test Smart Route Comparison - So sánh tất cả phương án di chuyển
"""
import pytest
import asyncio
from integration.google_map_api import GoogleMapsAPI


@pytest.mark.asyncio
async def test_compare_all_route_options():
    """Test so sánh tất cả phương án: Nhanh nhất, Carbon thấp nhất, Thông minh"""
    maps = GoogleMapsAPI()
    
    # Test: Bến Thành → Bitexco (khoảng cách ngắn ~ 1-2km)
    result = await maps.compare_routes_all_options(
        origin="Chợ Bến Thành, TP.HCM",
        destination="Bitexco Tower, TP.HCM",
        max_time_ratio=1.5  # Chấp nhận chậm hơn 50%
    )
    
    print("\n" + "="*80)
    print("🎯 SO SÁNH TẤT CẢ PHƯƠNG ÁN DI CHUYỂN")
    print("="*80)
    print(f"📍 Từ: {result['summary']['origin']}")
    print(f"📍 Đến: {result['summary']['destination']}")
    print(f"📊 Tổng số phương án: {result['summary']['total_options']}")
    print()
    
    # 1. Route nhanh nhất
    fastest = result["fastest_route"]
    print(f"⚡ {fastest['highlight']}")
    print(f"   Phương thức: {fastest['mode_display']}")
    print(f"   Khoảng cách: {fastest['distance_km']} km")
    print(f"   Thời gian: {fastest['duration_text']} ({fastest['duration_minutes']} phút)")
    print(f"   Carbon: {fastest['carbon_emission']['co2_kg']} kg CO₂")
    print()
    
    # 2. Route carbon thấp nhất
    lowest_carbon = result["lowest_carbon_route"]
    print(f"🌱 {lowest_carbon['highlight']}")
    print(f"   Phương thức: {lowest_carbon['mode_display']}")
    print(f"   Khoảng cách: {lowest_carbon['distance_km']} km")
    print(f"   Thời gian: {lowest_carbon['duration_text']} ({lowest_carbon['duration_minutes']} phút)")
    print(f"   Carbon: {lowest_carbon['carbon_emission']['co2_kg']} kg CO₂")
    print(f"   💚 Tiết kiệm: {lowest_carbon.get('carbon_saved_vs_driving', 0)} kg CO₂ so với xe hơi")
    if "health_benefit" in lowest_carbon:
        print(f"   💪 Lợi ích sức khỏe: {lowest_carbon['health_benefit']}")
    print()
    
    # 3. Smart route (nếu có)
    if result["smart_route"]:
        smart = result["smart_route"]
        print(f"🧠 {smart['highlight']}")
        print(f"   Phương thức: {smart['mode_display']}")
        print(f"   Khoảng cách: {smart['distance_km']} km")
        print(f"   Thời gian: {smart['duration_text']} ({smart['duration_minutes']} phút)")
        print(f"   Carbon: {smart['carbon_emission']['co2_kg']} kg CO₂")
        
        if "smart_route_info" in smart:
            info = smart["smart_route_info"]
            print(f"   ⏱️  Chậm hơn route nhanh nhất: {info['time_difference_minutes']} phút (x{info['time_ratio']})")
            print(f"   💚 Tiết kiệm carbon: {info['carbon_saving_kg']} kg ({info['carbon_saving_percent']}%)")
            print(f"   ✅ Khuyến nghị: {'CÓ' if info['is_recommended'] else 'KHÔNG'}")
        
        if "transit_details" in smart:
            transit = smart["transit_details"]
            print(f"   🚌 Số chuyến xe bus/tàu: {transit['total_transit_steps']}")
            print(f"   🚶 Số đoạn đi bộ: {transit['total_walking_steps']}")
            
            if transit["transit_steps"]:
                print(f"   📋 Chi tiết:")
                for step in transit["transit_steps"]:
                    print(f"      • {step['vehicle']} {step['line']}: {step['departure_stop']} → {step['arrival_stop']}")
                    print(f"        ({step['num_stops']} trạm, {step['duration']})")
        print()
    else:
        print("🧠 SMART ROUTE: Không có (khoảng cách quá ngắn hoặc transit không khả dụng)")
        print()
    
    # 4. Tất cả options
    print("-" * 80)
    print("📊 TẤT CẢ PHƯƠNG ÁN (sắp xếp theo thời gian):")
    print("-" * 80)
    for idx, option in enumerate(result["all_options"], 1):
        print(f"{idx}. {option['mode_display']}")
        print(f"   ⏱️  {option['duration_text']} | 📏 {option['distance_km']} km | 🌱 {option['carbon_emission']['co2_kg']} kg CO₂")
        if option.get("eco_score"):
            print(f"   🌟 Eco Score: {option['eco_score']}/100")
        print()
    
    await maps.close()
    
    # Assertions
    assert result["fastest_route"] is not None
    assert result["lowest_carbon_route"] is not None
    assert result["lowest_carbon_route"]["carbon_emission"]["co2_kg"] == 0  # Should be walking or biking


@pytest.mark.asyncio
async def test_compare_long_distance_route():
    """Test route dài hơn để thấy smart route shine"""
    maps = GoogleMapsAPI()
    
    # Test: Bến Thành → Sân bay Tân Sơn Nhất (khoảng cách trung bình ~ 8-10km)
    result = await maps.compare_routes_all_options(
        origin="Chợ Bến Thành, TP.HCM",
        destination="Sân bay Tân Sơn Nhất, TP.HCM",
        max_time_ratio=1.3  # Chấp nhận chậm hơn 30%
    )
    
    print("\n" + "="*80)
    print("🎯 SO SÁNH ROUTE DÀI (Bến Thành → Sân bay)")
    print("="*80)
    
    # Hiển thị top 3 recommendations
    print("\n🏆 TOP 3 KHUYẾN NGHỊ:\n")
    
    print(f"1️⃣  {result['fastest_route']['highlight']}")
    print(f"    {result['fastest_route']['mode_display']} - {result['fastest_route']['duration_text']}")
    print(f"    Carbon: {result['fastest_route']['carbon_emission']['co2_kg']} kg CO₂\n")
    
    print(f"2️⃣  {result['lowest_carbon_route']['highlight']}")
    print(f"    {result['lowest_carbon_route']['mode_display']} - {result['lowest_carbon_route']['duration_text']}")
    print(f"    Carbon: {result['lowest_carbon_route']['carbon_emission']['co2_kg']} kg CO₂")
    print(f"    Tiết kiệm: {result['lowest_carbon_route'].get('carbon_saved_vs_driving', 0)} kg CO₂\n")
    
    if result["smart_route"]:
        print(f"3️⃣  {result['smart_route']['highlight']} ⭐ RECOMMENDED")
        print(f"    {result['smart_route']['mode_display']} - {result['smart_route']['duration_text']}")
        print(f"    Carbon: {result['smart_route']['carbon_emission']['co2_kg']} kg CO₂")
        
        if "smart_route_info" in result["smart_route"]:
            info = result["smart_route"]["smart_route_info"]
            print(f"    Chậm hơn {info['time_difference_minutes']} phút nhưng tiết kiệm {info['carbon_saving_percent']}% CO₂")
    
    await maps.close()
    
    assert result["summary"]["total_options"] >= 2


@pytest.mark.asyncio
async def test_carbon_emission_calculator():
    """Test tính carbon emission cho từng phương thức"""
    maps = GoogleMapsAPI()
    
    distance_km = 10  # 10km
    
    print("\n" + "="*80)
    print("🧮 TÍNH CARBON EMISSION CHO 10KM")
    print("="*80)
    
    modes = ["driving", "motorbike", "transit", "bus", "train", "bicycling", "walking"]
    
    for mode in modes:
        carbon = maps._calculate_carbon_emission(distance_km, mode)
        
        icon = {
            "driving": "🚗",
            "motorbike": "🏍️",
            "transit": "🚌",
            "bus": "🚌",
            "train": "🚄",
            "bicycling": "🚴",
            "walking": "🚶"
        }.get(mode, "🚗")
        
        print(f"{icon} {mode.upper()}:")
        print(f"   Carbon: {carbon['co2_kg']} kg ({carbon['co2_grams']} grams)")
        print(f"   Emission factor: {carbon['emission_factor_g_per_km']} g/km")
        print()
    
    await maps.close()


@pytest.mark.asyncio
async def test_display_smart_route_recommendation():
    """Test hiển thị recommendation cho user"""
    maps = GoogleMapsAPI()
    
    result = await maps.compare_routes_all_options(
        origin="Bitexco Tower, TP.HCM",
        destination="Đại học Khoa học Tự nhiên, TP.HCM",
        max_time_ratio=1.5
    )
    
    print("\n" + "="*80)
    print("💡 RECOMMENDATION CHO USER")
    print("="*80)
    
    # Tạo message recommendation
    fastest = result["fastest_route"]
    lowest_carbon = result["lowest_carbon_route"]
    smart = result.get("smart_route")
    
    print(f"\n📍 Bạn muốn đi từ {result['summary']['origin']}")
    print(f"📍 Đến {result['summary']['destination']}\n")
    
    # Recommendation logic
    if smart and smart.get("smart_route_info", {}).get("is_recommended"):
        print("✅ KHUYẾN NGHỊ: SMART ROUTE 🧠")
        print(f"   Đi {smart['mode_display']}")
        print(f"   Thời gian: {smart['duration_text']}")
        print(f"   Tiết kiệm {smart['smart_route_info']['carbon_saving_percent']}% CO₂ so với xe hơi")
        print(f"   Chỉ chậm hơn {smart['smart_route_info']['time_difference_minutes']} phút so với route nhanh nhất")
        print()
        print("   💚 Lý do: Cân bằng hoàn hảo giữa thời gian và môi trường!")
    
    elif lowest_carbon["duration_minutes"] <= fastest["duration_minutes"] * 1.2:
        print("✅ KHUYẾN NGHỊ: GREEN ROUTE 🌱")
        print(f"   Đi {lowest_carbon['mode_display']}")
        print(f"   Thời gian: {lowest_carbon['duration_text']}")
        print(f"   Carbon: 0 kg CO₂")
        print(f"   Tiết kiệm {lowest_carbon.get('carbon_saved_vs_driving', 0)} kg CO₂")
        if "health_benefit" in lowest_carbon:
            print(f"   Bonus: {lowest_carbon['health_benefit']}")
        print()
        print("   💚 Lý do: Tốt cho môi trường VÀ sức khỏe!")
    
    else:
        print("✅ KHUYẾN NGHỊ: FAST ROUTE ⚡")
        print(f"   Đi {fastest['mode_display']}")
        print(f"   Thời gian: {fastest['duration_text']}")
        print(f"   Carbon: {fastest['carbon_emission']['co2_kg']} kg CO₂")
        print()
        print("   ⚠️ Lưu ý: Đây là route nhanh nhất nhưng không thân thiện với môi trường")
        print(f"   💡 Tip: Cân nhắc {lowest_carbon['mode_display']} để giảm {lowest_carbon.get('carbon_saved_vs_driving', 0)} kg CO₂")
    
    print("\n" + "="*80)
    
    await maps.close()


if __name__ == "__main__":
    # Run tests manually
    asyncio.run(test_compare_all_route_options())
    asyncio.run(test_compare_long_distance_route())
    asyncio.run(test_carbon_emission_calculator())
    asyncio.run(test_display_smart_route_recommendation())
