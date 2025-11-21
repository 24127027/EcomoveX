"use client";

import React, { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  Home,
  MapPin,
  Bot,
  User,
  ChevronRight,
  Sun,
  Loader2,
  Map,
  Plus,
} from "lucide-react";
import { Jost, Abhaya_Libre, Knewave } from "next/font/google";
import { api, TravelPlan, PlanActivity } from "@/lib/api";

// --- Font Setup ---
const knewave = Knewave({ subsets: ["latin"], weight: ["400"] });
const jost = Jost({ subsets: ["latin"], weight: ["400", "500", "600", "700"] });
const abhaya_libre = Abhaya_Libre({
  subsets: ["latin"],
  weight: ["400", "500", "600", "800"],
});

// Helper: Chuyển chuỗi "DD/MM/YYYY" thành Date Object để so sánh
const parseDate = (dateStr: string) => {
  if (!dateStr) return new Date(0);
  const [day, month, year] = dateStr.split("/").map(Number);
  return new Date(year, month - 1, day);
};

export default function PlanningPage() {
  // --- State quản lý dữ liệu và giao diện ---
  const [activeTab, setActiveTab] = useState<"Current" | "Previous">("Current");

  const [currentPlan, setCurrentPlan] = useState<TravelPlan | null>(null);
  const [previousPlans, setPreviousPlans] = useState<TravelPlan[]>([]);

  const [expandedPlanId, setExpandedPlanId] = useState<number | null>(null); // Cho Accordion bên Previous
  const [loading, setLoading] = useState(true);

  // --- Logic Fetch & Sort ---
  useEffect(() => {
    const initData = async () => {
      try {
        setLoading(true);

        // 1. Gọi API lấy toàn bộ danh sách
        const allPlans = await api.getPlans();

        if (!allPlans || allPlans.length === 0) {
          setCurrentPlan(null);
          setPreviousPlans([]);
          return;
        }

        // 2. Chuẩn bị ngày hiện tại (xóa giờ phút giây để so sánh chính xác)
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        // 3. Phân loại
        // - Future: Ngày >= Hôm nay
        // - Past: Ngày < Hôm nay
        const futurePlans = allPlans.filter((p) => parseDate(p.date) >= today);
        const pastPlans = allPlans.filter((p) => parseDate(p.date) < today);

        // 4. Xác định Current Plan
        if (futurePlans.length > 0) {
          // Lấy chuyến đi có ngày NHỎ NHẤT trong tương lai (gần hôm nay nhất)
          futurePlans.sort(
            (a, b) => parseDate(a.date).getTime() - parseDate(b.date).getTime()
          );

          setCurrentPlan(futurePlans[0]);
          setPreviousPlans(pastPlans);
        } else {
          setCurrentPlan(null);
          setPreviousPlans(pastPlans);
        }

        pastPlans.sort(
          (a, b) => parseDate(b.date).getTime() - parseDate(a.date).getTime()
        );
        setPreviousPlans(pastPlans);
      } catch (error) {
        console.error("Failed to fetch plans:", error);
      } finally {
        setLoading(false);
      }
    };

    initData();
  }, []);

  // Helper: Toggle Accordion cho Previous Plan
  const handleTogglePlan = (id: number) => {
    setExpandedPlanId(expandedPlanId === id ? null : id);
  };

  // Helper: Lọc activity theo buổi cho Current Plan
  const getActivitiesByTime = (activities: PlanActivity[], slot: string) => {
    if (!activities) return [];
    return activities.filter((a) => a.time_slot === slot);
  };

  return (
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      <div className="w-full max-w-md bg-[#F5F7F5] h-screen shadow-2xl relative flex flex-col overflow-hidden">
        {/* --- HEADER --- */}
        <div className="px-6 pt-10 pb-4 bg-[#F5F7F5] shrink-0">
          <h1
            className={`${knewave.className} text-[#53B552] text-3xl tracking-wide uppercase`}
          >
            Planning
          </h1>
        </div>

        {/* --- TABS --- */}
        <div className="px-4 mb-4 flex shrink-0">
          <button
            onClick={() => setActiveTab("Current")}
            className={`${
              jost.className
            } flex-1 py-3 rounded-l-lg text-sm font-bold transition-colors ${
              activeTab === "Current"
                ? "bg-[#53B552] text-white"
                : "bg-[#E3F1E4] text-[#53B552]"
            }`}
          >
            Current Plan
          </button>
          <button
            onClick={() => setActiveTab("Previous")}
            className={`${
              jost.className
            } flex-1 py-3 rounded-r-lg text-sm font-bold transition-colors ${
              activeTab === "Previous"
                ? "bg-[#53B552] text-white"
                : "bg-[#E3F1E4] text-[#53B552]"
            }`}
          >
            Previous Plan
          </button>
        </div>

        {/* --- MAIN CONTENT --- */}
        <main className="flex-1 overflow-y-auto px-4 pb-24 scroll-smooth">
          {loading && (
            <div className="h-full flex flex-col items-center justify-center text-gray-400 gap-2">
              <Loader2 className="animate-spin" size={32} />
              <span className={`${jost.className}`}>Checking schedule...</span>
            </div>
          )}

          {/* ================= VIEW: CURRENT PLAN ================= */}
          {!loading &&
            activeTab === "Current" &&
            (!currentPlan ? (
              // --- EMPTY STATE ---
              <div className="h-full flex flex-col items-center justify-center text-center opacity-80 -mt-10 animate-in fade-in duration-500">
                <div className="bg-white p-6 rounded-full shadow-sm mb-6">
                  <Map
                    size={64}
                    className="text-[#53B552] opacity-80"
                    strokeWidth={1.5}
                  />
                </div>
                <h3
                  className={`${jost.className} text-2xl font-bold text-gray-700 mb-2`}
                >
                  No plans yet
                </h3>
                <p
                  className={`${abhaya_libre.className} text-gray-500 text-lg max-w-[250px] leading-tight`}
                >
                  You haven't created any upcoming travel plans.
                </p>
                <Link href="/planning_page/create_plan" className="w-full mt-8">
                  <button
                    className={`${jost.className} w-full border-2 border-[#53B552] text-[#53B552] bg-white hover:bg-[#53B552] hover:text-white transition-all text-lg font-bold py-3 rounded-full shadow-sm flex items-center justify-center gap-2`}
                  >
                    <Plus size={20} /> Create New Plan
                  </button>
                </Link>
              </div>
            ) : (
              // --- ACTIVE STATE ---
              <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="bg-white rounded-full px-4 py-3 flex justify-between items-center shadow-sm mb-2 cursor-pointer hover:bg-gray-50 transition-colors">
                  <div className="flex items-center gap-2 text-gray-800">
                    <MapPin className="text-red-500 fill-red-500" size={18} />
                    <span className={`${jost.className} font-bold text-sm`}>
                      {currentPlan.destination}
                    </span>
                  </div>
                  <ChevronRight size={20} className="text-gray-400" />
                </div>

                <p className="text-right text-[10px] text-gray-400 mb-4 italic">
                  Date: {currentPlan.date}
                </p>

                {/* Day Header */}
                <div className="flex justify-between items-end mb-3 px-1">
                  <span
                    className={`${abhaya_libre.className} text-xl italic text-gray-700`}
                  >
                    Day 1
                  </span>
                  <div className="flex items-center gap-1 text-gray-600">
                    <span className={`${abhaya_libre.className} italic`}>
                      Morning
                    </span>
                    <Sun
                      size={18}
                      className="text-yellow-500 fill-yellow-500"
                    />
                  </div>
                </div>
                <div className="space-y-3 mb-6">
                  {getActivitiesByTime(currentPlan.activities, "Morning").map(
                    (item) => (
                      <ActivityCard key={item.id} item={item} />
                    )
                  )}
                </div>

                {/* Afternoon Header */}
                <div className="flex justify-between items-end mb-3 px-1">
                  <span
                    className={`${abhaya_libre.className} text-xl italic text-gray-700`}
                  >
                    Day 1
                  </span>
                  <div className="flex items-center gap-1 text-gray-600">
                    <span className={`${abhaya_libre.className} italic`}>
                      Afternoon
                    </span>
                    <div className="w-4 h-4 rounded-full bg-yellow-400 overflow-hidden relative border border-gray-200">
                      <div className="absolute left-1/2 w-4 h-4 bg-gray-600"></div>
                    </div>
                  </div>
                </div>
                <div className="space-y-3 mb-8">
                  {getActivitiesByTime(currentPlan.activities, "Afternoon").map(
                    (item) => (
                      <ActivityCard key={item.id} item={item} />
                    )
                  )}
                </div>

                {/* --- BUTTONS ACTION --- */}
                <div className="flex flex-col gap-3 mb-8">
                  {/* Nút Edit Places hiện tại */}
                  <button
                    className={`${jost.className} w-full border-2 border-[#53B552] text-[#53B552] bg-[#F5F7F5] hover:bg-green-50 transition-all text-lg font-bold py-3 rounded-full shadow-sm`}
                  >
                    Edit Places
                  </button>

                  {/* Nút Create New Plan MỚI */}
                  <Link href="/planning_page/create_plan">
                    <button
                      className={`${jost.className} w-full bg-[#53B552] text-white hover:bg-green-600 transition-all text-lg font-bold py-3 rounded-full shadow-lg flex justify-center items-center gap-2`}
                    >
                      <Plus size={20} /> Create New Plan
                    </button>
                  </Link>
                </div>
              </div>
            ))}

          {/* ================= VIEW: PREVIOUS PLAN ================= */}
          {!loading && activeTab === "Previous" && (
            <div className="space-y-3 pt-2 animate-in fade-in duration-300">
              {previousPlans.length === 0 ? (
                <div className="text-center text-gray-400 mt-10 italic">
                  No history available.
                </div>
              ) : (
                previousPlans.map((plan) => (
                  <div
                    key={plan.id}
                    className="bg-white rounded-2xl shadow-sm overflow-hidden transition-all duration-300"
                  >
                    <div
                      onClick={() => handleTogglePlan(plan.id)}
                      className="p-4 flex items-center justify-between cursor-pointer hover:bg-gray-50 select-none"
                    >
                      <div className="flex items-center gap-3">
                        <MapPin
                          className="text-[#D9534F]"
                          size={20}
                          fill="#D9534F"
                        />
                        <div>
                          <h4
                            className={`${jost.className} font-bold text-gray-800 text-base`}
                          >
                            {plan.destination}
                          </h4>
                          <p
                            className={`${jost.className} text-gray-500 text-xs mt-0.5`}
                          >
                            Time: {plan.date}
                          </p>
                        </div>
                      </div>
                      <ChevronRight
                        size={20}
                        className={`text-gray-400 transition-transform duration-300 ${
                          expandedPlanId === plan.id ? "rotate-90" : ""
                        }`}
                      />
                    </div>

                    {expandedPlanId === plan.id && (
                      <div className="px-4 pb-4 pt-0 border-t border-gray-100 animate-in slide-in-from-top-2">
                        <div className="mt-3 mb-2">
                          <span
                            className={`${abhaya_libre.className} italic text-sm text-gray-500`}
                          >
                            Trip Details
                          </span>
                        </div>

                        {plan.activities.length > 0 ? (
                          <div className="space-y-2">
                            {plan.activities.map((act) => (
                              <ActivityCard
                                key={act.id}
                                item={act}
                                isSmall={true}
                              />
                            ))}
                          </div>
                        ) : (
                          <p className="text-center text-xs text-gray-300 italic py-2">
                            No activity data recorded.
                          </p>
                        )}

                        <div className="mt-3 flex justify-end">
                          <button
                            className={`${jost.className} text-xs text-[#53B552] font-bold hover:underline`}
                          >
                            View Full Report
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}
        </main>

        {/* --- FOOTER --- */}
        <footer className="bg-white shadow-[0_-5px_15px_rgba(0,0,0,0.05)] sticky bottom-0 w-full z-20 shrink-0">
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
            <div className="flex flex-col items-center text-[#53B552]">
              <MapPin size={24} strokeWidth={2.5} />
              <span className={`${jost.className} text-xs font-bold mt-1`}>
                Planning
              </span>
            </div>
            <Link
              href="#"
              className="flex flex-col items-center text-gray-400 hover:text-green-600 transition-colors"
            >
              <Bot size={24} strokeWidth={2} />
              <span className={`${jost.className} text-xs font-medium mt-1`}>
                Ecobot
              </span>
            </Link>
            <Link
              href="/user_page/profile_page"
              className="flex flex-col items-center text-gray-400 hover:text-green-600 transition-colors"
            >
              <User size={24} strokeWidth={2} />
              <span className={`${jost.className} text-xs font-medium mt-1`}>
                User
              </span>
            </Link>
          </div>
        </footer>
      </div>
    </div>
  );
}

// Component ActivityCard tái sử dụng
function ActivityCard({
  item,
  isSmall = false,
}: {
  item: PlanActivity;
  isSmall?: boolean;
}) {
  return (
    <div
      className={`${
        isSmall ? "bg-gray-50 border border-gray-100" : "bg-white shadow-sm"
      } rounded-2xl p-3 flex gap-3 items-center`}
    >
      <div className="flex-1 min-w-0">
        <h4
          className={`${jost.className} font-semibold text-gray-900 text-sm truncate`}
        >
          {item.title}
        </h4>
        <p
          className={`${jost.className} text-gray-500 text-[10px] sm:text-xs mt-1 line-clamp-1 leading-relaxed`}
        >
          {item.address}
        </p>
      </div>
      <div
        className={`${
          isSmall ? "w-14 h-10" : "w-20 h-14"
        } shrink-0 relative rounded-lg overflow-hidden bg-gray-100`}
      >
        <Image
          src={item.image_url}
          alt={item.title}
          fill
          className="object-cover"
        />
      </div>
    </div>
  );
}
