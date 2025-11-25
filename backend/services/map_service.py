from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from schemas.route_schema import DirectionsResponse
from integration.map_api import create_map_client
from schemas.destination_schema import DestinationCreate
from schemas.map_schema import *
from services.destination_service import DestinationService
from schemas.destination_schema import Location

FIELD_GROUPS = {
    PlaceDataCategory.BASIC: [
        "place_id", "name", "formatted_address", "geometry/location", 
        "geometry/viewport","photos", "types", "address_components", "utc_offset"
    ],
    PlaceDataCategory.CONTACT: [
        "formatted_phone_number", "website", "opening_hours"
    ],
    PlaceDataCategory.ATMOSPHERE: [
        "rating", "user_ratings_total", "reviews", "price_level"
    ]
}

class mapService:
    @staticmethod
    async def search_location(db: AsyncSession, data: AutocompleteRequest) -> AutocompleteResponse:
        try:            
            try:
                map = await create_map_client()
                response = await map.autocomplete_place(data)
                for prediction in response.predictions:
                    await DestinationService.create_destination(
                        db, DestinationCreate(place_id=prediction.place_id)
                    )
                return response
            finally:
                if map:
                    await map.close()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search location: {str(e)}"
            )
    
    @staticmethod
    async def get_location_details(data: PlaceDetailsRequest) -> PlaceDetailsResponse:
        # 1. Validation
        if not data.place_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="place_id is required"
            )

        map_client = None
        try:
            final_fields = set()
            for cat in data.categories:
                # cat.value gets the string "basic" from the Enum
                group = FIELD_GROUPS.get(cat.value, [])
                final_fields.update(group)

            # Fallback: if list is empty, fetch basic info
            if not final_fields:
                final_fields.update(FIELD_GROUPS[PlaceDataCategory.BASIC])

            # 3. Call API
            map_client = await create_map_client()
            return await map_client.get_place_details(
                place_id=data.place_id, 
                fields=list(final_fields), # Convert set back to list
                session_token=data.session_token
            )

        except HTTPException:
            # Re-raise HTTP exceptions so 400 stays 400
            raise 
        except Exception as e:
            # Handle unexpected errors
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get location details: {str(e)}"
            )
        finally:
            if map_client:
                await map_client.close()
            
    @staticmethod
    async def geocode_address(address: str) -> GeocodingResponse:
        try:
            map = await create_map_client()
            return await map.geocode(address=address)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to geocode address: {str(e)}"
            )
        finally:
            if map:
                await map.close()
            
    @staticmethod
    async def reverse_geocode(location: Location) -> GeocodingResponse:
        try:
            map = await create_map_client()
            return await map.reverse_geocode(location=location)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to reverse geocode location: {str(e)}"
            )
        finally:
            if map:
                await map.close()
                
    @staticmethod
    async def get_nearby_places(
        data: NearbyPlaceRequest,
    ) -> NearbyPlacesResponse:
        try:
            map = await create_map_client()
            return await map.get_nearby_places_for_map(
                data=data,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get nearby places: {str(e)}"
            )
        finally:
            if map:
                await map.close()
                
    @staticmethod
    async def get_next_page_nearby_places(
        page_token: str,
    ) -> NearbyPlacesResponse:
        try:
            map = await create_map_client()
            return await map.get_next_page_nearby_places(
                page_token=page_token,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get next page of nearby places: {str(e)}"
            )
        finally:
            if map:
                await map.close()
                
    @staticmethod
    async def search_along_route(
        dỉrection_data: DirectionsResponse,
        search_type: str,
    ) -> SearchAlongRouteResponse:
        try:
            map = await create_map_client()
            return await map.search_along_route(
                directions=dỉrection_data,
                search_type=search_type,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search along route: {str(e)}"
            )
        finally:
            if map:
                await map.close()