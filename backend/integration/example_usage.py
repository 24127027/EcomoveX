"""
Example: Cách sử dụng Smart Route Comparison trong EcomoveX
"""
import asyncio
from integration.google_map_api import GoogleMapsAPI


async def example_basic_comparison():
    """Example 1: So sánh cơ bản"""
    print("\n" + "="*80)
    print("EXAMPLE 1: SO SÁNH CƠ BẢN")
    print("="*80)
    
    maps = GoogleMapsAPI()
    
    result = await maps.compare_routes_all_options(
        origin="Chợ Bến Thành, TP.HCM",
        destination="Bitexco Tower, TP.HCM"
    )
    
    # Hiển thị summary
    print(f"\n📍 {result['summary']['origin']} → {result['summary']['destination']}")
    print(f"📊 Tìm thấy {result['summary']['total_options']} phương án\n")
    
    # Top 3 recommendations
    print("🏆 TOP 3 RECOMMENDATIONS:\n")
    
    # 1. Fastest
    fastest = result["fastest_route"]
    print(f"1️⃣  ⚡ NHANH NHẤT")
    print(f"    {fastest['mode_display']}")
    print(f"    ⏱️  {fastest['duration_text']} | 📏 {fastest['distance_km']}km | 🌱 {fastest['carbon_emission']['co2_kg']}kg CO₂\n")
    
    # 2. Greenest
    green = result["lowest_carbon_route"]
    print(f"2️⃣  🌱 XANH NHẤT")
    print(f"    {green['mode_display']}")
    print(f"    ⏱️  {green['duration_text']} | 📏 {green['distance_km']}km | 🌱 {green['carbon_emission']['co2_kg']}kg CO₂")
    print(f"    💚 Tiết kiệm {green.get('carbon_saved_vs_driving', 0)}kg CO₂")
    if 'health_benefit' in green:
        print(f"    💪 {green['health_benefit']}\n")
    
    # 3. Smart (if available)
    if result.get("smart_route"):
        smart = result["smart_route"]
        print(f"3️⃣  🧠 THÔNG MINH ⭐")
        print(f"    {smart['mode_display']}")
        print(f"    ⏱️  {smart['duration_text']} | 📏 {smart['distance_km']}km | 🌱 {smart['carbon_emission']['co2_kg']}kg CO₂")
        if 'smart_route_info' in smart:
            info = smart['smart_route_info']
            print(f"    ⚡ Chậm hơn {info['time_difference_minutes']} phút")
            print(f"    💚 Tiết kiệm {info['carbon_saving_percent']}% CO₂")
    else:
        print(f"3️⃣  🧠 THÔNG MINH: Không có (khoảng cách quá ngắn)\n")
    
    await maps.close()


