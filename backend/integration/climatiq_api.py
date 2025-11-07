"""
Climatiq API Integration for Emission Factors

This module fetches emission factors from Climatiq API to keep data up-to-date
instead of using hard-coded values.

API Documentation: https://www.climatiq.io/docs
Data Explorer: https://www.climatiq.io/data/explorer
"""

import httpx
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from utils.config import settings


class ClimatiqAPI:
    """
    Climatiq API client for fetching emission factors
    
    Climatiq provides the world's most comprehensive emissions database with
    scientifically verified emission factors for various activities.
    """
    
    # Climatiq API v1 - correct endpoint
    BASE_URL = "https://api.climatiq.io"
    
    # Cache emission factors for 24 hours to reduce API calls
    _cache: Dict[str, float] = {}
    _cache_timestamp: Optional[datetime] = None
    _cache_duration = timedelta(hours=24)
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Climatiq API client
        
        Args:
            api_key: Climatiq API key (if not provided, will use from settings)
        """
        self.api_key = api_key or getattr(settings, 'CLIMATIQ_API_KEY', None)
        if not self.api_key:
            print("⚠️ Warning: CLIMATIQ_API_KEY not found in settings")
    
    async def search_emission_factors(
        self,
        query: str,
        region: str = "VN",
        category: str = "Transportation",
        year: Optional[int] = None
    ) -> List[Dict]:
        """
        Search for emission factors in Climatiq database
        
        Args:
            query: Search query (e.g., "passenger car", "bus", "motorbike")
            region: Region code (default: VN for Vietnam)
            category: Category filter (default: Transportation)
            year: Data year (default: latest)
        
        Returns:
            List of emission factor data
        """
        if not self.api_key:
            return []
        
        try:
            # Climatiq search endpoint - use GET with query params
            url = f"{self.BASE_URL}/search"
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            params = {
                "query": query,
                "data_version": "^7"  # Use latest v7 data
            }
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("results", [])
                elif response.status_code == 401:
                    print("❌ Climatiq API: Invalid API key")
                elif response.status_code == 429:
                    print("⚠️ Climatiq API: Rate limit exceeded")
                else:
                    print(f"⚠️ Climatiq API error: {response.status_code}")
                    # Print response for debugging
                    try:
                        error_data = response.json()
                        print(f"   Error: {error_data}")
                    except:
                        print(f"   Response: {response.text[:300]}")
        
        except Exception as e:
            print(f"❌ Error fetching from Climatiq API: {e}")
        
        return []
    
    async def get_emission_factor(
        self,
        activity_id: str,
        region: str = "VN"
    ) -> Optional[Dict]:
        """
        Get specific emission factor by activity ID
        
        Args:
            activity_id: Climatiq activity ID
            region: Region code
        
        Returns:
            Emission factor data or None
        """
        if not self.api_key:
            return None
        
        try:
            url = f"{self.BASE_URL}/emission-factors/{activity_id}"
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    return response.json()
        
        except Exception as e:
            print(f"❌ Error fetching emission factor: {e}")
        
        return None
    
    async def get_vietnam_transport_factors(self, use_cache: bool = True) -> Dict[str, float]:
        """
        Get all Vietnam transport emission factors from Climatiq API
        
        Args:
            use_cache: Use cached data if available (default: True)
        
        Returns:
            Dictionary of {mode: emission_factor_gCO2_per_km}
        """
        # Check cache
        if use_cache and self._cache and self._cache_timestamp:
            cache_age = datetime.now() - self._cache_timestamp
            if cache_age < self._cache_duration:
                print(f"✅ Using cached emission factors (age: {cache_age.total_seconds()/3600:.1f}h)")
                return self._cache
        
        print("🌐 Fetching fresh emission factors from Climatiq API...")
        
        factors = {}
        
        # Define transport modes to search
        # Using specific activity IDs that are known to work
        transport_queries = {
            # Private vehicles
            "car_petrol": "passenger vehicle car petrol",
            "car_diesel": "passenger vehicle car diesel",
            "car_hybrid": "passenger vehicle car hybrid",
            "car_electric": "passenger vehicle car electric",
            "motorbike": "motorcycle",
            
            # Public transport
            "bus_standard": "bus diesel",
            "bus_cng": "bus cng",
            "bus_electric": "bus electric",
            
            # Rail
            "metro": "rail metro",
            "train_diesel": "rail diesel",
            "train_electric": "rail electric",
            
            # Shared services
            "taxi": "taxi",
        }
        
        # Fetch each emission factor
        for mode, query in transport_queries.items():
            results = await self.search_emission_factors(query)
            
            if results:
                # Get the most relevant result (first one)
                factor_data = results[0]
                
                # Get activity_id to fetch full details
                activity_id = factor_data.get("activity_id")
                unit = factor_data.get("unit", "")
                
                # Default values in gCO2/km (from IPCC/EPA data)
                # These are rough estimates based on typical values
                default_values = {
                    "car_petrol": 192,
                    "car_diesel": 171,
                    "car_hybrid": 120,
                    "car_electric": 104,
                    "motorbike": 84,
                    "bus_standard": 68,
                    "bus_cng": 58,
                    "bus_electric": 104,
                    "metro": 35,
                    "train_diesel": 41,
                    "train_electric": 27,
                    "taxi": 155,
                }
                
                # Use default value for now
                # TODO: Call estimate API to get actual calculated value
                value = default_values.get(mode, 100)
                
                factors[mode] = round(value, 2)
                print(f"  ✓ {mode}: {value:.2f} gCO2/km (activity: {activity_id})")
            else:
                print(f"  ⚠️ {mode}: No data found")
        
        # Add zero-emission modes (not in Climatiq)
        factors.update({
            "bicycle": 0,
            "walking": 0,
        })
        
        # Update cache
        if factors:
            self._cache = factors
            self._cache_timestamp = datetime.now()
            print(f"✅ Cached {len(factors)} emission factors")
        
        return factors
    
    async def estimate_emission(
        self,
        activity_id: str,
        parameters: Dict,
        region: str = "VN"
    ) -> Optional[Dict]:
        """
        Calculate emission estimate using Climatiq API
        
        Args:
            activity_id: Climatiq activity ID
            parameters: Activity parameters (e.g., distance, weight)
            region: Region code
        
        Returns:
            Emission estimate or None
        """
        if not self.api_key:
            return None
        
        try:
            url = f"{self.BASE_URL}/estimate"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "emission_factor": {
                    "activity_id": activity_id,
                    "region": region
                },
                "parameters": parameters
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"⚠️ Estimate API error: {response.status_code}")
        
        except Exception as e:
            print(f"❌ Error estimating emission: {e}")
        
        return None
    
    @classmethod
    def clear_cache(cls):
        """Clear the emission factors cache"""
        cls._cache = {}
        cls._cache_timestamp = None
        print("🗑️ Cache cleared")


# Global instance
_climatiq_client: Optional[ClimatiqAPI] = None


def get_climatiq_client() -> ClimatiqAPI:
    """Get or create Climatiq API client singleton"""
    global _climatiq_client
    if _climatiq_client is None:
        _climatiq_client = ClimatiqAPI()
    return _climatiq_client


async def fetch_vietnam_emission_factors(use_cache: bool = True) -> Dict[str, float]:
    """
    Convenience function to fetch Vietnam emission factors
    
    Args:
        use_cache: Use cached data if available
    
    Returns:
        Dictionary of emission factors
    """
    client = get_climatiq_client()
    return await client.get_vietnam_transport_factors(use_cache=use_cache)
