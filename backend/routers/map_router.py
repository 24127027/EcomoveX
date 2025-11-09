# from typing import List
# from fastapi import APIRouter, Depends, Query, Body, status
# from sqlalchemy.ext.asyncio import AsyncSession
# from models.user import *
# from models.route import *
# from database.destination_database import get_destination_db
# from database.user_database import get_user_db
# from schemas.map_schema import *
# from schemas.user_schema import *
# from services.map_service import MapService
# from services.user_service import UserActivityService
# from utils.authentication_util import get_current_user

# router = APIRouter(prefix="/map", tags=["Map & Navigation"])

# # ============= EXISTING ENDPOINTS =============

# @router.post("/search", response_model=SearchLocationResponse, status_code=status.HTTP_200_OK)
# async def search_location(
#     request: SearchLocationRequest,
#     dest_db: AsyncSession = Depends(get_destination_db)
# ):
#     result = await MapService.search_location(dest_db, request)
#     return result

# @router.get("/place/{place_id}", response_model=PlaceDetailsResponse, status_code=status.HTTP_200_OK)
# async def get_place_details(
#     place_id: str,
#     language: str = Query("vi"),
#     user_db: AsyncSession = Depends(get_user_db),
#     current_user: dict = Depends(get_current_user)
# ):
#     result = await MapService.get_location_details(
#         place_id=place_id,
#         language=language
#     )
    
#     activity_data = UserActivityCreate(
#         activity_type=Activity.search_destination,
#         destination_id=place_id
#     )
#     await UserActivityService.log_user_activity(user_db, current_user["user_id"], activity_data)
    
#     return result

# # ============= NEW ENDPOINTS FOR FRONTEND =============

# @router.post("/routes/with-traffic", response_model=RouteWithTrafficResponse, status_code=status.HTTP_200_OK)
# async def get_route_with_traffic(
#     origin: Tuple[float, float] = Body(...),
#     destination: Tuple[float, float] = Body(...),
#     mode: TransportMode = Body(...),
#     departure_time: str = Body("now")
# ):
#     return await MapService.get_route_with_traffic(origin, destination, mode, departure_time)

# @router.post("/routes/eco", response_model=EcoRouteResponse, status_code=status.HTTP_200_OK)
# async def get_eco_routes(
#     request: EcoRouteRequest
# ):
#     return await MapService.get_eco_routes(request)

# @router.post("/routes/compare", response_model=RouteComparisonResponse, status_code=status.HTTP_200_OK)
# async def compare_routes(
#     origin: Tuple[float, float] = Body(...),
#     destination: Tuple[float, float] = Body(...),
#     modes: List[TransportMode] = Body(...)
# ):
#     return await MapService.compare_routes_by_mode(origin, destination, modes)

# @router.get("/air-quality", status_code=status.HTTP_200_OK)
# async def get_air_quality(
#     lat: float = Query(...),
#     lng: float = Query(...),
#     include_pollutants: bool = Query(False)
# ):
#     return await MapService.get_air_quality_data(lat, lng, include_pollutants)

# @router.get("/air-quality/heatmap", status_code=status.HTTP_200_OK)
# async def get_air_quality_heatmap(
#     lat: float = Query(...),
#     lng: float = Query(...),
#     zoom: int = Query(12, ge=1, le=20)
# ):
#     return await MapService.get_air_quality_heatmap_tile(lat, lng, zoom)

# @router.get("/green-infrastructure/ev-charging", response_model=NearbyPlacesResponse, status_code=status.HTTP_200_OK)
# async def search_ev_charging_stations(
#     lat: float = Query(...),
#     lng: float = Query(...),
#     radius: int = Query(5000, ge=100, le=50000)
# ):
#     return await MapService.search_ev_charging_stations(lat, lng, radius)

# @router.get("/green-infrastructure/bike-sharing", response_model=NearbyPlacesResponse, status_code=status.HTTP_200_OK)
# async def search_bike_sharing_stations(
#     lat: float = Query(...),
#     lng: float = Query(...),
#     radius: int = Query(2000, ge=100, le=10000)
# ):
#     return await MapService.search_bike_stations(lat, lng, radius)

# @router.get("/nearby", response_model=NearbyPlacesResponse, status_code=status.HTTP_200_OK)
# async def search_nearby_places(
#     lat: float = Query(...),
#     lng: float = Query(...),
#     radius: int = Query(1000, ge=100, le=50000),
#     place_type: Optional[str] = Query(None),
#     keyword: Optional[str] = Query(None)
# ):
#     return await MapService.search_nearby_places(lat, lng, radius, place_type, keyword)

# @router.post("/distance-matrix", response_model=DistanceMatrixResponse, status_code=status.HTTP_200_OK)
# async def get_distance_matrix(
#     origins: List[Tuple[float, float]] = Body(...),
#     destinations: List[Tuple[float, float]] = Body(...),
#     mode: TransportMode = Body(...)
# ):
#     return await MapService.get_distance_matrix(origins, destinations, mode)

# @router.post("/routes/search-along", response_model=SearchAlongRouteResponse, status_code=status.HTTP_200_OK)
# async def search_along_route(
#     origin: Tuple[float, float] = Body(...),
#     destination: Tuple[float, float] = Body(...),
#     search_type: str = Body(...),
#     mode: TransportMode = Body(TransportMode.car)
# ):
#     return await MapService.search_places_along_route(origin, destination, search_type, mode)

# @router.post("/geocode/batch", response_model=BatchGeocodeResponse, status_code=status.HTTP_200_OK)
# async def batch_geocode(
#     request: BatchGeocodeRequest
# ):
#     return await MapService.batch_geocode_addresses(request)

# @router.get("/geocode/reverse", response_model=GeocodingResponse, status_code=status.HTTP_200_OK)
# async def reverse_geocode(
#     lat: float = Query(...),
#     lng: float = Query(...),
#     language: str = Query("vi")
# ):
#     return await MapService.reverse_geocode(lat, lng, language)

# @router.get("/photo", status_code=status.HTTP_200_OK)
# async def get_photo_url(
#     photo_reference: str = Query(...),
#     max_width: int = Query(400, ge=1, le=1600)
# ):
#     return {"photo_url": await MapService.get_photo_url(photo_reference, max_width)}