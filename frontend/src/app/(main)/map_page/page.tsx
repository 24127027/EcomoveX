"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Search,
  Home,
  MapPin,
  Bot,
  User,
  ChevronLeft,
  Navigation,
} from "lucide-react";
import { api, AutocompletePrediction, PlaceDetails, Position } from "@/lib/api";
import { useRouter, useSearchParams } from "next/navigation";
import { useGoogleMaps } from "@/lib/useGoogleMaps";

interface PlaceDetailsWithDistance extends PlaceDetails {
  distanceText: string;
}

const addDistanceText = async (
  details: PlaceDetails,
  userPos: Position
): Promise<PlaceDetailsWithDistance> => {
  const destination: Position = details.geometry.location;
  const distanceKm = await api.birdDistance(userPos, destination);
  const distanceText =
    distanceKm < 1
      ? `${Math.round(distanceKm * 1000)}m away`
      : `${distanceKm.toFixed(1)}km away`;

  return {
    ...details,
    distanceText,
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
  const searchParams = useSearchParams();
  const { isLoaded, loadError } = useGoogleMaps();

  const urlQuery = searchParams.get("q") || "";
  const latParam = searchParams.get("lat");
  const lngParam = searchParams.get("lng");

  const [userLocation, setUserLocation] = useState<Position>(() => {
    if (latParam && lngParam) {
      const lat = parseFloat(latParam);
      const lng = parseFloat(lngParam);
      if (!isNaN(lat) && !isNaN(lng)) {
        return { lat, lng };
      }
    }
    return { lat: 10.7756, lng: 106.7019 };
  });

  const [selectedLocation, setSelectedLocation] =
    useState<PlaceDetailsWithDistance | null>(null);

  const [searchQuery, setSearchQuery] = useState(urlQuery);
  const prevSearchQuery = usePrevious(searchQuery);

  const [locations, setLocations] = useState<PlaceDetailsWithDistance[]>([]);
  const [searchResults, setSearchResults] = useState<
    PlaceDetailsWithDistance[]
  >([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isLoadingRecommendations, setIsLoadingRecommendations] =
    useState(true);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [sheetHeight, setSheetHeight] = useState(40);

  // Drag sheet state
  const [isDragging, setIsDragging] = useState(false);
  const [startY, setStartY] = useState(0);
  const [startHeight, setStartHeight] = useState(40);

  const mapRef = useRef<HTMLDivElement>(null);
  const googleMapRef = useRef<google.maps.Map | null>(null);
  const markersRef = useRef<google.maps.Marker[]>([]);
  const sheetRef = useRef<HTMLDivElement>(null);
  const searchTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const initialLoadRef = useRef(true);

  useEffect(() => {
    if (latParam && lngParam) {
      const newLat = parseFloat(latParam);
      const newLng = parseFloat(lngParam);
      if (!isNaN(newLat) && !isNaN(newLng)) {
        const newPos = { lat: newLat, lng: newLng };
        if (
          newPos.lat !== userLocation.lat ||
          newPos.lng !== userLocation.lng
        ) {
          setUserLocation(newPos);
          if (googleMapRef.current) {
            googleMapRef.current.setCenter(newPos);
            googleMapRef.current.setZoom(14);
          }
        }
      }
    }
  }, [latParam, lngParam, mapLoaded]);

  useEffect(() => {
    if (urlQuery !== searchQuery) {
      setSearchQuery(urlQuery);
    }
  }, [urlQuery]);

  // Fetch recommendations khi mới vào (nếu không có search query)
  useEffect(() => {
    if (!urlQuery && !searchQuery) {
      fetchRecommendations();
      initialLoadRef.current = false;
    }
  }, [userLocation]); // Chạy lại khi location thay đổi để lấy gợi ý quanh đó

  // --- MAIN SEARCH EFFECT ---
  useEffect(() => {
    // --- Part 1: Update URL (Debounce) ---
    const handler = setTimeout(() => {
      // Chỉ push URL nếu query thay đổi và khác URL hiện tại
      if (searchQuery !== urlQuery) {
        const params = new URLSearchParams();
        if (searchQuery.trim()) params.set("q", searchQuery);

        // [QUAN TRỌNG] Giữ lại lat/lng trên URL nếu có
        if (latParam) params.set("lat", latParam);
        if (lngParam) params.set("lng", lngParam);

        router.push(`/map_page?${params.toString()}`, { scroll: false });
      }
    }, 500);

    // --- Part 2: Call API Search ---
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (searchQuery.trim() === "") {
      setSearchResults([]);
      setIsSearching(false);
      setSelectedLocation(null);
      setSheetHeight(40);
      // Nếu xóa hết text search thì load lại recommend
      if (locations.length === 0) fetchRecommendations();
      return () => clearTimeout(handler);
    }

    // Logic gọi API (chạy khi query đổi hoặc location đổi)
    if (prevSearchQuery !== searchQuery || initialLoadRef.current) {
      setIsSearching(true);
      searchTimeoutRef.current = setTimeout(async () => {
        try {
          // console.log("Searching for:", searchQuery, "at", userLocation);
          const response = await api.searchPlaces({
            query: searchQuery,
            user_location: userLocation,
            radius: 5000,
          });

          const detailedResults = await Promise.all(
            response.predictions.slice(0, 6).map(async (prediction) => {
              try {
                const details = await api.getPlaceDetails(prediction.place_id);
                return await addDistanceText(details, userLocation);
              } catch (error) {
                return null;
              }
            })
          );

          const finalResults = detailedResults.filter(
            (r): r is PlaceDetailsWithDistance => r !== null
          );
          setSearchResults(finalResults);

          if (finalResults.length > 0) {
            setSheetHeight(70);
          } else {
            setSelectedLocation(null);
          }
        } catch (error) {
          console.error("Search failed:", error);
          setSearchResults([]);
        } finally {
          setIsSearching(false);
          initialLoadRef.current = false; // Đánh dấu đã load xong lần đầu
        }
      }, 500);
    }

    return () => {
      clearTimeout(handler);
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchQuery, userLocation, router, urlQuery, latParam, lngParam]); // Thêm dependencies

  const fetchRecommendations = async () => {
    setIsLoadingRecommendations(true);
    try {
      const response = await api.searchPlaces({
        query: "park",
        user_location: userLocation,
        radius: 5000,
        place_types: "park|tourist_attraction|point_of_interest",
      });

      if (!response || !response.predictions) {
        setLocations([]);
        return;
      }

      const detailedRecommendations = await Promise.all(
        response.predictions.slice(0, 8).map(async (prediction) => {
          try {
            const details = await api.getPlaceDetails(prediction.place_id);
            return await addDistanceText(details, userLocation);
          } catch (error) {
            return null;
          }
        })
      );

      setLocations(
        detailedRecommendations.filter(
          (r): r is PlaceDetailsWithDistance => r !== null
        )
      );
      setSheetHeight(65);
    } catch (error) {
      console.error("Failed to fetch recommendations:", error);
      setLocations([]);
    } finally {
      setIsLoadingRecommendations(false);
    }
  };

  const displayedLocations =
    searchQuery.trim() !== "" ? searchResults : locations;

  // --- MAP INITIALIZATION ---
  useEffect(() => {
    if (!isLoaded || !mapRef.current) return;

    const map = new window.google.maps.Map(mapRef.current, {
      center: userLocation,
      zoom: 14,
      styles: [
        {
          featureType: "poi",
          elementType: "labels",
          stylers: [{ visibility: "off" }],
        },
      ],
      disableDefaultUI: true,
      gestureHandling: "cooperative",
    });

    googleMapRef.current = map;
    setMapLoaded(true);
  }, [isLoaded]);

  // --- MARKERS MANAGEMENT ---
  useEffect(() => {
    if (!googleMapRef.current || !mapLoaded) return;

    // Clear old markers
    markersRef.current.forEach((marker) => marker.setMap(null));
    markersRef.current = [];

    // Add new markers
    displayedLocations.forEach((location) => {
      const marker = new window.google.maps.Marker({
        position: {
          lat: location.geometry.location.lat,
          lng: location.geometry.location.lng,
        },
        map: googleMapRef.current,
        title: location.name,
        icon: {
          path: window.google.maps.SymbolPath.CIRCLE,
          scale: 10,
          fillColor: "#53B552",
          fillOpacity: 1,
          strokeColor: "#ffffff",
          strokeWeight: 3,
        },
      });

      marker.addListener("click", () => {
        handleLocationSelect(location);
        googleMapRef.current?.panTo({
          lat: location.geometry.location.lat,
          lng: location.geometry.location.lng,
        });
      });

      markersRef.current.push(marker);
    });
  }, [displayedLocations, mapLoaded]);

  const handleLocationSelect = (location: PlaceDetailsWithDistance) => {
    setSelectedLocation(location);
  };

  const handleCardClick = async (location: PlaceDetailsWithDistance) => {
    try {
      const fullDetails = await api.getPlaceDetails(location.place_id);
      const withDistance = await addDistanceText(fullDetails, userLocation);
      setSelectedLocation(withDistance);
      if (googleMapRef.current) {
        googleMapRef.current.panTo(withDistance.geometry.location);
        googleMapRef.current.setZoom(16);
      }
    } catch (error) {
      setSelectedLocation(location); // Fallback
      if (googleMapRef.current) {
        googleMapRef.current.panTo(location.geometry.location);
        googleMapRef.current.setZoom(16);
      }
    }
  };

  const handleNavigateToDetail = () => {
    if (selectedLocation) {
      router.push(`/location/${selectedLocation.place_id}`);
    }
  };

  const handleCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const pos = {
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          };
          setUserLocation(pos);

          // [FIX] Update URL khi bấm nút định vị
          const params = new URLSearchParams(window.location.search);
          params.set("lat", pos.lat.toString());
          params.set("lng", pos.lng.toString());
          router.replace(`/map_page?${params.toString()}`);

          if (googleMapRef.current) {
            googleMapRef.current.setCenter(pos);
            googleMapRef.current.setZoom(15);
          }
        },
        (error) => {
          console.error("Error getting location:", error);
          alert("Unable to get your location");
        }
      );
    }
  };

  // --- BOTTOM SHEET GESTURES ---
  const handleTouchStart = (e: React.TouchEvent) => {
    setIsDragging(true);
    setStartY(e.touches[0].clientY);
    setStartHeight(sheetHeight);
    document.body.style.overflow = "hidden";
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
    document.body.style.overflow = "";
    if (sheetHeight < 25) setSheetHeight(15);
    else if (sheetHeight < 50) setSheetHeight(40);
    else if (sheetHeight < 70) setSheetHeight(65);
    else setSheetHeight(90);
  };

  useEffect(() => {
    if (isDragging) {
      document.addEventListener("touchmove", handleTouchMove, {
        passive: false,
      });
      document.addEventListener("touchend", handleTouchEnd);
      return () => {
        document.removeEventListener("touchmove", handleTouchMove);
        document.removeEventListener("touchend", handleTouchEnd);
      };
    }
  }, [isDragging, startY, startHeight]);

  if (loadError) return <div>Error loading map: {loadError.message}</div>;

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

        {/* Bottom Sheet */}
        <div
          ref={sheetRef}
          style={{ height: `${sheetHeight}vh`, touchAction: "none" }}
          className={`bg-white rounded-t-3xl shadow-[0_-5px_15px_rgba(0,0,0,0.15)] z-10 shrink-0 relative overflow-hidden ${
            isDragging ? "" : "transition-all duration-300 ease-out"
          }`}
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
            style={{ height: "calc(100% - 56px)" }}
            onTouchStart={(e) => {
              if (sheetHeight < 60) e.stopPropagation();
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
                      {selectedLocation.rating &&
                        selectedLocation.rating > 0 && (
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
              <div className="mb-4">
                <h3 className="text-gray-900 text-lg font-bold mb-1">
                  {searchQuery.trim() !== ""
                    ? "Search Results"
                    : "Nearby Eco Locations"}
                </h3>
                <p className="text-gray-500 text-sm mb-3">
                  {searchQuery.trim() !== ""
                    ? `Found ${displayedLocations.length} results`
                    : "Select a location from the map"}
                </p>
              </div>
            )}

            {/* Loading */}
            {(isLoadingRecommendations || isSearching) &&
              displayedLocations.length === 0 && (
                <div className="flex justify-center items-center py-8">
                  <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-green-600 border-r-transparent"></div>
                </div>
              )}

            {/* Results Grid */}
            {!isSearching && displayedLocations.length > 0 && (
              <div className="grid grid-cols-2 gap-3 pb-2">
                {displayedLocations.map((location) => (
                  <div
                    key={location.place_id}
                    onClick={() => handleCardClick(location)}
                    className={`bg-white rounded-xl overflow-hidden shadow-md cursor-pointer transition-all transform active:scale-[0.95] ${
                      selectedLocation?.place_id === location.place_id
                        ? "ring-2 ring-green-500"
                        : ""
                    }`}
                  >
                    <div className="relative h-28 bg-gray-200">
                      <img
                        src={
                          location.photos?.[0]?.photo_reference
                            ? `https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference=${location.photos[0].photo_reference}&key=${process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY}`
                            : "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=400"
                        }
                        alt={location.name}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.currentTarget.src =
                            "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=400";
                        }}
                      />
                    </div>
                    <div className="p-3">
                      <h4 className="font-bold text-gray-900 text-sm mb-1 line-clamp-1">
                        {location.name}
                      </h4>
                      <p className="text-xs text-gray-500 mb-2 line-clamp-1">
                        {location.distanceText}
                      </p>
                      <div className="flex items-center justify-between">
                        <span className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded-full font-semibold">
                          {location.types?.[0]?.replace(/_/g, " ") || "Spot"}
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
          <div className="h-0.5 bg-linear-to-r from-transparent via-green-300 to-transparent opacity-70"></div>
          <div className="flex justify-around items-center px-2 pt-2 pb-3">
            <a
              href="/user_page/main_page"
              className="flex flex-col items-center justify-center w-1/4 text-gray-400 hover:text-green-600 transition-colors"
            >
              <Home className="size-6" strokeWidth={2.0} />
              <span className="text-xs font-medium mt-0.5">Home</span>
            </a>
            <a
              href="#"
              className="flex flex-col items-center justify-center w-1/4 text-green-600 transition-colors"
            >
              <MapPin className="size-6" strokeWidth={2.0} />
              <span className="text-xs font-medium mt-0.5">Planning</span>
            </a>
            <a
              href="#"
              className="flex flex-col items-center justify-center w-1/4 text-gray-400 hover:text-green-600 transition-colors"
            >
              <Bot className="size-6" strokeWidth={1.5} />
              <span className="text-xs font-medium mt-0.5">Ecobot</span>
            </a>
            <a
              href="/user_page/profile_page"
              className="flex flex-col items-center justify-center w-1/4 text-gray-400 hover:text-green-600 transition-colors"
            >
              <User className="size-6" strokeWidth={1.5} />
              <span className="text-xs font-medium mt-0.5">User</span>
            </a>
          </div>
        </footer>
      </div>
    </div>
  );
}
