"use client";

import React, {
  useState,
  useEffect,
  useRef,
  Suspense,
  useCallback,
} from "react";
import {
  Search,
  MapPin,
  ChevronLeft,
  Navigation,
  Check,
  BookmarkPlus,
  BookmarkMinus,
} from "lucide-react";
import {
  api,
  AutocompletePrediction,
  PlaceDetails,
  Position,
  PlaceSearchResult,
  SavedDestination,
  birdDistance,
} from "@/lib/api";
import { useRouter, useSearchParams } from "next/navigation";
import { useGoogleMaps } from "@/lib/useGoogleMaps";
import { flushSync } from "react-dom";
import { MobileNavMenu } from "@/components/MobileNavMenu";
import { MAP_NAV_LINKS } from "@/constants/navLinks";
import { Jost } from "next/font/google";

const jost = Jost({ subsets: ["latin"], weight: ["400", "500", "600", "700"] });
const MAP_LOCATION_PREFERENCE_KEY = "map_page_use_current_location";

interface PlaceDetailsWithDistance extends PlaceDetails {
  distanceText: string;
}

// --- HELPER FUNCTIONS ---
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
    sustainable_certificate: "Not Green Verified",
    distanceText: distanceText,
    rating: 0,
  };
};

const generateSessionToken = () => {
  if (window.google?.maps?.places) {
    return new google.maps.places.AutocompleteSessionToken().toString();
  }
  return crypto.randomUUID();
};

