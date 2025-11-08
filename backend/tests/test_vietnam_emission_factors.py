"""
Test Vietnam-specific emission factors
"""
import pytest
import asyncio
from services.carbon_service import CarbonService
from integration.google_map_api import GoogleMapsAPI


@pytest.mark.asyncio
async def test_emission_factors_vietnam():
    """Test emission factors cho Việt Nam"""
    print("\n" + "="*80)
    print("🇻🇳 EMISSION FACTORS FOR VIETNAM")
    print("="*80)
    
    print("\n📊 EMISSION FACTORS (gCO2/km):\n")
    
    categories = {
        "🚗 Private Vehicles": ["car_petrol", "car_diesel", "car_hybrid", "motorbike", "motorbike_small"],
        "🚌 Public Transport": ["bus_standard", "bus_cng", "metro", "train_diesel"],
        "🚴 Active Transport": ["bicycle", "bicycle_electric", "walking"],
        "🚖 Ride-sharing": ["taxi", "grab_car", "grab_bike"]
    }
    
    for category, modes in categories.items():
        print(f"{category}:")
        for mode in modes:
            factor = await CarbonService.get_emission_factor(mode)
            print(f"   {mode:20s}: {factor:6.1f} gCO2/km")
        print()
    
    # Electric vehicles with grid intensity
    print("⚡ ELECTRIC VEHICLES (depends on grid):")
    print(f"   Grid Intensity: {CarbonService.GRID_INTENSITY_VN} gCO2/kWh")
    print()
    
    ev_modes = ["car_electric", "bus_electric", "motorbike_electric"]
    for mode in ev_modes:
        factor = await CarbonService.get_emission_factor(mode)
        efficiency = CarbonService.EV_EFFICIENCY[mode]
        print(f"   {mode:20s}: {factor:6.1f} gCO2/km (efficiency: {efficiency} kWh/km)")
    print()


@pytest.mark.asyncio
async def test_realtime_grid_intensity():
    """Test lấy real-time grid intensity từ Electricity Maps"""
    print("\n" + "="*80)
    print("⚡ REAL-TIME GRID INTENSITY FROM ELECTRICITY MAPS")
    print("="*80)
    
    print(f"\n📍 Zone: Vietnam (VN)")
    print(f"🔑 API Key: {'✅ Available' if hasattr(CarbonService, '_grid_intensity_cache') else '❌ Not configured'}")
    print()
    
    intensity = await CarbonService.get_realtime_grid_intensity("VN")
    
    if intensity:
        print(f"✅ Real-time grid intensity: {intensity} gCO2/kWh")
        print(f"📊 Default (static): {CarbonService.GRID_INTENSITY_VN} gCO2/kWh")
        print(f"📈 Difference: {intensity - CarbonService.GRID_INTENSITY_VN:+.1f} gCO2/kWh")
    else:
        print("⚠️ Could not fetch real-time data, using default")
        print(f"📊 Default: {CarbonService.GRID_INTENSITY_VN} gCO2/kWh")


@pytest.mark.asyncio
async def test_calculate_emission_for_trip():
    """Test tính emission cho một chuyến đi"""
    print("\n" + "="*80)
    print("🧮 CALCULATE EMISSION FOR A TRIP")
    print("="*80)
    
    # Trip: 10km by different modes
    distance = 10
    modes = ["car_petrol", "motorbike", "bus_standard", "metro", "bicycle"]
    
    print(f"\n📏 Distance: {distance} km\n")
    
    for mode in modes:
        result = await CarbonService.calculate_emission_by_mode(distance, mode)
        
        icon = {
            "car_petrol": "🚗",
            "motorbike": "🏍️",
            "bus_standard": "🚌",
            "metro": "🚇",
            "bicycle": "🚴"
        }.get(mode, "🚗")
        
        print(f"{icon} {mode:15s}: {result['co2e_total']:.3f} kg CO₂ ({result['emission_factor_g_per_km']:.0f} g/km)")
    
    print()


@pytest.mark.asyncio
async def test_compare_transport_modes():
    """Test so sánh các phương thức di chuyển"""
    print("\n" + "="*80)
    print("📊 COMPARE TRANSPORT MODES")
    print("="*80)
    
    # Compare for a typical commute: 5km
    distance = 5
    modes = ["car_petrol", "motorbike", "bus_standard", "grab_bike", "bicycle"]
    
    comparison = await CarbonService.compare_transport_modes(distance, modes)
    
    print(f"\n📏 Distance: {distance} km\n")
    print("Ranking (lowest to highest CO₂):")
    print("-" * 60)
    
    sorted_modes = sorted(
        comparison["modes"].items(),
        key=lambda x: x[1]["co2e_total"]
    )
    
    for idx, (mode, data) in enumerate(sorted_modes, 1):
        icon = {
            "car_petrol": "🚗",
            "motorbike": "🏍️",
            "bus_standard": "🚌",
            "grab_bike": "🏍️",
            "bicycle": "🚴"
        }.get(mode, "🚗")
        
        print(f"{idx}. {icon} {mode:15s}: {data['co2e_total']:.3f} kg CO₂")
    
    print()
    print("Summary:")
    print(f"   🌱 Best: {comparison['best_option']['mode']} ({comparison['best_option']['co2_kg']:.3f} kg)")
    print(f"   🔴 Worst: {comparison['worst_option']['mode']} ({comparison['worst_option']['co2_kg']:.3f} kg)")
    print(f"   💚 Savings potential: {comparison['savings_potential_kg']:.3f} kg CO₂")
    print()


