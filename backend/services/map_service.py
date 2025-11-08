from typing import Dict, List, Optional, Any, Tuple
from schemas.destination_schema import DestinationCreate
from integration.google_map_api import create_maps_client
from fastapi import HTTPException, status
from schemas.map_schema import (
    SearchLocationResponse,
    SearchSuggestion,
    PlaceDetailsResponse,
    PhotoInfo,
    OpeningHours
)

class MapService:
    @staticmethod
    async def search_location(
        input_text: str,
        user_location: Optional[Tuple[float, float]] = None,
        search_radius: Optional[int] = None,
        place_types: Optional[str] = None,
        language: str = "vi"
    ) -> SearchLocationResponse:
        try:
            if not input_text or len(input_text.strip()) < 2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Search text must be at least 2 characters"
                )
            
            maps = await create_maps_client()
            
            try:

                result = await maps.autocomplete_place(
                    input_text=input_text.strip(),
                    location=user_location,
                    radius=search_radius,
                    types=place_types,
                    language=language
                )
                
                if result.get("status") not in ["OK", "ZERO_RESULTS"]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Google Maps API error: {result.get('status')}"
                    )
                
                suggestions = []
                for prediction in result.get("predictions", []):
                    structured = prediction.get("structured_formatting", {})
                    
                    suggestions.append(SearchSuggestion(
                        place_id=prediction.get("place_id"),
                        description=prediction.get("description"),
                        main_text=structured.get("main_text", ""),
                        secondary_text=structured.get("secondary_text", ""),
                        types=prediction.get("types", []),
                        distance_meters=prediction.get("distance_meters")
                    ))
                
                return SearchLocationResponse(
                    status="OK",
                    query=input_text,
                    suggestions=suggestions,
                    total_results=len(suggestions),
                    user_location=DestinationCreate(
                        latitude=user_location[0],
                        longitude=user_location[1]
                    ) if user_location else None
                )
            
            finally:
                await maps.close()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search location: {str(e)}"
            )
    
    @staticmethod
    async def get_location_details(
        place_id: str,
        language: str = "vi"
    ) -> PlaceDetailsResponse:
        try:
            if not place_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="place_id is required"
                )
            
            maps = await create_maps_client()
            
            try:
                result = await maps.get_place_details_from_autocomplete(
                    place_id=place_id,
                    language=language
                )
                
                if result.get("status") != "OK":
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Place not found: {result.get('status')}"
                    )
                
                place = result.get("result", {})
                location = place.get("geometry", {}).get("location", {})
                
                photos = []
                for photo in place.get("photos", [])[:5]:
                    photos.append(PhotoInfo(
                        photo_reference=photo.get("photo_reference"),
                        width=photo.get("width"),
                        height=photo.get("height")
                    ))
                
                opening_hours_data = place.get("opening_hours")
                opening_hours = None
                if opening_hours_data:
                    opening_hours = OpeningHours(
                        open_now=opening_hours_data.get("open_now"),
                        weekday_text=opening_hours_data.get("weekday_text", [])
                    )
                
                return PlaceDetailsResponse(
                    status="OK",
                    place_id=place.get("place_id"),
                    name=place.get("name"),
                    formatted_address=place.get("formatted_address"),
                    location={
                        "lat": location.get("lat"),
                        "lng": location.get("lng")
                    },
                    rating=place.get("rating"),
                    phone=place.get("formatted_phone_number"),
                    website=place.get("website"),
                    opening_hours=opening_hours,
                    photos=photos,
                    types=place.get("types", [])
                )
            
            finally:
                await maps.close()
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get location details: {str(e)}"
            )