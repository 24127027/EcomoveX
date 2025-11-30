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
  Home,
  MapPin,
  Bot,
  User,
  Search,
  Heart,
  Map,
  Calendar,
  ArrowRight,
  Trophy,
  Loader2,
  Route,
  Star,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  api,
  TravelPlan,
  UserRewardResponse,
  GreenPlaceRecommendation,
} from "@/lib/api";

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

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState("");
  const router = useRouter();
  const [requestCount, setRequestCount] = useState(0);

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

  // State Saved Locations
  const [savedPlaceIds, setSavedPlaceIds] = useState<Set<string>>(new Set());
  const [togglingId, setTogglingId] = useState<string | null>(null);

  // --- HÀM LẤY VỊ TRÍ TỐI ƯU (PROMISE WRAPPER) ---
  const getUserLocation = async (): Promise<{ lat: number; lng: number }> => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error("Geolocation not supported"));
        return;
      }

      // Cấu hình 1: Ưu tiên chính xác cao, thử nhanh trong 5s
      const highAccuracyOptions = {
        enableHighAccuracy: true,
        timeout: 5000,
        maximumAge: 60000, // Chấp nhận vị trí cũ trong 1 phút (cache)
      };

      navigator.geolocation.getCurrentPosition(
        (pos) =>
          resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        (err) => {
          console.warn(
            "High accuracy GPS failed, trying low accuracy...",
            err.message
          );

          // Cấu hình 2: Nếu thất bại, thử lấy vị trí qua Wifi/Cell (kém chính xác hơn nhưng nhanh)
          const lowAccuracyOptions = {
            enableHighAccuracy: false,
            timeout: 10000, // Cho phép đợi lâu hơn chút
            maximumAge: Infinity, // Lấy bất kỳ vị trí cache nào có thể
          };

          navigator.geolocation.getCurrentPosition(
            (pos) =>
              resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
            (err2) => reject(err2), // Nếu vẫn lỗi thì mới reject
            lowAccuracyOptions
          );
        },
        highAccuracyOptions
      );
    });
  };

  // --- FETCH DATA ---
  useEffect(() => {
    let isMounted = true;

    const fetchAllData = async () => {
      setLoadingGreenPlaces(true);

      // 1. Xác định toạ độ (Real GPS -> Default)
      let lat = DEFAULT_LAT;
      let lng = DEFAULT_LNG;

      try {
        const pos = await getUserLocation();
        lat = pos.lat;
        lng = pos.lng;
        console.log("📍 Using REAL User Location:", lat, lng);
      } catch (error) {
        console.warn("⚠️ Cannot get location, using DEFAULT:", error);
      }

      // 2. Gọi API lấy địa điểm xanh
      try {
        const recommendations = await api.getNearbyGreenPlaces(lat, lng, 10, 5);

        if (isMounted && recommendations && recommendations.length > 0) {
          // Lấy ảnh & Rating song song
          const placesWithPhotos = await Promise.all(
            recommendations.map(async (place) => {
              try {
                if (!place.photo_url) {
                  const details = await api.getPlaceDetails(place.place_id);
                  return {
                    ...place,
                    photo_url:
                      details.photos?.[0]?.photo_url ||
                      "/images/tao-dan-park.png",
                    rating: details.rating || place.rating,
                  };
                }
                return place;
              } catch {
                return { ...place, photo_url: "/images/tao-dan-park.png" };
              }
            })
          );
          setGreenPlaces(placesWithPhotos);

          // Check saved status
          try {
            const savedList = await api.getSavedDestinations();
            setSavedPlaceIds(new Set(savedList.map((i) => i.destination_id)));
          } catch (e) {
            console.error(e);
          }
        } else {
          if (isMounted) setGreenPlaces([]);
        }
      } catch (error) {
        console.error("API Error:", error);
        if (isMounted) setGreenPlaces([]);
      } finally {
        if (isMounted) setLoadingGreenPlaces(false);
      }
    };

    fetchAllData();

    return () => {
      isMounted = false;
    };
  }, []);

  // ... (Giữ nguyên các useEffect fetchRequests, fetchUpcomingPlan, fetchRewardData)
  useEffect(() => {
    const f = async () => {
      try {
        const l = await api.getPendingRequests();
        setRequestCount(l.length);
      } catch {}
    };
    f();
  }, []);
  useEffect(() => {
    const f = async () => {
      try {
        const p = await api.getPlans();
        const t = new Date();
        t.setHours(0, 0, 0, 0);
        const fp = p.filter((i) => {
          const d = parseDate(i.date);
          return d >= t;
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

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim())
      router.push(`/map_page?q=${encodeURIComponent(searchQuery.trim())}`);
    else router.push("/map_page");
  };

  const handleSearchNearby = async () => {
    try {
      // Dùng lại hàm getUserLocation xịn sò ở trên
      const pos = await getUserLocation();
      router.push(`/map_page?q=eco-friendly&lat=${pos.lat}&lng=${pos.lng}`);
    } catch {
      alert("Please enable location services to search nearby.");
      router.push("/map_page?q=eco-friendly");
    }
  };

  const handleTagClick = async (tag: string) => {
    try {
      const pos = await getUserLocation();
      router.push(
        `/map_page?q=${encodeURIComponent(tag)}&lat=${pos.lat}&lng=${pos.lng}`
      );
    } catch {
      router.push(`/map_page?q=${encodeURIComponent(tag)}`);
    }
  };

  return (
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      <div className="w-full max-w-md bg-gray-50 h-screen flex flex-col overflow-hidden shadow-2xl relative">
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
                className={`${abhaya_libre.className} w-full rounded-full py-2 pl-10 pr-12 text-sm bg-white text-black focus:outline-none focus:ring-2 focus:ring-green-300 placeholder:text-green-700 placeholder:font-semibold`}
                placeholder="Search for an eco-friendly place"
                value={searchQuery}
                onChange={handleChange}
              />
              <button
                type="button"
                onClick={() => router.push("/map_page")}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-gray-100 transition-colors"
              >
                <Map className="size-5 text-green-600" />
              </button>
            </div>
            <div
              className={`${knewave.className} text-white font-bold text-2xl select-none`}
            >
              EcomoveX
            </div>
          </form>
          <div className="flex justify-center gap-3 mt-4 flex-wrap">
            {["Café", "Restaurant", "Park", "Hotel", "Shopping"].map((i) => (
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

        <footer
          className={`bg-white shadow-[0_-5px_15px_rgba(0,0,0,0.05)] sticky bottom-0 w-full z-20`}
        >
          <div className="h-1 bg-linear-to-r from-transparent via-green-200 to-transparent"></div>
          <div className="flex justify-around items-center py-3">
            <Link
              href="/homepage"
              className="flex flex-col items-center justify-center w-1/4 text-green-600"
            >
              <Home className="size-6" strokeWidth={2.0} />
              <span className="text-[10px] font-bold mt-1">Home</span>
            </Link>
            <Link
              href="/track_page/leaderboard"
              className="flex flex-col items-center justify-center w-1/4 text-gray-400 hover:text-green-600 transition-colors"
            >
              <Route size={24} strokeWidth={1.5} />
              <span
                className={`${jost.className} text-[10px] font-medium mt-1`}
              >
                Track
              </span>
            </Link>
            <Link
              href="/planning_page/showing_plan_page"
              className="flex flex-col items-center justify-center w-1/4 text-gray-400 hover:text-green-600 transition-colors"
            >
              <MapPin className="size-6" strokeWidth={1.5} />
              <span className="text-[10px] font-medium mt-1">Planning</span>
            </Link>
            <Link
              href="#"
              className="flex flex-col items-center justify-center w-1/4 text-gray-400 hover:text-green-600 transition-colors"
            >
              <Bot className="size-6" strokeWidth={1.5} />
              <span className="text-[10px] font-medium mt-1">Ecobot</span>
            </Link>
            <Link
              href="user_page/main_page"
              className="flex flex-col items-center justify-center w-1/4 text-gray-400 hover:text-green-600 transition-colors relative"
            >
              <div className="relative">
                <User className="size-6" strokeWidth={1.5} />
                {requestCount > 0 && (
                  <span className="absolute -top-1.5 -right-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white shadow-sm animate-in zoom-in">
                    {requestCount > 9 ? "9+" : requestCount}
                  </span>
                )}
              </div>
              <span className="text-[10px] font-medium mt-1">User</span>
            </Link>
          </div>
        </footer>
      </div>
    </div>
  );
}
