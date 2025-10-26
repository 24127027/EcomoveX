# carbon_calculate_service.py
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
# Assuming these imports exist relative to your project structure
from .carbon_calculate_schema import VehicleType, FuelType

class CarbonCalculateService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # Placeholder emission factors (g CO2e/km)
        # In a real app, these would come from the database or a config
        self.emission_factors = {
            VehicleType.car: {
                FuelType.petrol: 170,  # g CO2e/km for average petrol car
                FuelType.diesel: 150, # g CO2e/km for average diesel car
                FuelType.hybrid: 100, # g CO2e/km for average hybrid car
                FuelType.electric: 50, # g CO2e/km for EV (depends on grid, average example)
            },
            VehicleType.bus: {
                FuelType.petrol: 80,  # per passenger-km (average, varies wildly)
                FuelType.diesel: 70,  # per passenger-km
                FuelType.electric: 20, # per passenger-km
                FuelType.none: 0, # Should not happen for bus, but for completeness
            },
            VehicleType.motorbike: {
                FuelType.petrol: 90,  # g CO2e/km for average motorbike
                FuelType.diesel: 80,
            },
            VehicleType.walk_or_cycle: {
                FuelType.none: 0, # Effectively zero direct emissions
            }
        }
        # A quick lookup for fuel types that don't apply to specific vehicles (e.g., petrol bus)
        # This will need refinement for real-world scenarios or strict validation.
        self.valid_fuel_for_vehicle = {
            VehicleType.car: [FuelType.petrol, FuelType.diesel, FuelType.electric, FuelType.hybrid],
            VehicleType.bus: [FuelType.petrol, FuelType.diesel, FuelType.electric], # Assuming some electric buses exist
            VehicleType.motorbike: [FuelType.petrol, FuelType.diesel],
            VehicleType.walk_or_cycle: [FuelType.none],
        }


    async def calculate_single_trip_emission(
        self,
        vehicle_type: VehicleType,
        distance_km: float,
        fuel_type: FuelType
    ) -> float:
        # Basic validation (could be more robust)
        if vehicle_type not in self.emission_factors:
            raise ValueError(f"Unknown vehicle type: {vehicle_type}")

        if fuel_type not in self.emission_factors[vehicle_type]:
            # Handle cases where fuel type might not be relevant or is incorrect for vehicle
            if vehicle_type == VehicleType.walk_or_cycle and fuel_type == FuelType.none:
                # Correct for walk/cycle
                pass
            else:
                raise ValueError(f"Invalid fuel type '{fuel_type}' for vehicle type '{vehicle_type}'")


        # Get the emission factor in g CO2e/km
        emission_factor_g_per_km = self.emission_factors[vehicle_type][fuel_type]

        # Calculate total emission in grams
        total_emission_g = emission_factor_g_per_km * distance_km

        # Convert to kilograms
        total_emission_kg = total_emission_g / 1000

        return total_emission_kg

    # In a real application, you might add methods to fetch emission factors from DB:
    # async def _get_emission_factor_from_db(self, vehicle_type: VehicleType, fuel_type: FuelType) -> float:
    #    # Query your database here using self.db
    #    # Example: factor = await self.db.execute(select(EmissionFactor.value).where(...))
    #    # return factor.scalar_one()
    #    pass