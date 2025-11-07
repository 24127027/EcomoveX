# Emission Factors Migration Summary

## Overview
Migrated all Vietnam-specific emission factors logic from `integration/emission_factors.py` into `services/carbon_service.py` for better code organization and maintainability.

## What Changed

### ✅ Moved to `services/carbon_service.py`

All emission factor constants, calculations, and API integrations are now centralized in `CarbonService`:

#### 1. **Vietnam-Specific Emission Factors** (gCO2/km)
```python
EMISSION_FACTORS_VN = {
    # Private vehicles
    "car_petrol": 192,
    "car_diesel": 171,
    "car_hybrid": 120,
    "car_electric": 0,  # Calculated from grid
    "motorbike": 84,
    "motorbike_small": 65,
    "motorbike_large": 95,
    
    # Public transport
    "bus_standard": 68,
    "bus_cng": 58,
    "bus_electric": 0,  # Calculated from grid
    
    # Rail
    "metro": 35,
    "train_diesel": 41,
    "train_electric": 27,
    
    # Active transport
    "bicycle": 0,
    "bicycle_electric": 7,
    "walking": 0,
    
    # Shared services
    "taxi": 155,
    "grab_car": 155,
    "grab_bike": 84,
}
```

#### 2. **Grid Carbon Intensity**
- Static default: `GRID_INTENSITY_VN = 519 gCO2/kWh`
- Real-time API integration: `get_realtime_grid_intensity(zone="VN")`
- Uses Electricity Maps API for live data

#### 3. **Electric Vehicle Efficiency** (kWh/km)
```python
EV_EFFICIENCY = {
    "car_electric": 0.20,
    "bus_electric": 1.30,
    "motorbike_electric": 0.03,
    "bicycle_electric": 0.01,
}
```

#### 4. **Mode Mapping**
Maps common transport mode names to emission factor keys:
```python
MODE_MAPPING = {
    "driving": "car_petrol",
    "car": "car_petrol",
    "transit": "bus_standard",
    "bicycle": "bicycle",
    "walking": "walking",
    # ... etc
}
```

#### 5. **New Methods Added to CarbonService**

##### `get_realtime_grid_intensity(zone: str = "VN") -> Optional[float]`
- Fetches real-time carbon intensity from Electricity Maps API
- Updates internal cache
- Returns None if API fails (falls back to static 519 gCO2/kWh)

##### `get_emission_factor_for_mode(mode: str) -> str`
- Maps common mode names to emission factor keys
- Example: "driving" → "car_petrol"

##### `get_emission_factor(mode: str, use_realtime_grid: bool = True) -> float`
- Returns emission factor for a given mode
- For EVs, calculates from grid intensity * efficiency
- For regular vehicles, returns pre-defined factor

##### `calculate_emission_by_mode(distance_km, mode, passengers=1, use_realtime_grid=True) -> Dict`
- Main calculation method using Vietnam-specific factors
- Returns detailed emission breakdown:
  - `total_co2_kg`: Total emissions
  - `per_passenger_co2_kg`: Per-passenger emissions
  - `emission_factor_g_per_km`: Factor used
  - `grid_intensity_used`: Grid intensity for EVs
  - `data_source`: Attribution string

##### `compare_transport_modes(distance_km: float, modes: list) -> Dict`
- Compares multiple transport modes
- Returns best/worst options
- Calculates potential carbon savings

##### `get_all_emission_factors() -> Dict[str, float]`
- Returns all emission factors (static + calculated EV factors)

### ✅ Updated `integration/google_map_api.py`

#### Removed Dependencies
```python
# REMOVED:
from integration.emission_factors import get_emission_factors, get_emission_factor_for_mode
```

