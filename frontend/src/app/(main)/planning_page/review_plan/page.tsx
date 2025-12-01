"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
  DragOverEvent,
  DragOverlay,
  defaultDropAnimationSideEffects,
  DropAnimation, // Import type này
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
  ChevronLeft,
  CalendarDays,
  Save,
  Sparkles,
  GripVertical,
  Pencil,
  Sun,
  Sunset,
  Moon,
  Plus,
  BrainCircuit,
  MessageSquare,
  X,
  Trash2,
  Send,
  ArrowRight,
} from "lucide-react";
import { Jost } from "next/font/google";
import { api, PlanActivity, PlaceDetails } from "@/lib/api";
import Link from "next/link";

// --- FONTS ---
const jost = Jost({ subsets: ["latin"], weight: ["400", "500", "600", "700"] });

// --- STORAGE KEYS ---
const STORAGE_KEY_RAW = "temp_plan_destinations";
const STORAGE_KEY_STRUCTURED = "current_plan_activities";
const AI_SHOWN_KEY = "has_shown_ai_gen";

// --- AI MESSAGES ---
const AI_STEPS = [
  "Analyzing your selected destinations...",
  "Optimizing travel routes...",
  "Checking opening hours...",
  "Generating your perfect schedule...",
];

const STORAGE_KEY_INFO = "temp_plan_info";

// --- [FIX] CONFIG DROP ANIMATION ---
const dropAnimationConfig: DropAnimation = {
  sideEffects: defaultDropAnimationSideEffects({
    styles: {
      active: {
        opacity: "0.5",
      },
    },
  }),
};

// ==========================================
// 1. COMPONENT ITEM (Draggable)
// ==========================================
interface SortableItemProps {
  activity: PlanActivity;
  onDelete: (id: string | number) => void;
}

function SortableItem({ activity, onDelete }: SortableItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: activity.id, data: { ...activity } });

  const style = {
    transform: CSS.Translate.toString(transform),
    transition,
    opacity: isDragging ? 0.3 : 1,
    zIndex: isDragging ? 999 : "auto",
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`bg-white p-3 rounded-xl shadow-sm border mb-3 flex gap-3 items-center group touch-none relative ${
        isDragging
          ? "border-[#53B552] ring-2 ring-[#53B552]/20"
          : "border-gray-100"
      }`}
    >
      <div className="w-12 h-12 bg-gray-100 rounded-lg overflow-hidden shrink-0">
        <img
          src={activity.image_url || "https://via.placeholder.com/100"}
          alt=""
          className="w-full h-full object-cover"
        />
      </div>

      <div className="flex-1 min-w-0">
        <h3
          className={`${jost.className} font-bold text-gray-800 truncate text-sm`}
        >
          {activity.title}
        </h3>
        <p className="text-[10px] text-gray-400 truncate">{activity.address}</p>
      </div>

      <button
        onClick={(e) => {
          e.stopPropagation();
          onDelete(activity.id);
        }}
        className="p-2 text-gray-300 hover:text-red-500 transition-colors"
      >
        <Trash2 size={16} />
      </button>

      <div
        {...attributes}
        {...listeners}
        className="cursor-grab text-gray-300 hover:text-gray-500 p-2 border-l border-gray-100 pl-2"
      >
        <GripVertical size={18} />
      </div>
    </div>
  );
}

