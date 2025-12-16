"use client";

import React, { useEffect, useState, Suspense } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  ChevronRight,
  Sun,
  Loader2,
  Map,
  MapPin,
  Plus,
  Calendar,
  Clock,
  Route,
  Sunset,
  Moon,
  Trash2,
} from "lucide-react";
import { Jost, Abhaya_Libre, Knewave } from "next/font/google";
import { api, TravelPlan, PlanActivity } from "@/lib/api";
import { MobileNavMenu } from "@/components/MobileNavMenu";
import { PRIMARY_NAV_LINKS } from "@/constants/navLinks";

// --- Font Setup ---
const knewave = Knewave({ subsets: ["latin"], weight: ["400"] });
const jost = Jost({ subsets: ["latin"], weight: ["400", "500", "600", "700"] });
const abhaya_libre = Abhaya_Libre({
  subsets: ["latin"],
  weight: ["400", "500", "600", "800"],
});

const parseDate = (dateStr: string) => {
  if (!dateStr) return new Date(0);
  if (dateStr.includes("-")) {
    return new Date(dateStr);
  }
  if (dateStr.includes("/")) {
    const [day, month, year] = dateStr.split("/").map(Number);
    return new Date(year, month - 1, day);
  }
  return new Date(dateStr);
};

// --- CONTENT COMPONENT ---
function PlanningContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [activeTab, setActiveTab] = useState<
    "Incoming" | "Future" | "Previous"
  >("Incoming");

  // Plan list state
  const [incomingPlan, setIncomingPlan] = useState<TravelPlan | null>(null);
  const [futurePlans, setFuturePlans] = useState<TravelPlan[]>([]);
  const [previousPlans, setPreviousPlans] = useState<TravelPlan[]>([]);

  const [expandedPlanId, setExpandedPlanId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentUserId, setCurrentUserId] = useState<number | null>(null);

  const getPlanDays = (startDate: string, endDate?: string) => {
    const start = parseDate(startDate);
    const end = endDate ? parseDate(endDate) : parseDate(startDate);
    const days = [];

    for (let dt = new Date(start); dt <= end; dt.setDate(dt.getDate() + 1)) {
      days.push(new Date(dt));
    }
    return days;
  };

  const refreshData = async () => {
    try {
      setLoading(true);
      console.log("🔄 Fetching plans from API...");
      const allPlans = await api.getPlans();

      if (!allPlans || allPlans.length === 0) {
        setIncomingPlan(null);
        setFuturePlans([]);
        setPreviousPlans([]);
        return;
      }

      const validPlans = allPlans.filter(
        (p) => p.activities && p.activities.length >= 2
      );

      if (validPlans.length === 0) {
        setIncomingPlan(null);
        setFuturePlans([]);
        setPreviousPlans([]);
        return;
      }
      const today = new Date();
      today.setHours(0, 0, 0, 0);

      const allActiveAndFuture = validPlans.filter((p) => {
        const checkDate = p.end_date
          ? parseDate(p.end_date)
          : parseDate(p.date);
        return checkDate >= today;
      });

      const allPast = validPlans.filter((p) => {
        const checkDate = p.end_date
          ? parseDate(p.end_date)
          : parseDate(p.date);
        return checkDate < today;
      });

      if (allActiveAndFuture.length > 0) {
        allActiveAndFuture.sort(
          (a, b) => parseDate(a.date).getTime() - parseDate(b.date).getTime()
        );

        setIncomingPlan(allActiveAndFuture[0]);
        setFuturePlans(allActiveAndFuture.slice(1));
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

  useEffect(() => {
    const loadCurrentUser = async () => {
      try {
        const storedUser = localStorage.getItem("user");
        if (storedUser) {
          const user = JSON.parse(storedUser);
          setCurrentUserId(user.id);
        } else {
          const profile = await api.getUserProfile();
          setCurrentUserId(profile.id);
          localStorage.setItem("user", JSON.stringify(profile));
        }
      } catch (error) {
        console.error("Failed to load current user:", error);
      }
    };

    loadCurrentUser();
    refreshData();
  }, []);

  useEffect(() => {
    const refreshParam = searchParams.get("refresh");
    if (refreshParam) {
      console.log("🔄 Detected refresh param, reloading data...");
      setTimeout(() => {
        refreshData();
        router.replace("/planning_page/showing_plan_page", { scroll: false });
      }, 100);
    }
  }, [searchParams, router]);

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        console.log("Page visible, refreshing data...");
        refreshData();
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, []);

  const handleTogglePlan = (id: number) => {
    setExpandedPlanId(expandedPlanId === id ? null : id);
  };

  const handleDeletePlan = async (id: number, planUserId?: number) => {
    if (currentUserId && planUserId && planUserId !== currentUserId) {
      alert("Only the plan owner can delete this plan.");
      return;
    }

    if (!confirm("Are you sure you want to delete this plan?")) return;

    try {
      await api.deletePlan(id);
      refreshData();
    } catch (error) {
      console.error("Error deleting plan:", error);
      alert("Failed to delete plan.");
    }
  };

  const getActivitiesByDayAndTime = (
    activities: PlanActivity[],
    targetDate: Date,
    slot: string
  ) => {
    if (!activities) return [];
    const targetDateStr = targetDate.toISOString().split("T")[0];
    return activities
      .filter((a) => {
        if (!a.date && !a.day) return false;
        let activityDateStr: string | null = null;
        if (a.date) {
          activityDateStr = a.date.split("T")[0];
        } else if (a.day) {
          return false;
        }
        return activityDateStr === targetDateStr && a.time_slot === slot;
      })
      .sort((a, b) => (a.order_in_day || 0) - (b.order_in_day || 0));
  };

  return (
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      <div className="w-full max-w-md bg-[#F5F7F5] h-screen shadow-2xl relative flex flex-col overflow-hidden">
        <MobileNavMenu items={PRIMARY_NAV_LINKS} activeKey="planning" />
        {/* --- HEADER --- */}
        <div className="px-6 pt-10 pb-4 bg-[#F5F7F5] shrink-0">
          <h1
            className={`${knewave.className} text-[#53B552] text-3xl tracking-wide uppercase`}
          >
            Planning
          </h1>
        </div>

        {/* --- TABS --- */}
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
        <main className="flex-1 overflow-y-auto px-4 pb-40 scroll-smooth">
          {loading && (
            <div className="h-full flex flex-col items-center justify-center text-gray-400 gap-2">
              <Loader2 className="animate-spin" size={32} />
              <span className={`${jost.className}`}>Loading schedules...</span>
            </div>
          )}

          {!loading && (
            <>
              {activeTab === "Incoming" &&
                (incomingPlan ? (
                  <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 pb-4">
                    {/* Header Card Incoming */}
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
                      <div className="flex items-center gap-2">
                        {/* Delete button for the incoming plan */}
                        {currentUserId &&
                          incomingPlan.user_id === currentUserId && (
                            <button
                              onClick={(e) => {
                                e.preventDefault();
                                handleDeletePlan(
                                  incomingPlan.id,
                                  incomingPlan.user_id
                                );
                              }}
                              className="p-2 bg-red-50 text-red-400 rounded-full hover:bg-red-100 hover:text-red-500 transition-colors"
                              title="Delete plan (owner only)"
                            >
                              <Trash2 size={16} />
                            </button>
                          )}
                        <Link
                          href={`/planning_page/preview_page?id=${incomingPlan.id}`}
                        >
                          <button
                            className="px-3 py-1.5 text-xs font-semibold text-green-600 hover:bg-green-50 rounded-full transition-colors border border-green-200"
                            title="View Plan"
                          >
                            View
                          </button>
                        </Link>
                      </div>
                    </div>

                    <div className="flex justify-end items-center gap-1 mb-6 pr-2">
                      <Calendar size={12} className="text-gray-400" />
                      <p className="text-[12px] text-gray-500 italic font-medium">
                        {new Date(incomingPlan.date).toLocaleDateString()}
                        {incomingPlan.end_date
                          ? ` - ${new Date(
                              incomingPlan.end_date
                            ).toLocaleDateString()}`
                          : ""}
                      </p>
                    </div>

                    <span
                      className={`${abhaya_libre.className} text-xl italic text-gray-700 block mb-4 px-1`}
                    >
                      Schedule
                    </span>

                    {getPlanDays(incomingPlan.date, incomingPlan.end_date).map(
                      (dayDate, index) => {
                        const dayIndex = index + 1;
                        return (
                          <div
                            key={index}
                            className="mb-8 border-b last:border-0 border-gray-200 pb-4 last:pb-0"
                          >
                            <div className="flex items-center gap-2 mb-4">
                              <div className="bg-green-100 text-green-700 font-bold px-3 py-1 rounded-full text-xs">
                                Day {dayIndex}
                              </div>
                              <p
                                className={`${jost.className} font-semibold text-gray-600`}
                              >
                                {dayDate.toLocaleDateString("vi-VN")}
                              </p>
                            </div>

                            <TimeSection
                              title="Morning"
                              icon={
                                <Sun
                                  size={18}
                                  className="text-yellow-500 fill-yellow-500"
                                />
                              }
                              activities={getActivitiesByDayAndTime(
                                incomingPlan.activities,
                                dayDate,
                                "Morning"
                              )}
                              showTime={false}
                            />

                            <TimeSection
                              title="Afternoon"
                              icon={
                                <Sunset size={18} className="text-orange-500" />
                              }
                              activities={getActivitiesByDayAndTime(
                                incomingPlan.activities,
                                dayDate,
                                "Afternoon"
                              )}
                              showTime={false}
                            />

                            <TimeSection
                              title="Evening"
                              icon={
                                <Moon size={18} className="text-purple-500" />
                              }
                              activities={getActivitiesByDayAndTime(
                                incomingPlan.activities,
                                dayDate,
                                "Evening"
                              )}
                              showTime={false}
                            />
                          </div>
                        );
                      }
                    )}

                    {currentUserId &&
                      incomingPlan.user_id === currentUserId && (
                        <div className="flex flex-col gap-3 mt-6">
                          <button
                            onClick={() => {
                              router.push(
                                `/planning_page/review_plan?id=${incomingPlan.id}`
                              );
                            }}
                            className={`${jost.className} w-full border-2 border-[#53B552] text-[#53B552] bg-white hover:bg-green-50 transition-all text-lg font-bold py-3 rounded-full shadow-sm`}
                          >
                            Edit Schedule
                          </button>
                        </div>
                      )}
                  </div>
                ) : (
                  <EmptyState
                    message="No incoming trips planned."
                    showCreateButton={true}
                  />
                ))}

              {activeTab === "Future" &&
                (futurePlans.length > 0 ? (
                  <div className="space-y-3 pt-2">
                    {futurePlans.map((plan) => (
                      <PlanSummaryCard
                        key={plan.id}
                        plan={plan}
                        expandedId={expandedPlanId}
                        onToggle={handleTogglePlan}
                        onDelete={() => handleDeletePlan(plan.id, plan.user_id)}
                        currentUserId={currentUserId}
                        type="future"
                      />
                    ))}
                  </div>
                ) : (
                  <EmptyState message="No other future trips." />
                ))}

              {activeTab === "Previous" &&
                (previousPlans.length > 0 ? (
                  <div className="space-y-3 pt-2">
                    {previousPlans.map((plan) => (
                      <PlanSummaryCard
                        key={plan.id}
                        plan={plan}
                        expandedId={expandedPlanId}
                        onToggle={handleTogglePlan}
                        onDelete={() => handleDeletePlan(plan.id, plan.user_id)}
                        currentUserId={currentUserId}
                        type="past"
                      />
                    ))}
                  </div>
                ) : (
                  <EmptyState message="No travel history." />
                ))}
            </>
          )}

          <Link href="/planning_page/create_plan">
            <button
              className="absolute bottom-60 right-6 bg-[#53B552] text-white p-4 rounded-full shadow-xl hover:bg-green-600 transition-transform hover:scale-110 active:scale-95 z-30 flex items-center justify-center group"
              title="Create New Plan"
            >
              <Plus size={28} />
              <div className="absolute inset-0 rounded-full ring-2 ring-white/30 group-hover:ring-4 transition-all"></div>
            </button>
          </Link>
        </main>
      </div>
    </div>
  );
}

// --- SUB-COMPONENTS ---

function TimeSection({
  title,
  icon,
  activities,
  showTime = true,
}: {
  title: string;
  icon: React.ReactNode;
  activities: PlanActivity[];
  showTime?: boolean;
}) {
  return (
    <div className="mb-4">
      <div className="flex justify-between items-end mb-3 px-1">
        <div className="flex items-center gap-1 text-gray-600">
          <span className={`${abhaya_libre.className} italic text-lg`}>
            {title}
          </span>
          {icon}
        </div>
      </div>
      <div className="space-y-3">
        {activities.length > 0 ? (
          activities.map((item) => (
            <ActivityCard key={item.id} item={item} showTime={showTime} />
          ))
        ) : (
          <div className="border border-dashed border-gray-300 rounded-xl p-3 text-center">
            <p className={`${jost.className} text-gray-400 text-xs italic`}>
              No activities.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

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

function ActivityCard({
  item,
  isSmall = false,
  showTime = true,
}: {
  item: PlanActivity;
  isSmall?: boolean;
  showTime?: boolean;
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

        {showTime && item.time && (
          <span className="text-[10px] text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded-md ml-2">
            {item.time}
          </span>
        )}

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
          <div className="w-full h-full flex items-center justify-center text-gray-400 text-[10px]">
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
  onDelete,
  currentUserId,
  type,
}: {
  plan: TravelPlan;
  expandedId: number | null;
  onToggle: (id: number) => void;
  onDelete: () => void;
  currentUserId: number | null;
  type: "future" | "past";
}) {
  const isExpanded = expandedId === plan.id;
  const dateObj = parseDate(plan.date);
  const isOwner = currentUserId && plan.user_id === currentUserId;

  return (
    <div className="bg-white rounded-2xl shadow-sm overflow-hidden transition-all duration-300 border border-gray-100">
      <div className="p-4 flex items-center justify-between cursor-pointer hover:bg-gray-50 select-none">
        <div
          className="flex items-center gap-3 flex-1"
          onClick={() => onToggle(plan.id)}
        >
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

        <div className="flex items-center gap-3">
          {isOwner && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              className="p-2 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors"
              title="Delete plan (owner only)"
            >
              <Trash2 size={18} />
            </button>
          )}
          <Link href={`/planning_page/preview_page?id=${plan.id}`}>
            <button
              className="px-3 py-1.5 text-xs font-semibold text-green-600 hover:bg-green-50 rounded-full transition-colors border border-green-200"
              title="View Plan"
            >
              View
            </button>
          </Link>
        </div>
      </div>

      {isExpanded && (
        <div className="px-4 pb-4 pt-0 border-t border-gray-100 animate-in slide-in-from-top-2">
          <div className="mt-3 flex justify-end gap-2">
            <Link href={`/planning_page/preview_page?id=${plan.id}`}>
              <button
                className={`${jost.className} px-4 py-2 text-sm text-green-600 font-bold hover:bg-green-50 rounded-lg transition-colors border border-green-200`}
              >
                View Details
              </button>
            </Link>
            {isOwner && (
              <Link href={`/planning_page/review_plan?id=${plan.id}`}>
                <button
                  className={`${jost.className} px-4 py-2 text-sm bg-green-600 text-white font-bold hover:bg-green-700 rounded-lg transition-colors`}
                >
                  Edit Plan
                </button>
              </Link>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// --- MAIN WRAPPER COMPONENT ---
export default function PlanningPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-gray-200 flex items-center justify-center">
          <div className="bg-white p-4 rounded-full shadow-md">
            <Loader2 className="animate-spin text-[#53B552]" size={32} />
          </div>
        </div>
      }
    >
      <PlanningContent />
    </Suspense>
  );
}
