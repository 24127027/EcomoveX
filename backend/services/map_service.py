# from fastapi import HTTPException, status
# from sqlalchemy.ext.asyncio import AsyncSession
# from typing import List
# from integration.google_map_api import create_maps_client
# from models.route import TransportMode
# from schemas.destination_schema import DestinationCreate
# from schemas.map_schema import *
# from services.destination_service import DestinationService

# class MapService:
#     @staticmethod
#     async def search_location(db: AsyncSession, data: SearchLocationRequest) -> SearchLocationResponse:
#         try:
#             if not data.query or len(data.query.strip()) < 2:
#                 raise HTTPException(
#                     status_code=status.HTTP_400_BAD_REQUEST,
#                     detail="Search text must be at least 2 characters"
#                 )
            
#             try:
#                 maps = await create_maps_client()
#                 result = await maps.autocomplete_place(
#                     input_text=data.query.strip(),
#                     location=data.user_location,
#                     radius=data.radius,
#                     types=data.place_types,
#                     language=data.language
#                 )
                
#                 if result.get("status") not in ["OK", "ZERO_RESULTS"]:
#                     raise HTTPException(
#                         status_code=status.HTTP_400_BAD_REQUEST,
#                         detail=f"Google Maps API error: {result.get('status')}"
#                     )
                
#                 suggestions = []
#                 for prediction in result.get("predictions", []):
#                     structured = prediction.get("structured_formatting", {})
                    
#                     suggestions.append(SearchSuggestion(
#                         place_id=prediction.get("place_id"),
#                         description=prediction.get("description"),
#                         main_text=structured.get("main_text", ""),
#                         secondary_text=structured.get("secondary_text", ""),
#                         types=prediction.get("types", []),
#                         distance_meters=prediction.get("distance_meters")
#                     ))
#                     new_destination = DestinationCreate(
#                         place_id=prediction.get("place_id"),
#                     )
#                     await DestinationService.create_destination(db, new_destination)

#                 return SearchLocationResponse(
#                     status="OK",
#                     query=data.query.strip(),
#                     suggestions=suggestions,
#                 )
            
#             finally:
#                 if maps:
#                     await maps.close()
#         except Exception as e:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to search location: {str(e)}"
#             )
    
#     @staticmethod
#     async def get_location_details(
#         place_id: str,
#         language: str = "vi"
#     ) -> PlaceDetailsResponse:
#         try:
#             if not place_id:
#                 raise HTTPException(
#                     status_code=status.HTTP_400_BAD_REQUEST,
#                     detail="place_id is required"
#                 )
#             try:
#                 maps = await create_maps_client()
#                 result = await maps.get_place_details_from_autocomplete(
#                     place_id=place_id,
#                     language=language
#                 )
                
#                 if result.get("status") != "OK":
#                     raise HTTPException(
#                         status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"Place not found: {result.get('status')}"
#                     )
                
#                 place = result.get("result", {})
#                 location = place.get("geometry", {}).get("location", {})
                
#                 photos = []
#                 for photo in place.get("photos", [])[:5]:
#                     photos.append(PhotoInfo(
#                         photo_reference=photo.get("photo_reference"),
#                         width=photo.get("width"),
#                         height=photo.get("height")
#                     ))
                
#                 opening_hours_data = place.get("opening_hours")
#                 opening_hours = None
#                 if opening_hours_data:
#                     opening_hours = OpeningHours(
#                         open_now=opening_hours_data.get("open_now"),
#                         weekday_text=opening_hours_data.get("weekday_text", [])
#                     )
                
#                 return PlaceDetailsResponse(
#                     status="OK",
#                     place_id=place.get("place_id"),
#                     name=place.get("name"),
#                     formatted_address=place.get("formatted_address"),
#                     location=(location.get("lat"), location.get("lng")),
#                     rating=place.get("rating"),
#                     phone=place.get("formatted_phone_number"),
#                     website=place.get("website"),
#                     opening_hours=opening_hours,
#                     photos=photos,
#                     types=place.get("types", [])
#                 )
            
#             finally:
#                 if maps:
#                     await maps.close()
#         except Exception as e:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to get location details: {str(e)}"
#             )
    
#     # ============= NEW METHODS FOR FRONTEND =============
    
#     @staticmethod
#     async def get_route_with_traffic(
#         origin: Tuple[float, float],
#         destination: Tuple[float, float],
#         mode: TransportMode,
#         departure_time: str = "now"
#     ) -> RouteWithTrafficResponse:
#         """Get route with real-time traffic information"""
#         try:
#             maps = await create_maps_client()
#             result = await maps.get_directions_with_traffic(
#                 origin=origin,
#                 destination=destination,
#                 mode=mode,
#                 departure_time=departure_time
#             )
#             return result
#         except Exception as e:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to get route with traffic: {str(e)}"
#             )
#         finally:
#             if maps:
#                 await maps.close()
        
#     @staticmethod
#     async def get_eco_routes(
#         request: EcoRouteRequest
#     ) -> EcoRouteResponse:
#         """Get eco-friendly route recommendations"""
#         try:
#             maps = await create_maps_client()
#             result = await maps.get_eco_optimized_routes(request)
#             return result
#         except Exception as e:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to get eco routes: {str(e)}"
#             )
#         finally:
#             if maps:
#                 await maps.close()
    
#     @staticmethod
#     async def compare_routes_by_mode(
#         origin: Tuple[float, float],
#         destination: Tuple[float, float],
#         modes: List[TransportMode]
#     ) -> RouteComparisonResponse:
#         """Compare routes across different transport modes with carbon data"""
#         try:
#             maps = await create_maps_client()
#             result = await maps.get_multiple_routes_for_comparison(
#                 origin=origin,
#                 destination=destination,
#                 modes=modes
#             )
#             return result
#         except Exception as e:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to compare routes: {str(e)}"
#             )
#         finally:
#             if maps:
#                 await maps.close()
    