// ==========================================
// 2. CONTAINER COMPONENT (Time Slot)
// ==========================================
function TimeSlotContainer({
  id,
  title,
  icon,
  items,
  onDelete,
  onAddPlace,
}: {
  id: string;
  title: string;
  icon: React.ReactNode;
  items: PlanActivity[];
  onDelete: (id: string | number) => void;
  onAddPlace: () => void;
}) {
  const { setNodeRef } = useSortable({ id });

  return (
    <div
      ref={setNodeRef}
      className="bg-[#F9FAF9] p-3 rounded-2xl mb-4 border border-gray-200"
    >
      <div className="flex items-center justify-between mb-3 px-1">
        <div className="flex items-center gap-2">
          {icon}
          <h3
            className={`${jost.className} font-bold text-gray-600 uppercase text-xs tracking-wider`}
          >
            {title}
          </h3>
          <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
            {items.length}
          </span>
        </div>

        <button
          onClick={onAddPlace}
          className="text-[#53B552] hover:bg-green-50 p-1 rounded-full transition-colors"
        >
          <Plus size={16} />
        </button>
      </div>

      <SortableContext
        items={items.map((i) => i.id)}
        strategy={verticalListSortingStrategy}
      >
        <div className="min-h-[60px]">
          {items.length === 0 && (
            <div className="h-16 border-2 border-dashed border-gray-200 rounded-xl flex items-center justify-center text-gray-300 text-xs">
              Drop here
            </div>
          )}
          {items.map((activity) => (
            <SortableItem
              key={activity.id}
              activity={activity}
              onDelete={onDelete}
            />
          ))}
        </div>
      </SortableContext>
    </div>
  );
}

