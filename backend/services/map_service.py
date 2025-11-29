from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.route_schema import DirectionsResponse
from integration.map_api import create_map_client
from schemas.destination_schema import DestinationCreate
from schemas.map_schema import *
from services.destination_service import DestinationService
from schemas.destination_schema import Location

FIELD_GROUPS = {
    PlaceDataCategory.BASIC: [
        "place_id",
        "name",
        "formatted_address",
        "geometry/location",
        "geometry/viewport",
        "photos",
        "types",
        "address_components",
        "utc_offset",
    ],
    PlaceDataCategory.CONTACT: ["formatted_phone_number", "website", "opening_hours"],
    PlaceDataCategory.ATMOSPHERE: [
        "rating",
        "user_ratings_total",
        "reviews",
        "price_level",
    ],
}


class MapService:
    @staticmethod
    async def text_search_place(
        db: AsyncSession, data: TextSearchRequest
    ) -> TextSearchResponse:
        map_client = await create_map_client()

        try:
            response = await map_client.text_search_place(data)

            for result in response.results:
                try:
                    await DestinationService.create_destination(
                        db, DestinationCreate(place_id=result.place_id)
                    )
                except Exception:
                    pass

            return response

        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search location: {str(e)}",
            )
        finally:
            await map_client.close()

    @staticmethod
    async def autocomplete(
        db: AsyncSession, data: AutocompleteRequest
    ) -> AutocompleteResponse:
        map_client = None
        try:
            map_client = await create_map_client()
            response = await map_client.autocomplete_place(data)
            for prediction in response.predictions:
                try:
                    await DestinationService.create_destination(
                        db, DestinationCreate(place_id=prediction.place_id)
                    )
                except Exception:
                    pass
            return response
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search location: {str(e)}",
            )
        finally:
            if map_client:
                await map_client.close()

    @staticmethod
    async def get_location_details(data: PlaceDetailsRequest) -> PlaceDetailsResponse:
        if not data.place_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="place_id is required"
            )

        map_client = None
        try:
            final_fields = set()
            for cat in data.categories:
                group = FIELD_GROUPS.get(cat.value, [])
                final_fields.update(group)

            if not final_fields:
                final_fields.update(FIELD_GROUPS[PlaceDataCategory.BASIC])

            map_client = await create_map_client()
            return await map_client.get_place_details(
                place_id=data.place_id,
                fields=list(final_fields),  # Convert set back to list
                session_token=data.session_token,
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get location details: {str(e)}",
            )
        finally:
            if map_client:
                await map_client.close()

    @staticmethod
    async def geocode_address(address: str) -> GeocodingResponse:
        map_client = None
        try:
            map_client = await create_map_client()
            return await map_client.geocode(address=address)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to geocode address: {str(e)}",
            )
        finally:
            if map_client:
                await map_client.close()

    @staticmethod
    async def reverse_geocode(location: Location) -> GeocodingResponse:
        map_client = None
        try:
            map_client = await create_map_client()
            return await map_client.reverse_geocode(location=location)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to reverse geocode location: {str(e)}",
            )
        finally:
            if map_client:
                await map_client.close()

    @staticmethod
    async def get_nearby_places(
        data: NearbyPlaceRequest,
    ) -> NearbyPlacesResponse:
        map_client = None
        try:
            map_client = await create_map_client()
            return await map_client.get_nearby_places_for_map(
                data=data,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get nearby places: {str(e)}",
            )
        finally:
            if map_client:
                await map_client.close()

    @staticmethod
    async def get_next_page_nearby_places(
        page_token: str,
    ) -> NearbyPlacesResponse:
        map_client = None
        try:
            map_client = await create_map_client()
            return await map_client.get_next_page_nearby_places(
                page_token=page_token,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get next page of nearby places: {str(e)}",
            )
        finally:
            if map_client:
                await map_client.close()

    @staticmethod
    async def search_along_route(
        direction_data: DirectionsResponse,
        search_type: str,
    ) -> SearchAlongRouteResponse:
        map_client = None
        try:
            map_client = await create_map_client()
            return await map_client.search_along_route(
                directions=direction_data,
                search_type=search_type,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search along route: {str(e)}",
            )
        finally:
            if map_client:
                await map_client.close()
