# Google Maps API Integration - Carbon Emission Guide

## ✅ System Already Compatible!

The carbon emission system is **already fully compatible** with Google Maps API modes. **NO FUEL TYPE NEEDED!**

## How It Works

### 1. Google Maps API Returns Simple Modes

Google Maps API provides these travel modes:
- `driving` - Car route
- `walking` - Walking route
- `bicycling` - Bicycle route
- `transit` - Public transportation (bus/metro/train)

### 2. Automatic Mapping to Vietnam Emission Factors

The system **automatically maps** Google Maps modes to Vietnam-specific emission factors:

```python
MODE_MAPPING = {
    "driving"   → "car_petrol"    (192 gCO2/km)
    "walking"   → "walking"       (0 gCO2/km)
    "bicycling" → "bicycle"       (0 gCO2/km)
    "transit"   → "bus_standard"  (68 gCO2/km)
}
```

### 3. Usage Examples

#### Example 1: Calculate Emission from Google Maps Route

```python
from services.carbon_service import CarbonService

# Google Maps returns: mode = "driving", distance = 5.5 km
result = await CarbonService.calculate_emission_by_mode(
    distance_km=5.5,
    mode="driving"  # ✅ NO FUEL TYPE NEEDED!
)

print(result)
# {
#     "distance_km": 5.5,
#     "mode": "car_petrol",
#     "emission_factor_g_per_km": 192.0,
#     "total_co2_kg": 1.056,
#     "data_source": "Vietnam-specific (Climatiq + Electricity Maps)"
# }
```

#### Example 2: Compare Multiple Routes

```python
# Google Maps returns 3 routes
routes = [
    {"mode": "driving", "distance_km": 5.5},
    {"mode": "transit", "distance_km": 6.2},
    {"mode": "bicycling", "distance_km": 5.8}
]

# Compare all routes
modes = ["driving", "transit", "bicycling"]
comparison = await CarbonService.compare_transport_modes(5.5, modes)

print(comparison["best_option"])
# {"mode": "bicycling", "co2_kg": 0.0}

print(comparison["worst_option"])
# {"mode": "driving", "co2_kg": 1.056}
```

#### Example 3: Integration with Google Maps API

```python
from integration.google_map_api import GoogleMapsAPI

# Get directions
api = GoogleMapsAPI()
directions = await api.get_directions(
    origin="Bến Thành Market",
    destination="Bitexco Tower",
    mode="driving"
)

# Extract distance from Google Maps response
distance_km = directions["routes"][0]["legs"][0]["distance"]["value"] / 1000

# Calculate carbon emission (NO FUEL TYPE!)
carbon = await CarbonService.calculate_emission_by_mode(
    distance_km=distance_km,
    mode="driving"  # ✅ Direct from Google Maps
)

print(f"CO2 Emission: {carbon['total_co2_kg']} kg")
```

## API Endpoints

### POST /carbon/calculate-by-mode

Calculate emission for a single mode (Google Maps compatible)

**Request:**
```json
{
    "distance_km": 5.5,
    "mode": "driving",
    "passengers": 1,
    "use_realtime_grid": true
}
```

**Response:**
```json
{
    "distance_km": 5.5,
    "mode": "car_petrol",
    "passengers": 1,
    "emission_factor_g_per_km": 192.0,
    "total_co2_grams": 1056.0,
    "total_co2_kg": 1.056,
    "per_passenger_co2_kg": 1.056,
    "data_source": "Vietnam-specific (Climatiq + Electricity Maps)"
}
```

### POST /carbon/compare-modes

Compare multiple transport modes

**Request:**
```json
{
    "distance_km": 5.5,
    "modes": ["driving", "transit", "bicycling", "walking"]
}
```

**Response:**
```json
{
    "distance_km": 5.5,
    "modes": {
        "driving": {"total_co2_kg": 1.056, ...},
        "transit": {"total_co2_kg": 0.374, ...},
        "bicycling": {"total_co2_kg": 0.0, ...},
        "walking": {"total_co2_kg": 0.0, ...}
    },
    "best_option": {"mode": "walking", "co2_kg": 0.0},
    "worst_option": {"mode": "driving", "co2_kg": 1.056},
    "savings_potential_kg": 1.056
}
```

