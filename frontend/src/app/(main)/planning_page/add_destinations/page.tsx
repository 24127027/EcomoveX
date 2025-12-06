"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  ChevronLeft,
  MapPin,
  Plus,
  Trash2,
  List,
  X,
  Loader2,
  Star,
  Eye,
  Check,
  ArrowRight, // Icon for finish button
} from "lucide-react";
import { useGoogleMaps } from "@/lib/useGoogleMaps";
import {
  api,
  PlaceDetails,
  AutocompletePrediction,
  Position,
  PlaceSearchResult,
} from "@/lib/api";
import { Jost } from "next/font/google";

const jost = Jost({ subsets: ["latin"], weight: ["400", "500", "600", "700"] });

const STORAGE_KEY = "temp_plan_destinations";
const CURRENT_VIEWING_KEY = "current_viewing_place";
const STORAGE_KEY_INFO = "temp_plan_info"; // Key for persisted plan info

type ListedPlace = PlaceDetails & { distanceText?: string };

const toRadians = (value: number) => (value * Math.PI) / 180;

const calculateDistanceKm = (from: Position, to: Position) => {
  const earthRadiusKm = 6371;
  const dLat = toRadians(to.lat - from.lat);
  const dLng = toRadians(to.lng - from.lng);
  const lat1 = toRadians(from.lat);
  const lat2 = toRadians(to.lat);

  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.sin(dLng / 2) * Math.sin(dLng / 2) * Math.cos(lat1) * Math.cos(lat2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return earthRadiusKm * c;
};

const formatDistanceText = (from: Position, to?: Position) => {
  if (!to) return undefined;
  const distanceKm = calculateDistanceKm(from, to);
  if (distanceKm < 1) {
    return `${Math.round(distanceKm * 1000)} m away`;
  }
  return `${distanceKm.toFixed(1)} km away`;
};

const convertTextSearchResult = (
  result: PlaceSearchResult,
  origin: Position
): ListedPlace => {
  const fallbackLocation = origin;
  const location = result.location || fallbackLocation;

  return {
    place_id: result.id,
    name: result.displayName?.text || "Unnamed place",
    formatted_address: result.formattedAddress || "",
    geometry: {
      location,
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
    distanceText: formatDistanceText(origin, location),
  };
};

const enhanceDetailsWithDistance = (
  details: PlaceDetails,
  origin: Position
): ListedPlace => {
  const location = details.geometry?.location;
  return {
    ...details,
    distanceText: location ? formatDistanceText(origin, location) : undefined,
  };
};

// District coordinates mapping for Ho Chi Minh City
const DISTRICT_COORDINATES: { [key: string]: { lat: number; lng: number } } = {
  "District 1": { lat: 10.7756, lng: 106.7019 },
  "District 2": { lat: 10.7897, lng: 106.7428 },
  "District 3": { lat: 10.7839, lng: 106.6881 },
  "District 4": { lat: 10.7577, lng: 106.702 },
  "District 5": { lat: 10.755, lng: 106.6667 },
  "District 6": { lat: 10.7481, lng: 106.6354 },
  "District 7": { lat: 10.7333, lng: 106.7208 },
  "District 8": { lat: 10.7294, lng: 106.6597 },
  "District 10": { lat: 10.7726, lng: 106.67 },
  "District 11": { lat: 10.7626, lng: 106.6503 },
  "District 12": { lat: 10.8633, lng: 106.6975 },
  "Binh Thanh District": { lat: 10.8025, lng: 106.7067 },
  "Binh Tan District": { lat: 10.7948, lng: 106.6054 },
  "Tan Binh District": { lat: 10.8007, lng: 106.6528 },
  "Tan Phu District": { lat: 10.7844, lng: 106.6297 },
  "Go Vap District": { lat: 10.8383, lng: 106.6758 },
  "Phu Nhuan District": { lat: 10.7981, lng: 106.6831 },
  "Thu Duc City": { lat: 10.8517, lng: 106.7636 },
  "Cu Chi District": { lat: 11.0, lng: 106.4931 },
  "Hoc Mon District": { lat: 10.8842, lng: 106.5925 },
  "Binh Chanh District": { lat: 10.7139, lng: 106.605 },
  "Nha Be District": { lat: 10.7, lng: 106.7281 },
  "Can Gio District": { lat: 10.4078, lng: 106.9542 },
};

export default function AddDestinationPage() {
  const [showWelcome, setShowWelcome] = useState(true); // Show onboarding modal
  const router = useRouter();
  const { isLoaded } = useGoogleMaps();

  // --- REFS ---
  const sessionTokenRef = useRef(Math.random().toString(36).substring(2));
  const refreshSessionToken = () => {
    sessionTokenRef.current = Math.random().toString(36).substring(2);
  };

  // --- STATE ---
  const [addedDestinations, setAddedDestinations] = useState<PlaceDetails[]>(
    []
  );
  const [showSelectedList, setShowSelectedList] = useState(false);
  const [showSavedList, setShowSavedList] = useState(false); // Controls saved destinations dropdown
  const [savedDestinations, setSavedDestinations] = useState<PlaceDetails[]>(
    []
  );
  const [isLoadingSaved, setIsLoadingSaved] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [predictions, setPredictions] = useState<AutocompletePrediction[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<PlaceDetails | null>(
    null
  );
  const [isSearching, setIsSearching] = useState(false);
  const [greenSuggestions, setGreenSuggestions] = useState<ListedPlace[]>([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [searchResults, setSearchResults] = useState<ListedPlace[]>([]);
  const [isLoadingResults, setIsLoadingResults] = useState(false);
  const [lastSearchQuery, setLastSearchQuery] = useState("");
  const [searchError, setSearchError] = useState<string | null>(null);
  const [suggestionError, setSuggestionError] = useState<string | null>(null);

  // Default Location (HCM)
  const [userLocation, setUserLocation] = useState<Position>({
    lat: 10.7756,
    lng: 106.7019,
  });

  const mapRef = useRef<HTMLDivElement>(null);
  const googleMapRef = useRef<google.maps.Map | null>(null);
  const markersRef = useRef<google.maps.Marker[]>([]);
  const searchTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);

  // --- 1. INIT ---
  useEffect(() => {
    const storedList = sessionStorage.getItem(STORAGE_KEY);
    if (storedList) {
      try {
        const parsed = JSON.parse(storedList);
        // Clean up place_id by removing numeric suffixes ("-0", "-1", etc.)
        const cleaned = parsed.map((dest: PlaceDetails) => {
          let placeId = dest.place_id;
          const lastDashIndex = placeId.lastIndexOf("-");
          if (lastDashIndex !== -1) {
            const suffix = placeId.substring(lastDashIndex + 1);
            if (!isNaN(Number(suffix))) {
              placeId = placeId.substring(0, lastDashIndex);
            }
          }
          return {
            ...dest,
            place_id: placeId,
          };
        });
        setAddedDestinations(cleaned);
      } catch (e) {
        console.error(e);
      }
    }

    const storedCurrent = sessionStorage.getItem(CURRENT_VIEWING_KEY);
    if (storedCurrent) {
      try {
        setSelectedLocation(JSON.parse(storedCurrent));
      } catch (e) {
        console.error(e);
      }
    }

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((pos) => {
        const newPos = { lat: pos.coords.latitude, lng: pos.coords.longitude };
        setUserLocation(newPos);
        if (googleMapRef.current && !storedCurrent) {
          googleMapRef.current.panTo(newPos);
        }
      });
    }

    // Center map on a district selected during plan creation
    const planInfo = sessionStorage.getItem(STORAGE_KEY_INFO);
    if (planInfo) {
      try {
        const parsed = JSON.parse(planInfo);
        if (parsed.district && DISTRICT_COORDINATES[parsed.district]) {
          const districtPos = DISTRICT_COORDINATES[parsed.district];
          setUserLocation(districtPos);
          console.log(`Moving map to ${parsed.district}:`, districtPos);
        }
      } catch (e) {
        console.error("Error parsing plan info:", e);
      }
    }
  }, []);

  // --- LOAD SAVED DESTINATIONS ---
  useEffect(() => {
    const loadSavedDestinations = async () => {
      setIsLoadingSaved(true);
      try {
        const saved = await api.getSavedDestinations();

        // Fetch full details for each saved destination
        const detailsPromises = saved.map(async (item) => {
          try {
            const details = await api.getPlaceDetails(item.destination_id);
            return details;
          } catch (error) {
            console.error(
              `Failed to load details for ${item.destination_id}:`,
              error
            );
            return null;
          }
        });

        const allDetails = await Promise.all(detailsPromises);
        const validDetails = allDetails.filter(
          (d): d is PlaceDetails => d !== null
        );

        setSavedDestinations(validDetails);
      } catch (error) {
        console.error("Failed to load saved destinations:", error);
      } finally {
        setIsLoadingSaved(false);
      }
    };

    loadSavedDestinations();
  }, []);

  useEffect(() => {
    let isCancelled = false;

    const fetchGreenSuggestions = async () => {
      setIsLoadingSuggestions(true);
      setSuggestionError(null);
      try {
        const res = await api.textSearchPlace({
          query: "eco friendly park nature",
          location: userLocation,
          radius: 8000,
        });

        if (isCancelled) return;
        const mapped = (res.places || []).map((place) =>
          convertTextSearchResult(place, userLocation)
        );
        setGreenSuggestions(mapped);
      } catch (error) {
        if (!isCancelled) {
          console.error("Initial green search failed:", error);
          setSuggestionError("Could not load nearby green destinations.");
        }
      } finally {
        if (!isCancelled) {
          setIsLoadingSuggestions(false);
        }
      }
    };

    fetchGreenSuggestions();

    return () => {
      isCancelled = true;
    };
  }, [userLocation]);
  // --- MAP SETUP ---
  useEffect(() => {
    if (!isLoaded || !mapRef.current) return;

    const map = new window.google.maps.Map(mapRef.current, {
      center: userLocation,
      zoom: 13,
      disableDefaultUI: true,
      clickableIcons: false,
      styles: [
        {
          featureType: "poi",
          elementType: "labels",
          stylers: [{ visibility: "off" }],
        },
      ],
      gestureHandling: "greedy",
    });

    googleMapRef.current = map;
  }, [isLoaded, userLocation]);

  // Marker logic: automatically pan/zoom when the selection changes
  useEffect(() => {
    if (
      !googleMapRef.current ||
      !selectedLocation ||
      !selectedLocation.geometry?.location
    )
      return;

    markersRef.current.forEach((m) => m.setMap(null));
    markersRef.current = [];

    const marker = new window.google.maps.Marker({
      position: selectedLocation.geometry.location,
      map: googleMapRef.current,
      title: selectedLocation.name,
      animation: google.maps.Animation.DROP,
    });
    markersRef.current.push(marker);

    googleMapRef.current.panTo(selectedLocation.geometry.location);
    googleMapRef.current.setZoom(16);
  }, [selectedLocation]);

  // --- SEARCH LOGIC ---
  useEffect(() => {
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);

    if (!searchQuery.trim() || searchQuery.length < 2) {
      setPredictions([]);
      return;
    }

    searchTimeoutRef.current = setTimeout(async () => {
      try {
        const res = await api.autocomplete({
          query: searchQuery,
          user_location: userLocation,
          radius: 5000,
          session_token: sessionTokenRef.current,
        });

        if (res && res.predictions) {
          setPredictions(res.predictions.slice(0, 5));
        }
      } catch (error) {
        console.error(error);
      }
    }, 300);

    return () => clearTimeout(searchTimeoutRef.current);
  }, [searchQuery, userLocation]);

  useEffect(() => {
    if (searchQuery === "") {
      setSearchResults([]);
      setLastSearchQuery("");
      setSearchError(null);
    }
  }, [searchQuery]);

  const executeTextSearch = async (rawQuery: string) => {
    const trimmed = rawQuery.trim();
    if (!trimmed) {
      setSearchResults([]);
      setLastSearchQuery("");
      setSearchError(null);
      return;
    }

    setIsLoadingResults(true);
    setSearchError(null);
    try {
      const response = await api.textSearchPlace({
        query: trimmed,
        location: userLocation,
        radius: 8000,
      });

      const mapped = (response.places || []).map((place) =>
        convertTextSearchResult(place, userLocation)
      );
      setSearchResults(mapped);
      setLastSearchQuery(trimmed);

      if (mapped.length === 0) {
        setSearchError("No locations found. Try a different keyword.");
      }
    } catch (error) {
      console.error("Text search failed:", error);
      setSearchError("Couldn't load search results. Please try again.");
    } finally {
      setIsLoadingResults(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    executeTextSearch(searchQuery);
  };

  const focusPlaceById = async (placeId: string) => {
    setIsSearching(true);
    try {
      const details = await api.getPlaceDetails(
        placeId,
        sessionTokenRef.current,
        ["basic", "contact", "atmosphere"]
      );

      const enriched = enhanceDetailsWithDistance(details, userLocation);
      setSelectedLocation(enriched);
      sessionStorage.setItem(CURRENT_VIEWING_KEY, JSON.stringify(enriched));
      refreshSessionToken();
    } catch (error) {
      console.error("Details Error:", error);
      alert("Could not fetch location details.");
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectPrediction = (prediction: AutocompletePrediction) => {
    setSearchQuery(prediction.description);
    setPredictions([]);
    focusPlaceById(prediction.place_id);
  };

  // --- ACTIONS ---

  const handleCloseDetail = () => {
    setSelectedLocation(null);
    sessionStorage.removeItem(CURRENT_VIEWING_KEY);
  };

  // Handle click on an item from the selected list
  const handleClickSavedItem = (place: PlaceDetails) => {
    const enriched = enhanceDetailsWithDistance(place, userLocation);
    setSelectedLocation(enriched);
    sessionStorage.setItem(CURRENT_VIEWING_KEY, JSON.stringify(enriched));
    setShowSelectedList(false);
  };

  const handleAddLocation = () => {
    if (!selectedLocation) {
      console.log("❌ No selected location");
      return;
    }

    console.log(`🔍 Checking if ${selectedLocation.place_id} already added...`);
    console.log(
      `   Current list:`,
      addedDestinations.map((d) => d.place_id)
    );

    const exists = addedDestinations.find(
      (d) => d.place_id === selectedLocation.place_id
    );
    if (exists) {
      console.log(`⚠️ Already exists! Skipping.`);
      return;
    }

    console.log(`✅ Adding ${selectedLocation.name}`);
    const newList = [...addedDestinations, selectedLocation];
    setAddedDestinations(newList);
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(newList));

    setSearchQuery("");
    handleCloseDetail();

    if (googleMapRef.current) {
      googleMapRef.current.setZoom(13);
      googleMapRef.current.panTo(userLocation);
    }
  };

  const handleRemoveLocation = (placeId: string, e?: React.MouseEvent) => {
    e?.stopPropagation();
    const newList = addedDestinations.filter((d) => d.place_id !== placeId);
    setAddedDestinations(newList);
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(newList));
  };

  const handleFinish = () => {
    // Validate minimum number of destinations
    if (addedDestinations.length < 2) {
      alert(
        `You need at least 2 destinations to continue! (Current: ${addedDestinations.length})`
      );
      return;
    }

    // Determine whether we are editing an existing plan
    const planId = sessionStorage.getItem("EDITING_PLAN_ID");

    if (planId) {
      console.log(`EDIT MODE: Returning to review_plan with planId: ${planId}`);
      router.push(`/planning_page/review_plan?id=${planId}`);
    } else {
      console.log(`CREATE MODE: Keeping destinations in storage`);
      router.push("/planning_page/review_plan");
    }
  };

  const isAlreadyAdded =
    selectedLocation &&
    addedDestinations.some((d) => d.place_id === selectedLocation.place_id);

  // Debug: log when the selected location changes
  useEffect(() => {
    if (selectedLocation) {
      const isAdded = addedDestinations.some(
        (d) => d.place_id === selectedLocation.place_id
      );
      console.log(`🔎 isAlreadyAdded check for ${selectedLocation.place_id}:`);
      console.log(`   - Result: ${isAdded}`);
      console.log(
        `   - Added list:`,
        addedDestinations.map((d) => d.place_id)
      );
    }
  }, [selectedLocation, addedDestinations]);

  const hasSearchResults = searchResults.length > 0;
  const listPlaces = hasSearchResults ? searchResults : greenSuggestions;
  const isListLoading = hasSearchResults
    ? isLoadingResults
    : isLoadingSuggestions;
  const listTitle = hasSearchResults
    ? `Search results${lastSearchQuery ? ` for "${lastSearchQuery}"` : ""}`
    : "🌿 Green destinations nearby";
  const listSubtitle = hasSearchResults
    ? "Tap a place to preview and add it to your plan"
    : "Start with these eco-friendly highlights";
  const emptyStateMessage = hasSearchResults
    ? searchError || "No locations found. Try searching again."
    : suggestionError || "We couldn't load suggestions right now.";

  return (
    <div className="min-h-screen w-full bg-gray-200 flex justify-center items-center sm:py-0">
      <div className="w-full max-w-md bg-white h-screen relative flex flex-col overflow-hidden shadow-2xl">
        {/* HEADER */}
        <div className="bg-white px-4 pt-4 pb-2 shadow-sm z-20 flex items-center gap-2 border-b border-gray-100">
          <button
            onClick={() => router.back()}
            className="p-2 rounded-full hover:bg-gray-100 active:scale-95 transition-transform"
          >
            <ChevronLeft size={24} className="text-gray-600" />
          </button>

          <div className="flex-1 relative">
            <form
              onSubmit={handleSearchSubmit}
              className="flex items-center bg-gray-100 rounded-full px-3 py-2.5 transition-all focus-within:ring-2 focus-within:ring-green-100"
            >
              <Search size={18} className="text-gray-500 mr-2" />
              <input
                type="text"
                placeholder="Search location..."
                className={`${jost.className} bg-transparent outline-none w-full text-sm font-medium text-gray-700 placeholder:text-gray-400`}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => {
                    setSearchQuery("");
                    setPredictions([]);
                  }}
                  className="p-1"
                >
                  <X size={16} className="text-gray-400" />
                </button>
              )}
              <button
                type="submit"
                className="ml-1 flex items-center justify-center w-9 h-9 rounded-full bg-[#53B552] text-white shadow-sm hover:bg-green-600 active:scale-95 transition-all"
                aria-label="Confirm search"
              >
                <ArrowRight size={16} strokeWidth={3} />
              </button>
            </form>

            {/* Prediction Dropdown */}
            {predictions.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-xl z-50 overflow-hidden border border-gray-100 max-h-64 overflow-y-auto">
                {/* Header to separate suggestions from explicit search results */}
                <div className="bg-gray-50 px-3 py-2 border-b border-gray-100">
                  <p
                    className={`${jost.className} text-xs font-bold text-green-600 uppercase tracking-wide`}
                  >
                    Search Results
                  </p>
                </div>

                {predictions.map((p) => (
                  <div
                    key={p.place_id}
                    onClick={() => handleSelectPrediction(p)}
                    className="p-3 hover:bg-green-50 active:bg-green-100 cursor-pointer border-b border-gray-50 last:border-0 flex items-start gap-3 transition-colors"
                  >
                    <div className="bg-gray-100 p-1.5 rounded-full shrink-0">
                      <MapPin size={16} className="text-gray-500" />
                    </div>
                    <div>
                      <p
                        className={`${jost.className} text-sm font-semibold text-gray-800 line-clamp-1`}
                      >
                        {p.structured_formatting?.main_text || p.description}
                      </p>
                      <p
                        className={`${jost.className} text-xs text-gray-500 line-clamp-1`}
                      >
                        {p.structured_formatting?.secondary_text}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* LISTS CONTAINER - Vertical Stack */}
          <div className="relative flex flex-col gap-2">
            {/* YOUR LIST BUTTON */}
            <button
              onClick={() => {
                setShowSelectedList(!showSelectedList);
                setShowSavedList(false); // Close saved list when opening this
              }}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-full transition-all shadow-sm border ${
                showSelectedList
                  ? "bg-green-100 text-green-700 border-green-200 ring-2 ring-green-100"
                  : "bg-white text-gray-700 border-gray-200 hover:border-green-400 hover:text-green-600"
              }`}
            >
              <div className="relative">
                <List size={20} />
                {addedDestinations.length > 0 && (
                  <span className="absolute -top-1.5 -right-1.5 bg-red-500 text-white text-[10px] w-4 h-4 flex items-center justify-center rounded-full font-bold shadow-sm">
                    {addedDestinations.length}
                  </span>
                )}
              </div>
              <span
                className={`${jost.className} text-sm font-bold hidden sm:block`}
              >
                Your List
              </span>
            </button>

            {/* SAVED DESTINATIONS BUTTON */}
            <button
              onClick={() => {
                setShowSavedList(!showSavedList);
                setShowSelectedList(false); // Close your list when opening this
              }}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-full transition-all shadow-sm border ${
                showSavedList
                  ? "bg-blue-100 text-blue-700 border-blue-200 ring-2 ring-blue-100"
                  : "bg-white text-gray-700 border-gray-200 hover:border-blue-400 hover:text-blue-600"
              }`}
            >
              <div className="relative">
                <Star
                  size={20}
                  className={showSavedList ? "fill-blue-500" : ""}
                />
                {savedDestinations.length > 0 && (
                  <span className="absolute -top-1.5 -right-1.5 bg-blue-500 text-white text-[10px] w-4 h-4 flex items-center justify-center rounded-full font-bold shadow-sm">
                    {savedDestinations.length}
                  </span>
                )}
              </div>
              <span
                className={`${jost.className} text-sm font-bold hidden sm:block`}
              >
                Saved
              </span>
            </button>

            {/* Selected List Dropdown */}
            {showSelectedList && (
              <div className="absolute top-full right-0 mt-3 w-72 bg-white rounded-2xl shadow-[0_10px_40px_-10px_rgba(0,0,0,0.2)] z-50 overflow-hidden border border-gray-100 animate-in fade-in zoom-in-95 duration-200">
                <div className="bg-gray-50 px-4 py-3 border-b border-gray-100 flex justify-between items-center">
                  <h3
                    className={`${jost.className} font-bold text-gray-700 text-sm`}
                  >
                    Selected ({addedDestinations.length})
                  </h3>
                  <button onClick={() => setShowSelectedList(false)}>
                    <X size={16} className="text-gray-400 hover:text-red-500" />
                  </button>
                </div>

                <div className="max-h-60 overflow-y-auto p-2 space-y-2">
                  {addedDestinations.length === 0 ? (
                    <div className="py-6 text-center">
                      <p className={`${jost.className} text-gray-400 text-xs`}>
                        No places added yet.
                      </p>
                    </div>
                  ) : (
                    addedDestinations.map((dest, idx) => (
                      <div
                        key={`${dest.place_id}-${idx}`}
                        // Clicking an item focuses it on the map
                        onClick={() => handleClickSavedItem(dest)}
                        className="flex items-center gap-3 bg-white p-2 rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow cursor-pointer hover:bg-green-50"
                      >
                        <div className="w-10 h-10 bg-gray-200 rounded-lg overflow-hidden shrink-0">
                          <img
                            src={
                              dest.photos?.[0]?.photo_url ||
                              "https://via.placeholder.com/100"
                            }
                            alt=""
                            className="w-full h-full object-cover"
                          />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p
                            className={`${jost.className} text-xs font-bold text-gray-800 truncate`}
                          >
                            {dest.name}
                          </p>
                          <p className="text-[10px] text-gray-500 truncate">
                            {dest.formatted_address}
                          </p>
                        </div>
                        <button
                          onClick={(e) =>
                            handleRemoveLocation(dest.place_id, e)
                          }
                          className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    ))
                  )}
                </div>
                {/* Finish button moved outside the dropdown */}
              </div>
            )}

            {/* Saved Destinations Dropdown */}
            {showSavedList && (
              <div className="absolute top-full right-0 mt-3 w-72 bg-white rounded-2xl shadow-[0_10px_40px_-10px_rgba(0,0,0,0.2)] z-50 overflow-hidden border border-gray-100 animate-in fade-in zoom-in-95 duration-200">
                <div className="bg-blue-50 px-4 py-3 border-b border-blue-100 flex justify-between items-center">
                  <h3
                    className={`${jost.className} font-bold text-blue-700 text-sm`}
                  >
                    Saved Destinations ({savedDestinations.length})
                  </h3>
                  <button onClick={() => setShowSavedList(false)}>
                    <X size={16} className="text-gray-400 hover:text-red-500" />
                  </button>
                </div>

                <div className="max-h-60 overflow-y-auto p-2 space-y-2">
                  {isLoadingSaved ? (
                    <div className="py-6 text-center">
                      <Loader2
                        className="animate-spin text-blue-500 mx-auto mb-2"
                        size={24}
                      />
                      <p className={`${jost.className} text-gray-400 text-xs`}>
                        Loading saved destinations...
                      </p>
                    </div>
                  ) : savedDestinations.length === 0 ? (
                    <div className="py-6 text-center">
                      <Star className="text-gray-300 mx-auto mb-2" size={32} />
                      <p className={`${jost.className} text-gray-400 text-xs`}>
                        No saved destinations yet.
                      </p>
                      <p
                        className={`${jost.className} text-gray-400 text-[10px] mt-1`}
                      >
                        Save destinations to see them here!
                      </p>
                    </div>
                  ) : (
                    savedDestinations.map((dest, idx) => {
                      const isAlreadyAdded = addedDestinations.some(
                        (d) => d.place_id === dest.place_id
                      );

                      return (
                        <div
                          key={`${dest.place_id}-saved-${idx}`}
                          className="flex items-center gap-3 bg-white p-2 rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow"
                        >
                          <div className="w-10 h-10 bg-gray-200 rounded-lg overflow-hidden shrink-0">
                            <img
                              src={
                                dest.photos?.[0]?.photo_url ||
                                "https://via.placeholder.com/100"
                              }
                              alt=""
                              className="w-full h-full object-cover"
                            />
                          </div>
                          <div
                            className="flex-1 min-w-0 cursor-pointer"
                            onClick={() => {
                              handleClickSavedItem(dest);
                              setShowSavedList(false);
                            }}
                          >
                            <p
                              className={`${jost.className} text-xs font-bold text-gray-800 truncate`}
                            >
                              {dest.name}
                            </p>
                            <p className="text-[10px] text-gray-500 truncate">
                              {dest.formatted_address}
                            </p>
                          </div>

                          {isAlreadyAdded ? (
                            <div className="p-1.5 text-green-500 bg-green-50 rounded-full">
                              <Check size={14} />
                            </div>
                          ) : (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleClickSavedItem(dest);
                                setShowSavedList(false);
                              }}
                              className="p-1.5 text-blue-500 hover:text-blue-700 hover:bg-blue-50 rounded-full transition-colors"
                              title="View on map"
                            >
                              <Eye size={14} />
                            </button>
                          )}
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* MAP AREA */}
        <div className="flex-1 relative w-full h-full bg-[#E9F5EB]">
          {!isLoaded ? (
            <div className="w-full h-full flex flex-col items-center justify-center">
              <Loader2 className="animate-spin text-green-500 mb-2" size={32} />
              <span className={`${jost.className} text-gray-500 text-sm`}>
                Loading map...
              </span>
            </div>
          ) : (
            <div ref={mapRef} className="w-full h-full" />
          )}

          {isSearching && (
            <div className="absolute inset-0 bg-white/50 backdrop-blur-sm z-10 flex items-center justify-center">
              <Loader2 className="animate-spin text-[#53B552]" size={40} />
            </div>
          )}
        </div>

        <div className="bg-white border-t border-gray-100">
          {selectedLocation && (
            <div className="px-4 py-4 border-b border-gray-100">
              <div className="flex gap-4">
                <div className="w-20 h-20 rounded-xl bg-gray-200 overflow-hidden shrink-0 shadow-inner">
                  <img
                    src={
                      selectedLocation.photos?.[0]?.photo_url ||
                      "https://via.placeholder.com/150"
                    }
                    className="w-full h-full object-cover"
                    alt={selectedLocation.name}
                  />
                </div>

                <div className="flex-1 min-w-0 flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-start">
                      <h3
                        className={`${jost.className} font-bold text-gray-900 text-lg truncate pr-2`}
                      >
                        {selectedLocation.name}
                      </h3>
                      <button
                        onClick={handleCloseDetail}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        <X size={20} />
                      </button>
                    </div>
                    <p
                      className={`${jost.className} text-gray-500 text-xs line-clamp-1 mt-0.5`}
                    >
                      {selectedLocation.formatted_address}
                    </p>

                    <div className="flex items-center gap-3 mt-2">
                      {selectedLocation.rating && (
                        <div className="flex items-center gap-1 bg-yellow-50 px-1.5 py-0.5 rounded-md border border-yellow-100">
                          <Star
                            size={10}
                            className="fill-yellow-400 text-yellow-400"
                          />
                          <span className="text-[10px] font-bold text-yellow-700">
                            {selectedLocation.rating}
                          </span>
                          <span className="text-[10px] text-yellow-600/70">
                            ({selectedLocation.user_ratings_total || 0})
                          </span>
                        </div>
                      )}
                      {selectedLocation.types?.[0] && (
                        <div className="text-[10px] text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded-md capitalize truncate max-w-[100px]">
                          {selectedLocation.types[0].replace(/_/g, " ")}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex gap-3 mt-4">
                    <button
                      onClick={() =>
                        router.push(
                          `/place_detail_page?place_id=${selectedLocation.place_id}`
                        )
                      }
                      className={`${jost.className} flex-1 bg-gray-100 text-gray-700 py-2.5 rounded-lg font-bold text-sm hover:bg-gray-200 active:scale-[0.98] transition-all flex justify-center items-center gap-2`}
                    >
                      <Eye size={16} /> View Details
                    </button>

                    <button
                      onClick={handleAddLocation}
                      disabled={isAlreadyAdded || false}
                      className={`${
                        jost.className
                      } flex-1 py-2.5 rounded-lg font-bold text-sm shadow-md transition-all flex justify-center items-center gap-2
                        ${
                          isAlreadyAdded
                            ? "bg-gray-50 text-gray-400 cursor-not-allowed border border-gray-200 shadow-none"
                            : "bg-[#53B552] text-white hover:bg-green-600 active:scale-[0.98]"
                        }
                      `}
                    >
                      {isAlreadyAdded ? (
                        <>
                          <Check size={16} /> Added
                        </>
                      ) : (
                        <>
                          <Plus size={16} strokeWidth={3} /> Add to Plan
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="px-4 py-4 space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <p
                  className={`${jost.className} text-[11px] font-bold uppercase tracking-wide text-gray-500`}
                >
                  {listTitle}
                </p>
                <p className={`${jost.className} text-xs text-gray-500 mt-0.5`}>
                  {listSubtitle}
                </p>
              </div>
              {hasSearchResults && (
                <button
                  onClick={() => {
                    setSearchQuery("");
                    setSearchResults([]);
                    setLastSearchQuery("");
                    setSearchError(null);
                  }}
                  className={`${jost.className} text-xs font-semibold text-green-600 hover:text-green-700`}
                >
                  Clear
                </button>
              )}
            </div>

            <div className="max-h-60 overflow-y-auto pr-1 space-y-3">
              {isListLoading ? (
                <div className="py-6 flex flex-col items-center justify-center text-gray-500">
                  <Loader2
                    className="animate-spin text-green-500 mb-2"
                    size={22}
                  />
                  <p className={`${jost.className} text-xs`}>
                    {hasSearchResults
                      ? "Fetching matching places..."
                      : "Loading green highlights..."}
                  </p>
                </div>
              ) : listPlaces.length === 0 ? (
                <div className="py-6 text-center">
                  <p className={`${jost.className} text-xs text-gray-500`}>
                    {emptyStateMessage}
                  </p>
                </div>
              ) : (
                listPlaces.map((place) => (
                  <button
                    key={place.place_id}
                    onClick={() => focusPlaceById(place.place_id)}
                    className="w-full flex items-center gap-3 rounded-2xl border border-gray-100 bg-white p-3 shadow-sm hover:shadow-md transition-all text-left"
                  >
                    <div className="w-14 h-14 rounded-xl bg-gray-200 overflow-hidden shrink-0">
                      <img
                        src={
                          place.photos?.[0]?.photo_url ||
                          "https://via.placeholder.com/120"
                        }
                        alt={place.name}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p
                        className={`${jost.className} text-sm font-semibold text-gray-900 truncate`}
                      >
                        {place.name}
                      </p>
                      <p className="text-xs text-gray-500 line-clamp-1">
                        {place.formatted_address}
                      </p>
                      {place.distanceText && (
                        <p className="text-[10px] text-green-600 font-semibold mt-1">
                          {place.distanceText}
                        </p>
                      )}
                    </div>
                    <div className="flex flex-col items-end gap-1 text-xs font-semibold text-green-600">
                      <span>{hasSearchResults ? "View" : "Pick"}</span>
                      <Plus size={16} />
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>

          {!selectedLocation && addedDestinations.length > 0 && (
            <div className="px-4 pb-6">
              <button
                onClick={handleFinish}
                className={`${jost.className} w-full bg-[#53B552] hover:bg-green-600 text-white shadow-[0_4px_15px_rgba(83,181,82,0.4)] px-6 py-3.5 rounded-2xl font-bold text-sm flex items-center justify-center gap-2 transition-all active:scale-[0.97]`}
              >
                <span>Finish & Review ({addedDestinations.length})</span>
                <ArrowRight size={18} />
              </button>
            </div>
          )}
        </div>
        {showWelcome && (
          <div className="absolute inset-0 z-60 bg-black/40 backdrop-blur-[2px] flex items-center justify-center p-4 animate-in fade-in duration-300">
            <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-6 relative animate-in zoom-in-95 duration-300">
              <button
                onClick={() => setShowWelcome(false)}
                className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>

              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <MapPin size={24} className="text-green-600" />
              </div>

              <h2
                className={`${jost.className} text-xl font-bold text-gray-800 mb-2`}
              >
                Let’s plan your trip!
              </h2>
              <p
                className={`${jost.className} text-gray-500 text-sm mb-6 leading-relaxed`}
              >
                Start by searching for locations. We have suggested some{" "}
                <span className="text-green-600 font-bold">
                  Green Destinations
                </span>{" "}
                nearby for you.
                <br />
                <br />
                Add at least <strong>2 places</strong> to create your route.
              </p>

              <button
                onClick={() => setShowWelcome(false)}
                className={`${jost.className} w-full bg-[#53B552] hover:bg-green-600 text-white font-bold py-3 rounded-xl shadow-lg shadow-green-200 transition-all active:scale-95`}
              >
                Got it, let’s go!
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
