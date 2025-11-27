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
  Calendar,
  Clock,
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
  const [activeTab, setActiveTab] = useState<
    "Incoming" | "Future" | "Previous"
  >("Incoming");

  const [incomingPlan, setIncomingPlan] = useState<TravelPlan | null>(null);
  const [previousPlans, setPreviousPlans] = useState<TravelPlan[]>([]);
  const [futurePlans, setFuturePlans] = useState<TravelPlan[]>([]);

  const [expandedPlanId, setExpandedPlanId] = useState<number | null>(null); // Cho Accordion bên Previous
  const [loading, setLoading] = useState(true);

  // --- Logic Fetch & Sort ---
  useEffect(() => {
    const initData = async () => {
      try {
        setLoading(true);

        const allPlans = await api.getPlans();

        if (!allPlans || allPlans.length === 0) {
          setIncomingPlan(null);
          setFuturePlans([]);
          setPreviousPlans([]);
          return;
        }

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const allFuture = allPlans.filter((p) => parseDate(p.date) >= today);
        const allPast = allPlans.filter((p) => parseDate(p.date) < today);

        if (allFuture.length > 0) {
          allFuture.sort(
            (a, b) => parseDate(a.date).getTime() - parseDate(b.date).getTime()
          );

          setIncomingPlan(allFuture[0]);
          setFuturePlans(allFuture.slice(1));
        } else {
          setIncomingPlan(null);
          setFuturePlans([]);
        }

        allPast.sort(
          (a, b) => parseDate(b.date).getTime() - parseDate(a.date).getTime()
        );
        setPreviousPlans(allPast);
      } catch (error) {
        console.error("Failed to fetch plans:", error);
      } finally {
        setLoading(false);
      }
    };

    initData();
  }, []);

  const handleTogglePlan = (id: number) => {
    setExpandedPlanId(expandedPlanId === id ? null : id);
  };

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

        {/* --- TABS (3 SECTIONS) --- */}
        <div className="px-4 mb-4 flex shrink-0 gap-1">
          {(["Incoming", "Future", "Previous"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`${
                jost.className
              } flex-1 py-2.5 rounded-lg text-xs font-bold transition-all shadow-sm ${
                activeTab === tab
                  ? "bg-[#53B552] text-white shadow-md transform scale-105"
                  : "bg-white text-gray-400 border border-transparent hover:border-green-200"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* --- MAIN CONTENT --- */}
        <main className="flex-1 overflow-y-auto px-4 pb-24 scroll-smooth">
          {loading && (
            <div className="h-full flex flex-col items-center justify-center text-gray-400 gap-2">
              <Loader2 className="animate-spin" size={32} />
              <span className={`${jost.className}`}>Loading schedules...</span>
            </div>
          )}

          {!loading && (
            <>
              {/* ================= VIEW: INCOMING PLAN (Detail View) ================= */}
              {activeTab === "Incoming" &&
                (incomingPlan ? (
                  <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 pb-4">
                    <div className="bg-white rounded-full px-4 py-3 flex justify-between items-center shadow-sm mb-2 cursor-pointer hover:bg-gray-50 transition-colors border border-green-100">
                      <div className="flex items-center gap-2 text-gray-800">
                        <MapPin
                          className="text-[#53B552]"
                          size={18}
                          fill="#53B552"
                          fillOpacity={0.2}
                        />
                        <span
                          className={`${jost.className} font-bold text-base text-[#53B552]`}
                        >
                          {incomingPlan.destination}
                        </span>
                      </div>
                      <Link href={`/planning_page/${incomingPlan.id}/edit`}>
                        <ChevronRight size={20} className="text-gray-400" />
                      </Link>
                    </div>

                    <div className="flex justify-end items-center gap-1 mb-6 pr-2">
                      <Calendar size={12} className="text-gray-400" />
                      <p className="text-[12px] text-gray-500 italic font-medium">
                        Start Date:{" "}
                        {new Date(incomingPlan.date).toLocaleDateString()}
                      </p>
                    </div>

                    {/* Morning Section */}
                    <div className="flex justify-between items-end mb-3 px-1">
                      <span
                        className={`${abhaya_libre.className} text-xl italic text-gray-700`}
                      >
                        Schedule
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
                      {getActivitiesByTime(incomingPlan.activities, "Morning")
                        .length > 0 ? (
                        getActivitiesByTime(
                          incomingPlan.activities,
                          "Morning"
                        ).map((item) => (
                          <ActivityCard key={item.id} item={item} />
                        ))
                      ) : (
                        <EmptySlotMessage />
                      )}
                    </div>

                    {/* Afternoon Section */}
                    <div className="flex justify-between items-end mb-3 px-1">
                      <div className="w-full h-px bg-gray-200 mr-4 self-center"></div>
                      <div className="flex items-center gap-1 text-gray-600 shrink-0">
                        <span className={`${abhaya_libre.className} italic`}>
                          Afternoon
                        </span>
                        <div className="w-4 h-4 rounded-full bg-orange-400 overflow-hidden relative border border-gray-200">
                          {/* Simple Icon for afternoon */}
                        </div>
                      </div>
                    </div>

                    <div className="space-y-3 mb-8">
                      {getActivitiesByTime(incomingPlan.activities, "Afternoon")
                        .length > 0 ? (
                        getActivitiesByTime(
                          incomingPlan.activities,
                          "Afternoon"
                        ).map((item) => (
                          <ActivityCard key={item.id} item={item} />
                        ))
                      ) : (
                        <EmptySlotMessage />
                      )}
                    </div>

                    {/* Action Buttons */}
                    <div className="flex flex-col gap-3 mt-6">
                      <button
                        className={`${jost.className} w-full border-2 border-[#53B552] text-[#53B552] bg-white hover:bg-green-50 transition-all text-lg font-bold py-3 rounded-full shadow-sm`}
                      >
                        Edit Schedule
                      </button>
                    </div>
                  </div>
                ) : (
                  <EmptyState message="No incoming trips planned." />
                ))}

              {/* ================= VIEW: FUTURE PLAN (List View) ================= */}
              {activeTab === "Future" &&
                (futurePlans.length > 0 ? (
                  <div className="space-y-3 pt-2 animate-in fade-in duration-300">
                    <p
                      className={`${jost.className} text-sm text-gray-500 mb-2 px-1`}
                    >
                      Upcoming trips after your next one:
                    </p>
                    {futurePlans.map((plan) => (
                      <PlanSummaryCard
                        key={plan.id}
                        plan={plan}
                        expandedId={expandedPlanId}
                        onToggle={handleTogglePlan}
                        type="future"
                      />
                    ))}
                  </div>
                ) : (
                  <EmptyState
                    message="No other future trips planned."
                    showCreateButton={true}
                  />
                ))}

              {/* ================= VIEW: PREVIOUS PLAN (List View) ================= */}
              {activeTab === "Previous" &&
                (previousPlans.length > 0 ? (
                  <div className="space-y-3 pt-2 animate-in fade-in duration-300">
                    {previousPlans.map((plan) => (
                      <PlanSummaryCard
                        key={plan.id}
                        plan={plan}
                        expandedId={expandedPlanId}
                        onToggle={handleTogglePlan}
                        type="past"
                      />
                    ))}
                  </div>
                ) : (
                  <EmptyState message="No travel history found." />
                ))}
            </>
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

// --- SUB-COMPONENTS ---

function EmptyState({
  message,
  showCreateButton = false,
}: {
  message: string;
  showCreateButton?: boolean;
}) {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center opacity-80 -mt-10">
      <div className="bg-white p-6 rounded-full shadow-sm mb-6">
        <Map
          size={64}
          className="text-[#53B552] opacity-50"
          strokeWidth={1.5}
        />
      </div>
      <h3 className={`${jost.className} text-xl font-bold text-gray-700 mb-2`}>
        Empty List
      </h3>
      <p
        className={`${abhaya_libre.className} text-gray-500 text-lg max-w-[250px] leading-tight`}
      >
        {message}
      </p>
      {showCreateButton && (
        <Link href="/planning_page/create_plan" className="mt-6 w-full px-8">
          <button
            className={`${jost.className} w-full bg-[#53B552] text-white hover:bg-green-600 transition-all text-sm font-bold py-3 rounded-full shadow-lg flex justify-center items-center gap-2`}
          >
            <Plus size={18} /> Create New Plan
          </button>
        </Link>
      )}
    </div>
  );
}

