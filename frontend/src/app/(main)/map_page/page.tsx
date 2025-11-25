"use client";

import React, { useState, useEffect, useRef } from "react";
import { Search, Home, MapPin, Bot, User, ChevronLeft, Navigation } from "lucide-react";
import { api, AutocompletePrediction, PlaceDetails, Position } from "@/lib/api";
import { useRouter, useSearchParams } from "next/navigation";
import { useGoogleMaps } from "@/lib/useGoogleMaps";
import { flushSync } from 'react-dom';
import { url } from "inspector";

interface PlaceDetailsWithDistance extends PlaceDetails {
  distanceText: string;
}

const addDistanceText = async (details: PlaceDetails, userPos: Position): Promise<PlaceDetailsWithDistance> => {
  const destination: Position = details.geometry.location;
  const distanceKm = await api.birdDistance(userPos, destination);
  const distanceText = distanceKm < 1 
    ? `${Math.round(distanceKm * 1000)}m away`
    : `${distanceKm.toFixed(1)}km away`;
  
  return {
    ...details,
    distanceText
  };
};

function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T>(undefined);
  useEffect(() => {
    ref.current = value;
  });
  return ref.current;
}

export default function MapPage() {
  const router = useRouter();
  const { isLoaded, loadError } = useGoogleMaps();
  const [selectedLocation, setSelectedLocation] = useState<PlaceDetailsWithDistance | null>(null);
  const urlQuery = useSearchParams().get("q") || "";
  const [searchQuery, setSearchQuery] = useState(urlQuery);
  const prevSearchQuery = usePrevious(searchQuery);
  const [locations, setLocations] = useState<PlaceDetailsWithDistance[]>([]);
  const [searchResults, setSearchResults] = useState<PlaceDetailsWithDistance[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [autocompletePredictions, setAutocompletePredictions] = useState<AutocompletePrediction[]>([]);
  const [isLoadingRecommendations, setIsLoadingRecommendations] = useState(true);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [sheetHeight, setSheetHeight] = useState(40);
  const [isDragging, setIsDragging] = useState(false);
  const [startY, setStartY] = useState(0);
  const [startHeight, setStartHeight] = useState(40);
  const [userLocation, setUserLocation] = useState<Position>({ lat: 10.7756, lng: 106.7019 });
  const [enableTransition, setEnableTransition] = useState(true);
  const [sessionToken, setSessionToken] = useState<string | null>(null);

  const mapRef = useRef<HTMLDivElement>(null);
  const googleMapRef = useRef<google.maps.Map | null>(null);
  const markersRef = useRef<google.maps.Marker[]>([]);
  const userMarkerRef = useRef<google.maps.Marker | null>(null);
  const sheetRef = useRef<HTMLDivElement>(null);
  const searchTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const initialLoadRef = useRef(true);

  // This is for handling browser back/forward navigation
  useEffect(() => {
    if (urlQuery !== searchQuery) {
      setSearchQuery(urlQuery);
    }
  }, [urlQuery]);

  // Fetch recommendations on component mount
  useEffect(() => {
    if (!urlQuery) {
      fetchRecommendations();
      initialLoadRef.current = false;
    }
  }, [userLocation]);

  // Fetch autocomplete predictions as user types
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    // Clear predictions if search is empty or not focused
    if (searchQuery.trim() === '' || !isSearchFocused) {
      setAutocompletePredictions([]);
      if (searchQuery.trim() === '') {
        setSearchResults([]);
        setSelectedLocation(null);
        setSheetHeight(40);
        setSessionToken(null);
        if (locations.length === 0) {
          fetchRecommendations();
        }
        // Clear URL query if search is empty
        if (urlQuery) {
          router.push('/map_page', { scroll: false });
        }
      }
      return;
    }

    if (searchQuery.trim().length < 4) {
      setAutocompletePredictions([]);
      return;
    }

    // Fetch autocomplete predictions with debounce
    searchTimeoutRef.current = setTimeout(async () => {
      try {
        setIsSearching(true);
        
        // 🔑 PASS TOKEN: Send the token with the autocomplete request
        const response = await api.searchPlaces({
        query: searchQuery,
        user_location: userLocation,
        radius: 5000,
        session_token: sessionToken, 
      });
        
        setAutocompletePredictions(response.predictions.slice(0, 8));
      } catch (error) {
        console.error('Autocomplete failed:', error);
        setAutocompletePredictions([]);
      } finally {
        setIsSearching(false);
      }
    }, 300); // Faster debounce for autocomplete

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchQuery, userLocation, isSearchFocused, urlQuery, router]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      // Check if click is outside the search bar container
      if (isSearchFocused && !target.closest('.search-container')) {
        setIsSearchFocused(false);
        setEnableTransition(true); // Enable transition for smooth restoration
        // Restore sheet height based on content
        if (searchResults.length > 0) {
          setSheetHeight(65);
        } else if (locations.length > 0) {
          setSheetHeight(65);
        } else {
          setSheetHeight(40);
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('touchstart', handleClickOutside as any);
    
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside as any);
    };
  }, [isSearchFocused, searchResults, locations]);

