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
} from "lucide-react";
import { useRouter } from "next/navigation";

import { Jost, Abhaya_Libre, Knewave } from "next/font/google";
import { api, UserProfile, SavedDestination } from "@/lib/api";

// --- Font Setup ---
const jost = Jost({ subsets: ["latin"], weight: ["400", "500", "700"] });
const abhaya_libre = Abhaya_Libre({
  subsets: ["latin"],
  weight: ["400", "700", "800"],
});
const knewave = Knewave({ subsets: ["latin"], weight: ["400"] });

export default function ProfilePage() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [savedPlaces, setSavedPlaces] = useState<SavedDestination[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const handleViewProfileButton = () => {
    router.push("/user_page/profile_page");
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        const userData = await api.getUserProfile();
        setUser(userData);

        const places = await api.getSavedDestinations();

        if (places) {
          setSavedPlaces(places);
        }
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      <div className="w-full max-w-md bg-[#F5F7F5] h-screen shadow-2xl relative flex flex-col overflow-hidden">
        {/* --- HEADER --- */}
        <div className="bg-[#E3F1E4] h-[180px] rounded-b-[50px] relative w-full shrink-0">
          <button className="absolute top-6 left-4 bg-white px-4 py-1.5 rounded-full shadow-sm flex items-center gap-2 hover:bg-green-50 transition-colors">
            <Users size={18} className="text-green-600" />
            <span
              className={`${jost.className} text-green-700 text-xs font-bold`}
            >
              View Friends
            </span>
          </button>

          <Link href="/user_page/setting_page">
            <button className="absolute top-6 right-4 bg-white px-4 py-1.5 rounded-full shadow-sm flex items-center gap-2 hover:bg-green-50 transition-colors">
              <Settings size={18} className="text-green-600" />
              <span
                className={`${jost.className} text-green-700 text-xs font-bold`}
              >
                Settings
              </span>
            </button>
          </Link>
        </div>

        {/* --- INFO --- */}
        <div className="relative flex flex-col items-center -mt-[70px] px-4 shrink-0">
          <div className="p-1.5 bg-white rounded-full shadow-md z-10">
            <div className="relative w-32 h-32 rounded-full overflow-hidden border-4 border-white bg-gray-200">
              <Image
                src={user?.avatar_url || "/images/default-avatar.png"}
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

        {/* --- MAIN CONTENT --- */}
        <main className="flex-1 overflow-y-auto p-4 pt-8 pb-24">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-40 text-gray-400 gap-2">
              <Loader2 className="animate-spin" />
              <span className="text-sm">Loading saved places...</span>
            </div>
          ) : savedPlaces.length === 0 ? (
            // --- CASE 1: CHƯA CÓ DỮ LIỆU (Mảng rỗng) ---
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
              {savedPlaces.map((place) => (
                <div
                  key={place.id}
                  className="bg-white rounded-xl p-2 shadow-sm hover:shadow-md transition-shadow flex flex-col h-full"
                >
                  {/* Image: Backend trả về image_url thì dùng, không thì dùng ảnh mặc định */}
                  <div className="relative w-full h-32 rounded-lg overflow-hidden mb-2 bg-gray-100">
                    <Image
                      src={place.image_url || "/images/placeholder-place.png"}
                      alt={place.name || "Place"}
                      fill
                      className="object-cover"
                    />
                  </div>

                  {/* Info */}
                  <div className="flex flex-col flex-1 justify-between px-1">
                    <div>
                      <h3
                        className={`${abhaya_libre.className} font-bold text-gray-800 text-sm leading-tight line-clamp-2`}
                      >
                        {place.name || `Saved Place #${place.destination_id}`}
                      </h3>
                    </div>
                  </div>
                </div>
              ))}
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
              href="#"
              className="flex flex-col items-center text-gray-400 hover:text-green-600 transition-colors"
            >
              <MapPin size={24} strokeWidth={2} />
              <span className={`${jost.className} text-xs font-medium mt-1`}>
                Planning
              </span>
            </Link>
            <Link
              href="#"
              className="flex flex-col items-center text-gray-400 hover:text-green-600 transition-colors"
            >
              <Bot size={24} strokeWidth={2} />
              <span className={`${jost.className} text-xs font-medium mt-1`}>
                Ecobot
              </span>
            </Link>
            <div className="flex flex-col items-center text-[#53B552]">
              <User size={24} strokeWidth={2.5} />
              <span className={`${jost.className} text-xs font-bold mt-1`}>
                User
              </span>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