function EmptySlotMessage() {
  return (
    <div className="border border-dashed border-gray-300 rounded-xl p-4 text-center">
      <p className={`${jost.className} text-gray-400 text-xs italic`}>
        No activities planned for this time.
      </p>
    </div>
  );
}

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
        isSmall
          ? "bg-gray-50 border border-gray-100"
          : "bg-white shadow-sm border border-gray-50"
      } rounded-2xl p-3 flex gap-3 items-center transition-transform active:scale-95`}
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
        } shrink-0 relative rounded-lg overflow-hidden bg-gray-200`}
      >
        {item.image_url ? (
          <Image
            src={item.image_url}
            alt={item.title}
            fill
            className="object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gray-200 text-gray-400 text-xs">
            No Img
          </div>
        )}
      </div>
    </div>
  );
}

function PlanSummaryCard({
  plan,
  expandedId,
  onToggle,
  type,
}: {
  plan: TravelPlan;
  expandedId: number | null;
  onToggle: (id: number) => void;
  type: "future" | "past";
}) {
  const isExpanded = expandedId === plan.id;
  const dateObj = new Date(plan.date);

  return (
    <div className="bg-white rounded-2xl shadow-sm overflow-hidden transition-all duration-300 border border-gray-100">
      <div
        onClick={() => onToggle(plan.id)}
        className="p-4 flex items-center justify-between cursor-pointer hover:bg-gray-50 select-none"
      >
        <div className="flex items-center gap-3">
          <div
            className={`p-2 rounded-full ${
              type === "future" ? "bg-blue-50" : "bg-red-50"
            }`}
          >
            <Calendar
              className={type === "future" ? "text-blue-500" : "text-red-500"}
              size={18}
            />
          </div>
          <div>
            <h4
              className={`${jost.className} font-bold text-gray-800 text-base`}
            >
              {plan.destination}
            </h4>
            <div className="flex items-center gap-1 mt-0.5">
              <Clock size={10} className="text-gray-400" />
              <p className={`${jost.className} text-gray-500 text-xs`}>
                {dateObj.toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>
        <ChevronRight
          size={20}
          className={`text-gray-400 transition-transform duration-300 ${
            isExpanded ? "rotate-90" : ""
          }`}
        />
      </div>

      {isExpanded && (
        <div className="px-4 pb-4 pt-0 border-t border-gray-100 animate-in slide-in-from-top-2">
          <div className="mt-3 mb-2 flex justify-between items-center">
            <span
              className={`${abhaya_libre.className} italic text-sm text-gray-500`}
            >
              Preview Activities
            </span>
          </div>

          {plan.activities && plan.activities.length > 0 ? (
            <div className="space-y-2">
              {plan.activities.slice(0, 3).map((act) => (
                <ActivityCard key={act.id} item={act} isSmall={true} />
              ))}
              {plan.activities.length > 3 && (
                <p className="text-center text-xs text-gray-400 py-1">
                  +{plan.activities.length - 3} more activities
                </p>
              )}
            </div>
          ) : (
            <p className="text-center text-xs text-gray-300 italic py-2">
              No activity data recorded.
            </p>
          )}

          <div className="mt-3 flex justify-end">
            <Link href={`/planning_page/${plan.id}/details`}>
              <button
                className={`${jost.className} text-xs text-[#53B552] font-bold hover:underline`}
              >
                View Full Plan
              </button>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
