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
  Sunset,
  Moon,
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

// [FIX 1] Hàm parseDate hỗ trợ cả "YYYY-MM-DD" (Backend) và "DD/MM/YYYY"
const parseDate = (dateStr: string) => {
  if (!dateStr) return new Date(0); // Trả về ngày rất cũ nếu null

  // Trường hợp 1: YYYY-MM-DD (Từ Backend Python trả về)
  if (dateStr.includes("-")) {
    return new Date(dateStr);
  }

  // Trường hợp 2: DD/MM/YYYY (Nếu có)
  if (dateStr.includes("/")) {
    const [day, month, year] = dateStr.split("/").map(Number);
    return new Date(year, month - 1, day);
  }

  return new Date(dateStr);
};

export default function PlanningPage() {
  const [activeTab, setActiveTab] = useState<
    "Incoming" | "Future" | "Previous"
  >("Incoming");
  const [incomingPlan, setIncomingPlan] = useState<TravelPlan | null>(null);
  const [previousPlans, setPreviousPlans] = useState<TravelPlan[]>([]);
  const [futurePlans, setFuturePlans] = useState<TravelPlan[]>([]);
  const [expandedPlanId, setExpandedPlanId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initData = async () => {
      try {
        setLoading(true);

        const allPlans = await api.getPlans();

        if (!allPlans || allPlans.length === 0) {
          // ... (set null hết)
          return;
        }

        // [FIX QUAN TRỌNG]: LỌC BỎ CÁC PLAN KHÔNG ĐẠT CHUẨN (Ít hơn 2 địa điểm)
        // Những plan này sẽ không được tính là Incoming, Future hay Previous
        const validPlans = allPlans.filter(
          (p) => p.activities && p.activities.length >= 2
        );

        // --- XỬ LÝ PLAN RÁC (TÙY CHỌN) ---
        // Nếu bạn muốn xóa dùm người dùng luôn (Cẩn thận: có thể xóa nhầm lúc họ đang tạo dở)
        // const invalidPlans = allPlans.filter(p => p.activities.length < 2);
        // invalidPlans.forEach(p => api.deletePlan(p.id));

        // --- LOGIC PHÂN LOẠI (Dùng validPlans thay vì allPlans) ---
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const allActiveAndFuture = validPlans.filter((p) => {
          // Dùng validPlans
          const endDate = p.end_date
            ? parseDate(p.end_date)
            : parseDate(p.date);
          return endDate >= today;
        });

        const allPast = validPlans.filter((p) => {
          // Dùng validPlans
          const endDate = p.end_date
            ? parseDate(p.end_date)
            : parseDate(p.date);
          return endDate < today;
        });

        // ... (Phần sort và set state giữ nguyên logic cũ) ...

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

    initData();
  }, []);

  const handleTogglePlan = (id: number) => {
    setExpandedPlanId(expandedPlanId === id ? null : id);
  };

  const getActivitiesByTime = (activities: PlanActivity[], slot: string) => {
    if (!activities) return [];
    // [FIX 3 - Tạm thời] Vì mất giờ nên backend trả về toàn Morning.
    // Nếu bạn muốn hiển thị tạm để check data thì có thể bỏ filter,
    // nhưng tốt nhất là hiển thị đúng data backend trả về.
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
              {activeTab === "Incoming" &&
                (incomingPlan ? (
                  <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 pb-4">
                    {/* Header Card */}
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
                      <Link href={`/planning_page/${incomingPlan.id}/details`}>
                        <ChevronRight size={20} className="text-gray-400" />
                      </Link>
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

                    {/* Morning Section */}
                    <TimeSection
                      title="Morning"
                      icon={
                        <Sun
                          size={18}
                          className="text-yellow-500 fill-yellow-500"
                        />
                      }
                      activities={getActivitiesByTime(
                        incomingPlan.activities,
                        "Morning"
                      )}
                    />

                    {/* Afternoon Section */}
                    <TimeSection
                      title="Afternoon"
                      icon={<Sunset size={18} className="text-orange-500" />}
                      activities={getActivitiesByTime(
                        incomingPlan.activities,
                        "Afternoon"
                      )}
                    />

                    {/* Evening Section (Code cũ bị thiếu cái này) */}
                    <TimeSection
                      title="Evening"
                      icon={<Moon size={18} className="text-purple-500" />}
                      activities={getActivitiesByTime(
                        incomingPlan.activities,
                        "Evening"
                      )}
                    />

                    <div className="flex flex-col gap-3 mt-6">
                      <Link href={`/planning_page/${incomingPlan.id}/details`}>
                        <button
                          className={`${jost.className} w-full border-2 border-[#53B552] text-[#53B552] bg-white hover:bg-green-50 transition-all text-lg font-bold py-3 rounded-full shadow-sm`}
                        >
                          Edit Schedule
                        </button>
                      </Link>
                    </div>
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
                        type="future"
                      />
                    ))}
                  </div>
                ) : (
                  <EmptyState message="No future trips." />
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
              className="absolute bottom-24 right-6 bg-[#53B552] text-white p-4 rounded-full shadow-xl hover:bg-green-600 transition-transform hover:scale-110 active:scale-95 z-30 flex items-center justify-center group"
              title="Create New Plan"
            >
              <Plus size={28} />
              <div className="absolute inset-0 rounded-full ring-2 ring-white/30 group-hover:ring-4 transition-all"></div>
            </button>
          </Link>
        </main>

        <footer className="bg-white shadow-[0_-5px_15px_rgba(0,0,0,0.05)] sticky bottom-0 w-full z-20 shrink-0">
          <div className="h-1 bg-linear-to-r from-transparent via-green-200 to-transparent"></div>
          <div className="flex justify-around items-center py-3">
            <Link
              href="/homepage"
              className="flex flex-col items-center text-gray-400 hover:text-green-600"
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
              className="flex flex-col items-center text-gray-400 hover:text-green-600"
            >
              <Bot size={24} strokeWidth={2} />
              <span className={`${jost.className} text-xs font-medium mt-1`}>
                Ecobot
              </span>
            </Link>
            <Link
              href="/user_page/profile_page"
              className="flex flex-col items-center text-gray-400 hover:text-green-600"
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

// --- Component phụ hiển thị từng buổi ---
function TimeSection({
  title,
  icon,
  activities,
}: {
  title: string;
  icon: React.ReactNode;
  activities: PlanActivity[];
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
          activities.map((item) => <ActivityCard key={item.id} item={item} />)
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
  type,
}: {
  plan: TravelPlan;
  expandedId: number | null;
  onToggle: (id: number) => void;
  type: "future" | "past";
}) {
  const isExpanded = expandedId === plan.id;
  const dateObj = parseDate(plan.date); // Sử dụng hàm parseDate mới

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
          {/* Nội dung mở rộng giữ nguyên */}
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
