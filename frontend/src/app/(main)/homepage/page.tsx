"use client";
import {
  Knewave,
  Josefin_Sans,
  Abhaya_Libre,
  Poppins,
  Gotu,
  Jost,
} from "next/font/google";
import {
  Search,
  Heart,
  Map as MapIcon,
  Calendar,
  ArrowRight,
  Trophy,
  Loader2,
  Route,
  Star,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  api,
  TravelPlan,
  UserRewardResponse,
  GreenPlaceRecommendation,
} from "@/lib/api";
import { MobileNavMenu } from "@/components/MobileNavMenu";
import { PRIMARY_NAV_LINKS } from "@/constants/navLinks";

type Coordinates = {
  lat: number;
  lng: number;
};

// --- FONTS ---
export const gotu = Gotu({ subsets: ["latin"], weight: ["400"] });
export const jost = Jost({ subsets: ["latin"], weight: ["700"] });
export const abhaya_libre = Abhaya_Libre({
  subsets: ["latin"],
  weight: ["700"],
});
export const poppins = Poppins({ subsets: ["latin"], weight: ["300"] });
export const josefin_sans = Josefin_Sans({
  subsets: ["latin"],
  weight: ["700"],
});
export const knewave = Knewave({ subsets: ["latin"], weight: ["400"] });

const parseDate = (dateStr: string) => {
  if (!dateStr) return new Date(0);
  if (dateStr.includes("-")) {
    const [year, month, day] = dateStr.split("-").map(Number);
    return new Date(year, month - 1, day);
  }
  if (dateStr.includes("/")) {
    const [day, month, year] = dateStr.split("/").map(Number);
    return new Date(year, month - 1, day);
  }
  return new Date(dateStr);
};

