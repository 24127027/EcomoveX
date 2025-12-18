from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from schemas.destination_schema import Location
from schemas.map_schema import (
    AutocompleteRequest,
    AutocompleteResponse,
    GeocodingResponse,
    PlaceDataCategory,
    PlaceDetailsRequest,
    PlaceDetailsResponse,
    SearchAlongRouteResponse,
    TextSearchRequest,
    TextSearchResponse,
)
from schemas.route_schema import DirectionsResponse
from services.map_service import MapService
from utils.token.authentication_util import get_current_user

router = APIRouter(prefix="/map", tags=["Map & Navigation"])


@router.post(
    "/text-search", response_model=TextSearchResponse, status_code=status.HTTP_200_OK
)
async def text_search_place(
    request: TextSearchRequest,
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await MapService.text_search_place(
        user_db,
        request,
        current_user["user_id"],
        convert_photo_urls=request.convert_photo_urls
    )
    return result


@router.post(
    "/autocomplete", response_model=AutocompleteResponse, status_code=status.HTTP_200_OK
)
async def autocomplete(
    request: AutocompleteRequest, user_db: AsyncSession = Depends(get_db)
):
    return await MapService.autocomplete(user_db, request)


@router.get(
    "/place/{place_id}",
    response_model=PlaceDetailsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_place_details(
    place_id: str = Path(..., min_length=1),
    session_token: Optional[str] = Query(None),
    categories: List[PlaceDataCategory] = Query(default=[PlaceDataCategory.BASIC]),
    user_db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    request_data = PlaceDetailsRequest(
        place_id=place_id, session_token=session_token, categories=categories
    )

    result = await MapService.get_location_details(
        request_data, user_db, current_user["user_id"]
    )

    return result


@router.post(
    "/geocode", response_model=GeocodingResponse, status_code=status.HTTP_200_OK
)
async def geocode_address(
    address: str = Body(..., min_length=2),
):
    return await MapService.geocode_address(address=address)


@router.post(
    "/reverse-geocode", response_model=GeocodingResponse, status_code=status.HTTP_200_OK
)
async def reverse_geocode(
    lat: float = Body(..., ge=-90.0, le=90.0),
    lng: float = Body(..., ge=-180.0, le=180.0),
):
    location = Location(latitude=lat, longitude=lng)
    return await MapService.reverse_geocode(location=location)


@router.post(
    "/search-along-route",
    response_model=SearchAlongRouteResponse,
    status_code=status.HTTP_200_OK,
)
async def search_along_route(
    direction_data: DirectionsResponse = Body(...),
    search_type: str = Body(..., min_length=2),
):
    return await MapService.search_along_route(
        directions=direction_data,
        search_type=search_type,
    )