#### Updated Method
```python
async def _calculate_carbon_emission(self, distance_km: float, mode: str) -> Dict[str, Any]:
    """
    Calculate carbon emission using Vietnam-specific data from CarbonService
    """
    # Import CarbonService to avoid circular dependency
    from services.carbon_service import CarbonService
    
    # Calculate emission using Vietnam-specific factors
    result = await CarbonService.calculate_emission_by_mode(distance_km, mode)
    
    return {
        "co2_grams": result["total_co2_grams"],
        "co2_kg": result["total_co2_kg"],
        "emission_factor_g_per_km": result["emission_factor_g_per_km"],
        "distance_km": result["distance_km"],
        "mode": mode,
        "emission_mode": result["mode"],  # Actual mode used for calculation
        "data_source": result["data_source"]
    }
```

#### Updated All Method Calls
Changed all calls from synchronous to asynchronous:
```python
# BEFORE:
carbon = self._calculate_carbon_emission(distance_km, "driving")

# AFTER:
carbon = await self._calculate_carbon_emission(distance_km, "driving")
```

### ✅ Backward Compatibility Maintained

The legacy `EMISSION_FACTORS` dictionary (using `VehicleType` and `FuelType` enums) has been **updated** with Vietnam-specific values but kept for compatibility:

```python
EMISSION_FACTORS = {
    (VehicleType.car, FuelType.petrol): 0.192,      # Updated to Vietnam factor
    (VehicleType.car, FuelType.diesel): 0.171,      # Updated to Vietnam factor
    (VehicleType.car, FuelType.electric): 0.104,    # Updated: 0.20 kWh/km * 519 gCO2/kWh
    # ... etc
}
```

The `calculate_carbon_emission(vehicle_type, distance_km, fuel_type)` method still works for existing database records.

## Benefits

### 1. **Centralized Logic**
- All emission calculations in one service
- Easier to maintain and update
- Single source of truth for emission factors

### 2. **Better Code Organization**
- Service layer contains all business logic
- Integration layer (`google_map_api.py`) focuses on API calls
- Clear separation of concerns

### 3. **Consistency**
- Same emission factors used across entire backend
- Both direct carbon tracking and route comparisons use identical data
- Real-time grid updates benefit all features

### 4. **Easier Testing**
- All emission logic can be tested through `CarbonService`
- Mock `CarbonService` methods for integration tests
- No need to maintain separate test files

### 5. **Future Enhancements**
Easy to add new features:
- Time-of-day pricing for EVs
- Seasonal adjustments
- Vehicle-specific factors
- Traffic congestion multipliers

## Data Sources

All emission factors remain sourced from:
1. **Climatiq Data Explorer**: Vietnam transport sector emission factors
2. **Electricity Maps API**: Real-time grid carbon intensity
3. **IPCC 2019 Guidelines**: Standard calculation methodologies

## Migration Checklist

- ✅ Moved all emission factors to `CarbonService`
- ✅ Moved grid intensity constants and API integration
- ✅ Moved EV efficiency data
- ✅ Moved mode mapping logic
- ✅ Created new calculation methods in `CarbonService`
- ✅ Updated `google_map_api.py` to use `CarbonService`
- ✅ Changed all method calls to async/await
- ✅ Updated legacy emission factors with Vietnam data
- ✅ Translated all comments to English
- ✅ Verified no compilation errors
- ✅ Maintained backward compatibility

## Next Steps

1. **Update Tests**: Modify test files to import from `CarbonService` instead of `emission_factors`
2. **Remove Old File**: Delete `integration/emission_factors.py` after confirming all tests pass
3. **Update Documentation**: Update API documentation to reflect new structure
4. **Consider Caching**: Add Redis/memory cache for grid intensity (updates hourly)

## Files Modified

### Created/Modified
- ✅ `services/carbon_service.py` - Added ~300 lines of Vietnam emission logic
- ✅ `integration/google_map_api.py` - Updated to use CarbonService, translated comments

### To Be Updated (Next Steps)
- ⏳ `tests/test_vietnam_emission_factors.py` - Update imports
- ⏳ `tests/test_electricity_maps_api.py` - Update imports
- ⏳ `tests/test_smart_route_comparison.py` - Update imports

### To Be Removed (After Tests Pass)
- ⏳ `integration/emission_factors.py` - Can be deleted once migration complete

---

**Migration completed successfully! ✅**

All emission factor logic is now centralized in `CarbonService` with English comments throughout.
