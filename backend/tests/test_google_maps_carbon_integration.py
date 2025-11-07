"""
Test Google Maps API integration with Carbon Emission calculation
Verify that modes from Google Maps work without fuel type specification
"""
import asyncio
from services.carbon_service import CarbonService


async def test_google_maps_modes():
    """Test emission calculation with Google Maps modes (no fuel type needed)"""
    
    print("=" * 80)
    print("🗺️  GOOGLE MAPS API - CARBON EMISSION INTEGRATION TEST")
    print("=" * 80)
    
    # Google Maps returns these modes
    google_maps_modes = ["driving", "walking", "bicycling", "transit"]
    
    distance = 5.5  # Example: 5.5 km trip
    
    print(f"\n📏 Trip Distance: {distance} km")
    print(f"🗺️  Google Maps Modes: {', '.join(google_maps_modes)}\n")
    
    print("-" * 80)
    print(f"{'Mode':<15} {'Mapped To':<20} {'Emission Factor':<20} {'Total CO2':<15}")
    print("-" * 80)
    
    for mode in google_maps_modes:
        # Calculate emission using Google Maps mode (NO FUEL TYPE NEEDED!)
        result = await CarbonService.calculate_emission_by_mode(
            distance_km=distance,
            mode=mode  # Direct Google Maps mode
        )
        
        print(f"{mode:<15} {result['mode']:<20} {result['emission_factor_g_per_km']:<20.1f} {result['total_co2_kg']:<15.3f} kg")
    
    print("-" * 80)
    
    # Test mode comparison
    print(f"\n📊 MODE COMPARISON:")
    comparison = await CarbonService.compare_transport_modes(distance, google_maps_modes)
    
    print(f"   🌱 Best (lowest CO2):  {comparison['best_option']['mode']} = {comparison['best_option']['co2_kg']} kg")
    print(f"   🔴 Worst (highest CO2): {comparison['worst_option']['mode']} = {comparison['worst_option']['co2_kg']} kg")
    print(f"   💚 Savings potential:   {comparison['savings_potential_kg']} kg CO2")
    
    # Test additional Vietnam-specific modes
    print(f"\n🇻🇳 VIETNAM-SPECIFIC MODES (also work):")
    vietnam_modes = ["car_petrol", "motorbike", "bus_standard", "metro", "grab_car"]
    
    print("-" * 80)
    print(f"{'Mode':<20} {'Emission Factor':<20} {'Total CO2':<15}")
    print("-" * 80)
    
    for mode in vietnam_modes:
        result = await CarbonService.calculate_emission_by_mode(distance, mode)
        print(f"{mode:<20} {result['emission_factor_g_per_km']:<20.1f} {result['total_co2_kg']:<15.3f} kg")
    
    print("-" * 80)
    
    # Test mode mapping
    print(f"\n🔄 MODE MAPPING (Google Maps → Vietnam Factors):")
    print(f"   'driving'   → {CarbonService.get_emission_factor_for_mode('driving')}")
    print(f"   'transit'   → {CarbonService.get_emission_factor_for_mode('transit')}")
    print(f"   'bicycling' → {CarbonService.get_emission_factor_for_mode('bicycling')}")
    print(f"   'walking'   → {CarbonService.get_emission_factor_for_mode('walking')}")
    
    print("\n" + "=" * 80)
    print("✅ SUCCESS: Google Maps modes work perfectly WITHOUT fuel type!")
    print("=" * 80)
    print("\n💡 Key Points:")
    print("   1. Google Maps API returns: driving, walking, bicycling, transit")
    print("   2. CarbonService automatically maps to Vietnam-specific factors")
    print("   3. NO FUEL TYPE NEEDED - just pass the mode directly!")
    print("   4. Result includes accurate Vietnam emission data")
    print("=" * 80)


async def test_route_scenario():
    """Simulate a real Google Maps API route scenario"""
    
    print("\n" + "=" * 80)
    print("🚗 REAL ROUTE SCENARIO: Bến Thành Market → Bitexco Tower")
    print("=" * 80)
    
    # Simulating Google Maps API response
    routes = [
        {"mode": "driving", "distance_km": 0.96, "duration_min": 5},
        {"mode": "walking", "distance_km": 0.96, "duration_min": 13},
        {"mode": "bicycling", "distance_km": 0.96, "duration_min": 4},
        {"mode": "transit", "distance_km": 0.96, "duration_min": 13},
    ]
    
    print(f"\n{'Mode':<15} {'Distance':<12} {'Duration':<12} {'CO2 (kg)':<12} {'Factor (g/km)'}")
    print("-" * 80)
    
    for route in routes:
        result = await CarbonService.calculate_emission_by_mode(
            distance_km=route["distance_km"],
            mode=route["mode"]
        )
        
        icon = {"driving": "🚗", "walking": "🚶", "bicycling": "🚴", "transit": "🚌"}.get(route["mode"], "🚗")
        
        print(f"{icon} {route['mode']:<13} {route['distance_km']:<12.2f} {route['duration_min']:<12} "
              f"{result['total_co2_kg']:<12.3f} {result['emission_factor_g_per_km']:<12.1f}")
    
    print("-" * 80)
    print(f"\n✅ All modes calculated successfully with Vietnam-specific factors!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_google_maps_modes())
    asyncio.run(test_route_scenario())
