from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from integration.google_map_api import create_maps_client
from schemas.destination_schema import DestinationCreate
from schemas.map_schema import *
from services.destination_service import DestinationService

class MapService:
    @staticmethod
    async def search_location(db: AsyncSession, data: SearchLocationRequest) -> SearchLocationResponse:
        try:
            if not data.query or len(data.query.strip()) < 2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Search text must be at least 2 characters"
                )
            
            maps = await create_maps_client()
            
            try:

                result = await maps.autocomplete_place(
                    input_text=data.query.strip(),
                    location=data.user_location,
                    radius=data.radius,
                    types=data.place_types,
                    language=data.language
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
                    new_destination = DestinationCreate(
                        place_id=prediction.get("place_id"),
                    )
                    await DestinationService.create_destination(db, new_destination)

                return SearchLocationResponse(
                    status="OK",
                    query=data.query.strip(),
                    suggestions=suggestions,
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
                    location=(location.get("lat"), location.get("lng")),
                    rating=place.get("rating"),
                    phone=place.get("formatted_phone_number"),
                    website=place.get("website"),
                    opening_hours=opening_hours,
                    photos=photos,
                    types=place.get("types", [])
                )
            
            finally:
                await maps.close()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get location details: {str(e)}"
            )