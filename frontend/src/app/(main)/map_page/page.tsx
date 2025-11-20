"use client";

import React, { useState, useEffect, useRef } from "react";
import { Search, Home, MapPin, Bot, User, ChevronLeft, Navigation } from "lucide-react";

// Type definitions
interface EcoLocation {
  id: number;
  name: string;
  address: string;
  distance: string;
  rating: number;
  image: string;
  lat: number;
  lng: number;
  type: string;
}

// API Service Functions - Placeholder for API integration
const locationService = {
  // TODO: Replace with actual API endpoint
  searchLocations: async (query: string, lat: number, lng: number): Promise<EcoLocation[]> => {
    try {
      const response = await fetch(
        `/api/locations/search?q=${encodeURIComponent(query)}&lat=${lat}&lng=${lng}`
      );
      if (!response.ok) throw new Error('Search failed');
      return await response.json();
    } catch (error) {
      console.error('Error searching locations:', error);
      return [];
    }
  },

  // TODO: Replace with actual API endpoint
  getRecommendations: async (lat: number, lng: number, radius: number = 5000): Promise<EcoLocation[]> => {
    try {
      const response = await fetch(
        `/api/locations/recommendations?lat=${lat}&lng=${lng}&radius=${radius}`
      );
      if (!response.ok) throw new Error('Failed to fetch recommendations');
      return await response.json();
    } catch (error) {
      console.error('Error fetching recommendations:', error);
      // Fallback to mock data for development
      return mockLocations;
    }
  },

  // TODO: Replace with actual API endpoint
  getLocationById: async (id: number): Promise<EcoLocation | null> => {
    try {
      const response = await fetch(`/api/locations/${id}`);
      if (!response.ok) throw new Error('Failed to fetch location');
      return await response.json();
    } catch (error) {
      console.error('Error fetching location:', error);
      return null;
    }
  }
};

// Mock data for development - Remove when API is ready
const mockLocations: EcoLocation[] = [
  {
    id: 1,
    name: "The Hive Bean Coffee",
    address: "123 Nguyen Hue, District 1",
    distance: "1.2km",
    rating: 4.5,
    image: "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=400&h=300&fit=crop",
    lat: 10.7756,
    lng: 106.7019,
    type: "Cafe"
  },
  {
    id: 2,
    name: "Cafe Lokolo's",
    address: "456 Le Loi, District 1",
    distance: "1.5km",
    rating: 4.3,
    image: "https://images.unsplash.com/photo-1493857671505-72967e2e2760?w=400&h=300&fit=crop",
    lat: 10.7722,
    lng: 106.6989,
    type: "Cafe"
  },
  {
    id: 3,
    name: "Green Space Shop",
    address: "789 Dong Khoi, District 1",
    distance: "0.8km",
    rating: 4.7,
    image: "https://images.unsplash.com/photo-1426122402199-be02db90eb90?w=400&h=300&fit=crop",
    lat: 10.7769,
    lng: 106.7041,
    type: "Shop"
  },
  {
    id: 4,
    name: "La Vegetariana Restaurant",
    address: "321 Pasteur, District 3",
    distance: "2.1km",
    rating: 4.6,
    image: "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=400&h=300&fit=crop",
    lat: 10.7724,
    lng: 106.6910,
    type: "Restaurant"
  }
];

