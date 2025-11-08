# Enum Integration Refactoring - Carbon Service

## Overview
Successfully refactored `carbon_service.py` to use centralized enum definitions from `models.route` instead of hardcoded string literals. This improves code maintainability, consistency, and type safety.

## Changes Made

### 1. Import Enums from models.route
```python
from models.route import TransportMode, FuelType
```

### 2. Updated EMISSION_FACTORS_VN Dictionary
**Before:**
```python
EMISSION_FACTORS_VN = {
    "car_petrol": 192,
    "car_diesel": 171,
    "motorbike_petrol": 84,
    # ... etc
}
```

**After:**
```python
EMISSION_FACTORS_VN = {
    f"{TransportMode.car.value}_{FuelType.PETROL.value}": 192,
    f"{TransportMode.car.value}_{FuelType.DIESEL.value}": 171,
    f"{TransportMode.motorbike.value}_{FuelType.PETROL.value}": 84,
    # ... etc
}
```

### 3. Updated MODE_MAPPING Dictionary
**Before:**
```python
MODE_MAPPING = {
    "driving": "car",
    "motorbike": "motorbike",
    # ... etc
}
```

**After:**
```python
MODE_MAPPING = {
    "driving": TransportMode.car.value,
    "motorbike": TransportMode.motorbike.value,
    # ... etc
}
```

### 4. Updated EV_EFFICIENCY Dictionary
**Before:**
```python
EV_EFFICIENCY = {
    "car_electric": 0.20,
    "bus_electric": 1.30,
    # ... etc
}
```

**After:**
```python
EV_EFFICIENCY = {
    f"{TransportMode.car.value}_{FuelType.ELECTRIC.value}": 0.20,
    f"{TransportMode.bus.value}_{FuelType.ELECTRIC.value}": 1.30,
    # ... etc
}
```

### 5. Updated Default Values and Logic
**Before:**
```python
if not fuel_type:
    fuel_type = "petrol"

base_mode = CarbonService.MODE_MAPPING.get(mode_lower, "car")

if base_mode in ["walking", "bicycle", "metro"]:
    # ...
```

**After:**
```python
if not fuel_type:
    fuel_type = FuelType.PETROL.value

base_mode = CarbonService.MODE_MAPPING.get(mode_lower, TransportMode.car.value)

if base_mode in [TransportMode.walking.value, TransportMode.bicycle.value, TransportMode.metro.value]:
    # ...
```

### 6. Updated traffic_affected_modes List
**Before:**
```python
traffic_affected_modes = [
    "car_petrol", "car_gasoline", "car_diesel",
    # ... etc
]
```

**After:**
```python
traffic_affected_modes = [
    f"{TransportMode.car.value}_{FuelType.PETROL.value}",
    f"{TransportMode.car.value}_{FuelType.GASOLINE.value}",
    f"{TransportMode.car.value}_{FuelType.DIESEL.value}",
    # ... etc
]
```

## Bug Fixes

### Fixed Typo in carbon_schema.py
**Before:**
```python
from models.route import FuelType, TransportMode, RouteTyoe
```

**After:**
```python
from models.route import FuelType, TransportMode, RouteType
```

## Benefits

1. **DRY Principle**: Single source of truth for transport modes and fuel types
2. **Type Safety**: Enums provide compile-time checks for valid values
3. **IDE Support**: Autocomplete and refactoring tools work better with enums
4. **Consistency**: All parts of the codebase use the same enum definitions
5. **Maintainability**: Adding new modes/fuel types requires changes in one place only
6. **No Typos**: Using enum values prevents string typo errors

## Testing

Created comprehensive test suite (`test_enum_integration.py`) that verifies:
- ✅ All 7 fuel types calculate correctly (petrol, gasoline, diesel, hybrid, electric, CNG, LPG)
- ✅ All transport modes work with enum values
- ✅ MODE_MAPPING aliases resolve correctly to enum values
- ✅ Traffic multiplier applies correctly to enum-based modes
- ✅ Special cases (electric bicycle) work correctly
- ✅ Dictionary keys use enum values as expected
- ✅ No regressions in emission calculations

