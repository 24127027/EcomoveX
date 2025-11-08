from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from integration.text_generator_api import get_text_generator
from integration.climatiq_api import get_climatiq_client
from typing import Dict, Optional
import httpx
from utils.config import settings
from schemas.carbon_schema import EmissionResult, CompareModesResponse, ModeComparison, FuelType

class CarbonService:    
    # Vietnam emission factors by fuel type (gCO2/km per passenger) - Source: Climatiq, IPCC 2019
    EMISSION_FACTORS_VN = {
        # Cars by fuel type
        "car_petrol": 192,
        "car_gasoline": 192,  # Same as petrol
        "car_diesel": 171,
        "car_hybrid": 120,
        "car_electric": 0,
        "car_cng": 145,  # Compressed Natural Gas
        "car_lpg": 165,  # Liquefied Petroleum Gas
        
        # Motorbikes by fuel type
        "motorbike_petrol": 84,
        "motorbike_gasoline": 84,
        "motorbike_electric": 0,
        "motorbike_small": 65,
        "motorbike_large": 95,
        
        # Buses by fuel type
        "bus_diesel": 68,
        "bus_cng": 58,
        "bus_electric": 0,
        
        # Trains/Metro
        "metro": 35,
        "train_diesel": 41,
        "train_electric": 27,
        
        # Non-motorized
        "bicycle": 0,
        "bicycle_electric": 7,
        "walking": 0,
        
        # Taxis/Ride-sharing (default petrol)
        "taxi_petrol": 155,
        "taxi_hybrid": 110,
        "grab_car_petrol": 155,
        "grab_car_hybrid": 110,
        "grab_bike": 84,
        
        # Legacy mappings (default to petrol)
        "car": 192,
        "motorbike": 84,
        "bus": 68,
        "train": 41,
        "taxi": 155,
        "grab_car": 155,
        "driving": 192,
        "transit": 68,
        "bicycling": 0,
    }
    
    GRID_INTENSITY_VN = 519  # Vietnam grid carbon intensity (gCO2/kWh)
    
    EV_EFFICIENCY = {
        "car_electric": 0.20,
        "bus_electric": 1.30,
        "motorbike_electric": 0.03,
        "bicycle_electric": 0.01,
    }
    
    MODE_MAPPING = {
        "driving": "car",
        "car": "car",
        "motorbike": "motorbike",
        "motorcycle": "motorbike",
        "transit": "bus",
        "bus": "bus",
        "train": "train",
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
    
    _grid_intensity_cache = GRID_INTENSITY_VN
    _cache_timestamp = None
    _factors_refreshed = False

    @staticmethod
    async def refresh_emission_factors(force: bool = False) -> Dict[str, float]:
        """Refresh emission factors from Climatiq API"""
        if CarbonService._factors_refreshed and not force:
            return CarbonService.EMISSION_FACTORS_VN
        
        try:
            climatiq = get_climatiq_client()
            
            if not climatiq.api_key:
                print("⚠️  No Climatiq API key found, using fallback emission factors")
                return CarbonService.EMISSION_FACTORS_VN
            
            fresh_factors = await climatiq.get_vietnam_transport_factors(use_cache=not force)
            
            if fresh_factors and len(fresh_factors) > 2:
                updated_count = 0
                for mode, factor in fresh_factors.items():
                    if mode in CarbonService.EMISSION_FACTORS_VN:
                        old_value = CarbonService.EMISSION_FACTORS_VN[mode]
                        CarbonService.EMISSION_FACTORS_VN[mode] = factor
                        
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
    def get_emission_factor_for_mode(mode: str, fuel_type: Optional[str] = None) -> str:
        """
        Map transport mode and fuel type to emission factor key
        
        Args:
            mode: Transport mode (e.g., "car", "motorbike", "bus")
            fuel_type: Fuel type (e.g., "petrol", "diesel", "electric")
        
        Returns:
            Emission factor key (e.g., "car_petrol", "bus_diesel")
        """
        mode_lower = mode.lower()
        
        # Map mode to base type
        base_mode = CarbonService.MODE_MAPPING.get(mode_lower, "car")
        
        # For modes that don't use fuel (walking, bicycling, metro)
        if base_mode in ["walking", "bicycle", "metro"]:
            # Check for electric bicycle
            if base_mode == "bicycle" and fuel_type and fuel_type.lower() == "electric":
                return "bicycle_electric"
            return base_mode
        
        # Default fuel type is petrol if not specified
        if not fuel_type:
            fuel_type = "petrol"
        
        fuel_lower = fuel_type.lower()
        
        # Normalize gasoline to petrol
        if fuel_lower == "gasoline":
            fuel_lower = "petrol"
        
        # Combine mode and fuel type
        combined_key = f"{base_mode}_{fuel_lower}"
        
        # Check if combined key exists in emission factors
        if combined_key in CarbonService.EMISSION_FACTORS_VN:
            return combined_key
        
        # Fallback to base mode with default fuel
        fallback_key = f"{base_mode}_petrol"
        if fallback_key in CarbonService.EMISSION_FACTORS_VN:
            return fallback_key
        
        # Final fallback
        return base_mode if base_mode in CarbonService.EMISSION_FACTORS_VN else "car_petrol"
    
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
            grid_intensity = CarbonService._grid_intensity_cache
            return efficiency * grid_intensity
        
        # Return pre-defined factor from Vietnam-specific data
        return CarbonService.EMISSION_FACTORS_VN.get(mode_lower, CarbonService.EMISSION_FACTORS_VN.get("car_petrol", 192))
    
    @staticmethod
    def calculate_traffic_multiplier(congestion_ratio: float) -> float:
        """
        Calculate carbon emission multiplier based on traffic congestion
        
        Traffic increases fuel consumption due to:
        - Frequent acceleration/braking
        - Lower average speed (less efficient engine operation)
        - Longer idle time
        
        Based on research:
        - US EPA (2011): Stop-and-go traffic +40-50%
        - Berkeley Studies (2019): Severe congestion +65-80%
        - Vietnam MOST (2020): Hanoi rush hour +45%
        
        Args:
            congestion_ratio: duration_in_traffic / duration_normal
        
        Returns:
            Multiplier for carbon emission (1.0 = no traffic, higher = more congestion)
        """
        if congestion_ratio <= 1.0:
            # No traffic delay
            return 1.0
        elif congestion_ratio <= 1.2:
            # Light traffic: +10-20% emissions
            return 1.0 + (congestion_ratio - 1.0) * 1.0
        elif congestion_ratio <= 1.5:
            # Moderate traffic: +20-40% emissions
            return 1.2 + (congestion_ratio - 1.2) * 0.67
        elif congestion_ratio <= 2.0:
            # Heavy traffic: +40-70% emissions
            return 1.4 + (congestion_ratio - 1.5) * 0.6
        else:
            # Severe gridlock: +70-100% emissions (capped at 100%)
            # Based on extreme stop-and-go conditions with significant idle time
            multiplier = 1.7 + (congestion_ratio - 2.0) * 0.3
            return min(multiplier, 2.0)  # Cap at 100% increase
    
    @staticmethod
    async def calculate_emission_by_mode(
        distance_km: float,
        mode: str,
        fuel_type: Optional[str] = None,
        passengers: int = 1,
        use_realtime_grid: bool = True,
        congestion_ratio: float = 1.0
    ) -> EmissionResult:
        """
        Calculate carbon emission for a trip using Vietnam-specific emission factors
        
        Args:
            distance_km: Distance in kilometers
            mode: Transport mode
            fuel_type: Fuel type (petrol, diesel, electric, hybrid, cng, lpg). Default: petrol
            passengers: Number of passengers
            use_realtime_grid: Use real-time grid intensity for EVs
            congestion_ratio: Traffic congestion ratio (duration_in_traffic / duration_normal)
        """
        # Default fuel type to petrol if not specified
        if not fuel_type:
            fuel_type = "petrol"
        
        emission_mode = CarbonService.get_emission_factor_for_mode(mode, fuel_type)
        factor = await CarbonService.get_emission_factor(emission_mode, use_realtime_grid)
        
        # Apply traffic multiplier for vehicles affected by congestion
        traffic_multiplier = 1.0
        # Traffic affects all motorized vehicles except trains/metro
        traffic_affected_modes = [
            "car_petrol", "car_gasoline", "car_diesel", "car_hybrid", "car_cng", "car_lpg",
            "motorbike_petrol", "motorbike_gasoline", "motorbike",
            "taxi_petrol", "taxi_hybrid", "taxi",
            "grab_car_petrol", "grab_car_hybrid", "grab_car",
            "grab_bike", "driving"
        ]
        
        if emission_mode in traffic_affected_modes and congestion_ratio > 1.0:
            traffic_multiplier = CarbonService.calculate_traffic_multiplier(congestion_ratio)
            factor = factor * traffic_multiplier
        
        total_grams = distance_km * factor
        per_passenger_grams = total_grams / passengers if passengers > 0 else total_grams
        
        grid_intensity_used = None
        if emission_mode in CarbonService.EV_EFFICIENCY:
            grid_intensity_used = CarbonService._grid_intensity_cache
        
        result_data = {
            "distance_km": round(distance_km, 2),
            "mode": emission_mode,
            "fuel_type": fuel_type,
            "passengers": passengers,
            "emission_factor_g_per_km": round(factor, 2),
            "total_co2_grams": round(total_grams, 2),
            "total_co2_kg": round(total_grams / 1000, 3),
            "per_passenger_co2_grams": round(per_passenger_grams, 2),
            "per_passenger_co2_kg": round(per_passenger_grams / 1000, 3),
            "grid_intensity_used": grid_intensity_used,
            "data_source": "Vietnam-specific (Climatiq + Electricity Maps)"
        }
        
        # Add traffic info if applicable
        if congestion_ratio > 1.0 and traffic_multiplier > 1.0:
            result_data["traffic_congestion_ratio"] = round(congestion_ratio, 2)
            result_data["traffic_multiplier"] = round(traffic_multiplier, 2)
            result_data["emission_increase_percent"] = round((traffic_multiplier - 1.0) * 100, 1)
        
        return EmissionResult(**result_data)
    
    @staticmethod
    async def compare_transport_modes(distance_km: float, modes: list) -> CompareModesResponse:
        """Compare carbon emissions across multiple transport modes"""
        comparisons = []
        
        for mode in modes:
            try:
                emission = await CarbonService.calculate_emission_by_mode(distance_km, mode)
                comparisons.append(ModeComparison(
                    mode=mode,
                    result=emission
                ))
            except ValueError:
                # Skip invalid modes
                continue
        
        # Find lowest emission mode
        if not comparisons:
            raise ValueError("No valid transport modes provided")
        
        sorted_comparisons = sorted(comparisons, key=lambda x: x.result.total_co2_kg)
        lowest = sorted_comparisons[0]
        
        return CompareModesResponse(
            distance_km=distance_km,
            comparisons=comparisons,
            lowest_emission_mode=lowest.mode,
            lowest_emission_kg=lowest.result.total_co2_kg
        )
    
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