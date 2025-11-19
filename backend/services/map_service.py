from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from integration.google_map_api import create_maps_client
from models.route import TransportMode
from schemas.destination_schema import DestinationCreate
from schemas.map_schema import *
from services.destination_service import DestinationService
from schemas.air_schema import AirQualityResponse
class MapService:
    @staticmethod
    async def search_location(db: AsyncSession, data: SearchLocationRequest) -> AutocompleteResponse:
        try:            
            try:
                maps = await create_maps_client()
                response = await maps.autocomplete_place(data)
                for prediction in response.predictions:
                    await DestinationService.create_destination(
                        db, DestinationCreate(place_id=prediction.place_id)
                    )
            finally:
                if maps:
                    await maps.close()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search location: {str(e)}"
            )
    
    @staticmethod
    async def get_location_details(
        place_id: str,
    ) -> PlaceDetailsResponse:
        try:
            if not place_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="place_id is required"
                )
            try:
                maps = await create_maps_client()
                return await maps.get_place_details_from_autocomplete(place_id=place_id)
            finally:
                if maps:
                    await maps.close()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get location details: {str(e)}"
            )
            
    @staticmethod
    async def get_air_quality(location: Tuple[float, float]) -> AirQualityResponse:
        try:
            try:
                maps = await create_maps_client()
                return await maps.get_air_quality(location=location)
            finally:
                if maps:
                    await maps.close()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get air quality data: {str(e)}"
            )
            
    @staticmethod
    async def geocode_address(address: str) -> GeocodingResponse:
        try:
            maps = await create_maps_client()
            return await maps.geocode(address=address)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to geocode address: {str(e)}"
            )
        finally:
            if maps:
                await maps.close()
            
    @staticmethod
    async def reverse_geocode(location: Tuple[float, float]) -> GeocodingResponse:
        try:
            maps = await create_maps_client()
            return await maps.reverse_geocode(location=location)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to reverse geocode location: {str(e)}"
            )
        finally:
            if maps:
                await maps.close()
                
    @staticmethod
    async def get_nearby_places(
        data: NearbyPlaceRequest,
    ) -> NearbyPlacesResponse:
        try:
            maps = await create_maps_client()
            return await maps.get_nearby_places_for_map(
                data=data,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get nearby places: {str(e)}"
            )
        finally:
            if maps:
                await maps.close()
                
    @staticmethod
    async def get_next_page_nearby_places(
        page_token: str,
    ) -> NearbyPlacesResponse:
        try:
            maps = await create_maps_client()
            return await maps.get_next_page_nearby_places(
                page_token=page_token,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get next page of nearby places: {str(e)}"
            )
        finally:
            if maps:
                await maps.close()