// Handle URL query parameter changes (browser back/forward)
useEffect(() => {
  if (urlQuery && urlQuery !== searchQuery) {
    setSearchQuery(urlQuery);
    // Optionally trigger a search for the URL query
    const performSearch = async () => {
      try {
        const response = await api.searchPlaces({
          query: urlQuery,
          user_location: userLocation,
          radius: 5000,
        });
        
        const detailedResults = await Promise.all(
          response.predictions.slice(0, 8).map(async (prediction) => {
            try {
              const details = await api.getPlaceDetails(prediction.place_id);
              return await addDistanceText(details, userLocation);
            } catch (error) { return null; }
          })
        );
        
        const finalResults = detailedResults.filter((r): r is PlaceDetailsWithDistance => r !== null);
        setSearchResults(finalResults);
        
        if (finalResults.length > 0) {
          setSheetHeight(70);
          setSelectedLocation(finalResults[0]); // Auto-select first result
        }
      } catch (error) {
        console.error('Search failed:', error);
      }
    };
    
    performSearch();
  }
}, [urlQuery]);

  const handleSelectPrediction = async (prediction: AutocompletePrediction) => {
    // Update search query and close dropdown
    setSearchQuery(prediction.description);
    setIsSearchFocused(false);
    setAutocompletePredictions([]);
    setEnableTransition(true); // Enable transition for smooth expansion
    
    try {
      // Fetch full details using api
      const fullDetails = await api.getPlaceDetails(
        prediction.place_id,
        sessionToken
      );
      const withDistance = await addDistanceText(fullDetails, userLocation);
      
      setSelectedLocation(withDistance);
      setSearchResults([withDistance]);
      setSheetHeight(65); // Expand sheet to show result
      
      if (googleMapRef.current) {
        googleMapRef.current.panTo({ 
          lat: withDistance.geometry.location.lat, 
          lng: withDistance.geometry.location.lng 
        });
        googleMapRef.current.setZoom(16);
      }
      setSessionToken(null);
      // Update URL with the selected search
      router.push(`/map_page?q=${encodeURIComponent(prediction.description)}`, { scroll: false });
    } catch (error) {
      console.error('Failed to fetch place details:', error);
    }
  };

  const fetchRecommendations = async () => {
    setIsLoadingRecommendations(true);
    try {
      // Use searchPlaces with eco-friendly types for recommendations
      const response = await api.searchPlaces({
        query: "park",
        user_location: userLocation,
        radius: 5000, // 5km radius
        place_types: "park|tourist_attraction|point_of_interest",
      });
      
      if (!response || !response.predictions) {
        console.error('Invalid response from searchPlaces');
        setLocations([]);
        return;
      }
      
      // Fetch details for recommendations to get full info
      const detailedRecommendations = await Promise.all(
        response.predictions.slice(0, 8).map(async (prediction: AutocompletePrediction) => {
          try {
            const details = await api.getPlaceDetails(prediction.place_id);
            return await addDistanceText(details, userLocation);
          } catch (error) {
            console.error(`Failed to fetch details for ${prediction.place_id}:`, error);
            return null;
          }
        })
      );
      
      setLocations(detailedRecommendations.filter((r): r is PlaceDetailsWithDistance => r !== null));
      setSheetHeight(65);
    } catch (error) {
      console.error('Failed to fetch recommendations:', error);
      setLocations([]);
    } finally {
      setIsLoadingRecommendations(false);
    }
  };

  const displayedLocations = searchResults.length > 0 ? searchResults : (!isSearchFocused ? locations : []);

  useEffect(() => {
    if (!isLoaded || !mapRef.current) return;
    
    // Initialize map directly
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
      disableDefaultUI: true,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: false,
      panControl: false,
      zoomControl: false,

      gestureHandling: 'cooperative'
    });

    googleMapRef.current = map;
    setMapLoaded(true);
  }, [isLoaded]);

  if (loadError) {
    return <div>Error loading map: {loadError.message}</div>;
  }

  useEffect(() => {
    if (!googleMapRef.current || !mapLoaded) return;

    markersRef.current.forEach(marker => marker.setMap(null));
    markersRef.current = [];

    displayedLocations.forEach(location => {
      const marker = new window.google.maps.Marker({
        position: { lat: location.geometry.location.lat, lng: location.geometry.location.lng },
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
        googleMapRef.current?.panTo({ lat: location.geometry.location.lat, lng: location.geometry.location.lng });
      });

      markersRef.current.push(marker);
    });
  }, [displayedLocations, mapLoaded]);

  useEffect(() => {
    if (!googleMapRef.current || !mapLoaded) return;

    if (!userMarkerRef.current) {
      userMarkerRef.current = new window.google.maps.Marker({
        map: googleMapRef.current,
        icon: {
          path: `
            M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z
          `,
          fillColor: '#4285F4', // Google Blue
          fillOpacity: 1,
          strokeWeight: 0,
          rotation: 0,
          scale: 1.5,
          anchor: new window.google.maps.Point(12, 24),
        },
      });
    }

    // Update the marker's position to the latest userLocation
    userMarkerRef.current.setPosition({
      lat: userLocation.lat,
      lng: userLocation.lng
    });

  }, [userLocation, mapLoaded]);

  const handleLocationSelect = (location: PlaceDetailsWithDistance) => {
    setSelectedLocation(location);
  };

  const handleCardClick = async (location: PlaceDetailsWithDistance) => {
    try {
      // Fetch full details using api
      const fullDetails = await api.getPlaceDetails(location.place_id);
      const withDistance = await addDistanceText(fullDetails, userLocation);
      
      setSelectedLocation(withDistance);
      if (googleMapRef.current) {
        googleMapRef.current.panTo({ lat: withDistance.geometry.location.lat, lng: withDistance.geometry.location.lng });
        googleMapRef.current.setZoom(16);
      }
    } catch (error) {
      console.error('Failed to fetch place details:', error);
      // Fallback to existing location data
      setSelectedLocation(location);
      if (googleMapRef.current) {
        googleMapRef.current.panTo({ lat: location.geometry.location.lat, lng: location.geometry.location.lng });
        googleMapRef.current.setZoom(16);
      }
    }
  };

  const handleNavigateToDetail = () => {
    if (selectedLocation) {
      // Navigate to location detail page with place_id
      router.push(`/location/${selectedLocation.place_id}`);
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
    <div className="min-h-screen w-full bg-white sm:bg-gray-200 sm:flex sm:justify-center">
      <div className="w-full h-screen relative flex flex-col overflow-hidden sm:max-w-md sm:shadow-2xl">
        {/* Map Container */}
        <div className="flex-1 relative bg-[#E9F5EB] w-full overflow-hidden">
          {/* Search Bar */}
          <div className="absolute top-5 left-4 right-4 z-10 search-container">
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
                onFocus={() => {
                 flushSync(() => {
                 setEnableTransition(false);
                 setSheetHeight(8);
                 });
                 
                 if (window.google?.maps) {
                  const token = new google.maps.places.AutocompleteSessionToken();
                  setSessionToken(token.toString());
                 }

                 setIsSearchFocused(true);
                 setTimeout(() => setEnableTransition(true), 50);
                }}
                className="flex-1 outline-none text-gray-700 placeholder:text-gray-400 bg-transparent font-semibold"
              />
              {isSearching && (
                <div className="animate-spin h-4 w-4 border-2 border-green-600 border-t-transparent rounded-full"></div>
              )}
            </div>

            {/* Autocomplete Dropdown */}
            {isSearchFocused && autocompletePredictions.length > 0 && (
              <div className="mt-2 bg-white rounded-2xl shadow-xl overflow-hidden max-h-96 overflow-y-auto">
                {autocompletePredictions.map((prediction) => (
                  <div
                    key={prediction.place_id}
                    onClick={() => handleSelectPrediction(prediction)}
                    className="p-4 hover:bg-gray-50 active:bg-gray-100 cursor-pointer border-b border-gray-100 last:border-b-0 transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      <MapPin size={18} className="text-green-600 mt-1 shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-gray-900 font-semibold text-sm truncate">
                          {prediction.structured_formatting?.main_text}
                        </p>
                        <p className="text-gray-500 text-xs mt-0.5 line-clamp-1">
                          {prediction.structured_formatting?.secondary_text}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
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
          className={`bg-white rounded-t-3xl shadow-[0_-5px_15px_rgba(0,0,0,0.15)] z-10 shrink-0 relative overflow-hidden ${isDragging || !enableTransition ? '' : 'transition-all duration-300 ease-out'}`}
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
                      {selectedLocation.formatted_address}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full font-semibold">
                        {selectedLocation.distanceText}
                      </span>
                      {selectedLocation.rating && selectedLocation.rating > 0 && (
                        <span className="text-xs text-yellow-600 font-semibold">
                          ★ {selectedLocation.rating.toFixed(1)}
                        </span>
                      )}
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
              <>
                {/* Title Section - Only show when NOT searching */}
                {!isSearchFocused && (
                  <div className="mb-4">
                    <h3 className="text-gray-900 text-lg font-bold mb-1">
                      {searchResults.length > 0 ? 'Search Results' : 'Nearby Eco Locations'}
                    </h3>
                    <p className="text-gray-500 text-sm mb-3">
                      {searchResults.length > 0
                        ? `Found ${searchResults.length} results`
                        : 'Select a location from the map or list below'}
                    </p>
                  </div>
                )}

                {/* Show message when search is focused */}
                {isSearchFocused && autocompletePredictions.length === 0 && sheetHeight > 15 && (
                  <div className="text-center py-12">
                    <MapPin size={48} className="text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-400 text-sm">
                      {searchQuery.trim().length < 2 
                        ? 'Type at least 2 characters to search...' 
                        : 'Searching...'}
                    </p>
                  </div>
                )}
              </>
            )}

            {/* Loading State - Only when NOT searching */}
            {(isLoadingRecommendations || isSearching) && displayedLocations.length === 0 && !isSearchFocused && (
              <div className="flex justify-center items-center py-8">
                <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-green-600 border-r-transparent"></div>
              </div>
            )}

            {/* Empty State - Only when NOT searching */}
            {!isLoadingRecommendations && !isSearching && !isSearchFocused && displayedLocations.length === 0 && (
              <div className="text-center py-8">
                <p className="text-gray-500">No locations found</p>
              </div>
            )}

            {/* Recommendations Grid - Only show when NOT searching */}
            {!isSearching && !isSearchFocused && displayedLocations.length > 0 && (
              <div className="grid grid-cols-2 gap-3 pb-2">
                {displayedLocations.map((location) => (
                  <div
                    key={location.place_id}
                    onClick={() => handleCardClick(location)}
                    className={`bg-white rounded-xl overflow-hidden shadow-md cursor-pointer transition-all transform active:scale-[0.95] ${
                      selectedLocation?.place_id === location.place_id ? 'ring-2 ring-green-500' : ''
                    }`}
                  >
                    <div className="relative h-28 bg-gray-200">
                      <img
                        src={location.photos?.[0]?.photo_url || 'https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=400'}
                        alt={location.name}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.currentTarget.src = 'https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=400';
                        }}
                        loading="lazy"
                        decoding="async"
                      />
                    </div>
                    <div className="p-3">
                      <h4 className="font-bold text-gray-900 text-sm mb-1 line-clamp-1">
                        {location.name}
                      </h4>
                      <p className="text-xs text-gray-500 mb-2 line-clamp-1">{location.distanceText}</p>
                      <div className="flex items-center justify-between">
                        <span className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded-full font-semibold">
                          {location.types[0]?.replace(/_/g, ' ')}
                        </span>
                        {location.rating && location.rating > 0 && (
                          <span className="text-xs text-yellow-600 font-semibold">
                            ★ {location.rating.toFixed(1)}
                          </span>
                        )}
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