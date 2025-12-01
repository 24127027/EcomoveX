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
  ArrowRight, // Icon cho nút Finish
} from "lucide-react";
import { useGoogleMaps } from "@/lib/useGoogleMaps";
import { api, PlaceDetails, AutocompletePrediction, Position } from "@/lib/api";
import { Jost } from "next/font/google";

const jost = Jost({ subsets: ["latin"], weight: ["400", "500", "600", "700"] });

const STORAGE_KEY = "temp_plan_destinations";
const CURRENT_VIEWING_KEY = "current_viewing_place";

export default function AddDestinationPage() {
  const [showWelcome, setShowWelcome] = useState(true); // [NEW] Hiện modal hướng dẫn
  const [initialSuggestions, setInitialSuggestions] = useState<
    AutocompletePrediction[]
  >([]);
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
  const [searchQuery, setSearchQuery] = useState("");
  const [predictions, setPredictions] = useState<AutocompletePrediction[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<PlaceDetails | null>(
    null
  );
  const [isSearching, setIsSearching] = useState(false);

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
        // ✅ Clean up place_id by removing suffix like "-0", "-1", "-2"
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
  }, []);

  useEffect(() => {
    if (!userLocation || !sessionTokenRef.current) return;

    const fetchGreenSuggestions = async () => {
      try {
        // Tìm kiếm các từ khóa liên quan đến du lịch xanh
        const res = await api.autocomplete({
          query: "Green tourism nature", // Hoặc "Du lịch sinh thái"
          user_location: userLocation,
          radius: 10000, // Tìm rộng hơn chút (10km)
          session_token: sessionTokenRef.current,
        });

        if (res && res.predictions) {
          setInitialSuggestions(res.predictions.slice(0, 5));
          // Nếu chưa nhập gì thì gán luôn vào predictions để hiển thị ngay
          if (!searchQuery) {
            setPredictions(res.predictions.slice(0, 5));
          }
        }
      } catch (error) {
        console.error("Initial Green Search Error:", error);
      }
    };

    fetchGreenSuggestions();
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
  }, [isLoaded]);

  // Marker Logic (Tự động pan/zoom khi selectedLocation thay đổi)
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

  const handleSelectPrediction = async (prediction: AutocompletePrediction) => {
    setSearchQuery(prediction.description);
    setPredictions([]);
    setIsSearching(true);

    try {
      const details = await api.getPlaceDetails(
        prediction.place_id,
        sessionTokenRef.current,
        ["basic", "contact", "atmosphere"]
      );

      setSelectedLocation(details);
      sessionStorage.setItem(CURRENT_VIEWING_KEY, JSON.stringify(details));
      refreshSessionToken();
    } catch (error) {
      console.error("Details Error:", error);
      alert("Could not fetch location details.");
    } finally {
      setIsSearching(false);
    }
  };

  // --- ACTIONS ---

  const handleCloseDetail = () => {
    setSelectedLocation(null);
    sessionStorage.removeItem(CURRENT_VIEWING_KEY);
  };

  // [NEW] Hàm xử lý khi click vào item trong list đã chọn
  const handleClickSavedItem = (place: PlaceDetails) => {
    setSelectedLocation(place); // Set cái này thì useEffect sẽ tự pan map tới đó
    sessionStorage.setItem(CURRENT_VIEWING_KEY, JSON.stringify(place));
    setShowSelectedList(false); // Đóng list dropdown để user xem map
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
    // [UPDATE] Validate ít nhất 2 địa điểm
    if (addedDestinations.length < 2) {
      // Dùng window.confirm hoặc alert tùy ý, alert cho đơn giản
      alert(
        `You need at least 2 destinations to continue! (Current: ${addedDestinations.length})`
      );
      return;
    }

    // ✅ Get planId from sessionStorage to check if EDIT or CREATE mode
    const planId = sessionStorage.getItem("EDITING_PLAN_ID");

    if (planId) {
      // ✅ EDIT MODE: Keep destinations in storage for review_plan to merge with API data
      // Storage will be cleared AFTER save in review_plan
      console.log(
        `📎 EDIT MODE: Returning to review_plan with planId: ${planId}`
      );
      router.push(`/planning_page/review_plan?id=${planId}`);
    } else {
      // ✅ CREATE MODE: Keep destinations in storage for review_plan to use
      console.log(`📝 CREATE MODE: Keeping destinations in storage`);
      router.push("/planning_page/review_plan");
    }
  };

  const isAlreadyAdded =
    selectedLocation &&
    addedDestinations.some((d) => d.place_id === selectedLocation.place_id);

  // ✅ Debug: Log only when selectedLocation changes
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
            <div className="flex items-center bg-gray-100 rounded-full px-3 py-2.5 transition-all focus-within:ring-2 focus-within:ring-green-100">
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
                  onClick={() => {
                    setSearchQuery("");
                    setPredictions([]);
                  }}
                  className="p-1"
                >
                  <X size={16} className="text-gray-400" />
                </button>
              )}
            </div>

            {/* Prediction Dropdown */}
            {(predictions.length > 0 ||
              (searchQuery === "" && initialSuggestions.length > 0)) && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-xl z-50 overflow-hidden border border-gray-100 max-h-64 overflow-y-auto">
                {/* [NEW] Header nhỏ để phân biệt gợi ý hay kết quả tìm kiếm */}
                <div className="bg-gray-50 px-3 py-2 border-b border-gray-100">
                  <p
                    className={`${jost.className} text-xs font-bold text-green-600 uppercase tracking-wide`}
                  >
                    {searchQuery ? "Search Results" : "🌿 Green Places Nearby"}
                  </p>
                </div>

                {(searchQuery ? predictions : initialSuggestions).map((p) => (
                  <div
                    key={p.place_id}
                    onClick={() => handleSelectPrediction(p)}
                    className="p-3 hover:bg-green-50 active:bg-green-100 cursor-pointer border-b border-gray-50 last:border-0 flex items-start gap-3 transition-colors"
                  >
                    <div className="bg-gray-100 p-1.5 rounded-full shrink-0">
                      {/* Đổi icon lá cây nếu là gợi ý ban đầu */}
                      {!searchQuery ? (
                        <MapPin size={16} className="text-green-500" />
                      ) : (
                        <MapPin size={16} className="text-gray-500" />
                      )}
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

          <div className="relative">
            <button
              onClick={() => setShowSelectedList(!showSelectedList)}
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
                        // [UPDATE] Click vào item để xem chi tiết
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
                {/* [UPDATE] Đã bỏ nút Finish ở trong này ra ngoài */}
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

          {/* BOTTOM CARD: DETAIL INFO */}
          {selectedLocation ? (
            <div className="absolute bottom-6 left-4 right-4 bg-white rounded-2xl shadow-[0_10px_30px_rgba(0,0,0,0.15)] p-4 z-10 animate-in slide-in-from-bottom-10 duration-300">
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
          ) : (
            // [UPDATE] Nút Finish "Floating" hiện ra khi KHÔNG có thẻ chi tiết nào mở
            // Chỉ hiện nếu đã add ít nhất 1 địa điểm để user biết là cần bấm vào đây
            addedDestinations.length > 0 && (
              <div className="absolute bottom-6 right-4 z-10 animate-in slide-in-from-bottom-5 duration-300">
                <button
                  onClick={handleFinish}
                  className={`${jost.className} bg-[#53B552] hover:bg-green-600 text-white shadow-[0_4px_15px_rgba(83,181,82,0.4)] 
                        px-6 py-3.5 rounded-full font-bold text-sm flex items-center gap-2 transition-all active:scale-[0.95]`}
                >
                  <span>Finish & Review ({addedDestinations.length})</span>
                  <ArrowRight size={18} />
                </button>
              </div>
            )
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
                Let's plan your trip!
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
                Got it, let's go!
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
