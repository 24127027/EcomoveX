"""
Standalone Map API Test Server
Run this to test the map API with the frontend without modifying existing files
Usage: python test_map_server.py
Then access: http://localhost:8001/docs
"""

from fastapi import FastAPI, Query, Body, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Tuple, List
from integration.google_map_api import create_maps_client
from schemas.map_schema import SearchLocationRequest, PlaceDetailsResponse
import uvicorn

app = FastAPI(
    title="EcomoveX Map API Test Server",
    description="Test server for map API endpoints",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Map API Test Server"
    }


@app.post("/map/search", tags=["Map"])
async def search_location(request: SearchLocationRequest):
    """
    Search for places using autocomplete
    
    Request body:
    {
        "query": "string",
        "language": "vi" (optional),
        "user_location": [lat, lng] (optional),
        "radius": 5000 (optional)
    }
    """
    try:
        if not request.query or len(request.query.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search text must be at least 2 characters"
            )
        
        maps = await create_maps_client()
        result = await maps.autocomplete_place(
            data=request,
            components="country:vn"
        )
        await maps.close()
        return result
        
    except Exception as e:
        print(f"Search error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search location: {str(e)}"
        )


@app.get("/map/place/{place_id}", tags=["Map"])
async def get_place_details(
    place_id: str,
    language: str = Query("vi")
):
    """
    Get detailed information about a place
    
    Parameters:
    - place_id: The Google Maps place ID
    - language: Language code (default: vi for Vietnamese)
    """
    try:
        if not place_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="place_id is required"
            )
        
        maps = await create_maps_client()
        result = await maps.get_place_details_from_autocomplete(
            place_id=place_id,
            language=language
        )
        await maps.close()
        
        return result
        
    except Exception as e:
        print(f"Get place details error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get place details: {str(e)}"
        )


@app.post("/map/reverse-geocode", tags=["Map"])
async def reverse_geocode(
    lat: float = Body(...),
    lng: float = Body(...)
):
    """
    Get address from coordinates (reverse geocoding)
    
    Request body:
    {
        "lat": 10.775,
        "lng": 106.694
    }
    """
    try:
        maps = await create_maps_client()
        result = await maps.reverse_geocode(
            lat=lat,
            lng=lng
        )
        await maps.close()
        
        return result
        
    except Exception as e:
        print(f"Reverse geocode error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reverse geocode: {str(e)}"
        )


@app.post("/map/photo", tags=["Map"])
async def get_photo_url(photo_reference: str = Body(...)):
    """
    Get photo URL from photo reference
    
    Request body:
    {
        "photo_reference": "string"
    }
    """
    try:
        maps = await create_maps_client()
        photo_url = await maps.get_photo_url(
            photo_reference=photo_reference,
            max_width=400
        )
        await maps.close()
        
        return {"photo_url": photo_url}
        
    except Exception as e:
        print(f"Get photo error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get photo URL: {str(e)}"
        )


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "EcomoveX Map API Test Server",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


if __name__ == "__main__":
    print("🚀 Starting Map API Test Server on http://localhost:8001")
    print("📚 API Documentation: http://localhost:8001/docs")
    print("💡 This is a test server - does NOT modify existing files")
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