## Test Results

```
================================================================================
Testing Enum Integration in Carbon Service
================================================================================

1. Testing Car with All Fuel Types
--------------------------------------------------------------------------------
  PETROL       - Factor:  192.0 gCO2/km (expected:  192.0) - Total: 1.920 kg ✅
  GASOLINE     - Factor:  192.0 gCO2/km (expected:  192.0) - Total: 1.920 kg ✅
  DIESEL       - Factor:  171.0 gCO2/km (expected:  171.0) - Total: 1.710 kg ✅
  HYBRID       - Factor:  120.0 gCO2/km (expected:  120.0) - Total: 1.200 kg ✅
  ELECTRIC     - Factor:  103.8 gCO2/km (expected:  103.8) - Total: 1.038 kg ✅
  CNG          - Factor:  145.0 gCO2/km (expected:  145.0) - Total: 1.450 kg ✅
  LPG          - Factor:  165.0 gCO2/km (expected:  165.0) - Total: 1.650 kg ✅

2. Testing Different Transport Modes (Default Fuel)
--------------------------------------------------------------------------------
  All 7 transport modes tested successfully ✅

3. Testing MODE_MAPPING Aliases
--------------------------------------------------------------------------------
  All 5 aliases tested successfully ✅

4. Testing Traffic Multiplier with Different Fuel Types
--------------------------------------------------------------------------------
  Traffic multiplier correctly applies to all motorized vehicles ✅

5. Testing Special Cases (Electric Bicycle)
--------------------------------------------------------------------------------
  Regular and electric bicycles work correctly ✅

6. Verifying Enum-Based Dictionary Keys
--------------------------------------------------------------------------------
  All enum-based keys exist in dictionaries ✅

================================================================================
ALL TESTS PASSED!
================================================================================
```

## Architecture

### Enum Definitions (models/route.py)
```python
class TransportMode(str, Enum):
    car = "car"
    motorbike = "motorbike"
    bicycle = "bicycle"
    walking = "walking"
    metro = "metro"
    bus = "bus"
    taxi = "taxi"
    grab_car = "grab car"
    grab_bike = "grab bike"
    train = "train"
    
class FuelType(str, Enum):
    PETROL = "petrol"
    GASOLINE = "gasoline"
    DIESEL = "diesel"
    HYBRID = "hybrid"
    ELECTRIC = "electric"
    CNG = "cng"
    LPG = "lpg"
```

### Usage Pattern
1. **Models**: Define enums (TransportMode, FuelType)
2. **Schemas**: Import and use enums for validation
3. **Services**: Import and use enums for business logic
4. **Repositories/Routers**: Use enum values when interacting with database/API

## Files Modified
- ✅ `services/carbon_service.py` - Complete enum integration
- ✅ `schemas/carbon_schema.py` - Fixed typo (RouteTyoe → RouteType)
- ✅ `test_enum_integration.py` - Created comprehensive test suite

## Files Verified (No Changes Needed)
- ✅ `models/route.py` - Already has correct enum definitions
- ✅ Other schemas - Not redefining enums locally

## Verification
- ✅ No Pylance errors
- ✅ All tests pass
- ✅ No regressions in emission calculations
- ✅ Traffic multiplier still works correctly
- ✅ All fuel types calculate correctly
- ✅ All transport modes work as expected

## Future Improvements
1. Consider updating other services to use enums from models.route
2. Add enum validation at API boundary to prevent invalid values
3. Consider using Literal types for additional type safety in function signatures
4. Document enum usage patterns for team in developer guide

## Conclusion
Successfully refactored carbon_service.py to follow DRY principle by using centralized enum definitions. All functionality preserved, no regressions detected, and code is now more maintainable and type-safe.