async def example_user_preference():
    """Example 2: Recommendation dựa trên user preference"""
    print("\n" + "="*80)
    print("EXAMPLE 2: RECOMMENDATION DỰA TRÊN USER PREFERENCE")
    print("="*80)
    
    maps = GoogleMapsAPI()
    
    result = await maps.compare_routes_all_options(
        origin="Bitexco Tower, TP.HCM",
        destination="Đại học Khoa học Tự nhiên, TP.HCM",
        max_time_ratio=1.5
    )
    
    # Simulate 3 user types
    user_types = [
        {"name": "Nguyễn Văn A", "preference": "time", "icon": "⚡"},
        {"name": "Trần Thị B", "preference": "eco", "icon": "🌱"},
        {"name": "Lê Văn C", "preference": "balanced", "icon": "🧠"}
    ]
    
    print()
    for user in user_types:
        print(f"\n👤 User: {user['name']} ({user['icon']} Preference: {user['preference']})")
        print("-" * 60)
        
        if user['preference'] == "time":
            recommended = result["fastest_route"]
            print(f"✅ Khuyến nghị: {recommended['highlight']}")
            print(f"   {recommended['mode_display']} - {recommended['duration_text']}")
            print(f"   Lý do: Bạn muốn đến nhanh nhất có thể")
            
        elif user['preference'] == "eco":
            recommended = result["lowest_carbon_route"]
            print(f"✅ Khuyến nghị: {recommended['highlight']}")
            print(f"   {recommended['mode_display']} - {recommended['duration_text']}")
            print(f"   Tiết kiệm: {recommended.get('carbon_saved_vs_driving', 0)}kg CO₂")
            print(f"   Lý do: Bạn ưu tiên bảo vệ môi trường")
            
        else:  # balanced
            if result.get("smart_route"):
                recommended = result["smart_route"]
                print(f"✅ Khuyến nghị: {recommended['highlight']}")
                print(f"   {recommended['mode_display']} - {recommended['duration_text']}")
                info = recommended.get('smart_route_info', {})
                print(f"   Chậm hơn {info.get('time_difference_minutes', 0)} phút")
                print(f"   Nhưng tiết kiệm {info.get('carbon_saving_percent', 0)}% CO₂")
                print(f"   Lý do: Cân bằng hoàn hảo giữa thời gian & môi trường!")
            else:
                recommended = result["fastest_route"]
                print(f"✅ Khuyến nghị: {recommended['highlight']}")
                print(f"   Không có smart route, chọn nhanh nhất")
    
    await maps.close()


async def example_carbon_tracking():
    """Example 3: Track carbon saved"""
    print("\n" + "="*80)
    print("EXAMPLE 3: CARBON TRACKING & GAMIFICATION")
    print("="*80)
    
    # Simulate user trips trong 1 tuần
    trips = [
        {"route": "Nhà → Công ty", "distance_km": 5, "mode_chosen": "transit"},
        {"route": "Công ty → Quán cafe", "distance_km": 2, "mode_chosen": "walking"},
        {"route": "Quán cafe → Gym", "distance_km": 3, "mode_chosen": "bicycling"},
        {"route": "Gym → Nhà", "distance_km": 6, "mode_chosen": "transit"},
        {"route": "Nhà → Siêu thị", "distance_km": 1.5, "mode_chosen": "walking"},
    ]
    
    print("\n📊 TRIPS TUẦN NÀY:\n")
    
    total_carbon_saved = 0
    total_calories = 0
    
    maps = GoogleMapsAPI()
    
    for idx, trip in enumerate(trips, 1):
        # Calculate carbon
        actual_carbon = maps._calculate_carbon_emission(trip["distance_km"], trip["mode_chosen"])
        driving_carbon = maps._calculate_carbon_emission(trip["distance_km"], "driving")
        
        saved = driving_carbon["co2_kg"] - actual_carbon["co2_kg"]
        total_carbon_saved += saved
        
        # Calculate calories (estimated)
        if trip["mode_chosen"] == "walking":
            calories = trip["distance_km"] * 60
            total_calories += calories
            health = f"💪 +{int(calories)} calories"
        elif trip["mode_chosen"] == "bicycling":
            calories = trip["distance_km"] * 120
            total_calories += calories
            health = f"💪 +{int(calories)} calories"
        else:
            health = ""
        
        mode_icons = {
            "driving": "🚗",
            "walking": "🚶",
            "bicycling": "🚴",
            "transit": "🚌"
        }
        
        print(f"{idx}. {trip['route']}")
        print(f"   {mode_icons[trip['mode_chosen']]} {trip['mode_chosen']} - {trip['distance_km']}km")
        print(f"   💚 Tiết kiệm: {saved:.3f}kg CO₂ {health}")
        print()
    
    # Summary
    print("=" * 60)
    print("🏆 THÀNH TÍCH TUẦN NÀY:")
    print("=" * 60)
    print(f"🌱 Tổng carbon tiết kiệm: {total_carbon_saved:.2f} kg CO₂")
    print(f"🌳 Tương đương: {total_carbon_saved / 20:.1f} cây xanh")
    print(f"💪 Calories đốt cháy: {int(total_calories)} calories")
    print(f"⭐ Eco Points: {int(total_carbon_saved * 100)} points")
    
    # Level calculation
    level = int(total_carbon_saved / 5) + 1
    next_level_required = level * 5
    progress = (total_carbon_saved % 5) / 5 * 100
    
    print(f"\n🎖️  Level: {level}")
    print(f"📊 Tiến độ lên level {level + 1}: {progress:.0f}% ({total_carbon_saved:.2f}/{next_level_required}kg)")
    
    # Achievements
    print("\n🏅 HUY HIỆU:")
    if total_carbon_saved >= 5:
        print("   ✅ Eco Warrior - Tiết kiệm 5kg CO₂")
    if total_calories >= 500:
        print("   ✅ Health Champion - Đốt cháy 500 calories")
    if len(trips) >= 5:
        print("   ✅ Frequent Traveler - 5 trips trong tuần")
    
    await maps.close()


