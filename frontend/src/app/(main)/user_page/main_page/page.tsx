"use client";

import React, { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  Settings,
  Users,
  Heart,
  MapPin,
  Home,
  Bot,
  User,
  Loader2,
  Trash2,
  Navigation,
  ArrowRight,
  Route,
} from "lucide-react";
import { useRouter } from "next/navigation";

import { Jost, Abhaya_Libre, Knewave } from "next/font/google";
import {
  api,
  UserProfile,
  SavedDestination,
  PlaceDetails,
  Position,
} from "@/lib/api";

interface EnrichedSavedDestination extends SavedDestination {
  details?: PlaceDetails;
}

// --- Font Setup ---
const jost = Jost({ subsets: ["latin"], weight: ["400", "500", "700"] });
const abhaya_libre = Abhaya_Libre({
  subsets: ["latin"],
  weight: ["400", "700", "800"],
});
const knewave = Knewave({ subsets: ["latin"], weight: ["400"] });

export default function ProfilePage() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [savedPlaces, setSavedPlaces] = useState<EnrichedSavedDestination[]>(
    []
  );
  const [loading, setLoading] = useState(true);
  const [userLocation, setUserLocation] = useState<Position | null>(null);
  const [unsavingId, setUnsavingId] = useState<string | null>(null);
  const router = useRouter();
  const handleViewProfileButton = () => {
    router.push("/user_page/profile_page");
  };
  const [activeTab, setActiveTab] = useState<"profile" | "saved" | "settings">(
    "profile"
  );

  const handleViewDetails = (placeId: string) => {
    router.push(`/place_detail_page?place_id=${placeId}`);
  };

  const handleUnsave = async (placeId: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Ngăn chặn click vào card (tránh mở trang detail)
    if (unsavingId) return; // Đang xử lý cái khác thì bỏ qua

    const confirm = window.confirm(
      "Are you sure you want to unsave this place?"
    );
    if (!confirm) return;

    try {
      setUnsavingId(placeId);
      await api.unsaveDestination(placeId);

      // Cập nhật UI ngay lập tức: Xóa item khỏi danh sách
      setSavedPlaces((prev) =>
        prev.filter((item) => item.destination_id !== placeId)
      );
    } catch (error) {
      console.error("Failed to unsave:", error);
      alert("Failed to unsave. Please try again.");
    } finally {
      setUnsavingId(null);
    }
  };

  const calculateDistance = (
    lat1: number,
    lon1: number,
    lat2: number,
    lon2: number
  ) => {
    const R = 6371;
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLon = ((lon2 - lon1) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos((lat1 * Math.PI) / 180) *
        Math.cos((lat2 * Math.PI) / 180) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return (R * c).toFixed(1);
  };

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          });
        },
        (error) => {
          console.error("Error getting location:", error);
        }
      );
    }
  }, []);
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        const userData = await api.getUserProfile();
        setUser(userData);

        const places = await api.getSavedDestinations();

        if (places) {
          setSavedPlaces(places as any);
        }
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
      }
    };

    fetchData();
  }, []);

  useEffect(() => {
    const fetchSavedPlaces = async () => {
      try {
        const data = await api.getSavedDestinations();
        const enrichedData = await Promise.all(
          data.map(async (item) => {
            try {
              const details = await api.getPlaceDetails(item.destination_id);
              return { ...item, details };
            } catch (error) {
              console.error("Error fetching place details:", error);
              return item;
            }
          })
        );
        setSavedPlaces(enrichedData);
      } catch (error) {
        console.error("Error fetching saved places:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchSavedPlaces();
  }, [activeTab]);

  return (
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      <div className="w-full max-w-md bg-[#F5F7F5] h-screen shadow-2xl relative flex flex-col overflow-hidden">
        <div className="bg-[#E3F1E4] h-[180px] rounded-b-[50px] relative w-full shrink-0 overflow-hidden">
          {user?.cover_url && (
            <Image
              src={user.cover_url}
              alt="Cover Photo"
              fill
              className="object-cover"
              priority
            />
          )}

          <Link href="/user_page/friend_page">
            <button className="absolute top-6 left-4 z-10 bg-white/90 backdrop-blur-sm px-4 py-1.5 rounded-full shadow-sm flex items-center gap-2 hover:bg-white transition-colors">
              <Users size={18} className="text-green-600" />
              <span
                className={`${jost.className} text-green-700 text-xs font-bold`}
              >
                View Friends
              </span>
            </button>
          </Link>

          <Link href="/user_page/setting_page">
            <button className="absolute top-6 right-4 z-10 bg-white/90 backdrop-blur-sm px-4 py-1.5 rounded-full shadow-sm flex items-center gap-2 hover:bg-white transition-colors">
              <Settings size={18} className="text-green-600" />
              <span
                className={`${jost.className} text-green-700 text-xs font-bold`}
              >
                Settings
              </span>
            </button>
          </Link>
        </div>

        <div className="relative flex flex-col items-center -mt-[70px] px-4 shrink-0">
          <div className="p-1.5 bg-white rounded-full shadow-md z-10">
            <div className="relative w-32 h-32 rounded-full overflow-hidden border-4 border-white bg-gray-200">
              <Image
                src={user?.avt_url || "/images/default-avatar.png"}
                alt="Avatar"
                fill
                className="object-cover"
              />
            </div>
          </div>
          <h1
            className={`${knewave.className} text-[#53B552] text-2xl mt-3 tracking-wide`}
          >
            {user?.username || "User Name"}
          </h1>
          <button
            onClick={handleViewProfileButton}
            className={`${jost.className} mt-2 bg-[#53B552] text-white px-8 py-1.5 rounded-full text-sm font-bold shadow-md hover:bg-green-600 transition-all`}
          >
            View Profile →
          </button>
        </div>

        <div className="mt-6 w-full px-8 shrink-0">
          <div className="border-b-2 border-gray-200 relative flex justify-center">
            <div className="absolute -bottom-3.5 bg-[#F5F7F5] px-4">
              <Heart className="text-gray-400 fill-gray-400" size={28} />
            </div>
          </div>
        </div>

        <main className="flex-1 overflow-y-auto p-4 pt-8 pb-24">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-40 text-gray-400 gap-2">
              <Loader2 className="animate-spin" />
              <span className="text-sm">Loading saved places...</span>
            </div>
          ) : savedPlaces.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center opacity-60 mt-10">
              <Heart size={48} className="text-gray-300 mb-3" />
              <p className={`${abhaya_libre.className} text-gray-500 text-lg`}>
                No saved places yet.
              </p>
              <p className="text-sm text-gray-400 max-w-[200px]">
                Explore the map and save your favorite green spots!
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              {savedPlaces.map((place) => {
                const photoData = place.details?.photos?.[0];
                let imageUrl = "/images/placeholder-place.png";

                if (photoData?.photo_url) {
                  if (photoData.photo_url.startsWith("http")) {
                    imageUrl = photoData.photo_url;
                  } else {
                    imageUrl = `https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference=${photoData.photo_url}&key=${process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY}`;
                  }
                }

                // 2. XỬ LÝ KHOẢNG CÁCH
                let distanceText = "";
                if (userLocation && place.details?.geometry?.location) {
                  const dist = calculateDistance(
                    userLocation.lat,
                    userLocation.lng,
                    place.details.geometry.location.lat,
                    place.details.geometry.location.lng
                  );
                  distanceText = `${dist} km`;
                }

                return (
                  <div
                    key={place.destination_id}
                    className="bg-white rounded-xl p-2 shadow-sm hover:shadow-md transition-shadow flex flex-col h-full"
                  >
                    <div className="relative w-full h-32 rounded-lg overflow-hidden mb-2 bg-gray-100">
                      <Image
                        src={imageUrl}
                        alt={place.details?.name || "Place"}
                        fill
                        className="object-cover"
                      />
                      {distanceText && (
                        <div className="absolute bottom-1 right-1 bg-black/60 backdrop-blur-xs text-white text-[10px] px-2 py-0.5 rounded-full flex items-center gap-1">
                          <Navigation size={10} className="text-[#53B552]" />
                          {distanceText}
                        </div>
                      )}
                      <button
                        onClick={(e) => handleUnsave(place.destination_id, e)}
                        className="absolute top-2 right-2 bg-white/80 p-1.5 rounded-full text-red-500 hover:bg-white transition-colors z-10"
                        title="Unsave"
                      >
                        {unsavingId === place.destination_id ? (
                          <Loader2 size={14} className="animate-spin" />
                        ) : (
                          <Trash2 size={14} />
                        )}
                      </button>
                    </div>

                    <div className="p-3 flex flex-col flex-1">
                      <h3 className="font-bold text-gray-800 text-sm line-clamp-2 mb-1 flex-1">
                        {place.details ? place.details.name : "Loading..."}
                      </h3>

                      <p className="text-xs text-gray-500 line-clamp-1 mb-3">
                        {place.details?.formatted_address || "Unknown address"}
                      </p>

                      {/* Nút View Details */}
                      <button
                        onClick={() => handleViewDetails(place.destination_id)}
                        className="w-full mt-auto bg-[#E3F1E4] text-[#53B552] text-xs font-bold py-1.5 rounded-lg hover:bg-green-100 transition-colors flex items-center justify-center gap-1"
                      >
                        View Details <ArrowRight size={12} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </main>

        {/* --- FOOTER --- */}
        <footer className="bg-white shadow-[0_-5px_15px_rgba(0,0,0,0.05)] sticky bottom-0 w-full z-20">
          <div className="h-1 bg-linear-to-r from-transparent via-green-200 to-transparent"></div>
          <div className="flex justify-around items-center py-3">
            <Link
              href="/homepage"
              className="flex flex-col items-center text-gray-400 hover:text-green-600 transition-colors"
            >
              <Home size={24} strokeWidth={2} />
              <span className={`${jost.className} text-xs font-medium mt-1`}>
                Home
              </span>
            </Link>
            <Link
              href="/track_page/leaderboard"
              className="flex flex-col items-center text-gray-400 hover:text-green-600"
            >
              {" "}
              <Route size={24} strokeWidth={2} />
              <span className={`${jost.className} text-xs font-medium mt-1`}>
                Track
              </span>
            </Link>
            <Link
              href="/planning_page/showing_plan_page"
              className="flex flex-col items-center text-gray-400 hover:text-green-600 transition-colors"
            >
              <MapPin size={24} strokeWidth={2} />
              <span className={`${jost.className} text-xs font-medium mt-1`}>
                Planning
              </span>
            </Link>
            <Link
              href="ecobot_page"
              className="flex flex-col items-center text-gray-400 hover:text-green-600 transition-colors"
            >
              <Bot size={24} strokeWidth={2} />
              <span className={`${jost.className} text-xs font-medium mt-1`}>
                Ecobot
              </span>
            </Link>
            <Link
              href="main_page"
              className="flex flex-col items-center text-[#53B552]"
            >
              <User size={24} strokeWidth={2.5} />
              <span className={`${jost.className} text-xs font-bold mt-1`}>
                User
              </span>
            </Link>
          </div>
        </footer>
      </div>
    </div>
  );
}
