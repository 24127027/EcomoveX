from fastapi import HTTPException, status
from repository.carbon_repository import CarbonRepository
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.carbon_schema import CarbonEmissionCreate, CarbonEmissionResponse, CarbonEmissionUpdate
from models.carbon import VehicleType, FuelType
from datetime import datetime, timedelta
from integration.text_generator_api import get_text_generator
from integration.climatiq_api import get_climatiq_client
from typing import Dict, Optional
import httpx
from utils.config import settings


class CarbonService:
    """
    Carbon Emission Service for Vietnam
    
    This service provides carbon emission calculations using Vietnam-specific emission factors.
    Data sources:
    1. Climatiq Data Explorer (https://www.climatiq.io/data/explorer?sector=Transport&region=VN)
    2. Electricity Maps API (for real-time grid carbon intensity)
    3. IPCC Guidelines for National Greenhouse Gas Inventories
    """
    
    # Vietnam-specific emission factors (gCO2/km per passenger)
    # Source: Climatiq Data Explorer, IPCC 2019, Vietnam Ministry of Natural Resources and Environment
    # NOTE: These are FALLBACK values. Use refresh_emission_factors() to fetch latest from Climatiq API
    EMISSION_FACTORS_VN = {
        # Private vehicles
        "car_petrol": 192,          # Petrol car (average sedan)
        "car_diesel": 171,          # Diesel car
        "car_hybrid": 120,          # Hybrid car
        "car_electric": 0,          # Electric car (calculated from grid intensity)
        "motorbike": 84,            # Motorbike (125cc average)
        "motorbike_small": 65,      # Small motorbike (<125cc)
        "motorbike_large": 95,      # Large motorbike (>125cc)
        
        # Public transport
        "bus_standard": 68,         # Standard bus (diesel, avg occupancy 20)
        "bus_cng": 58,              # CNG bus
        "bus_electric": 0,          # Electric bus (calculated from grid intensity)
        
        # Rail
        "metro": 35,                # Metro/subway
        "train_diesel": 41,         # Diesel train
        "train_electric": 27,       # Electric train
        
        # Active transport
        "bicycle": 0,               # Bicycle
        "bicycle_electric": 7,      # Electric bicycle
        "walking": 0,               # Walking
        
        # Shared/Taxi services
        "taxi": 155,                # Taxi (assuming 1.5 passengers avg)
        "grab_car": 155,            # GrabCar
        "grab_bike": 84,            # GrabBike
        
        # Default fallbacks (if mode not found)
        "driving": 192,             # Default to petrol car
        "transit": 68,              # Default to standard bus
        "bicycling": 0,             # Bicycling
    }
    
    # Vietnam electricity grid carbon intensity (gCO2/kWh)
    # Source: Electricity Maps & Vietnam EVN (2024 average, coal-heavy grid)
    # Grid composition: 52% coal, 29% hydro, 13% gas, 6% renewable
    GRID_INTENSITY_VN = 519  # gCO2/kWh
    
    # Electric vehicle efficiency (kWh/km per passenger)
    EV_EFFICIENCY = {
        "car_electric": 0.20,       # 20 kWh/100km = 0.20 kWh/km
        "bus_electric": 1.30,       # 130 kWh/100km / 20 passengers = 1.3 kWh/km per passenger
        "motorbike_electric": 0.03, # 3 kWh/100km = 0.03 kWh/km
        "bicycle_electric": 0.01,   # 1 kWh/100km = 0.01 kWh/km
    }
    
    # Mapping from common transport mode names to emission factor keys
    MODE_MAPPING = {
        "driving": "car_petrol",
        "car": "car_petrol",
        "motorbike": "motorbike",
        "motorcycle": "motorbike",
        "transit": "bus_standard",
        "bus": "bus_standard",
        "train": "train_diesel",
        "subway": "metro",
        "metro": "metro",
        "bicycling": "bicycle",
        "bicycle": "bicycle",
        "walking": "walking",
        "walk": "walking",
        "taxi": "taxi",
        "grab": "grab_car",
        "grab_car": "grab_car",
        "grab_bike": "grab_bike",
    }
    
    # Legacy emission factors (kept for backward compatibility with VehicleType/FuelType enums)
    EMISSION_FACTORS = {
        (VehicleType.car, FuelType.petrol): 0.192,      # Updated to Vietnam factor
        (VehicleType.car, FuelType.diesel): 0.171,      # Updated to Vietnam factor
        (VehicleType.car, FuelType.electric): 0.104,    # Updated: 0.20 kWh/km * 519 gCO2/kWh
        (VehicleType.car, FuelType.hybrid): 0.120,      # Updated to Vietnam factor
        (VehicleType.bus, FuelType.petrol): 0.068,      # Updated to Vietnam factor
        (VehicleType.bus, FuelType.diesel): 0.068,      # Updated to Vietnam factor
        (VehicleType.bus, FuelType.electric): 0.675,    # Updated: 1.30 kWh/km * 519 gCO2/kWh
        (VehicleType.bus, FuelType.hybrid): 0.058,      # Updated to Vietnam factor (CNG)
        (VehicleType.motorbike, FuelType.petrol): 0.084, # Updated to Vietnam factor
        (VehicleType.motorbike, FuelType.electric): 0.016, # Updated: 0.03 kWh/km * 519 gCO2/kWh
        (VehicleType.walk_or_cycle, FuelType.none): 0.0,
    }
    
    # Singleton instance for grid intensity tracking
    _grid_intensity_cache = GRID_INTENSITY_VN
    _cache_timestamp = None
    
    # Flag to track if emission factors have been refreshed from Climatiq API
    _factors_refreshed = False

    @staticmethod
    async def refresh_emission_factors(force: bool = False) -> Dict[str, float]:
        """
        Refresh emission factors from Climatiq API
        
        This method fetches the latest emission factors from Climatiq API
        and updates the EMISSION_FACTORS_VN dictionary.
        
        Args:
            force: Force refresh even if already refreshed (default: False)
        
        Returns:
            Dictionary of updated emission factors
        """
        # Skip if already refreshed (unless forced)
        if CarbonService._factors_refreshed and not force:
            return CarbonService.EMISSION_FACTORS_VN
        
        try:
            climatiq = get_climatiq_client()
            
            # Check if API key is available
            if not climatiq.api_key:
                print("⚠️  No Climatiq API key found, using fallback emission factors")
                return CarbonService.EMISSION_FACTORS_VN
            
            # Fetch latest factors from Climatiq API
            fresh_factors = await climatiq.get_vietnam_transport_factors(use_cache=not force)
            
            if fresh_factors and len(fresh_factors) > 2:  # More than just bicycle and walking
                # Update the emission factors
                updated_count = 0
                for mode, factor in fresh_factors.items():
                    if mode in CarbonService.EMISSION_FACTORS_VN:
                        old_value = CarbonService.EMISSION_FACTORS_VN[mode]
                        CarbonService.EMISSION_FACTORS_VN[mode] = factor
                        
                        # Log changes
                        if abs(old_value - factor) > 1:
                            change_pct = ((factor - old_value) / old_value * 100) if old_value > 0 else 0
                            print(f"  📊 {mode}: {old_value} → {factor} gCO2/km ({change_pct:+.1f}%)")
                        
                        updated_count += 1
                
                CarbonService._factors_refreshed = True
                print(f"✅ Emission factors refreshed from Climatiq API ({updated_count} modes updated)")
                return fresh_factors
            else:
                print("⚠️  No sufficient data from Climatiq API, using fallback values")
        
        except Exception as e:
            print(f"❌ Error refreshing emission factors: {e}")
            print("⚠️  Using fallback emission factors")
        
        return CarbonService.EMISSION_FACTORS_VN

    @staticmethod
    async def get_realtime_grid_intensity(zone: str = "VN") -> Optional[float]:
        """
        Get real-time carbon intensity of electricity grid from Electricity Maps API
        
        Args:
            zone: Country/zone code (default: VN for Vietnam)
        
        Returns:
            Carbon intensity in gCO2/kWh, or None if API call fails
        """
        api_key = settings.ELECTRICCITYMAPS_API_KEY if hasattr(settings, 'ELECTRICCITYMAPS_API_KEY') else None
        if not api_key:
            return None
        
        try:
            url = f"https://api.electricitymap.org/v3/carbon-intensity/latest"
            headers = {"auth-token": api_key}
            params = {"zone": zone}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    # carbonIntensity is in gCO2eq/kWh
                    intensity = data.get("carbonIntensity")
                    if intensity:
                        # Update cache
                        CarbonService._grid_intensity_cache = intensity
                        CarbonService._cache_timestamp = datetime.now()
                        return intensity
        except Exception as e:
            print(f"Error fetching grid intensity: {e}")
        
        return None
    
    @staticmethod
    def get_emission_factor_for_mode(mode: str) -> str:
        """
        Map a common transport mode name to the corresponding emission factor key
        
        Args:
            mode: Transport mode name (e.g., "driving", "transit", "bicycling")
        
        Returns:
            Emission factor key for EMISSION_FACTORS_VN dictionary
        """
        return CarbonService.MODE_MAPPING.get(mode.lower(), "car_petrol")
    
    @staticmethod
    async def get_emission_factor(mode: str, use_realtime_grid: bool = True) -> float:
        """
        Get emission factor for a transport mode
        
        Args:
            mode: Transport mode (e.g., "car_petrol", "motorbike", "bus_standard")
            use_realtime_grid: Whether to use real-time grid intensity for electric vehicles
        
        Returns:
            Emission factor in gCO2/km per passenger
        """
        mode_lower = mode.lower()
        
        # Check if it's an electric vehicle
        if mode_lower in CarbonService.EV_EFFICIENCY:
            efficiency = CarbonService.EV_EFFICIENCY[mode_lower]
            
            # Use real-time grid intensity if available
            grid_intensity = CarbonService.GRID_INTENSITY_VN
            if use_realtime_grid:
                realtime_intensity = await CarbonService.get_realtime_grid_intensity()
                if realtime_intensity:
                    grid_intensity = realtime_intensity
            
            return efficiency * grid_intensity
        
        # Return pre-defined factor from Vietnam-specific data
        return CarbonService.EMISSION_FACTORS_VN.get(mode_lower, CarbonService.EMISSION_FACTORS_VN.get("driving", 192))
    
    @staticmethod
    async def calculate_emission_by_mode(
        distance_km: float,
        mode: str,
        passengers: int = 1,
        use_realtime_grid: bool = True
    ) -> Dict[str, any]:
        """
        Calculate carbon emission for a trip using Vietnam-specific emission factors
        
        Args:
            distance_km: Distance in kilometers
            mode: Transport mode (use MODE_MAPPING keys or direct factor keys)
            passengers: Number of passengers (to split emissions for shared vehicles)
            use_realtime_grid: Use real-time grid data for electric vehicles
        
        Returns:
            Dictionary containing:
                - distance_km: Trip distance
                - mode: Transport mode used
                - passengers: Number of passengers
                - emission_factor_g_per_km: Emission factor used
                - total_co2_grams: Total emissions in grams
                - total_co2_kg: Total emissions in kilograms
                - per_passenger_co2_grams: Emissions per passenger in grams
                - per_passenger_co2_kg: Emissions per passenger in kilograms
                - grid_intensity_used: Grid intensity used for EVs (if applicable)
                - data_source: Data source attribution
        """
        # Map mode to emission factor key if needed
        emission_mode = CarbonService.get_emission_factor_for_mode(mode)
        
        # Get emission factor
        factor = await CarbonService.get_emission_factor(emission_mode, use_realtime_grid)
        
        # Calculate total emissions
        total_grams = distance_km * factor
        
        # Per passenger (if shared vehicle)
        per_passenger_grams = total_grams / passengers if passengers > 0 else total_grams
        
        # Check if grid intensity was used
        grid_intensity_used = None
        if emission_mode in CarbonService.EV_EFFICIENCY:
            grid_intensity_used = CarbonService._grid_intensity_cache
        
        return {
            "distance_km": round(distance_km, 2),
            "mode": emission_mode,
            "passengers": passengers,
            "emission_factor_g_per_km": round(factor, 2),
            "total_co2_grams": round(total_grams, 2),
            "total_co2_kg": round(total_grams / 1000, 3),
            "per_passenger_co2_grams": round(per_passenger_grams, 2),
            "per_passenger_co2_kg": round(per_passenger_grams / 1000, 3),
            "grid_intensity_used": grid_intensity_used,
            "data_source": "Vietnam-specific (Climatiq + Electricity Maps)"
        }
    
    @staticmethod
    async def compare_transport_modes(distance_km: float, modes: list) -> Dict[str, any]:
        """
        Compare carbon emissions across multiple transport modes
        
        Args:
            distance_km: Distance in kilometers
            modes: List of transport mode names to compare
        
        Returns:
            Dictionary containing:
                - distance_km: Trip distance
                - modes: Emission details for each mode
                - best_option: Mode with lowest emissions
                - worst_option: Mode with highest emissions
                - savings_potential_kg: Potential carbon savings (worst - best)
        """
        results = {}
        
        for mode in modes:
            results[mode] = await CarbonService.calculate_emission_by_mode(distance_km, mode)
        
        # Find best and worst options
        sorted_modes = sorted(results.items(), key=lambda x: x[1]["total_co2_kg"])
        
        return {
            "distance_km": distance_km,
            "modes": results,
            "best_option": {
                "mode": sorted_modes[0][0],
                "co2_kg": sorted_modes[0][1]["total_co2_kg"]
            },
            "worst_option": {
                "mode": sorted_modes[-1][0],
                "co2_kg": sorted_modes[-1][1]["total_co2_kg"]
            },
            "savings_potential_kg": round(
                sorted_modes[-1][1]["total_co2_kg"] - sorted_modes[0][1]["total_co2_kg"],
                3
            )
        }
    
    @staticmethod
    def get_all_emission_factors() -> Dict[str, float]:
        """
        Get all Vietnam-specific emission factors including calculated EV factors
        
        Returns:
            Dictionary of all emission factors (mode -> gCO2/km)
        """
        all_factors = CarbonService.EMISSION_FACTORS_VN.copy()
        
        # Add calculated EV factors using current grid intensity
        for mode, efficiency in CarbonService.EV_EFFICIENCY.items():
            all_factors[mode] = round(efficiency * CarbonService._grid_intensity_cache, 2)
        
        return all_factors

    @staticmethod
    def calculate_carbon_emission(vehicle_type: VehicleType, distance_km: float, fuel_type: FuelType) -> float:
        """
        Calculate carbon emission using legacy VehicleType/FuelType enums
        (Kept for backward compatibility with existing database records)
        
        Args:
            vehicle_type: Type of vehicle (from VehicleType enum)
            distance_km: Distance in kilometers
            fuel_type: Type of fuel (from FuelType enum)
        
        Returns:
            Carbon emission in kilograms
        """
        emission_factor = CarbonService.EMISSION_FACTORS.get((vehicle_type, fuel_type), 0.0)
        return round(emission_factor * distance_km, 3)
    
    @staticmethod
    async def create_carbon_emission(db: AsyncSession, user_id: int, create_data: CarbonEmissionCreate):
        try:
            carbon_emission_kg = CarbonService.calculate_carbon_emission(
                create_data.vehicle_type,
                create_data.distance_km,
                create_data.fuel_type
            )
            new_emission = await CarbonRepository.create_carbon_emission(db, user_id, create_data, carbon_emission_kg)
            if not new_emission:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create carbon emission record"
                )
            return new_emission
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error creating carbon emission record: {e}"
            )
    
    @staticmethod
    async def get_carbon_emission_by_id(db: AsyncSession, emission_id: int, user_id: int):
        try:
            emission = await CarbonRepository.get_carbon_emission_by_id(db, emission_id, user_id)
            if not emission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Carbon emission record with ID {emission_id} not found"
                )
            return emission
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving carbon emission ID {emission_id}: {e}"
            )

    @staticmethod
    async def get_user_carbon_emissions(db: AsyncSession, user_id: int):
        try:
            emissions = await CarbonRepository.get_carbon_emissions_by_user(db, user_id)
            return emissions
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving carbon emissions for user ID {user_id}: {e}"
            )

    @staticmethod
    async def get_total_carbon_by_user(db: AsyncSession, user_id: int):
        try:
            total = await CarbonRepository.get_total_carbon_by_user(db, user_id)
            return {"user_id": user_id, "total_carbon_emission_kg": total}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error calculating total carbon emissions for user ID {user_id}: {e}"
            )

    @staticmethod
    async def get_total_carbon_by_day(db: AsyncSession, user_id: int, date: datetime):
        try:
            current_emissions = await CarbonRepository.get_carbon_emissions_by_user(db, user_id)
            current_day_data = [
                {
                    "vehicle_type": e.vehicle_type.value,
                    "fuel_type": e.fuel_type.value,
                    "distance_km": e.distance_km,
                    "carbon_emission_kg": e.carbon_emission_kg,
                    "calculated_at": e.calculated_at.isoformat()
                }
                for e in current_emissions if e.calculated_at.date() == date.date()
            ]
            
            previous_date = date - timedelta(days=1)
            previous_day_data = [
                {
                    "vehicle_type": e.vehicle_type.value,
                    "fuel_type": e.fuel_type.value,
                    "distance_km": e.distance_km,
                    "carbon_emission_kg": e.carbon_emission_kg,
                    "calculated_at": e.calculated_at.isoformat()
                }
                for e in current_emissions if e.calculated_at.date() == previous_date.date()
            ]
            
            text_generator = get_text_generator()
            prompt = f"""Analyze the following carbon emission data and provide a summary with a motivational message:

                Time Range: Daily comparison
                Current Day: {date.strftime("%Y-%m-%d")}
                Previous Day: {previous_date.strftime("%Y-%m-%d")}

                Current Day Data ({len(current_day_data)} trips):
                {current_day_data}

                Previous Day Data ({len(previous_day_data)} trips):
                {previous_day_data}

                Instructions:
                1. Calculate the total emissions for each day
                2. Compare the two days and determine the percentage change
                3. Analyze the types of transportation used
                4. Generate a short personalized message (2-3 sentences) that:
                - If emissions decreased: Congratulate the user and encourage them to keep it up
                - If emissions increased: Gently remind them and suggest eco-friendly alternatives
                - If emissions stayed the same: Encourage them to try reducing further
                5. Include specific insights about their travel patterns if relevant

                Format your response as a brief, friendly message."""

            summary_message = await text_generator.generate_text(prompt)
            
            return {
                "user_id": user_id,
                "date": date.strftime("%Y-%m-%d"),
                "summary": summary_message
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error calculating total carbon emissions for user ID {user_id} for day of {date}: {e}"
            )

    @staticmethod
    async def get_total_carbon_by_week(db: AsyncSession, user_id: int, date: datetime):
        try:
            start_of_week = date - timedelta(days=date.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            
            start_of_previous_week = start_of_week - timedelta(days=7)
            end_of_previous_week = start_of_previous_week + timedelta(days=6)
            
            current_emissions = await CarbonRepository.get_carbon_emissions_by_user(db, user_id)
            
            current_week_data = [
                {
                    "vehicle_type": e.vehicle_type.value,
                    "fuel_type": e.fuel_type.value,
                    "distance_km": e.distance_km,
                    "carbon_emission_kg": e.carbon_emission_kg,
                    "calculated_at": e.calculated_at.isoformat()
                }
                for e in current_emissions 
                if start_of_week.date() <= e.calculated_at.date() <= end_of_week.date()
            ]
            
            previous_week_data = [
                {
                    "vehicle_type": e.vehicle_type.value,
                    "fuel_type": e.fuel_type.value,
                    "distance_km": e.distance_km,
                    "carbon_emission_kg": e.carbon_emission_kg,
                    "calculated_at": e.calculated_at.isoformat()
                }
                for e in current_emissions 
                if start_of_previous_week.date() <= e.calculated_at.date() <= end_of_previous_week.date()
            ]
            
            text_generator = get_text_generator()
            prompt = f"""Analyze the following carbon emission data and provide a summary with a motivational message:

                Time Range: Weekly comparison
                Current Week: {start_of_week.strftime("%Y-%m-%d")} to {end_of_week.strftime("%Y-%m-%d")}
                Previous Week: {start_of_previous_week.strftime("%Y-%m-%d")} to {end_of_previous_week.strftime("%Y-%m-%d")}

                Current Week Data ({len(current_week_data)} trips):
                {current_week_data}

                Previous Week Data ({len(previous_week_data)} trips):
                {previous_week_data}

                Instructions:
                1. Calculate the total emissions for each week
                2. Compare the two weeks and determine the percentage change
                3. Analyze the patterns: most common transportation types, daily distribution, etc.
                4. Generate a short personalized message (2-3 sentences) that:
                - If emissions decreased: Celebrate their eco-friendly choices and motivate them to continue
                - If emissions increased: Suggest sustainable alternatives like public transportation, walking, or combining trips
                - If emissions stayed the same: Challenge them to reduce it next week
                5. Provide actionable insights based on their weekly travel patterns

                Format your response as a brief, encouraging message."""

            summary_message = await text_generator.generate_text(prompt)
            
            return {
                "user_id": user_id,
                "week_starting": start_of_week.strftime("%Y-%m-%d"),
                "week_ending": end_of_week.strftime("%Y-%m-%d"),
                "summary": summary_message
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error calculating total carbon emissions for user ID {user_id} for week of {date}: {e}"
            )
        
    @staticmethod
    async def get_total_carbon_by_month(db: AsyncSession, user_id: int, date: datetime):
        try:
            start_of_month = datetime(date.year, date.month, 1)
            if date.month == 12:
                end_of_month = datetime(date.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_of_month = datetime(date.year, date.month + 1, 1) - timedelta(days=1)
            
            if date.month == 1:
                start_of_previous_month = datetime(date.year - 1, 12, 1)
                end_of_previous_month = datetime(date.year - 1, 12, 31)
            else:
                start_of_previous_month = datetime(date.year, date.month - 1, 1)
                end_of_previous_month = datetime(date.year, date.month, 1) - timedelta(days=1)
            
            current_emissions = await CarbonRepository.get_carbon_emissions_by_user(db, user_id)
            
            current_month_data = [
                {
                    "vehicle_type": e.vehicle_type.value,
                    "fuel_type": e.fuel_type.value,
                    "distance_km": e.distance_km,
                    "carbon_emission_kg": e.carbon_emission_kg,
                    "calculated_at": e.calculated_at.isoformat()
                }
                for e in current_emissions 
                if start_of_month.date() <= e.calculated_at.date() <= end_of_month.date()
            ]
            
            previous_month_data = [
                {
                    "vehicle_type": e.vehicle_type.value,
                    "fuel_type": e.fuel_type.value,
                    "distance_km": e.distance_km,
                    "carbon_emission_kg": e.carbon_emission_kg,
                    "calculated_at": e.calculated_at.isoformat()
                }
                for e in current_emissions 
                if start_of_previous_month.date() <= e.calculated_at.date() <= end_of_previous_month.date()
            ]
            
            text_generator = get_text_generator()
            prompt = f"""Analyze the following carbon emission data and provide a summary with a motivational message:

                Time Range: Monthly comparison
                Current Month: {start_of_month.strftime("%B %Y")} ({start_of_month.strftime("%Y-%m-%d")} to {end_of_month.strftime("%Y-%m-%d")})
                Previous Month: {start_of_previous_month.strftime("%B %Y")} ({start_of_previous_month.strftime("%Y-%m-%d")} to {end_of_previous_month.strftime("%Y-%m-%d")})

                Current Month Data ({len(current_month_data)} trips):
                {current_month_data}

                Previous Month Data ({len(previous_month_data)} trips):
                {previous_month_data}

                Instructions:
                1. Calculate the total emissions for each month
                2. Compare the two months and determine the percentage change
                3. Analyze monthly patterns: preferred transportation modes, peak emission days, trends
                4. Generate a short personalized message (2-3 sentences) that:
                - If emissions decreased: Praise their commitment to sustainability and inspire them to maintain this trend
                - If emissions increased: Suggest planning eco-friendly travel routes, using greener transportation, or tracking daily emissions more carefully
                - If emissions stayed the same: Encourage them to set new reduction goals for next month
                5. Provide monthly insights and actionable recommendations

                Format your response as a brief, motivational message."""

            summary_message = await text_generator.generate_text(prompt)
            
            return {
                "user_id": user_id,
                "month": f"{date.year}-{date.month:02d}",
                "summary": summary_message
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error calculating total carbon emissions for user ID {user_id} for month {date.month}/{date.year}: {e}"
            )

    @staticmethod
    async def get_total_carbon_by_year(db: AsyncSession, user_id: int, year: int):
        try:
            current_emissions = await CarbonRepository.get_carbon_emissions_by_user(db, user_id)
            
            current_year_data = [
                {
                    "vehicle_type": e.vehicle_type.value,
                    "fuel_type": e.fuel_type.value,
                    "distance_km": e.distance_km,
                    "carbon_emission_kg": e.carbon_emission_kg,
                    "calculated_at": e.calculated_at.isoformat()
                }
                for e in current_emissions 
                if e.calculated_at.year == year
            ]
            
            previous_year = year - 1
            previous_year_data = [
                {
                    "vehicle_type": e.vehicle_type.value,
                    "fuel_type": e.fuel_type.value,
                    "distance_km": e.distance_km,
                    "carbon_emission_kg": e.carbon_emission_kg,
                    "calculated_at": e.calculated_at.isoformat()
                }
                for e in current_emissions 
                if e.calculated_at.year == previous_year
            ]
            
            text_generator = get_text_generator()
            prompt = f"""Analyze the following carbon emission data and provide a summary with a motivational message:

                Time Range: Annual comparison
                Current Year: {year}
                Previous Year: {previous_year}

                Current Year Data ({len(current_year_data)} trips):
                {current_year_data}

                Previous Year Data ({len(previous_year_data)} trips):
                {previous_year_data}

                Instructions:
                1. Calculate the total emissions for each year
                2. Compare the two years and determine the percentage change
                3. Analyze annual patterns: seasonal trends, most/least eco-friendly months, transportation preferences
                4. Generate a short personalized message (2-3 sentences) that:
                - If emissions decreased: Celebrate this impressive achievement and their dedication to fighting climate change
                - If emissions increased: Encourage them to set concrete goals for the new year, such as using electric vehicles, public transport more often, or offsetting emissions
                - If emissions stayed the same: Challenge them to make meaningful reductions in the coming year
                5. Provide a year-in-review perspective with long-term recommendations

                Format your response as a brief, impactful message."""

            summary_message = await text_generator.generate_text(prompt)
            
            return {
                "user_id": user_id,
                "year": year,
                "summary": summary_message
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error calculating total carbon emissions for user ID {user_id} for year {year}: {e}"
            )
        
    @staticmethod
    async def get_total_carbon_by_date_range(db: AsyncSession, user_id: int, start_date: datetime, end_date: datetime):
        try:
            total = await CarbonRepository.get_total_carbon_by_date_range(db, user_id, start_date, end_date)
            return {"user_id": user_id, "total_carbon_emission_kg": total}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error calculating total carbon emissions for user ID {user_id} from {start_date} to {end_date}: {e}"
            )

    @staticmethod
    async def update_carbon_emission(db: AsyncSession, emission_id: int, user_id: int, updated_data: CarbonEmissionUpdate):
        try:
            existing_emission = await CarbonRepository.get_carbon_emission_by_id(db, emission_id, user_id)
            if not existing_emission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Carbon emission record with ID {emission_id} not found"
                )
            
            vehicle_type = updated_data.vehicle_type if updated_data.vehicle_type is not None else existing_emission.vehicle_type
            distance_km = updated_data.distance_km if updated_data.distance_km is not None else existing_emission.distance_km
            fuel_type = updated_data.fuel_type if updated_data.fuel_type is not None else existing_emission.fuel_type
            
            carbon_emission_kg = CarbonService.calculate_carbon_emission(vehicle_type, distance_km, fuel_type)
            
            updated_emission = await CarbonRepository.update_carbon_emission(db, emission_id, updated_data, carbon_emission_kg)
            if not updated_emission:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Carbon emission record with ID {emission_id} not found"
                )
            return updated_emission
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error updating carbon emission ID {emission_id}: {e}"
            )

    @staticmethod
    async def delete_carbon_emission(db: AsyncSession, emission_id: int, user_id: int):
        try:
            success = await CarbonRepository.delete_carbon_emission(db, emission_id, user_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Carbon emission record with ID {emission_id} not found"
                )
            return {"detail": "Carbon emission record deleted successfully"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error deleting carbon emission ID {emission_id}: {e}"
            )