async def example_api_response():
    """Example 4: API Response format cho Frontend"""
    print("\n" + "="*80)
    print("EXAMPLE 4: API RESPONSE FORMAT (JSON)")
    print("="*80)
    
    maps = GoogleMapsAPI()
    
    result = await maps.compare_routes_all_options(
        origin="Chợ Bến Thành, TP.HCM",
        destination="Bitexco Tower, TP.HCM"
    )
    
    # Format response cho frontend
    api_response = {
        "status": "success",
        "data": {
            "origin": result["summary"]["origin"],
            "destination": result["summary"]["destination"],
            "total_options": result["summary"]["total_options"],
            
            "recommendations": {
                "fastest": {
                    "type": result["fastest_route"]["type"],
                    "mode": result["fastest_route"]["mode"],
                    "display_name": result["fastest_route"]["mode_display"],
                    "duration": {
                        "minutes": result["fastest_route"]["duration_minutes"],
                        "text": result["fastest_route"]["duration_text"]
                    },
                    "distance": {
                        "km": result["fastest_route"]["distance_km"],
                        "text": f"{result['fastest_route']['distance_km']}km"
                    },
                    "carbon": {
                        "kg": result["fastest_route"]["carbon_emission"]["co2_kg"],
                        "grams": result["fastest_route"]["carbon_emission"]["co2_grams"]
                    },
                    "badge": "⚡ NHANH NHẤT"
                },
                
                "greenest": {
                    "type": result["lowest_carbon_route"]["type"],
                    "mode": result["lowest_carbon_route"]["mode"],
                    "display_name": result["lowest_carbon_route"]["mode_display"],
                    "duration": {
                        "minutes": result["lowest_carbon_route"]["duration_minutes"],
                        "text": result["lowest_carbon_route"]["duration_text"]
                    },
                    "distance": {
                        "km": result["lowest_carbon_route"]["distance_km"]
                    },
                    "carbon": {
                        "kg": result["lowest_carbon_route"]["carbon_emission"]["co2_kg"],
                        "saved_vs_driving": result["lowest_carbon_route"].get("carbon_saved_vs_driving", 0)
                    },
                    "health_benefit": result["lowest_carbon_route"].get("health_benefit", ""),
                    "eco_score": result["lowest_carbon_route"].get("eco_score", 0),
                    "badge": "🌱 XANH NHẤT"
                },
                
                "smart": result["smart_route"] if result.get("smart_route") else None
            },
            
            "all_routes": result["all_options"]
        }
    }
    
    import json
    print("\n📋 JSON Response:\n")
    print(json.dumps(api_response, indent=2, ensure_ascii=False))
    
    await maps.close()


async def main():
    """Run all examples"""
    await example_basic_comparison()
    await example_user_preference()
    await example_carbon_tracking()
    await example_api_response()


if __name__ == "__main__":
    asyncio.run(main())