// ==========================================
// 3. CHATBOT COMPONENT
// ==========================================
function ChatWindow({ onClose }: { onClose: () => void }) {
  const [messages, setMessages] = useState<
    { role: "user" | "bot"; text: string }[]
  >([
    {
      role: "bot",
      text: "Hello! I'm your travel assistant. How can I help you adjust your plan?",
    },
  ]);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;
    const userMsg = input;
    setMessages((prev) => [...prev, { role: "user", text: userMsg }]);
    setInput("");

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: `I received: "${userMsg}". (API integration pending)`,
        },
      ]);
    }, 1000);
  };

  return (
    <div className="h-full flex flex-col bg-white border-t border-gray-200 shadow-[0_-5px_20px_rgba(0,0,0,0.1)]">
      <div className="flex justify-between items-center px-4 py-3 border-b border-gray-100 bg-gray-50">
        <div className="flex items-center gap-2">
          <BrainCircuit size={18} className="text-[#53B552]" />
          <span className={`${jost.className} font-bold text-gray-700`}>
            AI Assistant
          </span>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-red-500">
          <X size={20} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-[#F5F7F5]">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[80%] p-3 rounded-2xl text-sm ${
                msg.role === "user"
                  ? "bg-[#53B552] text-white rounded-tr-none"
                  : "bg-white text-gray-700 border border-gray-100 rounded-tl-none shadow-sm"
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-3 bg-white border-t border-gray-100 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask me to change schedule..."
          className="flex-1 bg-gray-100 rounded-full px-4 py-2 text-sm outline-none focus:ring-1 focus:ring-green-400"
        />
        <button
          onClick={handleSend}
          className="bg-[#53B552] text-white p-2 rounded-full hover:bg-green-600"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}

// ==========================================
// 4. MAIN PAGE
// ==========================================
export default function ReviewPlanPage() {
  const router = useRouter();

  // --- STATE ---
  const [isAiProcessing, setIsAiProcessing] = useState(false);
  const [aiStepIndex, setAiStepIndex] = useState(0);
  const [progress, setProgress] = useState(0);

  const [isSaving, setIsSaving] = useState(false);
  const [activities, setActivities] = useState<PlanActivity[]>([]);
  const [activeId, setActiveId] = useState<string | number | null>(null);

  const [planInfo, setPlanInfo] = useState({
    name: "My Awesome Trip",
    date: new Date().toISOString(),
    end_date: new Date().toISOString(),
  });
  const [isEditingHeader, setIsEditingHeader] = useState(false);

  // Split Screen State
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [planHeightPercent, setPlanHeightPercent] = useState(100);
  const containerRef = useRef<HTMLDivElement>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  // --- INIT DATA ---
  useEffect(() => {
    const storedInfo = sessionStorage.getItem(STORAGE_KEY_INFO);
    if (storedInfo) {
      try {
        const parsed = JSON.parse(storedInfo);
        setPlanInfo({
          name: parsed.name || "My Trip",
          date: parsed.start_date,
          end_date: parsed.end_date,
        });
      } catch (e) {
        console.error(e);
      }
    }
    const hasShownAI = sessionStorage.getItem(AI_SHOWN_KEY);
    const storedRaw = sessionStorage.getItem(STORAGE_KEY_RAW);

    if (!hasShownAI && storedRaw) {
      runAiSimulation();
    } else {
      loadDataFromStorage();
    }
  }, []);

  const runAiSimulation = () => {
    setIsAiProcessing(true);
    let step = 0;
    const interval = setInterval(() => {
      setAiStepIndex((s) => (s < AI_STEPS.length - 1 ? s + 1 : s));
      setProgress((p) => Math.min(p + 25, 100));
      step++;
      if (step > 4) {
        clearInterval(interval);
        setIsAiProcessing(false);
        sessionStorage.setItem(AI_SHOWN_KEY, "true");
        loadDataFromStorage();
      }
    }, 800);
  };

  const loadDataFromStorage = () => {
    const rawData = sessionStorage.getItem(STORAGE_KEY_RAW);
    const storedActivities = sessionStorage.getItem(STORAGE_KEY_STRUCTURED);

    if (storedActivities) {
      let currentList: PlanActivity[] = JSON.parse(storedActivities);
      if (rawData) {
        const rawList: PlaceDetails[] = JSON.parse(rawData);
        const newItems = rawList.filter(
          (raw) => !currentList.some((act) => act.id === raw.place_id)
        );

        const newActivities = newItems.map((place) => ({
          id: place.place_id,
          title: place.name,
          address: place.formatted_address,
          image_url: place.photos?.[0]?.photo_url || "",
          time_slot: "Morning" as const,
          date: new Date().toISOString(),
          type: place.types?.[0] || "place",
          order_in_day: 999,
        }));

        if (newActivities.length > 0) {
          currentList = [...currentList, ...newActivities];
        }
      }
      setActivities(currentList);
    } else if (rawData) {
      const rawList: PlaceDetails[] = JSON.parse(rawData);
      const initialActivities = rawList.map((place, idx) => ({
        id: place.place_id,
        title: place.name,
        address: place.formatted_address,
        image_url: place.photos?.[0]?.photo_url || "",
        time_slot: (idx % 3 === 0
          ? "Morning"
          : idx % 3 === 1
          ? "Afternoon"
          : "Evening") as "Morning" | "Afternoon" | "Evening",
        date: new Date().toISOString(),
        type: place.types?.[0] || "place",
        order_in_day: idx,
      }));
      setActivities(initialActivities);
    }
  };

  useEffect(() => {
    if (activities.length > 0) {
      sessionStorage.setItem(
        STORAGE_KEY_STRUCTURED,
        JSON.stringify(activities)
      );

      const rawListForMap = activities.map((act) => ({
        place_id: act.id,
        name: act.title,
        formatted_address: act.address,
        photos: [{ photo_url: act.image_url }],
      }));
      sessionStorage.setItem(STORAGE_KEY_RAW, JSON.stringify(rawListForMap));
    }
  }, [activities]);

  // --- SPLIT SCREEN LOGIC ---
  const handleToggleChat = () => {
    if (isChatOpen) {
      setIsChatOpen(false);
      setPlanHeightPercent(100);
    } else {
      setIsChatOpen(true);
      setPlanHeightPercent(60);
    }
  };

  const handleDragResizer = (e: React.MouseEvent | React.TouchEvent) => {
    e.preventDefault();
    const startY = "touches" in e ? e.touches[0].clientY : e.clientY;
    const startHeight =
      containerRef.current?.clientHeight || window.innerHeight;

    const onMove = (moveEvent: MouseEvent | TouchEvent) => {
      const currentY =
        "touches" in moveEvent
          ? moveEvent.touches[0].clientY
          : moveEvent.clientY;
      const newPercent = (currentY / startHeight) * 100;

      if (newPercent > 20 && newPercent < 80) {
        setPlanHeightPercent(newPercent);
      }
    };

    const onUp = () => {
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
      document.removeEventListener("touchmove", onMove);
      document.removeEventListener("touchend", onUp);
    };

    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
    document.addEventListener("touchmove", onMove, { passive: false });
    document.addEventListener("touchend", onUp);
  };

  // --- DND LOGIC ---
  const planDays = [planInfo.date];

  const findContainer = (id: string | number) => {
    if (String(id).includes("_")) return id;
    const item = activities.find((a) => a.id === id);
    if (!item) return null;
    const dateStr = item.date
      ? item.date.split("T")[0]
      : planDays[0].split("T")[0];
    return `${dateStr}_${item.time_slot}`;
  };

  const handleDragStart = (event: any) => setActiveId(event.active.id);

  const handleDragOver = (event: DragOverEvent) => {
    const { active, over } = event;
    const overId = over?.id;
    if (!overId || active.id === overId) return;
    const activeContainer = findContainer(active.id);
    const overContainer = findContainer(overId);
    if (!activeContainer || !overContainer || activeContainer === overContainer)
      return;

    setActivities((prev) => {
      const activeIndex = prev.findIndex((i) => i.id === active.id);
      const overIndex = prev.findIndex((i) => i.id === overId);
      const [newDate, newSlot] = String(overContainer).split("_");
      const newActivities = [...prev];
      newActivities[activeIndex] = {
        ...newActivities[activeIndex],
        time_slot: newSlot as any,
        date: new Date(newDate).toISOString(),
      };
      return arrayMove(
        newActivities,
        activeIndex,
        overIndex >= 0 ? overIndex : newActivities.length - 1
      );
    });
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over) {
      setActiveId(null);
      return;
    }
    if (active.id !== over.id) {
      const activeContainer = findContainer(active.id);
      const overContainer = findContainer(over.id);
      if (activeContainer === overContainer && activeContainer) {
        setActivities((items) => {
          const oldIndex = items.findIndex((item) => item.id === active.id);
          const newIndex = items.findIndex((item) => item.id === over.id);
          return arrayMove(items, oldIndex, newIndex);
        });
      }
    }
    setActiveId(null);
  };

  // --- ACTIONS ---
  const handleDeleteActivity = (id: string | number) => {
    if (confirm("Remove this place from plan?")) {
      setActivities((prev) => prev.filter((a) => a.id !== id));
    }
  };

  const handleAddPlaceToSlot = () => {
    router.push("/planning_page/add_destinations");
  };

  // src/app/(main)/planning_page/review_plan/page.tsx

  const handleSaveToBackend = async () => {
    setIsSaving(true);
    try {
      // 1. Lấy Budget
      const storedInfoRaw = sessionStorage.getItem(STORAGE_KEY_INFO);
      const budget = storedInfoRaw ? JSON.parse(storedInfoRaw).budget : 0;

      // 2. Chuẩn bị danh sách Destinations
      const destinationsPayload = activities.map((act, index) => {
        let validType = "attraction";
        const typeLower = (act.type || "").toLowerCase();
        if (typeLower.includes("restaurant") || typeLower.includes("food"))
          validType = "restaurant";
        else if (typeLower.includes("hotel") || typeLower.includes("lodging"))
          validType = "accommodation";
        else if (typeLower.includes("transit") || typeLower.includes("station"))
          validType = "transport";

        return {
          id: 0, // [QUAN TRỌNG] Gửi số 0 để vượt qua validator "int_parsing"
          destination_id: String(act.id), // [QUAN TRỌNG] Đây mới là ID Google Place
          destination_type: validType, // Gửi cả 2 field type để chắc chắn
          type: validType,
          visit_date: act.date
            ? act.date.split("T")[0]
            : planInfo.date.split("T")[0],
          order_in_day: index + 1,
          note: act.title,
          url: act.image_url,
          estimated_cost: 0,
        };
      });

      // 3. Gọi API
      const requestData = {
        place_name: planInfo.name,
        start_date: planInfo.date,
        end_date: planInfo.end_date,
        budget_limit: Number(budget),
        destinations: destinationsPayload,
      };

      console.log("Sending Plan Data:", requestData);

      await api.createPlan(requestData);

      alert("Plan saved successfully!");

      sessionStorage.removeItem(STORAGE_KEY_RAW);
      sessionStorage.removeItem(STORAGE_KEY_STRUCTURED);
      sessionStorage.removeItem(AI_SHOWN_KEY);
      sessionStorage.removeItem(STORAGE_KEY_INFO);

      router.push("/planning_page/showing_plan_page");
    } catch (e) {
      console.error("Save Error:", e);
      alert("Failed to save plan. Please check console for details.");
    } finally {
      setIsSaving(false);
    }
  };

  // --- RENDER AI ---
  if (isAiProcessing) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center p-8 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-64 h-64 bg-green-100 rounded-full blur-3xl opacity-50"></div>
        <div className="relative z-10 flex flex-col items-center max-w-sm w-full">
          <div className="w-20 h-20 bg-[#E3F1E4] rounded-full flex items-center justify-center animate-pulse mb-8">
            <Sparkles className="text-[#53B552] w-10 h-10 animate-spin-slow" />
          </div>
          <h2
            className={`${jost.className} text-xl font-bold text-gray-800 text-center mb-2`}
          >
            AI Generator
          </h2>
          <p className="text-gray-500 text-sm mb-8 text-center">
            {AI_STEPS[aiStepIndex]}
          </p>
          <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
            <div
              className="h-full bg-[#53B552] transition-all duration-300"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>
      </div>
    );
  }

  // --- RENDER MAIN ---
  return (
    <div className="h-screen w-full flex justify-center bg-gray-200 overflow-hidden">
      <div
        ref={containerRef}
        className="w-full max-w-md bg-[#F5F7F5] h-full shadow-2xl relative flex flex-col"
      >
        {/* === TOP PANEL: PLAN === */}
        <div
          style={{ height: isChatOpen ? `${planHeightPercent}%` : "100%" }}
          className="flex flex-col relative transition-[height] duration-100 ease-linear"
        >
          {/* HEADER */}
          <div className="bg-white px-4 py-4 shadow-sm z-10 flex justify-between items-center shrink-0">
            <div className="flex items-center gap-2">
              <Link href="/planning_page/add_destinations">
                <ChevronLeft className="text-gray-400" />
              </Link>
              <h1
                className={`${jost.className} text-gray-800 font-bold text-lg`}
              >
                Review Plan
              </h1>
            </div>
            <button
              onClick={handleSaveToBackend}
              disabled={isSaving}
              className="flex items-center gap-1 font-bold text-sm px-3 py-2 rounded-full text-[#53B552] bg-[#E3F1E4] hover:bg-green-100"
            >
              {isSaving ? (
                "Saving..."
              ) : (
                <>
                  <Save size={16} /> Save
                </>
              )}
            </button>
          </div>

          {/* SCROLLABLE CONTENT */}
          <div className="flex-1 overflow-y-auto p-4 pb-20">
            <div className="mb-4 bg-white p-4 rounded-xl shadow-sm border border-gray-100">
              <div className="flex justify-between items-start">
                <div>
                  {isEditingHeader ? (
                    <input
                      value={planInfo.name}
                      onChange={(e) =>
                        setPlanInfo({ ...planInfo, name: e.target.value })
                      }
                      onBlur={() => setIsEditingHeader(false)}
                      autoFocus
                      className="text-2xl font-bold text-gray-800 border-b border-green-500 outline-none w-full"
                    />
                  ) : (
                    <h2
                      onClick={() => setIsEditingHeader(true)}
                      className={`${jost.className} text-2xl font-bold text-gray-800 cursor-pointer hover:text-green-600`}
                    >
                      {planInfo.name}{" "}
                      <Pencil size={14} className="inline text-gray-300" />
                    </h2>
                  )}
                  <p className="text-gray-500 text-sm flex items-center gap-2 mt-1">
                    <CalendarDays size={16} />{" "}
                    {new Date(planInfo.date).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>

            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragStart={handleDragStart}
              onDragOver={handleDragOver}
              onDragEnd={handleDragEnd}
            >
              <div className="space-y-6">
                {planDays.map((day, idx) => {
                  const dayStr = day.split("T")[0];
                  return (
                    <div key={idx}>
                      <div className="flex items-center gap-2 mb-3 sticky top-0 bg-[#F5F7F5] z-10 py-2">
                        <div className="bg-[#53B552] text-white font-bold w-8 h-8 rounded-full flex items-center justify-center shadow-md">
                          {idx + 1}
                        </div>
                        <h3
                          className={`${jost.className} font-bold text-gray-800 text-lg`}
                        >
                          Day {idx + 1}
                        </h3>
                      </div>
                      <div className="pl-4 border-l-2 border-dashed border-gray-200 ml-4 space-y-2">
                        <TimeSlotContainer
                          id={`${dayStr}_Morning`}
                          title="Morning"
                          icon={<Sun size={18} className="text-orange-400" />}
                          items={activities.filter(
                            (a) => a.time_slot === "Morning"
                          )}
                          onDelete={handleDeleteActivity}
                          onAddPlace={handleAddPlaceToSlot}
                        />
                        <TimeSlotContainer
                          id={`${dayStr}_Afternoon`}
                          title="Afternoon"
                          icon={<Sunset size={18} className="text-red-400" />}
                          items={activities.filter(
                            (a) => a.time_slot === "Afternoon"
                          )}
                          onDelete={handleDeleteActivity}
                          onAddPlace={handleAddPlaceToSlot}
                        />
                        <TimeSlotContainer
                          id={`${dayStr}_Evening`}
                          title="Evening"
                          icon={<Moon size={18} className="text-purple-400" />}
                          items={activities.filter(
                            (a) => a.time_slot === "Evening"
                          )}
                          onDelete={handleDeleteActivity}
                          onAddPlace={handleAddPlaceToSlot}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
              <DragOverlay
                dropAnimation={dropAnimationConfig} // [FIX] Đã thay thế phần lỗi bằng object config
              >
                {activeId ? (
                  <div className="bg-white p-4 rounded-xl shadow-xl border-2 border-[#53B552]">
                    {activities.find((a) => a.id === activeId)?.title}
                  </div>
                ) : null}
              </DragOverlay>
            </DndContext>
          </div>

          {!isChatOpen && (
            <button
              onClick={handleToggleChat}
              className="absolute bottom-6 right-6 bg-white text-[#53B552] p-4 rounded-full shadow-[0_4px_20px_rgba(0,0,0,0.15)] hover:scale-110 transition-transform z-50 border border-green-100"
            >
              <MessageSquare size={24} fill="#53B552" className="text-white" />
            </button>
          )}
        </div>

        {/* === RESIZER === */}
        {isChatOpen && (
          <div
            onMouseDown={handleDragResizer}
            onTouchStart={handleDragResizer}
            className="w-full h-6 bg-gray-100 cursor-row-resize flex items-center justify-center hover:bg-gray-200 shrink-0 z-40"
          >
            <div className="w-12 h-1 bg-gray-300 rounded-full"></div>
          </div>
        )}

        {/* === CHATBOT === */}
        {isChatOpen && (
          <div className="flex-1 min-h-0 relative">
            <ChatWindow onClose={handleToggleChat} />
          </div>
        )}
      </div>
    </div>
  );
}