### GET /carbon/modes

Get all supported modes

**Response:**
```json
{
    "google_maps_modes": [
        "driving", "walking", "bicycling", "transit",
        "car", "motorbike", "bus", "metro", "taxi", "grab"
    ],
    "mode_mapping": {
        "driving": "car_petrol",
        "transit": "bus_standard",
        "bicycling": "bicycle",
        "walking": "walking"
    }
}
```

## Supported Modes

### Google Maps Standard Modes (✅ Work directly)
- `driving` → 192 gCO2/km (petrol car)
- `walking` → 0 gCO2/km
- `bicycling` → 0 gCO2/km
- `transit` → 68 gCO2/km (standard bus)

### Vietnam-Specific Modes (✅ Also supported)
- `car_petrol` → 192 gCO2/km
- `car_diesel` → 171 gCO2/km
- `car_hybrid` → 120 gCO2/km
- `car_electric` → ~104 gCO2/km (varies with grid)
- `motorbike` → 84 gCO2/km
- `motorbike_small` → 65 gCO2/km
- `motorbike_large` → 95 gCO2/km
- `bus_standard` → 68 gCO2/km
- `bus_cng` → 58 gCO2/km
- `bus_electric` → ~675 gCO2/km (varies with grid)
- `metro` → 35 gCO2/km
- `train_diesel` → 41 gCO2/km
- `train_electric` → 27 gCO2/km
- `bicycle` → 0 gCO2/km
- `bicycle_electric` → 7 gCO2/km
- `taxi` → 155 gCO2/km
- `grab_car` → 155 gCO2/km
- `grab_bike` → 84 gCO2/km

## Real-World Example

### Bến Thành Market → Bitexco Tower (0.96 km)

| Mode | Duration | CO2 Emission | Factor |
|------|----------|--------------|--------|
| 🚗 Driving | 5 min | 0.184 kg | 192 g/km |
| 🚶 Walking | 13 min | 0.000 kg | 0 g/km |
| 🚴 Bicycling | 4 min | 0.000 kg | 0 g/km |
| 🚌 Transit | 13 min | 0.065 kg | 68 g/km |

**Carbon Savings:**
- Walking vs Driving: **0.184 kg CO2 saved** (100%)
- Transit vs Driving: **0.119 kg CO2 saved** (64.7%)

## Key Features

✅ **No Fuel Type Required** - Just pass the mode from Google Maps
✅ **Automatic Mapping** - Google Maps modes → Vietnam factors
✅ **Real-time Grid Data** - Electric vehicle emissions use live data
✅ **Accurate Vietnam Data** - Climatiq + Electricity Maps sources
✅ **Multi-passenger Support** - Split emissions for shared vehicles
✅ **Mode Comparison** - Compare all route options automatically

## Migration from Old System

If you were using the old system with VehicleType + FuelType enums:

### ❌ Old Way (Complex)
```python
# Required fuel type specification
result = await CarbonService.create_carbon_emission(
    db=db,
    user_id=user_id,
    create_data=CarbonEmissionCreate(
        vehicle_type=VehicleType.car,
        fuel_type=FuelType.petrol,  # ❌ Extra complexity
        distance_km=5.5
    )
)
```

### ✅ New Way (Simple)
```python
# Just use mode from Google Maps
result = await CarbonService.calculate_emission_by_mode(
    distance_km=5.5,
    mode="driving"  # ✅ Direct from API
)
```

## Summary

The carbon emission system is **already optimized** for Google Maps API integration:

1. ✅ **Works with Google Maps modes directly** (driving, walking, bicycling, transit)
2. ✅ **No fuel type specification needed**
3. ✅ **Automatic mapping to Vietnam-specific factors**
4. ✅ **Real-time grid data for electric vehicles**
5. ✅ **Simple API endpoints available**
6. ✅ **Comprehensive mode support**

Just pass the mode from Google Maps API → Get accurate Vietnam emission data! 🎉