// Tọa độ mặc định (TP.HCM) dùng khi lỗi GPS
const DEFAULT_LAT = 10.7769;
const DEFAULT_LNG = 106.6953;
const LOCATION_TIMEOUT_MS = 10_000;
const LAST_LOCATION_STORAGE_KEY = "ecomovex:last-location";

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState("");
  const router = useRouter();

  // State for Plan & Rewards
  const [upcomingPlan, setUpcomingPlan] = useState<TravelPlan | null>(null);
  const [loadingPlan, setLoadingPlan] = useState(true);
  const [userReward, setUserReward] = useState<UserRewardResponse | null>(null);
  const [nextLevelTarget, setNextLevelTarget] = useState(100);
  const [loadingRewards, setLoadingRewards] = useState(true);

  // State cho Carousel
  const [greenPlaces, setGreenPlaces] = useState<GreenPlaceRecommendation[]>(
    []
  );
  const [loadingGreenPlaces, setLoadingGreenPlaces] = useState(true);
  const [cachedLocation, setCachedLocation] = useState<Coordinates | null>(
    null
  );

  // State Saved Locations
  const [savedPlaceIds, setSavedPlaceIds] = useState<Set<string>>(new Set());
  const [togglingId, setTogglingId] = useState<string | null>(null);

  const rememberLocation = useCallback(
    (coords: Coordinates, options?: { persist?: boolean }) => {
      setCachedLocation(coords);
      if (options?.persist === false || typeof window === "undefined") return;
      try {
        sessionStorage.setItem(
          LAST_LOCATION_STORAGE_KEY,
          JSON.stringify(coords)
        );
      } catch (error) {
        console.warn("Unable to cache location:", error);
      }
    },
    [setCachedLocation]
  );

  const readStoredLocation = useCallback((): Coordinates | null => {
    if (typeof window === "undefined") return null;
    try {
      const raw = sessionStorage.getItem(LAST_LOCATION_STORAGE_KEY);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (typeof parsed?.lat === "number" && typeof parsed?.lng === "number") {
        return parsed;
      }
    } catch (error) {
      console.warn("Unable to read cached location:", error);
    }
    return null;
  }, []);

  const getUserLocation = (): Promise<Coordinates> =>
    new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error("Geolocation is not supported"));
        return;
      }
      navigator.geolocation.getCurrentPosition(
        (position) =>
          resolve({
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          }),
        (error) => reject(error)
      );
    });

  useEffect(() => {
    let isMounted = true;
    let requestCounter = 0;
    let lastResolvedRequest = 0;
    let hasRenderedOnce = false;
    let fallbackTimer: ReturnType<typeof setTimeout> | null = null;

    const syncSavedDestinations = async () => {
      try {
        const savedList = await api.getSavedDestinations();
        if (isMounted) {
          setSavedPlaceIds(new Set(savedList.map((i) => i.destination_id)));
        }
      } catch (e) {
        console.error(e);
      }
    };

    const enhancePlacePhotos = async (
      basePlaces: GreenPlaceRecommendation[]
    ) => {
      const needingDetails = basePlaces.filter((place) => !place.photo_url);
      if (needingDetails.length === 0) return;

      const detailEntries = await Promise.allSettled(
        needingDetails.map(async (place) => {
          const details = await api.getPlaceDetails(place.place_id);
          return {
            ...place,
            photo_url:
              details.photos?.[0]?.photo_url || "/images/tao-dan-park.png",
            rating: details.rating || place.rating,
          };
        })
      );

      if (!isMounted) return;

      const replacementMap = new Map<string, GreenPlaceRecommendation>();
      detailEntries.forEach((result) => {
        if (result.status === "fulfilled") {
          replacementMap.set(result.value.place_id, result.value);
        }
      });

      if (replacementMap.size === 0) return;

      setGreenPlaces((prev) => {
        if (!Array.isArray(prev) || prev.length === 0) return prev;
        return prev.map((place) => replacementMap.get(place.place_id) ?? place);
      });
    };

    const loadGreenPlaces = async (
      coords: Coordinates,
      options: { showLoader?: boolean } = {}
    ) => {
      const { showLoader = true } = options;
      const currentRequestId = ++requestCounter;
      if (showLoader && isMounted) setLoadingGreenPlaces(true);
      try {
        const recommendations = await api.getNearbyGreenPlaces(
          coords.lat,
          coords.lng,
          10,
          5
        );

        if (!isMounted || currentRequestId < lastResolvedRequest) return;

        setGreenPlaces(Array.isArray(recommendations) ? recommendations : []);
        lastResolvedRequest = currentRequestId;

        syncSavedDestinations();
        enhancePlacePhotos(recommendations || []).catch((photoError) =>
          console.error("Photo enhancement error:", photoError)
        );
      } catch (error) {
        console.error("API Error:", error);
        if (isMounted) setGreenPlaces([]);
      } finally {
        if (showLoader && isMounted) setLoadingGreenPlaces(false);
      }
    };

    const defaultCoords = { lat: DEFAULT_LAT, lng: DEFAULT_LNG };

    const kickOffLoad = (coords: Coordinates, forceLoader = false) => {
      const showLoader = forceLoader || !hasRenderedOnce;
      loadGreenPlaces(coords, { showLoader });
      hasRenderedOnce = true;
    };

    const hydratedFromStorage = (() => {
      const stored = readStoredLocation();
      if (!stored) return false;
      rememberLocation(stored);
      kickOffLoad(stored, true);
      return true;
    })();

    if (!hydratedFromStorage) {
      fallbackTimer = setTimeout(() => {
        if (!isMounted || hasRenderedOnce) return;
        rememberLocation(defaultCoords, { persist: false });
        kickOffLoad(defaultCoords, true);
      }, LOCATION_TIMEOUT_MS);
    }

    getUserLocation()
      .then((pos) => {
        if (!isMounted) return;
        if (fallbackTimer) {
          clearTimeout(fallbackTimer);
          fallbackTimer = null;
        }
        rememberLocation(pos);
        kickOffLoad(pos);
      })
      .catch((error) => {
        console.warn("⚠️ Cannot get location, using DEFAULT:", error);
        if (!isMounted) return;
        if (!hasRenderedOnce) {
          if (fallbackTimer) {
            clearTimeout(fallbackTimer);
            fallbackTimer = null;
          }
          rememberLocation(defaultCoords, { persist: false });
          kickOffLoad(defaultCoords, true);
        }
      });

    return () => {
      isMounted = false;
      if (fallbackTimer) clearTimeout(fallbackTimer);
    };
  }, [readStoredLocation, rememberLocation]);

  // ... (Giữ nguyên các useEffect fetchUpcomingPlan, fetchRewardData)
  useEffect(() => {
    const f = async () => {
      try {
        const p = await api.getPlans();
        const t = new Date();
        t.setHours(0, 0, 0, 0);
        // Filter: future plans AND have at least 2 activities
        const fp = p.filter((i) => {
          const d = parseDate(i.date);
          const hasEnoughActivities = i.activities && i.activities.length >= 2;
          return d >= t && hasEnoughActivities;
        });
        fp.sort(
          (a, b) => parseDate(a.date).getTime() - parseDate(b.date).getTime()
        );
        if (fp.length > 0) setUpcomingPlan(fp[0]);
      } catch {
      } finally {
        setLoadingPlan(false);
      }
    };
    f();
  }, []);
  useEffect(() => {
    const f = async () => {
      try {
        const d = await api.getUserRewards();
        setUserReward(d);
        const p = d.total_points || 0;
        let t = 100;
        if (p >= 600) t = 1000;
        else if (p >= 300) t = 600;
        else if (p >= 100) t = 300;
        setNextLevelTarget(t);
      } catch {
      } finally {
        setLoadingRewards(false);
      }
    };
    f();
  }, []);

  const getCurrentLevel = (points: number) => {
    if (points >= 600) return 3;
    if (points >= 300) return 2;
    if (points >= 100) return 1;
    return 1;
  };
  const getProgressPercent = () => {
    if (!userReward) return 0;
    const p = userReward.total_points || 0;
    let pt = 0;
    if (nextLevelTarget === 300) pt = 100;
    else if (nextLevelTarget === 600) pt = 300;
    else if (nextLevelTarget === 1000) pt = 600;
    const pr = ((p - pt) / (nextLevelTarget - pt)) * 100;
    return Math.min(Math.max(pr, 0), 100);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) =>
    setSearchQuery(e.target.value);

  const handleToggleHeart = async (
    place: GreenPlaceRecommendation,
    e: React.MouseEvent
  ) => {
    e.stopPropagation();
    if (togglingId === place.place_id) return;
    setTogglingId(place.place_id);
    const isCurrentlySaved = savedPlaceIds.has(place.place_id);
    const newSet = new Set(savedPlaceIds);
    if (isCurrentlySaved) newSet.delete(place.place_id);
    else newSet.add(place.place_id);
    setSavedPlaceIds(newSet);
    try {
      if (!isCurrentlySaved) {
        await api.getPlaceDetails(place.place_id);
        await api.saveDestination(place.place_id);
      } else {
        await api.unsaveDestination(place.place_id);
      }
    } catch {
      setSavedPlaceIds(savedPlaceIds);
    } finally {
      setTogglingId(null);
    }
  };

  const buildMapHref = (query?: string, coords?: Coordinates | null) => {
    const params = new URLSearchParams();
    if (query && query.length > 0) params.set("q", query);
    if (coords) {
      params.set("lat", coords.lat.toString());
      params.set("lng", coords.lng.toString());
    }
    const search = params.toString();
    return search ? `/map_page?${search}` : "/map_page";
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = searchQuery.trim();
    router.push(buildMapHref(trimmed || undefined));
  };

  const handleSearchNearby = () => {
    if (cachedLocation) {
      router.push(buildMapHref("eco-friendly", cachedLocation));
      return;
    }

    router.push(buildMapHref("eco-friendly"));
    getUserLocation()
      .then((pos) => rememberLocation(pos))
      .catch(() => {
        alert("Please enable location services to search nearby.");
      });
  };

  const handleTagClick = (tag: string) => {
    if (cachedLocation) {
      router.push(buildMapHref(tag, cachedLocation));
      return;
    }

    router.push(buildMapHref(tag));
    getUserLocation()
      .then((pos) => rememberLocation(pos))
      .catch(() => {
        // ignore; default map already opened
      });
  };

  return (
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      <div className="w-full max-w-md bg-gray-50 h-screen flex flex-col overflow-hidden shadow-2xl relative">
        <MobileNavMenu items={PRIMARY_NAV_LINKS} activeKey="home" />
        {/* --- HEADER --- */}
        <header className="bg-[#53B552] px-4 pt-5 pb-6 shadow-md shrink-0 z-10">
          <form
            onSubmit={handleSearchSubmit}
            className={`flex justify-between items-center gap-4`}
          >
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-gray-400" />
              <input
                type="text"
                className={`${abhaya_libre.className} w-full rounded-full py-2 pl-10 pr-12 text-sm bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-300 placeholder:text-green-700 placeholder:font-semibold`}
                placeholder="Search for an eco-friendly place"
                value={searchQuery}
                onChange={handleChange}
              />
              <button
                type="button"
                onClick={() => router.push("/map_page")}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-gray-100 transition-colors"
              >
                <MapIcon className="size-5 text-green-600" />
              </button>
            </div>
            <div
              className={`${knewave.className} text-white font-bold text-2xl select-none`}
            >
              EcomoveX
            </div>
          </form>
          <div className="flex justify-center gap-3 mt-4 flex-wrap">
            {["Cafe", "Restaurant", "Park", "Hotel", "Shopping"].map((i) => (
              <button
                key={i}
                onClick={() => handleTagClick(i)}
                className={`${jost.className} cursor-pointer bg-white text-[#53B552] rounded-full px-4 py-1 text-sm font-medium hover:text-white hover:bg-green-500 transition-colors`}
              >
                {i}
              </button>
            ))}
          </div>
        </header>

        {/* --- MAIN CONTENT --- */}
        <main
          className={`p-4 flex-1 overflow-y-auto flex flex-col gap-5 pb-20`}
        >
          {/* SECTION 1: CAROUSEL */}
          <section
            className={`bg-[#F9FFF9] rounded-xl shadow-sm p-4 border border-green-100`}
          >
            <div className="flex justify-between items-center mb-3">
              <h2
                className={`${jost.className} font-bold text-green-600 uppercase text-xl tracking-wide`}
              >
                Recommended
              </h2>
              {!loadingGreenPlaces && greenPlaces.length > 0 && (
                <span className="text-[10px] text-green-500 bg-green-100 px-2 py-0.5 rounded-full font-bold">
                  Top {greenPlaces.length}
                </span>
              )}
            </div>

            {loadingGreenPlaces ? (
              <div className="h-56 w-full flex items-center justify-center bg-gray-100 rounded-lg">
                <Loader2 className="animate-spin text-green-600" />
              </div>
            ) : greenPlaces.length > 0 ? (
              <div className="flex overflow-x-auto gap-4 pb-2 snap-x snap-mandatory scrollbar-hide -mx-2 px-2">
                {greenPlaces.map((place) => {
                  const isSaved = savedPlaceIds.has(place.place_id);
                  return (
                    <div
                      key={place.place_id}
                      className="min-w-[85%] sm:min-w-[300px] snap-center bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden flex flex-col group cursor-pointer active:scale-95 transition-transform duration-200"
                      onClick={() =>
                        router.push(
                          `/place_detail_page?place_id=${place.place_id}`
                        )
                      }
                    >
                      <div className="relative h-32 w-full bg-gray-200">
                        {place.photo_url ? (
                          <Image
                            src={place.photo_url}
                            alt={place.name}
                            fill
                            className="object-cover"
                          />
                        ) : (
                          <div className="flex h-full items-center justify-center text-gray-400 text-xs">
                            No Image
                          </div>
                        )}
                        <div className="absolute top-2 left-2 bg-black/60 backdrop-blur-sm text-white text-[10px] px-2 py-0.5 rounded-full flex items-center gap-1">
                          <Route size={10} /> {place.distance_km} km
                        </div>
                        <button
                          onClick={(e) => handleToggleHeart(place, e)}
                          className="absolute top-2 right-2 p-1.5 bg-white/80 backdrop-blur-sm rounded-full hover:bg-white transition-colors"
                        >
                          <Heart
                            size={16}
                            className={`${
                              isSaved
                                ? "fill-green-600 text-green-600"
                                : "text-gray-500"
                            } transition-colors`}
                          />
                        </button>
                      </div>
                      <div className="p-3 flex flex-col justify-between flex-1">
                        <div>
                          <div className="flex justify-between items-start">
                            <h3
                              className={`${abhaya_libre.className} font-bold text-gray-800 text-base line-clamp-1`}
                            >
                              {place.name}
                            </h3>
                            {place.rating && (
                              <div className="flex items-center gap-0.5 bg-yellow-50 px-1.5 py-0.5 rounded text-[10px] text-yellow-700 font-bold border border-yellow-100">
                                <Star
                                  size={10}
                                  className="fill-yellow-400 text-yellow-400"
                                />
                                {place.rating}
                              </div>
                            )}
                          </div>
                          <p className="text-xs text-gray-500 mt-1 line-clamp-1">
                            {place.formatted_address}
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 text-sm bg-gray-50 rounded-lg border border-dashed border-gray-200">
                No green places found nearby.
              </div>
            )}
          </section>

          {/* SECTION 2 & 3 */}
          <section className={`grid grid-cols-2 gap-4`}>
            <div className="bg-linear-to-b from-green-500 to-green-600 rounded-xl p-4 text-white flex flex-col justify-between shadow-lg min-h-[150px] relative overflow-hidden group">
              <div className="absolute -right-6 -top-6 w-20 h-20 bg-white/10 rounded-full"></div>
              {loadingPlan ? (
                <div className="animate-pulse space-y-3">
                  <div className="h-4 bg-white/20 rounded w-1/2"></div>
                  <div className="h-6 bg-white/30 rounded w-3/4"></div>
                </div>
              ) : upcomingPlan ? (
                <>
                  <div>
                    <div className="flex items-center gap-1 mb-1 opacity-90">
                      <Calendar size={14} />
                      <span
                        className={`${jost.className} text-[10px] uppercase tracking-wider`}
                      >
                        Upcoming Trip
                      </span>
                    </div>
                    <h3
                      className={`${abhaya_libre.className} text-lg font-bold leading-tight line-clamp-2`}
                    >
                      {upcomingPlan.destination}
                    </h3>
                    <p className="text-xs text-green-100 mt-1 font-medium">
                      {upcomingPlan.date}
                    </p>
                  </div>
                  <Link href={`/planning_page/showing_plan_page`}>
                    <button className="mt-3 w-full bg-white/20 hover:bg-white/30 transition-colors rounded-full py-1.5 px-3 text-xs font-bold flex items-center justify-center gap-1 backdrop-blur-sm">
                      View Plan <ArrowRight size={12} />
                    </button>
                  </Link>
                </>
              ) : (
                <div className="flex flex-col h-full justify-center items-start">
                  <p
                    className={`${abhaya_libre.className} text-lg font-bold mb-2`}
                  >
                    New Adventure?
                  </p>
                  <Link href="/planning_page/create_plan" className="w-full">
                    <button className="w-full bg-white text-green-600 py-2 rounded-full text-xs font-bold shadow-md hover:bg-green-50 transition-colors">
                      + Create Plan
                    </button>
                  </Link>
                </div>
              )}
            </div>

            <div className="bg-[#F3FBF5] p-5 rounded-2xl flex flex-col justify-center items-center h-full shadow-sm border border-green-500 text-center relative overflow-hidden">
              <div className="absolute top-0 right-0 w-16 h-16 bg-green-100 rounded-bl-full opacity-50"></div>
              <h3
                className={`${abhaya_libre.className} text-green-700/80 uppercase tracking-widset text-sm mb-1`}
              >
                Nearby
              </h3>
              <h2
                className={`${abhaya_libre.className} text-green-600 text-xl font-bold leading-tight mb-4`}
              >
                ECO-FRIENDLY <br /> SPOTS
              </h2>
              <button
                onClick={handleSearchNearby}
                className="bg-[#53B552] text-white px-6 py-2 rounded-full text-sm font-bold shadow-md hover:bg-green-600 hover:shadow-lg transition-all active:scale-95 flex items-center gap-2"
              >
                Search Now
              </button>
            </div>
          </section>

          <section className="mt-0">
            <div className="bg-white p-5 rouned-3xl shadow-sm border border-gray-100">
              {loadingRewards ? (
                <div className="flex justify-center py-4">
                  <Loader2 className="animate-spin text-green-600" />
                </div>
              ) : (
                <>
                  <div className="flex justify-between items-center mb-3">
                    <h3
                      className={`${jost.className} font-bold text-lg text-gray-800`}
                    >
                      Your Eco Impact
                    </h3>
                    <span className="text-green-600 font-bold bg-green-50 px-3 py-1 rounded-full text-xs">
                      Level{" "}
                      {userReward
                        ? getCurrentLevel(userReward.total_points || 0)
                        : 1}
                    </span>
                  </div>
                  <div className="flex gap-4 items-center">
                    <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center text-yellow-600 shrink-0">
                      <Trophy size={24} />
                    </div>
                    <div className="flex-1">
                      <p
                        className={`${jost.className} text-sm font-bold text-gray-700`}
                      >
                        Eco Warrior Journey
                      </p>
                      <p className="text-xs text-gray-400 mb-2">
                        Earn points to reach Level{" "}
                        {userReward
                          ? getCurrentLevel(userReward.total_points || 0) + 1
                          : 2}
                      </p>
                      <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-green-500 h-full rounded-full transition-all duration-1000 ease-out"
                          style={{ width: `${getProgressPercent()}%` }}
                        ></div>
                      </div>
                      <div className="flex justify-between text-[10px] mt-1 text-gray-400 font-medium">
                        <span>
                          {userReward?.total_points || 0}/{nextLevelTarget} pts
                        </span>
                        <span className="text-green-600">Keep going!</span>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
