"use client";

import React, { useState, useEffect, useRef, Suspense } from "react";
import {
  Search,
  Home,
  MapPin,
  Bot,
  User,
  ChevronLeft,
  Navigation,
  Check,
} from "lucide-react";
import {
  api,
  AutocompletePrediction,
  PlaceDetails,
  Position,
  PlaceSearchResult,
} from "@/lib/api";
import { useRouter, useSearchParams } from "next/navigation";
import { useGoogleMaps } from "@/lib/useGoogleMaps";
import { flushSync } from "react-dom";

interface PlaceDetailsWithDistance extends PlaceDetails {
  distanceText: string;
}

// --- HELPER FUNCTIONS ---
const birdDistance = (pos1: Position, pos2: Position): number => {
  const toRad = (value: number) => (value * Math.PI) / 180;
  const R = 6371;
  const dLat = toRad(pos2.lat - pos1.lat);
  const dLon = toRad(pos2.lng - pos1.lng);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(pos1.lat)) *
      Math.cos(toRad(pos2.lat)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

const addDistanceText = async (
  details: PlaceDetails,
  userPos: Position
): Promise<PlaceDetailsWithDistance> => {
  const destination: Position = details.geometry.location;
  const distanceKm = birdDistance(userPos, destination);
  const distanceText =
    distanceKm < 1
      ? `${Math.round(distanceKm * 1000)}m away`
      : `${distanceKm.toFixed(1)}km away`;

  return {
    ...details,
    distanceText,
  };
};

const convertSearchResultToDetails = (
  result: PlaceSearchResult,
  userPos: Position
): PlaceDetailsWithDistance => {
  const distanceKm = result.location
    ? birdDistance(userPos, result.location)
    : 0;
  const distanceText =
    distanceKm < 1
      ? `${Math.round(distanceKm * 1000)}m away`
      : `${distanceKm.toFixed(1)}km away`;

  return {
    place_id: result.id,
    name: result.displayName?.text || "Unknown Place",
    formatted_address: result.formattedAddress || "",
    geometry: {
      location: result.location || { lat: 0, lng: 0 },
    },
    types: result.types || [],
    photos: result.photos
      ? [
          {
            photo_url: result.photos.photo_url,
            width: result.photos.size[0],
            height: result.photos.size[1],
          },
        ]
      : [],
    sustainable_certified: false,
    distanceText: distanceText,
    rating: 0,
  };
};

function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T>(undefined);
  useEffect(() => {
    ref.current = value;
  });
  return ref.current;
}

const generateSessionToken = () => {
  if (window.google?.maps?.places) {
    return new google.maps.places.AutocompleteSessionToken().toString();
  }
  return crypto.randomUUID();
};

