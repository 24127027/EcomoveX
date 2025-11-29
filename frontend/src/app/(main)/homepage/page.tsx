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
  Bookmark,
  Map,
  Calendar,
  ArrowRight,

  Trophy,
  Loader2,
  Route,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  api,
  TravelPlan,
  CurrentWeatherResponse,
  AirQualityResponse,
  UserRewardResponse,
  Mission,
} from "@/lib/api";

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

export default function HomePage() {
  const TAO_DAN_PLACE_ID = "ChIJq46ErLopCzER10OzGact5ew";

  const [searchQuery, setSearchQuery] = useState("");
  const [heart, setHeart] = useState(false);
  const [loadingHeart, setLoadingHeart] = useState(false);
  const router = useRouter();
  const [requestCount, setRequestCount] = useState(0);

  // State for Plan
  const [upcomingPlan, setUpcomingPlan] = useState<TravelPlan | null>(null);
  const [loadingPlan, setLoadingPlan] = useState(true);

  // State for Rewards
  const [userReward, setUserReward] = useState<UserRewardResponse | null>(null);
  const [nextLevelTarget, setNextLevelTarget] = useState(100);
  const [loadingRewards, setLoadingRewards] = useState(true);

  useEffect(() => {
    const checkSavedStatus = async () => {
      try {
        const savedList = await api.getSavedDestinations();
        const isSaved = savedList.some(
          (item) => item.destination_id === TAO_DAN_PLACE_ID
        );
        setHeart(isSaved);
      } catch (error) {
        console.error("Failed to check saved status", error);
      }
    };
    checkSavedStatus();
  }, []);

  useEffect(() => {
    const fetchRequests = async () => {
      try {
        const list = await api.getPendingRequests();
        setRequestCount(list.length);
      } catch (error) {
        console.error("Failed to fetch requests", error);
      }
    };
    fetchRequests();
  }, []);

  useEffect(() => {
    const fetchUpcomingPlan = async () => {
      try {
        const plans = await api.getPlans();

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const futurePlans = plans.filter((p) => {
          const planDate = parseDate(p.date);
          return planDate >= today;
        });

        futurePlans.sort(
          (a, b) => parseDate(a.date).getTime() - parseDate(b.date).getTime()
        );

        if (futurePlans.length > 0) {
          setUpcomingPlan(futurePlans[0]);
        }
      } catch (error) {
        console.error("Failed to load plans", error);
      } finally {
        setLoadingPlan(false);
      }
    };

    fetchUpcomingPlan();
  }, []);

  useEffect(() => {
    const fetchRewardData = async () => {
      try {
        const data = await api.getUserRewards();
        setUserReward(data);
        const points = data.total_points || 0;
        let target = 100;
        if (points >= 600) target = 1000;
        else if (points >= 300) target = 600;
        else if (points >= 100) target = 300;
        setNextLevelTarget(target);
      } catch (error) {
        console.error("Failed to fetch user rewards", error);
      } finally {
        setLoadingRewards(false);
      }
    };
    fetchRewardData();
  }, []);

  const getCurrentLevel = (points: number) => {
    if (points >= 600) return 3;
    if (points >= 300) return 2;
    if (points >= 100) return 1;
    return 1;
  };

  const getProgressPercent = () => {
    if (!userReward) return 0;
    const points = userReward.total_points || 0;
    let prevTarget = 0;
    if (nextLevelTarget === 300) prevTarget = 100;
    else if (nextLevelTarget === 600) prevTarget = 300;
    else if (nextLevelTarget === 1000) prevTarget = 600;
    const progress =
      ((points - prevTarget) / (nextLevelTarget - prevTarget)) * 100;
    return Math.min(Math.max(progress, 0), 100);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  const handleHeartClick = async () => {
    if (loadingHeart) return; // Prevent multiple clicks
    setLoadingHeart(true);
    const previousState = heart;
    setHeart(!heart);
    try {
      if (!previousState) {
        try {
          await api.getPlaceDetails(TAO_DAN_PLACE_ID);
        } catch (error) {
          console.error("Error fetching place details:", error);
        }
        await api.saveDestination(TAO_DAN_PLACE_ID);
        console.log("Destination saved");
      } else {
        await api.unsaveDestination(TAO_DAN_PLACE_ID);
        console.log("Destination unsaved");
      }
    } catch (error) {
      console.error("Error toggling save: ", error);
      setHeart(previousState); // Revert state on error
    } finally {
      setLoadingHeart(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/map_page?q=${encodeURIComponent(searchQuery.trim())}`);
    } else {
      router.push("/map_page");
    }
  };

  const handleSearchNearby = () => {
    const fallbackToMap = () => {
      console.log("Redirecting to map without location");
      router.push("/map_page?q=eco-friendly");
    };
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        router.push(
          `/map_page?q=eco-friendly&lat=${latitude}&lng=${longitude}`
        );
      },
      (error) => {
        console.warn("Geolocation error:", error);
        fallbackToMap();
      },
      { timeout: 10000, maximumAge: Infinity, enableHighAccuracy: false }
    );
  };

  const handleTagClick = (tag: string) => {
    if (!navigator.geolocation) {
      router.push(`/map_page?q=${encodeURIComponent(tag)}`);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        router.push(
          `/map_page?q=${encodeURIComponent(
            tag
          )}&lat=${latitude}&lng=${longitude}`
        );
      },
      (error) => {
        console.error("Error getting location:", error);
        router.push(`/map_page?q=${encodeURIComponent(tag)}`);
      },
      { timeout: 15000, maximumAge: Infinity, enableHighAccuracy: false }
    );
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
                type="button" // Đổi thành button để tránh submit form sai
                onClick={() => router.push("/map_page")}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-gray-100 transition-colors"
                title="View on Map"
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
          {/* SECTION 1: Most Visited */}
          <section
            className={`bg-[#F9FFF9] rounded-xl shadow-sm p-4 border border-green-100`}
          >
            <h2
              className={`${jost.className} font-bold text-green-600 uppercase mb-3 text-xl tracking-wide`}
            >
              Most Visited Green Places
            </h2>
            <div className="relative w-full h-48 rounded-lg overflow-hidden bg-gray-200">
              {/* Fallback nếu ảnh lỗi */}
              <Image
                src="/images/tao-dan-park.png"
                alt="Tao Dan Park"
                layout="fill"
                objectFit="cover"
                className="hover:scale-105 transition-transform duration-500"
              />
            </div>
            <div className="flex gap-2 justify-between items-center mt-3">
              <div className="flex gap-3">
                <button
                  onClick={handleHeartClick}
                  disabled={loadingHeart}
                  className="focus:outline-none"
                >
                  <Heart
                    className={`${
                      heart
                        ? "fill-green-600 stroke-green-600 scale-110"
                        : "stroke-green-600"
                    } cursor-pointer transition-all size-6 text-green-600 strokeWidth={1.5} hover:fill-green-600 `}
                    onClick={() => setHeart(!heart)}
                  />
                </button>
              </div>
              <div className="text-right">
                <p
                  className={`${abhaya_libre.className} font-semibold text-gray-800`}
                >
                  Tao Dan Park
                </p>
                <p
                  className={`${abhaya_libre.className} text-sm text-gray-500`}
                >
                  2km
                </p>
              </div>
            </div>
          </section>

          {/* SECTION 2: Upcoming Plan + Nearby */}
          <section className={`grid grid-cols-2 gap-4`}>
            {/* UPCOMING PLAN CARD (Đã sửa lỗi và điền nội dung) */}
            <div className="bg-linear-to-b from-green-500 to-green-600 rounded-xl p-4 text-white flex flex-col justify-between shadow-lg min-h-[150px] relative overflow-hidden group">
              {/* Decoration Circle */}
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

            {/* Search Nearby */}
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
                ECO-FRIENDLY <br />
                SPOTS
              </h2>
              <button
                onClick={handleSearchNearby}
                className="bg-[#53B552] text-white px-6 py-2 rounded-full text-sm font-bold shadow-md hover:bg-green-600 hover:shadow-lg transition-all active:scale-95 flex items-center gap-2"
              >
                Search Now
              </button>
            </div>
          </section>

          {/* SECTION 3: Your Eco Impact */}
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

        {/* --- FOOTER --- */}
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
