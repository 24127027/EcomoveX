"use client";

import { useEffect, useState, Suspense } from "react"; // Đã thêm Suspense
import { useRouter, useSearchParams } from "next/navigation";
import { api, PlanActivity, TravelPlan } from "@/lib/api";
import { Jost } from "next/font/google";
import {
  ArrowLeft,
  Calendar,
  MapPin,
  DollarSign,
  Users,
  Clock,
  Edit,
  Sun,
  Sunset,
  Moon,
  Navigation,
  Car,
  Fuel,
} from "lucide-react";

const jost = Jost({ subsets: ["latin"], weight: ["400", "500", "600", "700"] });

// --- LOADING COMPONENT ---
// Tách giao diện Loading ra để dùng chung cho cả Suspense Fallback và State Loading
const LoadingView = () => (
  <div className="min-h-screen w-full flex justify-center bg-gray-200">
    <div className="w-full max-w-md bg-[#F5F7F5] h-screen shadow-2xl relative flex flex-col overflow-hidden">
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-green-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className={`${jost.className} text-gray-600`}>Loading plan...</p>
        </div>
      </div>
    </div>
  </div>
);

// --- MAIN CONTENT COMPONENT ---
// Đổi tên component cũ thành Content và giữ nguyên logic
function PreviewPlanContent() {
  const router = useRouter();
  const searchParams = useSearchParams(); // Hook này nằm an toàn ở đây
  const planId = searchParams.get("id");

  const [plan, setPlan] = useState<TravelPlan | null>(null);
  const [activities, setActivities] = useState<PlanActivity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!planId) {
      // Nếu không có ID, redirect về home hoặc trang danh sách
      // Tuy nhiên trong lúc render server/build, router có thể chưa sẵn sàng,
      // nên logic này chạy ở client là an toàn nhất.
      return;
    }

    const loadPlan = async () => {
      try {
        const allPlans = await api.getPlans();
        const currentPlan = allPlans.find((p) => p.id === Number(planId));

        if (currentPlan) {
          console.log("Preview Plan - Full plan data:", currentPlan);
          console.log(
            "Preview Plan - Budget value:",
            currentPlan.budget_limit || currentPlan.budget
          );
          setPlan(currentPlan);
          setActivities(currentPlan.activities || []);
        } else {
          router.push("/homepage");
        }
      } catch (error) {
        console.error("Failed to load plan:", error);
      } finally {
        setLoading(false);
      }
    };

    loadPlan();
  }, [planId, router]);

  const groupActivitiesByDay = () => {
    if (!plan) return {};

    const grouped: { [key: string]: PlanActivity[] } = {};
    activities.forEach((activity) => {
      const dayKey = activity.date?.split("T")[0] || "No Date";
      if (!grouped[dayKey]) grouped[dayKey] = [];
      grouped[dayKey].push(activity);
    });

    // Sort activities within each day by time_slot and order_in_day
    Object.keys(grouped).forEach((day) => {
      grouped[day].sort((a, b) => {
        const slotOrder = { Morning: 0, Afternoon: 1, Evening: 2 };
        const slotA = slotOrder[a.time_slot as keyof typeof slotOrder] ?? 3;
        const slotB = slotOrder[b.time_slot as keyof typeof slotOrder] ?? 3;
        if (slotA !== slotB) return slotA - slotB;
        return (a.order_in_day ?? 0) - (b.order_in_day ?? 0);
      });
    });

    return grouped;
  };

  const getTimeSlotIcon = (slot: string) => {
    if (slot === "Morning")
      return <Sun size={18} className="text-orange-400" />;
    if (slot === "Afternoon")
      return <Sunset size={18} className="text-red-400" />;
    if (slot === "Evening")
      return <Moon size={18} className="text-indigo-400" />;
    return <Clock size={18} className="text-gray-400" />;
  };

  if (loading) {
    return <LoadingView />;
  }

  if (!plan) {
    // Trường hợp đã load xong nhưng không tìm thấy plan (và đang đợi redirect)
    return null;
  }

  const groupedActivities = groupActivitiesByDay();
  const sortedDays = Object.keys(groupedActivities).sort();

  return (
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      <div className="w-full max-w-md bg-[#F5F7F5] h-screen shadow-2xl relative flex flex-col overflow-hidden">
        {/* Header - Fixed */}
        <div className="bg-white shadow-sm shrink-0 border-b border-gray-100">
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <button
                onClick={() => router.push("/planning_page/showing_plan_page")}
                className="flex items-center gap-2 text-gray-600 hover:text-green-600 transition-colors"
              >
                <ArrowLeft size={20} />
                <span className={`${jost.className} font-semibold`}>Back</span>
              </button>
              <button
                onClick={() =>
                  router.push(`/planning_page/review_plan?id=${planId}`)
                }
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-full hover:bg-green-700 transition-colors shadow-md"
              >
                <Edit size={18} />
                <span className={`${jost.className} font-semibold`}>
                  Edit Plan
                </span>
              </button>
            </div>
          </div>
        </div>

        {/* Main Content - Scrollable */}
        <main className="flex-1 overflow-y-auto px-4 pb-6">
          {/* Hero Section */}
          <div className="py-4">
            <div className="bg-linear-to-r from-green-600 to-blue-600 rounded-3xl p-6 text-white shadow-2xl mb-6">
              <h1 className={`${jost.className} text-3xl font-bold mb-4`}>
                {plan.destination}
              </h1>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {/* Duration */}
                <div className="flex items-center gap-3 bg-white/10 backdrop-blur-sm rounded-xl p-3">
                  <Calendar size={20} />
                  <div>
                    <p className="text-xs opacity-80">Duration</p>
                    <p className={`${jost.className} font-semibold text-sm`}>
                      {new Date(plan.date).toLocaleDateString("en-US", {
                        month: "numeric",
                        day: "numeric",
                      })}{" "}
                      -{" "}
                      {plan.end_date
                        ? new Date(plan.end_date).toLocaleDateString("en-US", {
                            month: "numeric",
                            day: "numeric",
                          })
                        : new Date(plan.date).toLocaleDateString("en-US", {
                            month: "numeric",
                            day: "numeric",
                          })}
                    </p>
                  </div>
                </div>

                {/* Budget */}
                <div className="flex items-center gap-3 bg-white/10 backdrop-blur-sm rounded-xl p-3">
                  <DollarSign size={20} />
                  <div>
                    <p className="text-xs opacity-80">Budget</p>
                    <p className={`${jost.className} font-semibold text-sm`}>
                      {plan.budget_limit
                        ? `$${plan.budget_limit.toLocaleString()}`
                        : plan.budget
                        ? `$${plan.budget.toLocaleString()}`
                        : "N/A"}
                    </p>
                  </div>
                </div>

                {/* Destinations */}
                <div className="flex items-center gap-3 bg-white/10 backdrop-blur-sm rounded-xl p-3">
                  <MapPin size={20} />
                  <div>
                    <p className="text-xs opacity-80">Destinations</p>
                    <p className={`${jost.className} font-semibold text-sm`}>
                      {activities.length} places
                    </p>
                  </div>
                </div>

                {/* Transport - Coming Soon */}
                <div className="flex items-center gap-3 bg-white/10 backdrop-blur-sm rounded-xl p-3">
                  <Car size={20} />
                  <div>
                    <p className="text-xs opacity-80">Transport</p>
                    <p className={`${jost.className} font-semibold text-xs`}>
                      Not selected
                    </p>
                  </div>
                </div>

                {/* Fuel Saved - Coming Soon */}
                <div className="flex items-center gap-3 bg-white/10 backdrop-blur-sm rounded-xl p-3 md:col-span-2 lg:col-span-1">
                  <Fuel size={20} />
                  <div>
                    <p className="text-xs opacity-80">Fuel Saved</p>
                    <p className={`${jost.className} font-semibold text-xs`}>
                      To be calculated
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Itinerary */}
          <div className="space-y-4">
            <h2
              className={`${jost.className} text-xl font-bold text-gray-800 mb-4`}
            >
              Your Itinerary
            </h2>

            {sortedDays.length === 0 ? (
              <div className="bg-white rounded-xl p-8 text-center shadow-sm">
                <MapPin size={40} className="mx-auto text-gray-300 mb-3" />
                <p className={`${jost.className} text-gray-500`}>
                  No destinations added yet
                </p>
              </div>
            ) : (
              sortedDays.map((day, dayIndex) => (
                <div
                  key={day}
                  className="bg-white rounded-xl shadow-sm overflow-hidden border border-gray-100"
                >
                  {/* Day Header */}
                  <div className="bg-linear-to-r from-green-500 to-blue-500 p-4 text-white">
                    <div className="flex items-center gap-3">
                      <div className="bg-white text-green-600 font-bold w-10 h-10 rounded-full flex items-center justify-center shadow-md text-sm">
                        {dayIndex + 1}
                      </div>
                      <div>
                        <h3 className={`${jost.className} text-lg font-bold`}>
                          Day {dayIndex + 1}
                        </h3>
                        <p className="text-xs opacity-90">
                          {new Date(day).toLocaleDateString("en-US", {
                            weekday: "long",
                            year: "numeric",
                            month: "long",
                            day: "numeric",
                          })}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Activities */}
                  <div className="p-4 space-y-3">
                    {groupedActivities[day].map((activity, index) => (
                      <div
                        key={activity.id}
                        className="flex gap-3 p-3 rounded-lg bg-gray-50 border border-gray-100"
                      >
                        {/* Time Badge */}
                        <div className="shrink-0">
                          <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-white rounded-lg shadow-sm border border-gray-200">
                            {getTimeSlotIcon(activity.time_slot)}
                            <span
                              className={`${jost.className} text-xs font-semibold text-gray-700`}
                            >
                              {activity.time_slot}
                            </span>
                          </div>
                        </div>

                        {/* Activity Details */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex-1 min-w-0">
                              <h4
                                className={`${jost.className} font-bold text-gray-800 text-base mb-1 truncate`}
                              >
                                {activity.title}
                              </h4>
                              {activity.address && (
                                <p className="text-gray-600 text-xs flex items-center gap-1 truncate">
                                  <MapPin size={12} />
                                  {activity.address}
                                </p>
                              )}
                            </div>
                            {activity.image_url && (
                              <img
                                src={activity.image_url}
                                alt={activity.title}
                                className="w-16 h-16 rounded-lg object-cover shadow-sm shrink-0"
                              />
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Call to Action */}
          <div className="mt-6 mb-4 bg-linear-to-r from-green-100 to-blue-100 rounded-xl p-6 text-center border border-green-200">
            <Navigation size={36} className="mx-auto text-green-600 mb-3" />
            <h3
              className={`${jost.className} text-lg font-bold text-gray-800 mb-1`}
            >
              Ready to Go?
            </h3>
            <p className="text-gray-600 text-sm mb-4">Your adventure awaits!</p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={() =>
                  router.push(`/planning_page/review_plan?id=${planId}`)
                }
                className="flex items-center gap-2 px-5 py-2.5 bg-green-600 text-white rounded-full hover:bg-green-700 transition-colors shadow-md text-sm"
              >
                <Edit size={16} />
                <span className={`${jost.className} font-semibold`}>
                  Edit Plan
                </span>
              </button>
              <button
                onClick={() => router.push("/planning_page/showing_plan_page")}
                className="px-5 py-2.5 bg-white text-gray-700 rounded-full hover:bg-gray-100 transition-colors shadow-md border border-gray-200 text-sm"
              >
                <span className={`${jost.className} font-semibold`}>
                  Back to Plans
                </span>
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

// --- EXPORT DEFAULT WRAPPER ---
// Đây là component chính được export, nó bọc Content trong Suspense
export default function PreviewPlanPage() {
  return (
    <Suspense fallback={<LoadingView />}>
      <PreviewPlanContent />
    </Suspense>
  );
}