// --- MAIN COMPONENT ---
function MapPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isLoaded, loadError } = useGoogleMaps();

  const urlQuery = searchParams.get("q") || "";
  const latParam = searchParams.get("lat");
  const lngParam = searchParams.get("lng");

  // [NEW] Xác định chế độ Picker
  const mode = searchParams.get("mode");
  const isPickerMode = mode === "picker";

  const [selectedLocation, setSelectedLocation] =
    useState<PlaceDetailsWithDistance | null>(null);
  const [searchQuery, setSearchQuery] = useState(urlQuery);
  const [locations, setLocations] = useState<PlaceDetailsWithDistance[]>([]);
  const [searchResults, setSearchResults] = useState<
    PlaceDetailsWithDistance[]
  >([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [autocompletePredictions, setAutocompletePredictions] = useState<
    AutocompletePrediction[]
  >([]);
  const [isLoadingRecommendations, setIsLoadingRecommendations] =
    useState(true);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [sheetHeight, setSheetHeight] = useState(40);
  const [isDragging, setIsDragging] = useState(false);
  const [startY, setStartY] = useState(0);
  const [startHeight, setStartHeight] = useState(40);
  const [userLocation, setUserLocation] = useState<Position>({
    lat: 10.7756,
    lng: 106.7019,
  });
  const [enableTransition, setEnableTransition] = useState(true);
  const [sessionToken, setSessionToken] = useState<string | null>(null);

  const mapRef = useRef<HTMLDivElement>(null);
  const googleMapRef = useRef<google.maps.Map | null>(null);
  const markersRef = useRef<google.maps.Marker[]>([]);
  const userMarkerRef = useRef<google.maps.Marker | null>(null);
  const sheetRef = useRef<HTMLDivElement>(null);
  const searchTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const initialLoadRef = useRef(true);
  const sessionTokenRef = useRef<string | null>(null);
  const sheetHeightRef = useRef(sheetHeight);

  useEffect(() => {
    sessionTokenRef.current = sessionToken;
  }, [sessionToken]);

  useEffect(() => {
    if (urlQuery !== searchQuery) {
      setSearchQuery(urlQuery);
    }
  }, [urlQuery]);

  // useEffect(() => {
  //   if (!urlQuery) {
  //     fetchRecommendations();
  //     initialLoadRef.current = false;
  //   }
  // }, [userLocation]);

  // Autocomplete Effect
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (searchQuery.trim() === "" || !isSearchFocused) {
      if (searchQuery.trim() === "") {
        setAutocompletePredictions([]);
      }
      return;
    }

    if (searchQuery.trim().length < 2) {
      setAutocompletePredictions([]);
      return;
    }

    searchTimeoutRef.current = setTimeout(async () => {
      try {
        if (!isSearchFocused) return;

        let activeToken = sessionTokenRef.current;
        if (!activeToken) {
          activeToken = generateSessionToken();
          setSessionToken(activeToken);
          sessionTokenRef.current = activeToken;
        }

        const response = await api.autocomplete({
          query: searchQuery,
          user_location: userLocation,
          radius: 5000,
          session_token: activeToken,
        });

        setAutocompletePredictions(response.predictions.slice(0, 8));
      } catch (error) {
        console.error("Autocomplete failed:", error);
      }
    }, 300);

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchQuery, userLocation, isSearchFocused]);

  // --- HANDLERS ---

  const executeSearch = async (query: string) => {
    if (!query.trim()) return;

    // Tắt loading recommendations ngay lập tức để tránh xung đột spinner
    setIsLoadingRecommendations(false);
    setIsSearching(true);
    setIsSearchFocused(false);
    setAutocompletePredictions([]);

    try {
      const response = await api.textSearchPlace({
        query: query,
        location: userLocation,
        radius: 5000,
      });

      const list = response.places || [];
      const adaptedResults = list.map((res) =>
        convertSearchResultToDetails(res, userLocation)
      );

      setSearchResults(adaptedResults);

      // Logic zoom map vào kết quả
      if (adaptedResults.length > 0) {
        setSheetHeight(65);
        if (googleMapRef.current && window.google) {
          const bounds = new window.google.maps.LatLngBounds();
          adaptedResults.forEach((p) => {
            if (p.geometry.location) {
              bounds.extend(p.geometry.location);
            }
          });
          // Nếu chỉ có 1 kết quả thì zoom gần, nhiều thì fit bounds
          if (adaptedResults.length === 1) {
            googleMapRef.current.setCenter(adaptedResults[0].geometry.location);
            googleMapRef.current.setZoom(16);
          } else {
            googleMapRef.current.fitBounds(bounds);
          }
        }
      } else {
        setSheetHeight(40); // Không có kết quả thì thu gọn sheet
      }
    } catch (error) {
      console.error("Text search failed:", error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleTextSearch = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.currentTarget.blur();
      executeSearch(searchQuery); // Gọi hàm đã tách ở trên
    }
  };

  // 2. THÊM useEffect NÀY: Tự động tìm kiếm khi có urlQuery (từ Homepage)
  useEffect(() => {
    if (urlQuery) {
      // Nếu có query từ URL, chạy tìm kiếm ngay
      setSearchQuery(urlQuery);
      executeSearch(urlQuery);
    } else {
      // Nếu không có query, chạy logic gợi ý (recommendations) như cũ
      fetchRecommendations();
      initialLoadRef.current = false;
    }
  }, [urlQuery]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (isSearchFocused && !target.closest(".search-container")) {
        setIsSearchFocused(false);
        setEnableTransition(true);
        if (searchResults.length > 0 || locations.length > 0) {
          setSheetHeight(65);
        } else {
          setSheetHeight(40);
        }
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("touchstart", handleClickOutside as any);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("touchstart", handleClickOutside as any);
    };
  }, [isSearchFocused, searchResults, locations]);

  const handleSelectPrediction = async (prediction: AutocompletePrediction) => {
    setSearchQuery(prediction.description);
    setIsSearchFocused(false);
    setAutocompletePredictions([]);
    setEnableTransition(true);

    try {
      const fullDetails = await api.getPlaceDetails(
        prediction.place_id,
        sessionToken,
        ["basic"]
      );
      const withDistance = await addDistanceText(fullDetails, userLocation);

      setSelectedLocation(withDistance);
      setSearchResults([withDistance]);
      setSheetHeight(65);

      if (googleMapRef.current) {
        googleMapRef.current.panTo({
          lat: withDistance.geometry.location.lat,
          lng: withDistance.geometry.location.lng,
        });
        googleMapRef.current.setZoom(16);
      }
      setSessionToken(null);
    } catch (error) {
      console.error("Failed to fetch place details:", error);
    }
  };

  const fetchRecommendations = async () => {
    setIsLoadingRecommendations(true);
    try {
      const recToken = generateSessionToken();
      const response = await api.autocomplete({
        query: "park",
        user_location: userLocation,
        radius: 5000,
        place_types: "park|tourist_attraction|point_of_interest",
        session_token: recToken,
      });

      if (!response || !response.predictions) {
        setLocations([]);
        return;
      }

      const detailedRecommendations = await Promise.all(
        response.predictions
          .slice(0, 8)
          .map(async (prediction: AutocompletePrediction) => {
            try {
              const details = await api.getPlaceDetails(
                prediction.place_id,
                recToken,
                ["basic"]
              );
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
    searchResults.length > 0
      ? searchResults
      : !isSearchFocused
      ? locations
      : [];

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

  // Marker Management
  useEffect(() => {
    if (!googleMapRef.current || !mapLoaded) return;

    markersRef.current.forEach((marker) => marker.setMap(null));
    markersRef.current = [];

    displayedLocations.forEach((location) => {
      if (!location.geometry || !location.geometry.location) return;

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

  useEffect(() => {
    if (!googleMapRef.current || !mapLoaded) return;

    if (!userMarkerRef.current) {
      userMarkerRef.current = new window.google.maps.Marker({
        map: googleMapRef.current,
        icon: {
          path: `M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z`,
          fillColor: "#4285F4",
          fillOpacity: 1,
          strokeWeight: 0,
          rotation: 0,
          scale: 1.5,
          anchor: new window.google.maps.Point(12, 24),
        },
      });
    }

    userMarkerRef.current.setPosition({
      lat: userLocation.lat,
      lng: userLocation.lng,
    });
  }, [userLocation, mapLoaded]);

  const handleLocationSelect = (location: PlaceDetailsWithDistance) => {
    setSelectedLocation(location);
    setSheetHeight(65);
  };

  const handleCardClick = async (location: PlaceDetailsWithDistance) => {
    setSelectedLocation(location);
    if (googleMapRef.current) {
      googleMapRef.current.panTo({
        lat: location.geometry.location.lat,
        lng: location.geometry.location.lng,
      });
      googleMapRef.current.setZoom(16);
    }
  };

  const handleNavigateToDetail = () => {
    if (selectedLocation) {
      const url = "/place_detail_page?place_id=" + selectedLocation.place_id;
      router.push(url);
    }
  };

  const handlePickLocation = () => {
    if (selectedLocation) {
      sessionStorage.setItem("picked_location_name", selectedLocation.name);
      sessionStorage.setItem("picked_location_id", selectedLocation.place_id);

      sessionStorage.setItem(
        "picked_location_types",
        JSON.stringify(selectedLocation.types || [])
      );

      sessionStorage.setItem(
        "picked_location_lat",
        selectedLocation.geometry.location.lat.toString()
      );
      sessionStorage.setItem(
        "picked_location_lng",
        selectedLocation.geometry.location.lng.toString()
      );

      router.back();
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

  useEffect(() => {
    sheetHeightRef.current = sheetHeight;
  }, [sheetHeight]);

  const handleDragStart = (e: React.MouseEvent | React.TouchEvent) => {
    setIsDragging(true);
    const clientY = "touches" in e ? e.touches[0].clientY : e.clientY;
    setStartY(clientY);
    setStartHeight(sheetHeight);

    document.body.style.overflow = "hidden";
    document.body.style.userSelect = "none";
  };

  const handleDragMove = (e: MouseEvent | TouchEvent) => {
    if (!isDragging) return;

    const clientY =
      "touches" in e
        ? (e as TouchEvent).touches[0].clientY
        : (e as MouseEvent).clientY;

    const deltaY = startY - clientY;
    const windowHeight = window.innerHeight;
    const deltaPercent = (deltaY / windowHeight) * 100;

    let newHeight = startHeight + deltaPercent;
    newHeight = Math.max(15, Math.min(90, newHeight));

    setSheetHeight(newHeight);
    sheetHeightRef.current = newHeight;
  };

  const handleDragEnd = () => {
    setIsDragging(false);
    document.body.style.overflow = "";
    document.body.style.userSelect = "";

    const currentHeight = sheetHeightRef.current;
    const dragDistance = currentHeight - startHeight;

    const SNAP_MIN = 15;
    const SNAP_LOW = 40;
    const SNAP_MID = 65;
    const SNAP_HIGH = 90;

    const findNearest = (current: number) => {
      const points = [SNAP_MIN, SNAP_LOW, SNAP_MID, SNAP_HIGH];
      return points.reduce((prev, curr) =>
        Math.abs(curr - current) < Math.abs(prev - current) ? curr : prev
      );
    };

    if (dragDistance < -5) {
      if (startHeight >= SNAP_HIGH - 5) setSheetHeight(SNAP_MID);
      else if (startHeight >= SNAP_MID - 5) setSheetHeight(SNAP_LOW);
      else setSheetHeight(SNAP_MIN);
    } else if (dragDistance > 5) {
      if (startHeight <= SNAP_MIN + 5) setSheetHeight(SNAP_LOW);
      else if (startHeight <= SNAP_LOW + 5) setSheetHeight(SNAP_MID);
      else setSheetHeight(SNAP_HIGH);
    } else {
      setSheetHeight(findNearest(currentHeight));
    }
  };

  useEffect(() => {
    if (isDragging) {
      window.addEventListener("touchmove", handleDragMove, { passive: false });
      window.addEventListener("touchend", handleDragEnd);
      window.addEventListener("mousemove", handleDragMove);
      window.addEventListener("mouseup", handleDragEnd);

      return () => {
        window.removeEventListener("touchmove", handleDragMove);
        window.removeEventListener("touchend", handleDragEnd);
        window.removeEventListener("mousemove", handleDragMove);
        window.removeEventListener("mouseup", handleDragEnd);
      };
    }
  }, [isDragging]);

  return (
    <div className="min-h-screen w-full bg-white sm:bg-gray-200 sm:flex sm:justify-center">
      <div className="w-full h-screen relative flex flex-col overflow-hidden sm:max-w-md sm:shadow-2xl">
        <div className="flex-1 relative bg-[#E9F5EB] w-full overflow-hidden">
          <div className="absolute top-5 left-4 right-4 z-10 search-container">
            <div className="bg-white rounded-full shadow-lg flex items-center p-3 transition-transform active:scale-95">
              <div onClick={() => router.back()} className="cursor-pointer">
                <ChevronLeft className="text-gray-500 mr-2 hover:text-green-600" />
              </div>

              <Search size={18} className="text-green-600 mr-2" />
              <input
                type="text"
                placeholder="Search for a location..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={handleTextSearch}
                onFocus={() => {
                  flushSync(() => {
                    setEnableTransition(false);
                    setSheetHeight(8);
                  });
                  if (window.google?.maps) {
                    const token =
                      new google.maps.places.AutocompleteSessionToken();
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
                      <MapPin
                        size={18}
                        className="text-green-600 mt-1 shrink-0"
                      />
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

        {/* Bottom Sheet */}
        <div
          ref={sheetRef}
          style={{
            height: `${sheetHeight}vh`,
            touchAction: "none",
          }}
          className={`bg-white rounded-t-3xl shadow-[0_-5px_15px_rgba(0,0,0,0.15)] z-10 shrink-0 relative overflow-hidden ${
            isDragging || !enableTransition
              ? ""
              : "transition-all duration-300 ease-out"
          }`}
        >
          {/* Drag Handle Area */}
          <div
            className="w-full flex justify-center py-4 touch-none cursor-grab active:cursor-grabbing"
            onTouchStart={handleDragStart}
            onMouseDown={handleDragStart}
          >
            <div className="w-16 h-1.5 bg-gray-300 rounded-full"></div>
          </div>

          {/* Content Area */}
          <div
            className="px-6 pb-6 overflow-y-auto overscroll-contain scrollbar-hide"
            style={{ height: "calc(100% - 56px)" }}
            onTouchStart={(e) => {
              if (sheetHeight < 60) e.stopPropagation();
            }}
            onMouseDown={(e) => {
              if (sheetHeight < 60) e.stopPropagation();
            }}
          >
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

                {isPickerMode ? (
                  <button
                    onClick={handlePickLocation}
                    className="w-full bg-[#53B552] hover:bg-green-600 active:bg-green-700 text-white text-lg font-bold py-3 rounded-full shadow-lg transition-all transform active:scale-[0.98] flex items-center justify-center gap-2"
                  >
                    <Check size={20} strokeWidth={3} />
                    <span>Select This Location</span>
                  </button>
                ) : (
                  <button
                    onClick={handleNavigateToDetail}
                    className="w-full bg-[#53B552] hover:bg-green-600 active:bg-green-700 text-white text-lg font-bold py-3 rounded-full shadow-lg transition-all transform active:scale-[0.98]"
                  >
                    View Details
                  </button>
                )}
              </div>
            ) : (
              <>
                {!isSearchFocused && (
                  <div className="mb-4">
                    <h3 className="text-gray-900 text-lg font-bold mb-1">
                      {searchResults.length > 0
                        ? "Search Results"
                        : "Nearby Eco Locations"}
                    </h3>
                    <p className="text-gray-500 text-sm mb-3">
                      {searchResults.length > 0
                        ? `Found ${searchResults.length} results`
                        : "Select a location from the map or list below"}
                    </p>
                  </div>
                )}

                {isSearchFocused &&
                  autocompletePredictions.length === 0 &&
                  sheetHeight > 15 && (
                    <div className="text-center py-12">
                      <Search
                        size={48}
                        className="text-gray-300 mx-auto mb-3"
                      />
                      <p className="text-gray-400 text-sm">
                        Press <span className="font-bold">Enter</span> to search
                        for "{searchQuery}"
                      </p>
                    </div>
                  )}
              </>
            )}

            {(isLoadingRecommendations || isSearching) &&
              displayedLocations.length === 0 &&
              !isSearchFocused && (
                <div className="flex justify-center items-center py-8">
                  <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-green-600 border-r-transparent"></div>
                </div>
              )}

            {!isLoadingRecommendations &&
              !isSearching &&
              !isSearchFocused &&
              displayedLocations.length === 0 && (
                <div className="text-center py-8">
                  <p className="text-gray-500">No locations found</p>
                </div>
              )}

            {!isSearching &&
              !isSearchFocused &&
              displayedLocations.length > 0 && (
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
                            location.photos?.[0]?.photo_url
                              ? location.photos[0].photo_url
                              : "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=400"
                          }
                          alt={location.name}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            e.currentTarget.src =
                              "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=400";
                          }}
                          loading="lazy"
                          decoding="async"
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
                            {location.types[0]?.replace(/_/g, " ") || "Place"}
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

        {!isPickerMode && (
          <footer className="bg-white shadow-[0_-2px_6px_rgba(0,0,0,0.05)] shrink-0 z-20">
            <div className="h-0.5 bg-linear-to-r from-transparent via-green-300 to-transparent opacity-70"></div>
            <div className="flex justify-around items-center px-2 pt-2 pb-3">
              <a
                href="/homepage"
                className="flex flex-col items-center justify-center w-1/4 text-green-600"
              >
                <Home className="size-6" strokeWidth={2.0} />
                <span className="text-xs font-medium mt-0.5">Home</span>
              </a>
              <a
                href="/planning_page/showing_plan/page"
                className="flex flex-col items-center justify-center w-1/4 text-gray-400 hover:text-green-600 transition-colors"
              >
                <MapPin className="size-6" strokeWidth={2.0} />
                <span className="text-xs font-medium mt-0.5">Planning</span>
              </a>
              <a
                href="/ecobot_page"
                className="flex flex-col items-center justify-center w-1/4 text-gray-400 hover:text-green-600 transition-colors"
              >
                <Bot className="size-6" strokeWidth={1.5} />
                <span className="text-xs font-medium mt-0.5">Ecobot</span>
              </a>
              <a
                href="/user_page/main_page"
                className="flex flex-col items-center justify-center w-1/4 text-gray-400 hover:text-green-600 transition-colors"
              >
                <User className="size-6" strokeWidth={1.5} />
                <span className="text-xs font-medium mt-0.5">User</span>
              </a>
            </div>
          </footer>
        )}
      </div>
    </div>
  );
}

export default function MapPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-green-600 border-r-transparent mb-2"></div>
          <p className="text-gray-600 font-semibold">Loading map...</p>
        </div>
      </div>
    }>
      <MapPageContent />
    </Suspense>
  );
}