export default function MapPage() {
  const [selectedLocation, setSelectedLocation] = useState<EcoLocation | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [locations, setLocations] = useState<EcoLocation[]>([]);
  const [searchResults, setSearchResults] = useState<EcoLocation[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isLoadingRecommendations, setIsLoadingRecommendations] = useState(true);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [sheetHeight, setSheetHeight] = useState(40);
  const [isDragging, setIsDragging] = useState(false);
  const [startY, setStartY] = useState(0);
  const [startHeight, setStartHeight] = useState(40);
  const [userLocation, setUserLocation] = useState({ lat: 10.7756, lng: 106.7019 });
  
  const mapRef = useRef<HTMLDivElement>(null);
  const googleMapRef = useRef<google.maps.Map | null>(null);
  const markersRef = useRef<google.maps.Marker[]>([]);
  const sheetRef = useRef<HTMLDivElement>(null);
  const searchTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);

  // Fetch recommendations on component mount
  useEffect(() => {
    fetchRecommendations();
  }, [userLocation]);

  // Handle search with debounce
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (searchQuery.trim() === '') {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    searchTimeoutRef.current = setTimeout(async () => {
      const results = await locationService.searchLocations(
        searchQuery,
        userLocation.lat,
        userLocation.lng
      );
      setSearchResults(results);
      setIsSearching(false);
    }, 500); // 500ms debounce

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchQuery, userLocation]);

  const fetchRecommendations = async () => {
    setIsLoadingRecommendations(true);
    try {
      const recommendations = await locationService.getRecommendations(
        userLocation.lat,
        userLocation.lng
      );
      setLocations(recommendations);
    } catch (error) {
      console.error('Failed to fetch recommendations:', error);
      setLocations(mockLocations); // Fallback to mock data
    } finally {
      setIsLoadingRecommendations(false);
    }
  };

  const displayedLocations = searchQuery.trim() !== '' ? searchResults : locations;

  useEffect(() => {
    // Load Google Maps script
    const loadGoogleMaps = () => {
      if (window.google && window.google.maps) {
        initMap();
        return;
      }

      const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
      if (!apiKey) {
        console.error('Google Maps API key is not set in environment variables');
        return;
      }

      const script = document.createElement('script');
      script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places`;
      script.async = true;
      script.defer = true;
      script.onload = () => initMap();
      document.head.appendChild(script);
    };

    const initMap = () => {
      if (!mapRef.current) return;

      const map = new window.google.maps.Map(mapRef.current, {
        center: userLocation,
        zoom: 14,
        styles: [
          {
            featureType: "poi",
            elementType: "labels",
            stylers: [{ visibility: "off" }]
          }
        ],
        disableDefaultUI: false,
        zoomControl: true,
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: false
      });

      googleMapRef.current = map;
      setMapLoaded(true);
      
      // Get user's current location
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            const pos = {
              lat: position.coords.latitude,
              lng: position.coords.longitude
            };
            setUserLocation(pos);
            map.setCenter(pos);
          },
          () => {
            console.log('Error: The Geolocation service failed.');
          }
        );
      }
    };

    loadGoogleMaps();
  }, []);

  // Update markers when locations change
  useEffect(() => {
    if (!googleMapRef.current || !mapLoaded) return;

    // Clear existing markers
    markersRef.current.forEach(marker => marker.setMap(null));
    markersRef.current = [];

    // Add new markers
    displayedLocations.forEach(location => {
      const marker = new window.google.maps.Marker({
        position: { lat: location.lat, lng: location.lng },
        map: googleMapRef.current,
        title: location.name,
        icon: {
          path: window.google.maps.SymbolPath.CIRCLE,
          scale: 10,
          fillColor: "#53B552",
          fillOpacity: 1,
          strokeColor: "#ffffff",
          strokeWeight: 3
        }
      });

      marker.addListener('click', () => {
        handleLocationSelect(location);
        googleMapRef.current?.panTo({ lat: location.lat, lng: location.lng });
      });

      markersRef.current.push(marker);
    });
  }, [displayedLocations, mapLoaded]);

  const handleLocationSelect = (location: EcoLocation) => {
    setSelectedLocation(location);
  };

  const handleCardClick = (location: EcoLocation) => {
    setSelectedLocation(location);
    if (googleMapRef.current) {
      googleMapRef.current.panTo({ lat: location.lat, lng: location.lng });
      googleMapRef.current.setZoom(16);
    }
  };

  const handleNavigateToDetail = () => {
    if (selectedLocation) {
      // TODO: Navigate to detail page
      alert(`Navigating to detail page for: ${selectedLocation.name}`);
      // In real app: router.push(`/location/${selectedLocation.id}`);
    }
  };

  const handleCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const pos = {
            lat: position.coords.latitude,
            lng: position.coords.longitude
          };
          setUserLocation(pos);
          if (googleMapRef.current) {
            googleMapRef.current.setCenter(pos);
            googleMapRef.current.setZoom(15);
          }
        },
        (error) => {
          console.error('Error getting location:', error);
          alert('Unable to get your location');
        }
      );
    }
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    setIsDragging(true);
    setStartY(e.touches[0].clientY);
    setStartHeight(sheetHeight);
    document.body.style.overflow = 'hidden';
  };

  const handleTouchMove = (e: TouchEvent) => {
    if (!isDragging) return;
    
    const deltaY = startY - e.touches[0].clientY;
    const windowHeight = window.innerHeight;
    const deltaPercent = (deltaY / windowHeight) * 100;
    
    let newHeight = startHeight + deltaPercent;
    newHeight = Math.max(15, Math.min(90, newHeight));
    
    setSheetHeight(newHeight);
  };

  const handleTouchEnd = () => {
    setIsDragging(false);
    document.body.style.overflow = '';
    
    if (sheetHeight < 25) {
      setSheetHeight(15);
    } else if (sheetHeight < 50) {
      setSheetHeight(40);
    } else if (sheetHeight < 70) {
      setSheetHeight(65);
    } else {
      setSheetHeight(90);
    }
  };

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('touchmove', handleTouchMove, { passive: false });
      document.addEventListener('touchend', handleTouchEnd);
      
      return () => {
        document.removeEventListener('touchmove', handleTouchMove);
        document.removeEventListener('touchend', handleTouchEnd);
      };
    }
  }, [isDragging, startY, startHeight]);

  return (
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      <div className="w-full max-w-md bg-gray-50 h-screen shadow-2xl relative flex flex-col overflow-hidden">
        {/* Map Container */}
        <div className="flex-1 relative bg-[#E9F5EB] w-full overflow-hidden">
          {/* Search Bar */}
          <div className="absolute top-5 left-4 right-4 z-10">
            <div className="bg-white rounded-full shadow-lg flex items-center p-3 transition-transform active:scale-95">
              <a href="/homepage">
                <ChevronLeft className="text-gray-500 mr-2 cursor-pointer hover:text-green-600" />
              </a>
              <Search size={18} className="text-green-600 mr-2" />
              <input
                type="text"
                placeholder="Search for a location..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 outline-none text-gray-700 placeholder:text-gray-400 bg-transparent font-semibold"
              />
              {isSearching && (
                <div className="animate-spin h-4 w-4 border-2 border-green-600 border-t-transparent rounded-full"></div>
              )}
            </div>
          </div>

          {/* Current Location Button */}
          <button 
            onClick={handleCurrentLocation}
            className="absolute top-24 right-4 z-10 bg-white p-3 rounded-full shadow-lg hover:bg-gray-50 transition-colors active:scale-95"
          >
            <Navigation size={20} className="text-green-600" />
          </button>

          {/* Google Map */}
          <div ref={mapRef} className="w-full h-full" />
          
          {!mapLoaded && (
            <div className="absolute inset-0 flex items-center justify-center bg-[#E9F5EB]">
              <div className="text-center">
                <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-green-600 border-r-transparent mb-2"></div>
                <p className="text-gray-600 font-semibold">Loading map...</p>
              </div>
            </div>
          )}
        </div>

        {/* Bottom Sheet with Recommendations */}
        <div 
          ref={sheetRef}
          style={{ 
            height: `${sheetHeight}vh`,
            touchAction: 'none'
          }}
          className={`bg-white rounded-t-3xl shadow-[0_-5px_15px_rgba(0,0,0,0.15)] z-10 shrink-0 relative overflow-hidden ${isDragging ? '' : 'transition-all duration-300 ease-out'}`}
        >
          {/* Drag Handle */}
          <div 
            className="w-full flex justify-center py-4 touch-none"
            onTouchStart={handleTouchStart}
          >
            <div className="w-16 h-1.5 bg-gray-300 rounded-full"></div>
          </div>

          <div 
            className="px-6 pb-6 overflow-y-auto overscroll-contain scrollbar-hide" 
            style={{ height: 'calc(100% - 56px)' }}
            onTouchStart={(e) => {
              if (sheetHeight < 60) {
                e.stopPropagation();
              }
            }}
          >
            {/* Selected Location Card */}
            {selectedLocation ? (
              <div className="mb-4">
                <div className="bg-[#F9FFF9] border border-green-100 rounded-xl p-4 mb-3 flex items-start gap-3 shadow-sm">
                  <div className="bg-green-100 p-2.5 rounded-full shrink-0 mt-0.5">
                    <MapPin size={20} className="text-green-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-green-700 text-xs font-bold mb-1 uppercase tracking-wide">
                      Selected Location
                    </p>
                    <p className="text-gray-900 text-base font-bold leading-tight mb-1 truncate">
                      {selectedLocation.name}
                    </p>
                    <p className="text-gray-600 text-sm leading-tight line-clamp-2">
                      {selectedLocation.address}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full font-semibold">
                        {selectedLocation.distance}
                      </span>
                      <span className="text-xs text-yellow-600 font-semibold">
                        ★ {selectedLocation.rating}
                      </span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={handleNavigateToDetail}
                  className="w-full bg-[#53B552] hover:bg-green-600 active:bg-green-700 text-white text-lg font-bold py-3 rounded-full shadow-lg transition-all transform active:scale-[0.98]"
                >
                  View Details
                </button>
              </div>
            ) : (
              <div className="mb-4">
                <h3 className="text-gray-900 text-lg font-bold mb-1">
                  {searchQuery.trim() !== '' ? 'Search Results' : 'Nearby Eco Locations'}
                </h3>
                <p className="text-gray-500 text-sm mb-3">
                  {searchQuery.trim() !== '' 
                    ? `Found ${displayedLocations.length} results for "${searchQuery}"`
                    : 'Select a location from the map or list below'}
                </p>
              </div>
            )}

            {/* Loading State */}
            {(isLoadingRecommendations || isSearching) && (
              <div className="flex justify-center items-center py-8">
                <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-green-600 border-r-transparent"></div>
              </div>
            )}

            {/* Empty State */}
            {!isLoadingRecommendations && !isSearching && displayedLocations.length === 0 && (
              <div className="text-center py-8">
                <p className="text-gray-500">No locations found</p>
              </div>
            )}

            {/* Recommendations Grid */}
            {!isLoadingRecommendations && displayedLocations.length > 0 && (
              <div className="grid grid-cols-2 gap-3 pb-2">
                {displayedLocations.map((location) => (
                  <div
                    key={location.id}
                    onClick={() => handleCardClick(location)}
                    className={`bg-white rounded-xl overflow-hidden shadow-md cursor-pointer transition-all transform active:scale-[0.95] ${
                      selectedLocation?.id === location.id ? 'ring-2 ring-green-500' : ''
                    }`}
                  >
                    <div className="relative h-28 bg-gray-200">
                      <img
                        src={location.image}
                        alt={location.name}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <div className="p-3">
                      <h4 className="font-bold text-gray-900 text-sm mb-1 line-clamp-1">
                        {location.name}
                      </h4>
                      <p className="text-xs text-gray-500 mb-2 line-clamp-1">{location.distance}</p>
                      <div className="flex items-center justify-between">
                        <span className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded-full font-semibold">
                          {location.type}
                        </span>
                        <span className="text-xs text-yellow-600 font-semibold">
                          ★ {location.rating}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <footer className="bg-white shadow-[0_-2px_6px_rgba(0,0,0,0.05)] shrink-0 z-20">
          <div className="h-0.5 bg-gradient-to-r from-transparent via-green-300 to-transparent opacity-70"></div>
          <div className="flex justify-around items-center px-2 pt-2 pb-3">
            <a href="/homepage" className="flex flex-col items-center justify-center w-1/4 text-green-600">
              <Home className="size-6" strokeWidth={2.0} />
              <span className="text-xs font-medium mt-0.5">Home</span>
            </a>
            <a href="#" className="flex flex-col items-center justify-center w-1/4 text-gray-400 hover:text-green-600 transition-colors">
              <MapPin className="size-6" strokeWidth={2.0} />
              <span className="text-xs font-medium mt-0.5">Planning</span>
            </a>
            <a href="#" className="flex flex-col items-center justify-center w-1/4 text-gray-400 hover:text-green-600 transition-colors">
              <Bot className="size-6" strokeWidth={1.5} />
              <span className="text-xs font-medium mt-0.5">Ecobot</span>
            </a>
            <a href="/user_page/profile_page" className="flex flex-col items-center justify-center w-1/4 text-gray-400 hover:text-green-600 transition-colors">
              <User className="size-6" strokeWidth={1.5} />
              <span className="text-xs font-medium mt-0.5">User</span>
            </a>
          </div>
        </footer>
      </div>
    </div>
  );
}