#     @staticmethod
#     async def get_air_quality_data(
#         lat: float,
#         lng: float,
#         include_pollutants: bool = False
#     ) -> Dict[str, Any]:
#         """Get air quality data for a location"""
#         try:
#             maps = await create_maps_client()
#             extra_computations = ["POLLUTANT_ADDITIONAL_INFO"] if include_pollutants else None
#             result = await maps.get_air_quality(
#                 lat=lat,
#                 lng=lng,
#                 extra_computations=extra_computations
#             )
#             return result
#         except Exception as e:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to get air quality: {str(e)}"
#             )
#         finally:
#             if maps:
#                 await maps.close()
    
#     @staticmethod
#     async def get_air_quality_heatmap_tile(
#         lat: float,
#         lng: float,
#         zoom: int = 12
#     ) -> Dict[str, Any]:
#         """Get air quality heatmap tile URL for map overlay"""
#         try:
#             maps = await create_maps_client()
#             result = await maps.get_air_quality_heatmap(
#                 lat=lat,
#                 lng=lng,
#                 zoom=zoom
#             )
#             return result
#         except Exception as e:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to get air quality heatmap: {str(e)}"
#             )
#         finally:
#             if maps:
#                 await maps.close()
    
#     @staticmethod
#     async def search_ev_charging_stations(
#         lat: float,
#         lng: float,
#         radius: int = 5000
#     ) -> NearbyPlacesResponse:
#         """Search for EV charging stations"""
#         try:
#             maps = await create_maps_client()
#             result = await maps.search_ev_charging_stations(
#                 lat=lat,
#                 lng=lng,
#                 radius=radius
#             )
#             return result
#         except Exception as e:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to search EV stations: {str(e)}"
#             )
#         finally:
#             if maps:
#                 await maps.close()
    
#     @staticmethod
#     async def search_bike_stations(
#         lat: float,
#         lng: float,
#         radius: int = 2000
#     ) -> NearbyPlacesResponse:
#         """Search for bike sharing stations"""
#         try:
#             maps = await create_maps_client()
#             result = await maps.search_bike_sharing_stations(
#                 lat=lat,
#                 lng=lng,
#                 radius=radius
#             )
#             return result
#         except Exception as e:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to search bike stations: {str(e)}"
#             )
#         finally:
#             if maps:
#                 await maps.close()
    
#     @staticmethod
#     async def search_nearby_places(
#         lat: float,
#         lng: float,
#         radius: int = 1000,
#         place_type: Optional[str] = None,
#         keyword: Optional[str] = None
#     ) -> NearbyPlacesResponse:
#         """Search for nearby places"""
#         try:
#             maps = await create_maps_client()
#             result = await maps.get_nearby_places_for_map(
#                 lat=lat,
#                 lng=lng,
#                 radius=radius,
#                 place_type=place_type,
#                 keyword=keyword
#             )
#             return result
#         except Exception as e:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to search nearby places: {str(e)}"
#             )
#         finally:
#             if maps:
#                 await maps.close()
    
#     @staticmethod
#     async def get_distance_matrix(
#         origins: List[Tuple[float, float]],
#         destinations: List[Tuple[float, float]],
#         mode: TransportMode
#     ) -> DistanceMatrixResponse:
#         """Get distance matrix for route planning"""
#         try:
#             maps = await create_maps_client()
#             result = await maps.get_distance_matrix_for_ui(
#                 origins=origins,
#                 destinations=destinations,
#                 mode=mode
#             )
#             return result
#         except Exception as e:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to get distance matrix: {str(e)}"
#             )
#         finally:
#             if maps:
#                 await maps.close()
    
#     @staticmethod
#     async def search_places_along_route(
#         origin: Tuple[float, float],
#         destination: Tuple[float, float],
#         search_type: str,
#         mode: TransportMode = TransportMode.car
#     ) -> SearchAlongRouteResponse:
#         """Search for places along a route"""
#         try:
#             maps = await create_maps_client()
#             result = await maps.search_along_route(
#                 origin=origin,
#                 destination=destination,
#                 search_type=search_type,
#                 mode=mode
#             )
#             return result
#         except Exception as e:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to search along route: {str(e)}"
#             )
#         finally:
#             if maps:
#                 await maps.close()
    
#     @staticmethod
#     async def batch_geocode_addresses(
#         request: BatchGeocodeRequest
#     ) -> BatchGeocodeResponse:
#         """Geocode multiple addresses at once"""
#         try:
#             maps = await create_maps_client()
#             result = await maps.batch_geocode(request)
#             return result
#         except Exception as e:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to batch geocode: {str(e)}"
#             )
#         finally:
#             if maps:
#                 await maps.close()
    
#     @staticmethod
#     async def reverse_geocode(
#         lat: float,
#         lng: float,
#         language: str = "vi"
#     ) -> GeocodingResponse:
#         """Reverse geocode coordinates to address"""
#         try:
#             maps = await create_maps_client()
#             result = await maps.reverse_geocode((lat, lng), language)
#             return result
#         except Exception as e:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to reverse geocode: {str(e)}"
#             )
#         finally:
#             if maps:
#                 await maps.close()
    
#     @staticmethod
#     async def get_photo_url(
#         photo_reference: str,
#         max_width: int = 400
#     ) -> str:
#         """Get photo URL for displaying place images"""
#         try:
#             maps = await create_maps_client()
#             result = await maps.get_photo_url(
#                 photo_reference=photo_reference,
#                 max_width=max_width
#             )
#             return result
#         except Exception as e:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Failed to get photo URL: {str(e)}"
#             )
#         finally:
#             if maps:
#                 await maps.close()