@pytest.mark.asyncio
async def test_google_maps_integration():
    """Test integration với Google Maps API"""
    print("\n" + "="*80)
    print("🗺️ GOOGLE MAPS INTEGRATION WITH VIETNAM EMISSION FACTORS")
    print("="*80)
    
    maps = GoogleMapsAPI()
    
    # Test different Google Maps modes
    google_modes = ["driving", "walking", "bicycling", "transit"]
    distance = 10  # km
    
    print(f"\n📏 Distance: {distance} km\n")
    print("Google Maps Mode → Emission Factor:")
    print("-" * 60)
    
    for mode in google_modes:
        carbon = maps._calculate_carbon_emission(distance, mode)
        
        icon = {
            "driving": "🚗",
            "walking": "🚶",
            "bicycling": "🚴",
            "transit": "🚌"
        }.get(mode, "🚗")
        
        print(f"{icon} {mode:15s} → {carbon['emission_mode']:15s}: {carbon['co2_kg']:.3f} kg CO₂")
        print(f"   Factor: {carbon['emission_factor_g_per_km']:.0f} g/km | Source: {carbon['data_source']}")
        print()
    
    await maps.close()


@pytest.mark.asyncio
async def test_emission_comparison_real_route():
    """Test với route thực tế"""
    print("\n" + "="*80)
    print("🎯 REAL ROUTE EMISSION COMPARISON")
    print("="*80)
    
    maps = GoogleMapsAPI()
    
    # Get real route data
    origin = "Chợ Bến Thành, TP.HCM"
    destination = "Bitexco Tower, TP.HCM"
    
    print(f"\n📍 Route: {origin} → {destination}\n")
    
    # Get directions for different modes
    modes = {
        "driving": "🚗 Xe hơi",
        "walking": "🚶 Đi bộ",
        "bicycling": "🚴 Xe đạp",
        "transit": "🚌 Xe bus"
    }
    
    results = []
    
    for mode, display in modes.items():
        try:
            directions = await maps.get_directions(origin, destination, mode=mode)
            
            if directions.get("status") == "OK" and directions.get("routes"):
                leg = directions["routes"][0]["legs"][0]
                distance_km = leg["distance"]["value"] / 1000
                duration_min = leg["duration"]["value"] / 60
                
                # Calculate carbon
                carbon = maps._calculate_carbon_emission(distance_km, mode)
                
                results.append({
                    "mode": mode,
                    "display": display,
                    "distance_km": distance_km,
                    "duration_min": duration_min,
                    "co2_kg": carbon["co2_kg"],
                    "factor": carbon["emission_factor_g_per_km"]
                })
        except Exception as e:
            print(f"⚠️ Error getting directions for {mode}: {e}")
    
    # Display results
    if results:
        print("Results:")
        print("=" * 80)
        
        for r in sorted(results, key=lambda x: x["co2_kg"]):
            print(f"{r['display']:12s}: {r['distance_km']:.2f}km | {r['duration_min']:.0f}min | {r['co2_kg']:.3f}kg CO₂ | {r['factor']:.0f}g/km")
        
        # Calculate savings
        driving_result = next((r for r in results if r["mode"] == "driving"), None)
        if driving_result:
            print("\n💚 Carbon Savings vs Driving:")
            print("-" * 80)
            for r in results:
                if r["mode"] != "driving":
                    saved = driving_result["co2_kg"] - r["co2_kg"]
                    saved_pct = (saved / driving_result["co2_kg"] * 100) if driving_result["co2_kg"] > 0 else 0
                    print(f"{r['display']:12s}: -{saved:.3f}kg CO₂ ({saved_pct:.1f}% reduction)")
    
    await maps.close()


if __name__ == "__main__":
    # Run tests manually
    asyncio.run(test_emission_factors_vietnam())
    asyncio.run(test_realtime_grid_intensity())
    asyncio.run(test_calculate_emission_for_trip())
    asyncio.run(test_compare_transport_modes())
    asyncio.run(test_google_maps_integration())
    asyncio.run(test_emission_comparison_real_route())
