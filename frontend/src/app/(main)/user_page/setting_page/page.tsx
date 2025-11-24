"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  ChevronRight,
  Home,
  MapPin,
  Bot,
  User,
  Globe,
  LogOut,
  Trash2,
  Loader2,
} from "lucide-react";
import { Jost, Abhaya_Libre } from "next/font/google";
import { api, UserProfile } from "@/lib/api";

// --- Font Setup ---
const jost = Jost({ subsets: ["latin"], weight: ["400", "500", "700"] });
const abhaya_libre = Abhaya_Libre({
  subsets: ["latin"],
  weight: ["400", "700", "800"],
});

export default function SettingPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserProfile | null>(null);

  // --- States ---
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [loading, setLoading] = useState(false);

  // Lấy thông tin User
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const data = await api.getUserProfile();
        setUser(data);
      } catch (e) {
        console.error(e);
      }
    };
    fetchUser();
  }, []);

  // --- XỬ LÝ LOGIC ---

  // 1. Log Out
  const handleLogout = async () => {
    await api.logout();
    router.push("/login");
  };

  // 2. Delete Account
  const handleDeleteAccount = async () => {
    setLoading(true);
    try {
      await api.deleteUser();
      if (typeof window !== "undefined") {
        localStorage.clear();
      }
      router.replace("/signup");
    } catch (error) {
      alert("Failed to delete account.");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      <div className="w-full max-w-md bg-[#F5F7F5] h-screen shadow-2xl relative flex flex-col overflow-hidden">
        {/* --- HEADER --- */}
        <div className="bg-[#E3F1E4] pt-12 pb-20 px-6 rounded-b-[40px] relative z-0">
          <div className="flex items-center gap-4">
            <Link href="/user_page/main_page">
              <ArrowLeft
                className="text-gray-600 cursor-pointer hover:text-green-600 transition-colors"
                size={28}
              />
            </Link>
            <h1
              className={`${jost.className} text-2xl font-bold text-gray-600`}
            >
              Settings
            </h1>
          </div>
        </div>

        {/* --- AVATAR & NAME --- */}
        <div className="relative z-10 -mt-14 flex flex-col items-center mb-6">
          <div className="p-1.5 bg-white rounded-full shadow-md">
            <div className="relative w-28 h-28 rounded-full overflow-hidden border-4 border-white shadow-inner bg-gray-100">
              <Image
                src={user?.avt_url || "/images/default-avatar.png"}
                alt="User Avatar"
                fill
                className="object-cover"
              />
            </div>
          </div>
          <h2
            className={`${abhaya_libre.className} mt-3 text-2xl font-bold text-[#53B552]`}
          >
            {user?.username || "User Name"}
          </h2>
        </div>

        {/* --- MENU LIST --- */}
        <main className="flex-1 overflow-y-auto px-6 space-y-4 pb-24">
          {/* 1. Language (Fixed to English) */}
          <div className="bg-white rounded-xl p-5 shadow-sm flex justify-between items-center">
            <div className="flex items-center gap-3">
              <Globe className="text-gray-400" size={22} />
              <span
                className={`${abhaya_libre.className} text-lg font-bold text-gray-600`}
              >
                Language
              </span>
            </div>
            <span
              className={`${jost.className} text-gray-400 font-medium text-sm`}
            >
              English
            </span>
          </div>

          {/* 2. Log Out */}
          <div
            onClick={handleLogout}
            className="bg-white rounded-xl p-5 shadow-sm flex justify-between items-center cursor-pointer hover:bg-gray-50 transition-colors group"
          >
            <div className="flex items-center gap-3">
              <LogOut
                className="text-gray-400 group-hover:text-gray-600 transition-colors"
                size={22}
              />
              <span
                className={`${abhaya_libre.className} text-lg font-bold text-gray-600`}
              >
                Log out
              </span>
            </div>
            <ChevronRight className="text-gray-400" size={20} />
          </div>

          {/* 3. Delete Account */}
          <div
            onClick={() => setShowDeleteModal(true)}
            className="bg-white rounded-xl p-5 shadow-sm flex justify-between items-center cursor-pointer hover:bg-red-50 transition-colors group"
          >
            <div className="flex items-center gap-3">
              <Trash2
                className="text-gray-400 group-hover:text-red-500 transition-colors"
                size={22}
              />
              <span
                className={`${abhaya_libre.className} text-lg font-bold text-gray-600 group-hover:text-red-500 transition-colors`}
              >
                Delete account
              </span>
            </div>
            <ChevronRight
              className="text-gray-400 group-hover:text-red-500"
              size={20}
            />
          </div>
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
              href="/planning_page/showing_plan_page"
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
              <Link href="/user_page/main_page">
                <User size={24} strokeWidth={2.5} />
                <span className={`${jost.className} text-xs font-bold mt-1`}>
                  User
                </span>
              </Link>
            </div>
          </div>
        </footer>

        {/* --- MODAL: DELETE ACCOUNT --- */}
        {showDeleteModal && (
          <div className="absolute inset-0 bg-black/50 z-50 flex items-center justify-center px-4">
            <div className="bg-white rounded-2xl p-6 w-full max-w-sm shadow-2xl animate-in fade-in zoom-in duration-200 text-center">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <User className="text-red-500" size={32} />
              </div>
              <h3
                className={`${jost.className} text-xl font-bold text-gray-800 mb-2`}
              >
                Delete Account?
              </h3>
              <p className="text-gray-500 mb-6 text-sm">
                Are you sure? This action cannot be undone and all your data
                will be lost permanently.
              </p>

              <div className="flex gap-3">
                <button
                  onClick={() => setShowDeleteModal(false)}
                  className="flex-1 py-2.5 rounded-lg bg-gray-100 text-gray-600 font-bold hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteAccount}
                  disabled={loading}
                  className="flex-1 py-2.5 rounded-lg bg-red-500 text-white font-bold hover:bg-red-600 transition-colors disabled:opacity-70 flex justify-center items-center gap-2"
                >
                  {loading && <Loader2 className="animate-spin" size={18} />}
                  {loading ? "Deleting..." : "Delete"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
