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
  Wind,
  Sun,
  CloudRain,
  Cloud,
  CloudLightning,
  Snowflake,
  Trophy,
  Loader2,
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
} from "@/lib/api";

export const gotu = Gotu({ subsets: ["latin"], weight: ["400"], display: 'swap'});
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
  const parts = dateStr.split("/");
  if (parts.length === 3) {
    return new Date(
      parseInt(parts[2]),
      parseInt(parts[1]) - 1,
      parseInt(parts[0])
    );
  }
  return new Date(dateStr); // Fallback
};

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [heart, setHeart] = useState(false);
  const [bookMark, setBookMark] = useState(false);
  const router = useRouter();
  const [requestCount, setRequestCount] = useState(0);

  // State for Plan
  const [upcomingPlan, setUpcomingPlan] = useState<TravelPlan | null>(null);
  const [loadingPlan, setLoadingPlan] = useState(true);
  // State for Weather & AQI
  const [weather, setWeather] = useState<CurrentWeatherResponse | null>(null);
  const [airQuality, setAirQuality] = useState<AirQualityResponse | null>(null);
  const [loadingWeather, setLoadingWeather] = useState(true);
  const [locationError, setLocationError] = useState(false);

  // 1. Lấy số lượng lời mời kết bạn
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

  // 2. Lấy kế hoạch sắp tới
  useEffect(() => {
    const fetchUpcomingPlan = async () => {
      try {
        const plans = await api.getPlans();

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        // Lọc các plan có ngày >= hôm nay
        // Lưu ý: api.ts của bạn đang dùng field 'date' string kiểu "20/11/2025"
        const futurePlans = plans.filter((p) => {
          const planDate = parseDate(p.date);
          return planDate >= today;
        });

        // Sắp xếp: Plan nào gần nhất lên đầu
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

  // page.tsx

  useEffect(() => {
    if (!navigator.geolocation) {
      console.error("Geolocation not supported");
      setLoadingWeather(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        try {
          // BƯỚC 1: Đổi tọa độ sang Place ID (Gọi hàm reverseGeocode bạn vừa hỏi)
          const geoData = await api.reverseGeocode({
            lat: latitude,
            lng: longitude,
          });

          // Lấy place_id đầu tiên (chính xác nhất)
          const placeId = geoData.results[0]?.place_id;

          if (placeId) {
            // BƯỚC 2: Dùng Place ID để lấy thời tiết (Backend phải hỗ trợ tham số place_id nhé)
            // Lưu ý: api.getCurrentWeather phải được cập nhật để nhận (undefined, undefined, placeId) như mình hướng dẫn ở câu trước
            const [weatherRes, airRes] = await Promise.all([
              api.getCurrentWeather(3, 3),
              api.getAirQuality(latitude, longitude), // Air Quality thường vẫn cần lat/lng
            ]);

            setWeather(weatherRes);
            setAirQuality(airRes);
          } else {
            console.error("No place_id found for this location");
          }
        } catch (error) {
          console.error("Error fetching weather via place_id:", error);
        } finally {
          setLoadingWeather(false);
        }
      },
      (error) => {
        console.error("Location permission denied or error:", error);
        setLocationError(true);
        setLoadingWeather(false);
      }
    );
  }, []);

  const getWeatherIcon = (type?: string) => {
    if (!type) return <Sun size={32} className="text-orange-400" />;
    const t = type.toUpperCase();
    if (t.includes("RAIN") || t.includes("DRIZZLE"))
      return <CloudRain size={32} className="text-blue-500" />;
    if (t.includes("CLOUD"))
      return <Cloud size={32} className="text-gray-400" />;
    if (t.includes("THUNDER"))
      return <CloudLightning size={32} className="text-purple-500" />;
    if (t.includes("SNOW"))
      return <Snowflake size={32} className="text-blue-300" />;
    return <Sun size={32} className="text-orange-400" />;
  };

  const getAQIColor = (aqi: number) => {
    if (aqi <= 50) return "text-green-700";
    if (aqi <= 100) return "text-yellow-600";
    if (aqi <= 150) return "text-orange-600";
    return "text-red-600";
  };

  const getAQIText = (aqi: number) => {
    if (aqi <= 50) return "(Good)";
    if (aqi <= 100) return "(Moderate)";
    if (aqi <= 150) return "(Unhealthy)";
    return "(Hazardous)";
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
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
    router.push("/map_page?nearby=true");
  };

  const handleTagClick = (tag: string) => {
    router.push(`/map_page?q=${encodeURIComponent(tag)}`);
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
                onClick={() => handleTagClick(i)} // Thêm sự kiện click
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
                <Heart
                  className={`${
                    heart
                      ? "fill-green-600 stroke-green-600 scale-110"
                      : "stroke-green-600"
                  } cursor-pointer transition-all size-6 text-green-600 strokeWidth={1.5} hover:fill-green-600 `}
                  onClick={() => setHeart(!heart)}
                />
                <Bookmark
                  onClick={() => setBookMark(!bookMark)}
                  className={`${
                    bookMark
                      ? "fill-green-600 stroke-green-600 scale-110"
                      : "stroke-green-600"
                  } cursor-pointer transition-all size-6 text-green-600 strokeWidth={1.5} hover:fill-green-600 `}
                />
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

            {/* Weather CARD */}
            <div className="bg-[#E3F1E4] p-4 rounded-2xl flex flex-col justify-between h-full shadow-sm border border-green-100">
              {loadingWeather ? (
                <div className="flex flex-col items-center justify-center h-full gap-2 text-green-600/50">
                  <Loader2 className="animate-spin" size={24} />
                  <span className="text-xs font-bold">Checking weather...</span>
                </div>
              ) : locationError ? (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <span className="text-xs text-gray-500">
                    Location required for weather
                  </span>
                  <button
                    onClick={() => window.location.reload()}
                    className="mt-2 text-[10px] bg-green-500 text-white px-2 py-1 rounded"
                  >
                    Retry
                  </button>
                </div>
              ) : (
                <>
                  <div className="flex items-start justify-between">
                    <div>
                      {/* Nhiệt độ thật */}
                      <span className="text-3xl font-bold text-gray-800">
                        {Math.round(weather?.temperature.temperature || 0)}°C
                      </span>
                      {/* AQI thật */}
                      <div className="flex items-center gap-1 mt-1">
                        <Wind size={14} className="text-green-600" />
                        <span
                          className={`text-[10px] font-bold ${
                            airQuality
                              ? getAQIColor(airQuality.aqi_data.aqi)
                              : "text-gray-500"
                          }`}
                        >
                          AQI: {airQuality?.aqi_data.aqi || "--"}{" "}
                          {airQuality
                            ? getAQIText(airQuality.aqi_data.aqi)
                            : ""}
                        </span>
                      </div>
                    </div>
                    {/* Icon thời tiết thật */}
                    {getWeatherIcon(weather?.weather_condition.type)}
                  </div>
                </>
              )}
            </div>
          </section>

          {/* SECTION 3: Explore Activities */}
          <section className="bg-[#E9F5EB] rounded-2xl p-6 shadow-sm mt-0">
            <div className="bg-white p-5 rounded-3xl shadow-sm border border-gray-100">
              <div className="flex justify-between items-center mb-3">
                <h3 className="font-bold text-lg text-gray-800">
                  Your Eco Impact
                </h3>
                <span className="text-green-600 font-bold bg-green-50 px-3 py-1 rounded-full text-xs">
                  Level 2
                </span>
              </div>

              {/* Challenge Card */}
              <div className="flex gap-4 items-center">
                {/* Icon huy hiệu/cúp */}
                <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center text-yellow-600 shrink-0">
                  <Trophy size={24} />
                </div>

                <div className="flex-1">
                  <p className="text-sm font-bold text-gray-700">
                    Green Traveler Challenge
                  </p>
                  <p className="text-xs text-gray-400 mb-2">
                    Visit 3 parks this week to earn badge
                  </p>

                  {/* Progress Bar */}
                  <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
                    <div className="bg-[#53B552] h-full w-2/3 rounded-full"></div>
                  </div>
                  <div className="flex justify-between text-[10px] mt-1 text-gray-400">
                    <span>2/3 visited</span>
                    <span>+100 pts</span>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </main>

        {/* --- FOOTER --- */}
        <footer
          className={`bg-white shadow-[0_-2px_6px_rgba(0,0,0,0.05)] shrink-0 z-10`}
        >
          <div className="h-0.5 bg-linear-to-r from-transparent via-green-200 to-transparent opacity-70"></div>
          <div className="flex justify-around items-center px-2 pt-2 pb-3">
            <Link
              href="/homepage"
              className="flex flex-col items-center justify-center w-1/4 text-green-600"
            >
              <Home className="size-6" strokeWidth={2.0} />
              <span className="text-[10px] font-bold mt-1">Home</span>
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