// --- LOGIC COMPONENT (Đã đổi tên và tách ra) ---
function MapContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isLoaded } = useGoogleMaps();

  const urlQuery = searchParams.get("q") || "";
  const latParam = searchParams.get("lat");
  const lngParam = searchParams.get("lng");

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
  
  // Recommendation cache
  const [recommendationCache, setRecommendationCache] = useState<{
    data: PlaceDetailsWithDistance[];
    location: Position;
    timestamp: number;
  } | null>(null);
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
  const [isSavingLocation, setIsSavingLocation] = useState(false);
  const [savedPlaceIds, setSavedPlaceIds] = useState<string[]>([]);
  const [saveFeedback, setSaveFeedback] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const mapRef = useRef<HTMLDivElement>(null);
  const googleMapRef = useRef<google.maps.Map | null>(null);
  const markersRef = useRef<google.maps.Marker[]>([]);
  const userMarkerRef = useRef<google.maps.Marker | null>(null);
  const sheetRef = useRef<HTMLDivElement>(null);
  const searchTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const initialLoadRef = useRef(true);
  const sessionTokenRef = useRef<string | null>(null);
  const sheetHeightRef = useRef(sheetHeight);
  const pendingMapUpdateRef = useRef<{
    position: Position;
    zoom?: number;
  } | null>(null);
  const hasAttemptedAutoLocateRef = useRef(false);
  const [shouldUseCurrentLocation, setShouldUseCurrentLocation] = useState<
    boolean | null
  >(null);
  const [isLocating, setIsLocating] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const storedPreference = window.localStorage.getItem(
      MAP_LOCATION_PREFERENCE_KEY
    );

    if (storedPreference === "true") {
      setShouldUseCurrentLocation(true);
    } else {
      window.localStorage.setItem(MAP_LOCATION_PREFERENCE_KEY, "true");
      setShouldUseCurrentLocation(false);
    }
  }, []);

  useEffect(() => {
    sessionTokenRef.current = sessionToken;
  }, [sessionToken]);

  useEffect(() => {
    if (urlQuery !== searchQuery) {
      setSearchQuery(urlQuery);
    }
  }, [urlQuery]);

  useEffect(() => {
    setSaveFeedback(null);
  }, [selectedLocation?.place_id]);

  useEffect(() => {
    let isMounted = true;

    const loadSavedDestinations = async () => {
      try {
        const savedList: SavedDestination[] = await api.getSavedDestinations();
        if (!isMounted) return;
        const ids = savedList.map((destination) => destination.destination_id);
        setSavedPlaceIds(ids);
      } catch (error) {
        console.error("Failed to load saved destinations:", error);
      }
    };

    loadSavedDestinations();

    return () => {
      isMounted = false;
    };
  }, []);

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

        setAutocompletePredictions(response.predictions.slice(0, 3));
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

  const executeSearch = async (query: string) => {
    if (!query.trim()) return;

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

      if (adaptedResults.length > 0) {
        setSheetHeight(65);
        if (googleMapRef.current && window.google) {
          const bounds = new window.google.maps.LatLngBounds();
          adaptedResults.forEach((p) => {
            if (p.geometry.location) {
              bounds.extend(p.geometry.location);
            }
          });
          if (adaptedResults.length === 1) {
            googleMapRef.current.setCenter(adaptedResults[0].geometry.location);
            googleMapRef.current.setZoom(16);
          } else {
            googleMapRef.current.fitBounds(bounds);
          }
        }
      } else {
        setSheetHeight(40);
      }
    } catch (error) {
      console.error("Text search failed:", error);
    } finally {
      setIsSearching(false);
    }
  };

  const handleTextSearch = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.nativeEvent.isComposing) return;
    if (e.key === "Enter") {
      e.currentTarget.blur();
      executeSearch(searchQuery);
    }
  };

  useEffect(() => {
    if (urlQuery) {
      setSearchQuery(urlQuery);
      executeSearch(urlQuery);
    } else {
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
    // Check cache validity (5 minutes and within 1km)
    const now = Date.now();
    const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
    const CACHE_DISTANCE_KM = 1; // 1km threshold
    
    if (recommendationCache) {
      const timeDiff = now - recommendationCache.timestamp;
      const distance = birdDistance(userLocation, recommendationCache.location);
      
      if (timeDiff < CACHE_DURATION && distance < CACHE_DISTANCE_KM) {
        // Use cached data
        setLocations(recommendationCache.data);
        setIsLoadingRecommendations(false);
        setSheetHeight(65);
        return;
      }
    }
    
    setIsLoadingRecommendations(true);
    try {
      // Use personalized nearby recommendations from backend
      const response = await api.getNearbyGreenPlaces(
        userLocation.lat,
        userLocation.lng,
        5, // 5km radius
        8  // Get 8 recommendations
      );

      if (!response || !response.places || response.places.length === 0) {
        setLocations([]);
        return;
      }

      // Convert PlaceSearchResult to PlaceDetailsWithDistance
      const validRecommendations = response.places.map((result) =>
        convertSearchResultToDetails(result, userLocation)
      );
      
      setLocations(validRecommendations);
      
      // Update cache
      setRecommendationCache({
        data: validRecommendations,
        location: userLocation,
        timestamp: now,
      });
      
      setSheetHeight(65);
    } catch (error) {
      console.error("Failed to fetch recommendations:", error);
      setLocations([]);
    } finally {
      setIsLoadingRecommendations(false);
    }
  };

  const scheduleMapUpdate = useCallback(
    (position: Position, zoom?: number) => {
      if (googleMapRef.current && mapLoaded) {
        googleMapRef.current.panTo(position);
        if (typeof zoom === "number") {
          googleMapRef.current.setZoom(zoom);
        }
      } else {
        pendingMapUpdateRef.current = { position, zoom };
      }
    },
    [mapLoaded]
  );

  const locateUser = useCallback(
    (options: { silent?: boolean; zoom?: number } = {}) => {
      if (isLocating) return;

      if (typeof window === "undefined" || !("geolocation" in navigator)) {
        if (!options.silent) {
          alert("Geolocation is not supported by your browser!");
        }
        return;
      }

      setIsLocating(true);
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const pos: Position = {
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          };
          setUserLocation(pos);
          scheduleMapUpdate(pos, options.zoom ?? 15);
          setIsLocating(false);
        },
        (error) => {
          console.error("Error getting location:", error);
          if (!options.silent) {
            let errorMsg = "Unable to get your location";
            if (error.code === 1) errorMsg = "Please allow location access.";
            else if (error.code === 2)
              errorMsg = "Location unavailable. Please check your GPS!";
            else if (error.code === 3) errorMsg = "Location request timed out.";
            alert(errorMsg);
          }
          setIsLocating(false);
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0,
        }
      );
    },
    [isLocating, scheduleMapUpdate]
  );

  const displayedLocations =
    searchResults.length > 0
      ? searchResults
      : !isSearchFocused
      ? locations
      : [];

  const isPlaceSaved = (placeId: string) => savedPlaceIds.includes(placeId);

  const isCurrentLocationSaved = selectedLocation
    ? isPlaceSaved(selectedLocation.place_id)
    : false;

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

  const handleSaveLocation = async () => {
    if (!selectedLocation || isSavingLocation) return;

    const locationId = selectedLocation.place_id;
    if (isPlaceSaved(locationId)) {
      setSaveFeedback({
        type: "success",
        message: "You already saved this location.",
      });
      return;
    }

    setIsSavingLocation(true);
    setSaveFeedback(null);

    try {
      await api.saveDestination(locationId);
      setSavedPlaceIds((prev) =>
        prev.includes(locationId) ? prev : [...prev, locationId]
      );
      setSaveFeedback({
        type: "success",
        message: "Saved this location to your favorites!",
      });
    } catch (error: any) {
      console.error("Failed to save location:", error);
      const message =
        error?.message ||
        "Unable to save this location. Please try again later.";
      setSaveFeedback({ type: "error", message });
    } finally {
      setIsSavingLocation(false);
    }
  };

  const handleUnsaveLocation = async () => {
    if (!selectedLocation || isSavingLocation) return;

    const locationId = selectedLocation.place_id;
    if (!isPlaceSaved(locationId)) return;

    setIsSavingLocation(true);
    setSaveFeedback(null);

    try {
      await api.unsaveDestination(locationId);
      setSavedPlaceIds((prev) => prev.filter((id) => id !== locationId));
      setSaveFeedback({
        type: "success",
        message: "Removed this location from your favorites.",
      });
    } catch (error: any) {
      console.error("Failed to unsave location:", error);
      const message =
        error?.message ||
        "Unable to remove this location. Please try again later.";
      setSaveFeedback({ type: "error", message });
    } finally {
      setIsSavingLocation(false);
    }
  };

  const handleCurrentLocation = () => {
    locateUser();
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
    <div
      className={`min-h-screen w-full relative bg-linear-to-b from-[#F4F9F4] via-[#EFF6F2] to-[#E3F1EB] sm:flex sm:items-center sm:justify-center sm:px-4 ${jost.className}`}
    >
      <div className="w-full h-screen relative flex flex-col overflow-hidden sm:max-w-md sm:h-[calc(100vh-2rem)] sm:rounded-4xl sm:shadow-[0_30px_80px_rgba(10,126,70,0.15)] sm:border sm:border-white/40 sm:bg-white/10">
        {!isPickerMode && (
          <MobileNavMenu
            items={MAP_NAV_LINKS}
            activeKey="planning"
            className="drop-shadow-sm"
          />
        )}
        <div className="flex-1 relative w-full overflow-hidden">
          <div className="absolute top-5 left-4 right-4 sm:left-8 sm:right-8 z-10 search-container space-y-3">
            <div className="bg-white/90 backdrop-blur-xl border border-green-100 rounded-2xl shadow-[0_15px_45px_rgba(16,185,129,0.15)] p-4">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => router.back()}
                  className="p-2 rounded-full bg-green-50 text-green-600 hover:bg-green-100 transition-colors"
                >
                  <ChevronLeft size={18} />
                </button>
                <div className="flex-1 bg-white rounded-xl border border-gray-100 flex items-center px-4 py-2.5 shadow-inner">
                  <Search size={18} className="text-green-600 mr-2" />
                  <input
                    type="text"
                    placeholder="Where do you want to visit today?"
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
                    className="flex-1 outline-none caret-black bg-white text-gray-900 placeholder:text-gray-400 font-semibold"
                  />
                  {isSearching && (
                    <div className="ml-2 animate-spin h-4 w-4 border-2 border-green-600 border-t-transparent rounded-full"></div>
                  )}
                </div>
              </div>
            </div>

            {/* Autocomplete Dropdown */}
            {isSearchFocused && autocompletePredictions.length > 0 && (
              <div className="bg-white rounded-2xl shadow-2xl overflow-hidden max-h-96 overflow-y-auto border border-green-50">
                {autocompletePredictions.map((prediction) => (
                  <div
                    key={prediction.place_id}
                    onClick={() => handleSelectPrediction(prediction)}
                    className="p-4 hover:bg-green-50/60 active:bg-green-100 cursor-pointer border-b border-gray-100 last:border-b-0 transition-colors"
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
            className="absolute top-36 right-8 z-20 bg-white/90 backdrop-blur-lg p-3 rounded-2xl shadow-[0_8px_24px_rgba(15,118,110,0.2)] border border-white/60 hover:bg-white transition-colors active:scale-95"
          >
            {isLocating ? (
              <div className="animate-spin h-5 w-5 border-2 border-green-600 border-t-transparent rounded-full"></div>
            ) : (
              <Navigation size={20} className="text-green-600" />
            )}
          </button>

          {/* Google Map */}
          <div className="absolute inset-0">
            <div ref={mapRef} className="w-full h-full" />
          </div>

          {!mapLoaded && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center bg-white/80 backdrop-blur-sm rounded-2xl px-6 py-4 shadow-lg">
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
          className={`bg-[#F7FBF8] rounded-t-4xl border border-green-50 shadow-[0_-25px_60px_rgba(15,118,110,0.12)] z-10 shrink-0 relative overflow-hidden ${
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
            <div className="w-16 h-1.5 bg-green-200 rounded-full"></div>
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
                <div className="bg-linear-to-br from-white via-[#F2FBF5] to-[#E4F6EB] border border-white shadow-[0_20px_50px_rgba(15,118,110,0.12)] rounded-3xl p-4 mb-4 flex items-start gap-3">
                  <div className="bg-green-600/10 p-3 rounded-2xl shrink-0 mt-0.5">
                    <MapPin size={20} className="text-green-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-green-700 text-[11px] font-bold mb-1 uppercase tracking-[0.3em]">
                        Selected location
                      </p>
                      <span className="text-[11px] px-2 py-1 rounded-full bg-white text-gray-500 border border-gray-100">
                        {selectedLocation.types[0]?.replace(/_/g, " ") ||
                          "Spot"}
                      </span>
                    </div>
                    <p className="text-gray-900 text-lg font-bold leading-tight mb-1 truncate">
                      {selectedLocation.name}
                    </p>
                    <p className="text-gray-500 text-sm leading-tight line-clamp-2">
                      {selectedLocation.formatted_address}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-xs bg-white text-green-700 px-2.5 py-1 rounded-full font-semibold border border-green-100">
                        {selectedLocation.distanceText}
                      </span>
                      {selectedLocation.rating &&
                        selectedLocation.rating > 0 && (
                          <span className="text-xs text-yellow-600 font-semibold">
                            ★ {selectedLocation.rating.toFixed(1)}
                          </span>
                        )}
                      {isCurrentLocationSaved && (
                        <span className="text-xs bg-emerald-600 text-white px-2 py-1 rounded-full font-semibold">
                          Saved
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row gap-3">
                  <button
                    onClick={
                      isCurrentLocationSaved
                        ? handleUnsaveLocation
                        : handleSaveLocation
                    }
                    disabled={isSavingLocation}
                    className={`w-full border rounded-2xl font-semibold py-3.5 shadow-[0_10px_30px_rgba(15,118,110,0.18)] transition-all flex items-center justify-center gap-2 text-base active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed ${
                      isCurrentLocationSaved
                        ? "bg-linear-to-r from-rose-500 to-red-500 text-white border-red-200"
                        : "text-green-700 bg-white border-green-200"
                    }`}
                  >
                    {isCurrentLocationSaved ? (
                      <BookmarkMinus size={18} className="text-white" />
                    ) : (
                      <BookmarkPlus size={18} className="text-green-600" />
                    )}
                    {isSavingLocation
                      ? isCurrentLocationSaved
                        ? "Removing..."
                        : "Saving..."
                      : isCurrentLocationSaved
                      ? "Unsave"
                      : "Save Location"}
                  </button>

                  {isPickerMode ? (
                    <button
                      onClick={handlePickLocation}
                      className="w-full bg-linear-to-r from-emerald-500 to-green-600 text-white text-lg font-bold py-3.5 rounded-2xl shadow-[0_15px_35px_rgba(15,118,110,0.25)] transition-all transform active:scale-[0.98] flex items-center justify-center gap-2"
                    >
                      <Check size={20} strokeWidth={3} />
                      <span>Select This Location</span>
                    </button>
                  ) : (
                    <button
                      onClick={handleNavigateToDetail}
                      className="w-full bg-linear-to-r from-emerald-500 to-green-600 text-white text-lg font-bold py-3.5 rounded-2xl shadow-[0_15px_35px_rgba(15,118,110,0.25)] transition-all transform active:scale-[0.98]"
                    >
                      View Details
                    </button>
                  )}
                </div>

                {saveFeedback && (
                  <p
                    className={`text-sm mt-2 font-semibold ${
                      saveFeedback.type === "success"
                        ? "text-green-700"
                        : "text-red-500"
                    }`}
                  >
                    {saveFeedback.message}
                  </p>
                )}
              </div>
            ) : (
              <>
                {!isSearchFocused && (
                  <div className="mb-4 space-y-3">
                    <h3 className="text-gray-900 text-lg font-bold">
                      {searchResults.length > 0
                        ? "Search Results"
                        : "Nearby Eco Locations"}
                    </h3>
                    <p className="text-gray-500 text-sm">
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
                      className={`bg-white/90 rounded-2xl border border-green-50 overflow-hidden shadow-[0_12px_30px_rgba(15,118,110,0.08)] cursor-pointer transition-all transform active:scale-[0.97] ${
                        selectedLocation?.place_id === location.place_id
                          ? "ring-2 ring-green-500"
                          : ""
                      }`}
                    >
                      <div className="relative h-28 bg-gray-200 overflow-hidden">
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
                        <div className="absolute inset-0 bg-linear-to-t from-black/35 via-black/5 to-transparent" />
                        {isPlaceSaved(location.place_id) && (
                          <span className="absolute top-2 right-2 bg-[#53B552] text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow-md">
                            Saved
                          </span>
                        )}
                      </div>
                      <div className="p-3">
                        <h4 className="font-bold text-gray-900 text-sm mb-1 line-clamp-1">
                          {location.name}
                        </h4>
                        <p className="text-xs text-gray-500 mb-2 line-clamp-1">
                          {location.distanceText}
                        </p>
                        <div className="flex items-center justify-between">
                          <span className="text-[11px] bg-green-50 text-green-700 px-2 py-1 rounded-full font-semibold">
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

        {!isPickerMode && <div className="pb-6" />}
      </div>
    </div>
  );
}

// --- MAIN WRAPPER COMPONENT ---
export default function MapPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center text-green-600">
          Loading map configuration...
        </div>
      }
    >
      <MapContent />
    </Suspense>
  );
}
