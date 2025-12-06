"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
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
  ChevronRight,
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
  Users,
  User,
} from "lucide-react";
import { Jost } from "next/font/google";
import {
  api,
  PlanActivity,
  PlaceDetails,
  UserProfile,
  PlanMemberDetail,
} from "@/lib/api"; // ✅ Import PlanMemberDetail
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
function ChatWindow({
  onClose,
  planId,
}: {
  onClose: () => void;
  planId: number | null;
}) {
  const [messages, setMessages] = useState<
    { role: "user" | "bot"; text: string }[]
  >([
    {
      role: "bot",
      text: "👋 Hello! I'm your AI travel assistant.\n\n💡 Tips:\n• Drag & drop destinations to rearrange them\n• Click + to add destinations to different time slots\n• I can help optimize your schedule for better routes!\n\nHow can I help you plan your trip?",
    },
  ]); // ✅ Default welcome message
  const [input, setInput] = useState("");
  const [roomId, setRoomId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 1. Fetch Room ID
  useEffect(() => {
    const fetchRoom = async () => {
      try {
        if (planId) {
          // Existing plan - get room from backend
          const res = await api.getPlanChatRoom(planId);
          setRoomId(res.room_id);
        } else {
          // New plan - DON'T create temporary room, just set null
          // Chat feature will be disabled until plan is saved
          setRoomId(null);
          console.log("📝 New plan - chat disabled until saved");
        }
      } catch (error: any) {
        console.warn(
          "⚠️ Failed to get plan chat room (plan may not have room yet):",
          error?.message
        );
        // ✅ Set null and show default message - no chat history fetch
        setRoomId(null);
        setMessages([
          {
            role: "bot",
            text: "👋 Hello! I'm your AI travel assistant.\n\n💡 Tips:\n• Drag & drop destinations to rearrange them\n• Click + to add destinations to different time slots\n• I can help optimize your schedule for better routes!\n\nHow can I help you plan your trip?",
          },
        ]);
      }
    };
    fetchRoom();
  }, [planId]);

  // 2. Fetch History
  useEffect(() => {
    if (!roomId || !planId) return; // ✅ Only fetch history for saved plans with valid room
    const fetchHistory = async () => {
      try {
        const history = await api.getChatHistory(roomId);
        // Assuming sender_id === 0 is bot (SYSTEM_BOT_ID)
        const formatted = history
          .sort(
            (a, b) =>
              new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
          )
          .map((msg) => ({
            role: msg.sender_id === 0 ? "bot" : "user",
            text: msg.content || "",
          })) as { role: "user" | "bot"; text: string }[];

        if (formatted.length === 0) {
          setMessages([
            {
              role: "bot",
              text: "👋 Hello! I'm your AI travel assistant.\n\n💡 Tips:\n• Drag & drop destinations to rearrange them\n• Click + to add destinations to different time slots\n• I can help optimize your schedule for better routes!\n\nHow can I help you plan your trip?",
            },
          ]);
        } else {
          setMessages(formatted);
        }
      } catch (error: any) {
        console.warn(
          "⚠️ Failed to fetch chat history (user may not be room member):",
          error?.message
        );
        // ✅ Set default welcome message on error
        setMessages([
          {
            role: "bot",
            text: "👋 Hello! I'm your AI travel assistant.\n\n💡 Tips:\n• Drag & drop destinations to rearrange them\n• Click + to add destinations to different time slots\n• I can help optimize your schedule for better routes!\n\nHow can I help you plan your trip?",
          },
        ]);
      }
    };
    fetchHistory();
  }, [roomId, planId]); // ✅ Add planId dependency

  const handleSend = async () => {
    if (!input.trim() || !roomId || !planId || isLoading) return; // ✅ Require saved plan
    const userMsg = input;
    setInput(""); // Clear input first
    setIsLoading(true);
    setMessages((prev) => [...prev, { role: "user", text: userMsg }]);

    try {
      let userId = 0;
      const storedUser = localStorage.getItem("user_info");
      if (storedUser) {
        try {
          userId = JSON.parse(storedUser).id;
        } catch (e) {
          console.error("Error parsing user_info", e);
        }
      }

      if (!userId) {
        try {
          const profile = await api.getUserProfile();
          userId = profile.id;
          localStorage.setItem("user_info", JSON.stringify(profile));
        } catch (e) {
          console.error("Failed to fetch user profile", e);
          setMessages((prev) => [
            ...prev,
            {
              role: "bot",
              text: "Error: Could not identify user. Please log in again.",
            },
          ]);
          setIsLoading(false);
          return;
        }
      }

      const res = await api.sendBotMessage(userId, roomId, userMsg);

      if (res.ok && res.message) {
        setMessages((prev) => [...prev, { role: "bot", text: res.message }]);
      }
    } catch (error: any) {
      console.error("Failed to send message:", error);
      const errorMsg =
        error?.message?.includes("not a member") ||
        error?.message?.includes("403")
          ? "⚠️ You don't have access to this chat room. Only plan members can use the AI assistant."
          : "Sorry, I encountered an error.";
      setMessages((prev) => [...prev, { role: "bot", text: errorMsg }]);
    } finally {
      setIsLoading(false);
    }
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
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white text-gray-500 p-3 rounded-2xl rounded-tl-none shadow-sm text-sm italic">
              Thinking...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-3 bg-white border-t border-gray-100 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder={
            planId
              ? "Ask me to change schedule..."
              : "Save your plan first to use AI assistant"
          }
          disabled={!planId}
          className="flex-1 bg-gray-100 rounded-full px-4 py-2 text-sm outline-none focus:ring-1 focus:ring-green-400 disabled:opacity-50 disabled:cursor-not-allowed"
        />
        <button
          onClick={handleSend}
          disabled={!planId}
          className="bg-[#53B552] text-white p-2 rounded-full hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}

// ==========================================
// 4. MAIN PAGE (Inner Component)
// ==========================================
function ReviewPlanContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Store planId in state to persist across renders
  const [planId, setPlanId] = useState<string | null>(null);

  useEffect(() => {
    // Try to get from URL first
    const id = searchParams.get("id");
    console.log("🔍 Review Plan - useEffect running");
    console.log("   searchParams:", searchParams?.toString());
    console.log("   id from URL:", id);

    let finalId = id;

    // If no ID in URL, try to get from sessionStorage
    if (!id) {
      const storedId = sessionStorage.getItem("EDITING_PLAN_ID");
      console.log("   id from sessionStorage:", storedId);
      finalId = storedId;
    }

    // Update planId in state and sessionStorage
    if (finalId && finalId !== planId) {
      console.log("   ✅ Setting planId to:", finalId);
      setPlanId(finalId);
      sessionStorage.setItem("EDITING_PLAN_ID", finalId);
    } else if (!finalId && planId) {
      console.log("   ❌ Clearing planId");
      setPlanId(null);
      sessionStorage.removeItem("EDITING_PLAN_ID");
    }
  }, [searchParams, planId]);

  const toLocalISOString = (dateInput: string | Date) => {
    const date = new Date(dateInput);
    const offsetMs = date.getTimezoneOffset() * 60 * 1000;
    const localDate = new Date(date.getTime() - offsetMs);
    return localDate.toISOString().slice(0, 19); // Cắt bỏ phần milliseconds và chữ Z
  };

  // ✅ Helper để chuyển date thành format "YYYY-MM-DD" (chỉ date, không có time)
  const toDateOnlyString = (dateInput: string | Date) => {
    const date = new Date(dateInput);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  };

  // --- HELPER: Phân bố activities trên các ngày trong trip ---
  const distributeActivitiesAcrossDays = (
    activities: PlanActivity[],
    startDateStr: string,
    endDateStr?: string
  ): PlanActivity[] => {
    if (activities.length === 0) return activities;

    const startDate = new Date(startDateStr);
    const endDate = endDateStr ? new Date(endDateStr) : new Date(startDateStr);

    // Tính số ngày trong trip
    const daysInTrip =
      Math.floor(
        (endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)
      ) + 1;

    // Phân bố activities - chỉ điều chỉnh ngày, GIỮ NGUYÊN time slot
    return activities.map((activity, index) => {
      // Xác định ngày (phân bố đều)
      const dayOffset = Math.min(index % daysInTrip, daysInTrip - 1);
      const activityDate = new Date(startDate);
      activityDate.setDate(activityDate.getDate() + dayOffset);

      // Giữ nguyên time slot từ activity gốc
      const timeSlot = activity.time_slot || "Morning";

      // Set giờ ảo dựa trên time slot gốc để dễ sort sau này
      if (timeSlot === "Morning") activityDate.setHours(9, 0, 0);
      else if (timeSlot === "Afternoon") activityDate.setHours(14, 0, 0);
      else activityDate.setHours(19, 0, 0);

      return {
        ...activity,
        date: toLocalISOString(activityDate),
        time_slot: timeSlot,
      };
    });
  };

  // --- STATE ---
  const [isAiProcessing, setIsAiProcessing] = useState(false);
  const [aiStepIndex, setAiStepIndex] = useState(0);
  const [progress, setProgress] = useState(0);

  const [isSaving, setIsSaving] = useState(false);
  const [activities, setActivities] = useState<PlanActivity[]>([]);

  // ✅ Wrap setActivities to log all updates
  const setActivitiesWithLogging = (
    newActivities: PlanActivity[] | ((prev: PlanActivity[]) => PlanActivity[])
  ) => {
    console.log("🔄 setActivities called:", {
      type: typeof newActivities === "function" ? "function" : "direct",
      newLength:
        typeof newActivities === "function" ? "computed" : newActivities.length,
      stack: new Error().stack?.split("\n")[2]?.trim(), // Show caller
    });

    if (typeof newActivities === "function") {
      setActivities((prev) => {
        const result = newActivities(prev);
        console.log("  📊 Function result:", {
          prevLength: prev.length,
          newLength: result.length,
          first: result[0]?.title,
        });
        return result;
      });
    } else {
      console.log("  📊 Direct set:", {
        length: newActivities.length,
        first: newActivities[0]?.title,
      });
      setActivities(newActivities);
    }
  };

  const [activeId, setActiveId] = useState<string | number | null>(null);
  const activitiesRef = useRef<PlanActivity[]>([]); // Ref to always have latest activities

  // AI Generation States
  const [isAIGenerating, setIsAIGenerating] = useState(false);
  const [aiGenerationDone, setAiGenerationDone] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const aiGenerationAttemptedRef = useRef(false); // Track if AI generation was attempted
  const aiResultsSetRef = useRef(false); // ✅ Track if AI results were just set (prevent overwrite)
  const initialLoadDoneRef = useRef(false); // ✅ Track if initial data load completed

  const [planInfo, setPlanInfo] = useState({
    name: "My Awesome Trip",
    date: new Date().toISOString().split('T')[0], // YYYY-MM-DD format
    end_date: new Date().toISOString().split('T')[0],
    budget: 0,
  });
  const [isEditingHeader, setIsEditingHeader] = useState(false);

  // Member Management State
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [planOwnerId, setPlanOwnerId] = useState<number | null>(null);
  const [isOwner, setIsOwner] = useState(false);
  const [showMemberModal, setShowMemberModal] = useState(false);
  const [members, setMembers] = useState<PlanMemberDetail[]>([]); // ✅ Store full member objects

  // Split Screen State
  const [isChatOpen, setIsChatOpen] = useState(true); // ✅ Mở mặc định để show gợi ý
  const [planHeightPercent, setPlanHeightPercent] = useState(100);
  const containerRef = useRef<HTMLDivElement>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  // Load current user
  useEffect(() => {
    const loadUser = async () => {
      try {
        const user = await api.getUserProfile();
        setCurrentUser(user);
      } catch (error) {
        console.error("Failed to load user profile:", error);
      }
    };
    loadUser();
  }, []);

  // Clear AI generation flags on mount (run once)
  useEffect(() => {
    console.log("🧹 Clearing AI generation flags on mount");
    sessionStorage.removeItem("ai_generated_temp_plan");
    if (planId) {
      sessionStorage.removeItem(`ai_generated_plan_${planId}`);
    }
  }, []); // ✅ Empty deps - run once on mount

  // Check ownership when user or plan owner changes
  useEffect(() => {
    // ✅ If creating new plan (no planId), user is always owner
    if (!planId) {
      setIsOwner(true);
      return;
    }

    if (currentUser && planOwnerId) {
      const isUserOwner = currentUser.id === planOwnerId;
      setIsOwner(isUserOwner);
      console.log(`🔐 Permission check: ${isUserOwner ? "OWNER" : "MEMBER"}`);
    }
  }, [currentUser, planOwnerId, planId]);

  const getTimeSlot = (dateString?: string, timeStr?: string) => {
    // ✅ Ưu tiên dùng time field từ backend, nếu không thì tính từ dateString
    if (timeStr) {
      const hour = parseInt(timeStr.split(":")[0]);
      if (hour >= 18) return "Evening";
      if (hour >= 12) return "Afternoon";
      return "Morning";
    }

    if (!dateString) return "Morning"; // Mặc định
    const date = new Date(dateString);
    const hour = date.getHours();

    if (hour >= 18) return "Evening";
    if (hour >= 12) return "Afternoon";
    return "Morning";
  };

  // --- INIT DATA ---
  useEffect(() => {
    console.log("🔄 INIT DATA useEffect triggered", {
      planId,
      initialLoadDone: initialLoadDoneRef.current,
    });

    // ✅ Prevent multiple loads - only load once
    if (initialLoadDoneRef.current) {
      console.log("⏭️ Initial load already done, skipping");
      return;
    }

    const loadPlanDetail = async (id: string) => {
      try {
        setIsAiProcessing(true);

        // 1. Gọi API lấy danh sách
        const allPlans = await api.getPlans();
        const currentPlan = allPlans.find((p) => p.id === Number(id));

        if (currentPlan) {
          console.log(`📋 Loaded plan ${id}:`, currentPlan);
          console.log(`   - Destinations: ${currentPlan.activities?.length}`);
          currentPlan.activities?.forEach((act, idx) => {
            console.log(
              `     ${idx + 1}. ${act.title} | Date: ${
                act.date?.split("T")[0]
              } | Slot: ${act.time_slot}`
            );
          });

          // Set owner ID and check permission
          if (currentPlan.user_id) {
            setPlanOwnerId(currentPlan.user_id);
            console.log(`👤 Plan owner ID: ${currentPlan.user_id}`);
          }

          // Map dữ liệu cơ bản
          const apiPlanInfo = {
            name: currentPlan.destination,
            date: currentPlan.date,
            end_date: currentPlan.end_date || currentPlan.date,
            budget: currentPlan.budget_limit || currentPlan.budget || 0,
          };

          let apiActivities = currentPlan.activities;

          // 2. CHECK SESSION: Gộp địa điểm mới thêm (nếu có)
          const rawData = sessionStorage.getItem(STORAGE_KEY_RAW);
          if (rawData) {
            try {
              // --- FIX LỖI TẠI ĐÂY ---
              // Khai báo kiểu dữ liệu mở rộng có thêm visit_date
              type StoredPlace = PlaceDetails & { visit_date?: string };

              const rawList: StoredPlace[] = JSON.parse(rawData);
              // -----------------------

              console.log(`🔍 Checking for new destinations...`);
              console.log(`   - rawList count: ${rawList.length}`);
              console.log(`   - apiActivities count: ${apiActivities.length}`);

              // Lọc địa điểm mới chưa có trong list cũ
              const newItems = rawList.filter((raw) => {
                const isNew = !apiActivities.some((act) => {
                  // ✅ Extract place_id from act.id (remove suffix like "-0", "-1")
                  let actPlaceId = String(act.id);
                  const lastDashIndex = actPlaceId.lastIndexOf("-");
                  if (lastDashIndex !== -1) {
                    const suffix = actPlaceId.substring(lastDashIndex + 1);
                    if (!isNaN(Number(suffix))) {
                      actPlaceId = actPlaceId.substring(0, lastDashIndex);
                    }
                  }
                  const match = actPlaceId === raw.place_id;
                  if (match) {
                    console.log(
                      `     ⏭️ Skipping ${raw.name} (already exists)`
                    );
                  }
                  return match;
                });
                if (isNew) {
                  console.log(`     ➕ Found new: ${raw.name}`);
                }
                return isNew;
              });

              console.log(`   ✅ New items to add: ${newItems.length}`);

              // ✅ Đọc slot đã chọn từ sessionStorage (nếu có)
              let selectedDate = apiPlanInfo.date;
              let selectedTimeSlot: "Morning" | "Afternoon" | "Evening" =
                "Morning";

              const selectedSlotData =
                sessionStorage.getItem("selected_add_slot");
              if (selectedSlotData) {
                try {
                  const slot = JSON.parse(selectedSlotData);
                  if (slot.date) selectedDate = slot.date;
                  if (slot.time_slot) selectedTimeSlot = slot.time_slot;
                  console.log(
                    `✅ Using selected slot: ${selectedDate} ${selectedTimeSlot}`
                  );
                } catch (e) {
                  console.error("Error parsing selected_add_slot:", e);
                }
              }

              // --- SỬA ĐOẠN MAP NÀY ---
              const newActivitiesList = newItems.map((place) => {
                // ✅ Dùng slot đã chọn thay vì default
                let assignedSlot = selectedTimeSlot;
                let assignedDate = toLocalISOString(new Date(selectedDate)); // ← Convert to ISO

                // Nếu place có visit_date riêng (từ backend), ưu tiên dùng nó
                if (place.visit_date) {
                  assignedDate = place.visit_date;
                  assignedSlot = getTimeSlot(place.visit_date) as
                    | "Morning"
                    | "Afternoon"
                    | "Evening";
                }

                console.log(
                  `   📍 New activity: ${place.name} → Date: ${
                    assignedDate.split("T")[0]
                  } | Slot: ${assignedSlot}`
                );

                return {
                  id: place.place_id,
                  original_id: place.place_id, // ✅ Preserve original ID for AI matching
                  title: place.name,
                  address: place.formatted_address,
                  image_url: place.photos?.[0]?.photo_url || "",
                  time_slot: assignedSlot,
                  date: assignedDate,
                  type: place.types?.[0] || "place",
                  order_in_day: 999,
                };
              });
              // ------------------------

              if (newActivitiesList.length > 0) {
                // ❌ KHÔNG distribute activities mới - chỉ set mặc định vào Day 1 Morning
                // Người dùng sẽ kéo thả để arrange theo ý
                apiActivities = [...apiActivities, ...newActivitiesList];

                // ✅ Xóa selected_add_slot sau khi đã merge xong
                sessionStorage.removeItem("selected_add_slot");
              }
            } catch (e) {
              console.error("Error merging raw data:", e);
            }
          }

          // Cập nhật State
          setPlanInfo(apiPlanInfo);
          setActivities(apiActivities);

          // Lưu ngược lại Session để giữ đồng bộ
          sessionStorage.setItem(
            STORAGE_KEY_INFO,
            JSON.stringify({
              name: apiPlanInfo.name,
              start_date: apiPlanInfo.date,
              end_date: apiPlanInfo.end_date,
              budget: apiPlanInfo.budget,
            })
          );
          sessionStorage.setItem(
            STORAGE_KEY_STRUCTURED,
            JSON.stringify(apiActivities)
          );

          // Load plan members
          try {
            const membersResponse = await api.getPlanMembers(Number(id));
            // Backend now returns { plan_id, members: [...] } with full member details
            const loadedMembers = membersResponse.members || [];
            setMembers(loadedMembers);
            console.log(`👥 Loaded ${loadedMembers.length} member(s)`);

            // ✅ FALLBACK: If no members and current user is owner, auto-add as owner
            if (loadedMembers.length === 0) {
              console.warn(
                "⚠️ Plan has no members! Attempting to add current user as owner..."
              );
              try {
                // Get current user ID
                let currentUserId = 0;
                const storedUser = localStorage.getItem("user_info");
                if (storedUser) {
                  currentUserId = JSON.parse(storedUser).id;
                } else {
                  const profile = await api.getUserProfile();
                  currentUserId = profile.id;
                  localStorage.setItem("user_info", JSON.stringify(profile));
                }

                // Add current user as owner using correct API format
                await api.addPlanMembersWithRoles(Number(id), [
                  { user_id: currentUserId, role: "owner" },
                ]);

                // Reload members
                const updatedResponse = await api.getPlanMembers(Number(id));
                setMembers(updatedResponse.members || []);
                console.log("✅ Successfully added current user as owner");
              } catch (addError) {
                console.error("Failed to auto-add owner:", addError);
              }
            }
          } catch (error) {
            console.error("Failed to load members:", error);
          }
        }
      } catch (error) {
        console.error("Error loading plan:", error);
      } finally {
        setIsAiProcessing(false);
      }
    };

    // === LOGIC ĐIỀU HƯỚNG CHÍNH ===
    if (planId) {
      // EDIT MODE
      loadPlanDetail(planId);
    } else {
      // CREATE MODE
      const storedInfo = sessionStorage.getItem(STORAGE_KEY_INFO);
      if (storedInfo) {
        try {
          const parsed = JSON.parse(storedInfo);
          const today = new Date().toISOString().split('T')[0];
          setPlanInfo({
            name: parsed.name || "My Trip",
            date: parsed.start_date || today,
            end_date: parsed.end_date || parsed.start_date || today,
            budget: parsed.budget || 0,
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

      // ✅ Mark initial load as complete
      initialLoadDoneRef.current = true;
      console.log("✅ Initial load completed");
    }
  }, [planId]);

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
    console.log("📂 loadDataFromStorage called");

    // ✅ Don't overwrite if AI just set results
    if (aiResultsSetRef.current) {
      console.log("⏭️ Skipping loadDataFromStorage - AI results just set");
      aiResultsSetRef.current = false; // Reset flag
      return;
    }

    const rawData = sessionStorage.getItem(STORAGE_KEY_RAW);
    const storedActivities = sessionStorage.getItem(STORAGE_KEY_STRUCTURED);
    const storedInfo = sessionStorage.getItem(STORAGE_KEY_INFO);
    const selectedSlot = sessionStorage.getItem("selected_add_slot");

    // Lấy thông tin plan để biết date range
    let planStartDate = planInfo.date;
    let planEndDate = planInfo.end_date;

    // Lấy slot được chọn (nếu có)
    let selectedDate = planStartDate;
    let selectedTimeSlot: "Morning" | "Afternoon" | "Evening" = "Morning";

    if (selectedSlot) {
      try {
        const slot = JSON.parse(selectedSlot);
        selectedDate = slot.date;
        selectedTimeSlot = slot.time_slot;
        // ⚠️ KHÔNG xóa ngay - để logic merge trong useEffect load plan cũng đọc được
        // sessionStorage.removeItem("selected_add_slot");
      } catch (e) {
        console.error("Error parsing selected slot:", e);
      }
    }

    if (storedInfo) {
      try {
        const info = JSON.parse(storedInfo);
        planStartDate = info.start_date || planInfo.date;
        planEndDate = info.end_date || planInfo.end_date;
      } catch (e) {
        console.error("Error parsing stored info:", e);
      }
    }

    if (storedActivities) {
      // ✅ Load từ STORAGE_KEY_STRUCTURED (activities đã arrange với date/time_slot)
      let currentList: PlanActivity[] = JSON.parse(storedActivities);

      // Nhưng cần check xem có new items từ add_destinations không
      if (rawData) {
        const rawList: PlaceDetails[] = JSON.parse(rawData);
        const newItems = rawList.filter((raw) => {
          return !currentList.some((act) => {
            // ✅ Extract place_id from act.id (remove suffix like "-0", "-1")
            let actPlaceId = String(act.id);
            const lastDashIndex = actPlaceId.lastIndexOf("-");
            if (lastDashIndex !== -1) {
              const suffix = actPlaceId.substring(lastDashIndex + 1);
              if (!isNaN(Number(suffix))) {
                actPlaceId = actPlaceId.substring(0, lastDashIndex);
              }
            }
            return actPlaceId === raw.place_id;
          });
        });

        // Thêm new items vào currentList với date/time_slot được chọn
        if (newItems.length > 0) {
          const newActivities = newItems.map((place) => ({
            id: place.place_id,
            original_id: place.place_id, // ✅ Preserve original ID for AI matching
            title: place.name,
            address: place.formatted_address,
            image_url: place.photos?.[0]?.photo_url || "",
            time_slot: selectedTimeSlot, // ✅ Dùng slot được chọn
            date: toLocalISOString(new Date(selectedDate)), // ✅ Dùng ngày được chọn
            type: place.types?.[0] || "place",
            order_in_day: 999,
          }));

          currentList = [...currentList, ...newActivities];
          // ✅ Update lại STORAGE_KEY_STRUCTURED với new items
          sessionStorage.setItem(
            STORAGE_KEY_STRUCTURED,
            JSON.stringify(currentList)
          );
        }
      }

      setActivities(currentList);
    } else if (rawData) {
      // Fallback: nếu không có structured, tạo từ raw (lần đầu)
      const rawList: PlaceDetails[] = JSON.parse(rawData);
      const initialActivities = rawList.map((place) => ({
        id: place.place_id,
        title: place.name,
        address: place.formatted_address,
        image_url: place.photos?.[0]?.photo_url || "",
        time_slot: "Morning" as const,
        date: toLocalISOString(planStartDate),
        type: place.types?.[0] || "place",
        order_in_day: 0,
      }));
      // Distribute activities across days (lần đầu tiên - CHỈ khi AI simulation)
      // ⚠️ CHỈ distribute nếu đây là lần đầu tạo plan (AI_SHOWN_KEY chưa set)
      const hasShownAI = sessionStorage.getItem(AI_SHOWN_KEY);
      if (!hasShownAI) {
        const distributedList = distributeActivitiesAcrossDays(
          initialActivities,
          planStartDate,
          planEndDate
        );
        setActivities(distributedList);
      } else {
        // Nếu đã distribute rồi, chỉ set như bình thường
        setActivities(initialActivities);
      }
    }
  };

  useEffect(() => {
    console.log("💾 Save activities to sessionStorage useEffect:", {
      activitiesLength: activities.length,
      firstActivity: activities[0]?.title,
    });

    if (activities.length > 0) {
      sessionStorage.setItem(
        STORAGE_KEY_STRUCTURED,
        JSON.stringify(activities)
      );

      const rawListForMap = activities.map((act) => {
        // ✅ Extract original place_id (remove suffix like "-0", "-1", etc.)
        let placeId = String(act.id);
        const lastDashIndex = placeId.lastIndexOf("-");
        if (lastDashIndex !== -1) {
          const suffix = placeId.substring(lastDashIndex + 1);
          if (!isNaN(Number(suffix))) {
            placeId = placeId.substring(0, lastDashIndex);
          }
        }

        return {
          place_id: placeId,
          name: act.title,
          formatted_address: act.address,
          photos: [{ photo_url: act.image_url }],
        };
      });
      sessionStorage.setItem(STORAGE_KEY_RAW, JSON.stringify(rawListForMap));
    }
  }, [activities]);

  // Sync activities to ref for AI generation
  useEffect(() => {
    activitiesRef.current = activities;
  }, [activities]);

  // ✅ DEBUG: Log whenever activities changes
  useEffect(() => {
    console.log("🔔 Activities state changed:", {
      length: activities.length,
      items: activities.map((a) => ({
        id: a.id,
        title: a.title,
        slot: a.time_slot,
      })),
    });
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
  const getDaysArray = (start: string, end: string) => {
    const arr = [];
    const dt = new Date(start);
    const endDt = new Date(end);

    while (dt <= endDt) {
      arr.push(new Date(dt).toISOString());
      dt.setDate(dt.getDate() + 1);
    }

    if (arr.length === 0) return [start];
    return arr;
  };
  const planDays = getDaysArray(planInfo.date, planInfo.end_date);

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
    if (!isOwner) {
      alert("Only plan owner can delete destinations");
      return;
    }
    if (confirm("Remove this place from plan?")) {
      setActivities((prev) => prev.filter((a) => a.id !== id));
    }
  };

  // ==========================================
  // AI PLAN GENERATION
  // ==========================================
  const generateAIPlan = useCallback(async () => {
    // Use ref to get latest activities
    const currentActivities = activitiesRef.current;

    // Check điều kiện
    if (
      currentActivities.length < 2 ||
      aiGenerationDone ||
      isAIGenerating ||
      aiGenerationAttemptedRef.current
    ) {
      console.log("⏭️ Skip AI generation:", {
        notEnoughActivities: currentActivities.length < 2,
        alreadyDone: aiGenerationDone,
        inProgress: isAIGenerating,
        attempted: aiGenerationAttemptedRef.current,
      });
      return;
    }

    // Mark as attempted immediately to prevent concurrent calls
    aiGenerationAttemptedRef.current = true;

    // Check sessionStorage để đảm bảo chỉ generate 1 lần
    const storageKey = planId
      ? `ai_generated_plan_${planId}`
      : `ai_generated_temp_plan`;
    const hasGenerated = sessionStorage.getItem(storageKey);

    if (hasGenerated === "true") {
      console.log("✅ Plan đã được AI generate trước đó");
      setAiGenerationDone(true);
      return;
    }

    console.log("🤖 Starting AI plan generation...");
    setIsAIGenerating(true);
    setAiError(null);

    try {
      // Helper to convert to YYYY-MM-DD
      const toDateString = (dateInput: any): string => {
        if (!dateInput) return new Date().toISOString().split("T")[0];
        const d =
          typeof dateInput === "string" ? new Date(dateInput) : dateInput;
        return d.toISOString().split("T")[0];
      };

      // Prepare plan data
      const planData = {
        place_name: planInfo?.name || "My Travel Plan",
        start_date: toDateString(planInfo?.date),
        end_date: toDateString(planInfo?.end_date || planInfo?.date),
        budget_limit: Number(planInfo?.budget) || 100000, // Default budget if not set
        destinations: currentActivities.map((activity, index) => {
          // Determine destination type
          let validType = "attraction";
          const typeLower = (activity.type || "").toLowerCase();
          if (typeLower.includes("restaurant") || typeLower.includes("food"))
            validType = "restaurant";
          else if (typeLower.includes("hotel") || typeLower.includes("lodging"))
            validType = "accommodation";
          else if (
            typeLower.includes("transit") ||
            typeLower.includes("station")
          )
            validType = "transport";

          return {
            destination_id: String(activity.original_id || activity.id),
            destination_type: validType,
            visit_date: toDateString(activity.date || planInfo?.date),
            order_in_day: index + 1, // Start from 1, not 0
            time_slot: (activity.time_slot || "morning").toLowerCase(),
            note: activity.address || "",
            estimated_cost: 0,
          };
        }),
      };

      console.log("📤 Sending to AI:", JSON.stringify(planData, null, 2));

      // Call API
      const result = await api.generatePlan(planData);

      console.log("📥 AI Response:", result);

      // Validate response
      if (!result || !result.success) {
        throw new Error(result?.message || "AI generation failed");
      }

      // Check if we have destinations in response
      if (
        result.plan?.destinations &&
        Array.isArray(result.plan.destinations)
      ) {
        console.log("🔍 Mapping AI destinations to activities:", {
          aiDestinations: result.plan.destinations.length,
          currentActivities: currentActivities.length,
        });

        // Map AI response back to activities
        const optimizedActivities = result.plan.destinations
          .map((dest: any, idx: number) => {
            // Find original activity to preserve all fields
            // Compare as strings since destination_id can be Google Place ID
            const original = currentActivities.find(
              (a) =>
                String(a.original_id || a.id) === String(dest.destination_id)
            );

            if (!original) {
              console.warn(
                `⚠️ Destination ${dest.destination_id} not found in original activities`,
                {
                  lookingFor: dest.destination_id,
                  availableIds: currentActivities.map((a) => ({
                    id: a.id,
                    original_id: a.original_id,
                    title: a.title,
                  })),
                }
              );
              return null;
            }

            // Merge AI data with original data
            return {
              ...original,
              date: dest.visit_date || original.date,
              order_in_day: dest.order_in_day ?? idx,
              // ✅ Capitalize time_slot from backend (morning → Morning)
              time_slot: dest.time_slot
                ? ((dest.time_slot.charAt(0).toUpperCase() +
                    dest.time_slot.slice(1)) as
                    | "Morning"
                    | "Afternoon"
                    | "Evening")
                : original.time_slot,
              time: dest.suggested_time || original.time,
              day: idx + 1,
            };
          })
          .filter(Boolean); // Remove nulls

        console.log("✨ Optimized activities result:", {
          count: optimizedActivities.length,
          sample: optimizedActivities[0],
        });

        // Only update if we got valid results
        if (optimizedActivities.length > 0) {
          console.log("📝 Setting activities to:", optimizedActivities);
          aiResultsSetRef.current = true; // ✅ Mark that AI results are being set
          setActivities(optimizedActivities as PlanActivity[]);

          // Mark as generated
          sessionStorage.setItem(storageKey, "true");
          setAiGenerationDone(true);

          console.log("✅ AI plan generation successful!");
        } else {
          console.error(
            "❌ No valid destinations after mapping - keeping original plan"
          );
          // Keep original plan instead of clearing
          sessionStorage.setItem(storageKey, "true");
          setAiGenerationDone(true);
        }
      } else {
        console.log("ℹ️ AI không thay đổi thứ tự, giữ nguyên plan hiện tại");
        sessionStorage.setItem(storageKey, "true");
        setAiGenerationDone(true);
      }

      // Log warnings if any
      if (result.warnings && result.warnings.length > 0) {
        console.warn("⚠️ AI Warnings:", result.warnings);
      }
    } catch (error: any) {
      console.error("❌ AI generation error:", error);
      setAiError(error.message || "Failed to generate AI plan");

      // Don't block user - they can still use manual plan
      // Just log the error and continue
    } finally {
      setIsAIGenerating(false);
    }
  }, []); // Empty deps - function will use latest activities via closure

  // Auto-trigger AI plan generation on initial load
  useEffect(() => {
    console.log("🔍 Auto-trigger AI useEffect running:", {
      activitiesLength: activities.length,
      aiGenerationDone,
      isAIGenerating,
      isAiProcessing,
      planId,
    });

    // Only run if we have activities and haven't generated yet
    if (
      activities.length >= 2 &&
      !aiGenerationDone &&
      !isAIGenerating &&
      !isAiProcessing // Don't run during fake AI animation
    ) {
      console.log("🤖 Auto-triggering AI plan generation...", {
        activitiesCount: activities.length,
        planId,
        aiGenerationDone,
        isAIGenerating,
        isAiProcessing,
      });
      generateAIPlan();
    } else {
      console.log("⏭️ Skip auto AI generation:", {
        activitiesCount: activities.length,
        planId,
        aiGenerationDone,
        isAIGenerating,
        isAiProcessing,
        reason:
          activities.length < 2
            ? "Not enough activities"
            : aiGenerationDone
            ? "Already generated"
            : isAIGenerating
            ? "Currently generating"
            : isAiProcessing
            ? "AI animation in progress"
            : "Unknown",
      });
    }
  }, [
    planId,
    activities.length,
    aiGenerationDone,
    isAIGenerating,
    isAiProcessing,
    generateAIPlan,
  ]);

  const handleAddPlaceToSlot = (dayStr?: string, timeSlot?: string) => {
    if (!isOwner && planId) {
      alert("Only plan owner can add destinations");
      return;
    }
    // ✅ Lưu ngày/buổi được chọn vào storage để add_destinations biết
    if (dayStr && timeSlot) {
      sessionStorage.setItem(
        "selected_add_slot",
        JSON.stringify({ date: dayStr, time_slot: timeSlot })
      );
    }

    // ✅ Also save planId so add_destinations knows which plan to add to
    if (planId) {
      sessionStorage.setItem("EDITING_PLAN_ID", planId);
      console.log(`📎 Navigating to add_destinations with planId: ${planId}`);
      router.push(`/planning_page/add_destinations?id=${planId}`);
    } else {
      router.push("/planning_page/add_destinations");
    }
  };

  // src/app/(main)/planning_page/review_plan/page.tsx

  const handleSaveToBackend = async () => {
    // ✅ Validate tối thiểu 2 địa điểm
    if (activities.length < 2) {
      alert(
        `You need at least 2 destinations in your plan! (Current: ${activities.length})`
      );
      return;
    }

    console.log("📊 Current activities state before save:");
    activities.forEach((act, idx) => {
      console.log(
        `   ${idx + 1}. ${act.title} | Date: ${
          act.date?.split("T")[0]
        } | Slot: ${act.time_slot}`
      );
    });

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

        let realDestinationId = String(act.id);
        const lastDashIndex = realDestinationId.lastIndexOf("-");
        if (lastDashIndex !== -1) {
          const suffix = realDestinationId.substring(lastDashIndex + 1);
          if (!isNaN(Number(suffix))) {
            realDestinationId = realDestinationId.substring(0, lastDashIndex);
          }
        }

        const fallbackDate = planInfo.date || new Date().toISOString().split('T')[0];
        const visitDate = act.date
          ? toDateOnlyString(act.date)
          : toDateOnlyString(new Date(fallbackDate));

        const payload = {
          id: 0,
          destination_id: realDestinationId,
          destination_type: validType,
          type: validType,
          visit_date: visitDate,
          time_slot: act.time_slot.toLowerCase() as
            | "morning"
            | "afternoon"
            | "evening",
          order_in_day: index + 1,
          note: act.title,
          url: act.image_url,
          estimated_cost: 0,
        };

        console.log(
          `📤 Activity ${index + 1}: ${
            act.title
          } | Date: ${visitDate} | Slot: ${act.time_slot}`
        );

        return payload;
      });

      console.log("📦 Total destinations to save:", destinationsPayload.length);

      // 3. Chuẩn bị dữ liệu để gửi
      const today = new Date().toISOString().split('T')[0];
      const requestData = {
        place_name: planInfo.name,
        start_date: planInfo.date || today,
        end_date: planInfo.end_date || planInfo.date || today,
        budget_limit: Number(budget) > 0 ? Number(budget) : 1,
        destinations: destinationsPayload,
      };

      // === LOGIC XỬ LÝ ===
      if (planId) {
        // --- CHẾ ĐỘ EDIT ---
        console.log(`💾 EDITING PLAN ${planId}`);
        console.log(`   ✅ planId exists: "${planId}"`);
        console.log(`   - Activities to save: ${activities.length}`);
        activities.forEach((act, idx) => {
          console.log(
            `     ${idx + 1}. ${act.title} | Date: ${
              act.date?.split("T")[0]
            } | Slot: ${act.time_slot}`
          );
        });

        console.log(`📤 Calling updatePlan API...`);
        await api.updatePlan(Number(planId), {
          place_name: requestData.place_name,
          start_date: requestData.start_date,
          end_date: requestData.end_date,
          budget_limit: requestData.budget_limit,
          destinations: requestData.destinations,
        });
        console.log(`✅ updatePlan API returned successfully`);

        alert("Plan updated successfully!");
      } else {
        // --- CHẾ ĐỘ CREATE MỚI ---
        console.log(`📝 CREATING NEW PLAN`);
        console.log(`   ❌ planId is null/undefined`);
        console.log("Creating new plan...");
        await api.createPlan(requestData);
        console.log(`✅ createPlan API returned successfully`);
        alert("Plan created successfully!");
      }

      // 4. Dọn dẹp và chuyển hướng
      sessionStorage.removeItem(STORAGE_KEY_RAW);
      sessionStorage.removeItem(STORAGE_KEY_STRUCTURED);
      sessionStorage.removeItem(AI_SHOWN_KEY);
      sessionStorage.removeItem(STORAGE_KEY_INFO);
      sessionStorage.removeItem("selected_add_slot");
      sessionStorage.removeItem("EDITING_PLAN_ID"); // ← Clear planId after save

      // ✅ Navigate to transport selection page
      router.push(`/planning_page/transport_selection?id=${planId}`);
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
      <div className="h-screen w-full flex justify-center bg-gray-50">
        <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col items-center justify-center p-8 relative overflow-hidden">
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
              <button onClick={() => router.back()}>
                <ChevronLeft className="text-gray-400" />
              </button>
              <h1
                className={`${jost.className} text-gray-800 font-bold text-lg`}
              >
                Review Plan
              </h1>
              {!isOwner && planId && (
                <span className="ml-2 text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                  View Only
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              {planId && (
                <button
                  onClick={() => setShowMemberModal(true)}
                  className="flex items-center gap-1 font-bold text-sm px-3 py-2 rounded-full text-blue-600 bg-blue-50 hover:bg-blue-100 transition-all"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
                    />
                  </svg>
                  Members
                </button>
              )}
              <button
                onClick={() => {
                  if (activities.length < 2) {
                    alert(
                      `Add at least ${
                        2 - activities.length
                      } more destination(s)`
                    );
                    return;
                  }
                  router.push("/planning_page/transport_selection");
                }}
                disabled={activities.length < 2}
                className={`flex items-center gap-1 font-bold text-sm px-3 py-2 rounded-full transition-all ${
                  activities.length < 2
                    ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                    : "text-white bg-[#53B552] hover:bg-green-600"
                }`}
                title={
                  activities.length < 2
                    ? `Add at least ${
                        2 - activities.length
                      } more destination(s)`
                    : "Next: Choose transport"
                }
              >
                Next
                <ChevronRight size={16} />
              </button>
            </div>
          </div>

          {/* AI GENERATION BANNER */}
          {isAIGenerating && (
            <div className="bg-linear-to-r from-green-50 to-blue-50 px-4 py-3 border-b border-green-100">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center">
                  <Sparkles className="text-[#53B552] w-4 h-4 animate-spin" />
                </div>
                <div className="flex-1">
                  <p
                    className={`${jost.className} text-sm font-semibold text-gray-800`}
                  >
                    AI is optimizing your plan...
                  </p>
                  <p className="text-xs text-gray-500">
                    Analyzing best routes and timing
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* AI ERROR BANNER */}
          {aiError && (
            <div className="bg-red-50 px-4 py-3 border-b border-red-100">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center">
                  <svg
                    className="w-4 h-4 text-red-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </div>
                <div className="flex-1">
                  <p
                    className={`${jost.className} text-sm font-semibold text-red-800`}
                  >
                    AI optimization failed
                  </p>
                  <p className="text-xs text-red-600">{aiError}</p>
                </div>
                <button
                  onClick={() => setAiError(null)}
                  className="text-red-400 hover:text-red-600"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            </div>
          )}

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
                      onClick={() => isOwner && setIsEditingHeader(true)}
                      className={`${
                        jost.className
                      } text-2xl font-bold text-gray-800 ${
                        isOwner ? "cursor-pointer hover:text-green-600" : ""
                      }`}
                    >
                      {planInfo.name}{" "}
                      {isOwner && (
                        <Pencil size={14} className="inline text-gray-300" />
                      )}
                    </h2>
                  )}
                  <p className="text-gray-500 text-sm flex items-center gap-2 mt-1">
                    <CalendarDays size={16} />{" "}
                    <span>
                      {planInfo.date ? new Date(planInfo.date).toLocaleDateString() : 'No date'}
                      <span className="mx-2 text-gray-300">→</span>
                      {planInfo.end_date ? new Date(planInfo.end_date).toLocaleDateString() : 'No date'}
                    </span>
                  </p>
                </div>
              </div>
            </div>

            {/* ⚠️ WARNING: Ít hơn 2 địa điểm */}
            {activities.length < 2 && (
              <div className="mb-4 bg-red-50 border-l-4 border-red-400 p-4 rounded">
                <p
                  className={`${jost.className} text-red-700 font-bold text-sm`}
                >
                  ⚠️ Minimum 2 destinations required
                </p>
                <p className="text-red-600 text-xs mt-1">
                  You currently have {activities.length} destination
                  {activities.length !== 1 ? "s" : ""}. Please add at least{" "}
                  <strong>{2 - activities.length}</strong> more to save your
                  plan.
                </p>
              </div>
            )}

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

                  // ✅ DEBUG: Log filtering for this day
                  const morningItems = activities.filter(
                    (a) =>
                      a.time_slot === "Morning" &&
                      (a.date?.split("T")[0] === dayStr ||
                        (!a.date && dayStr === planDays[0].split("T")[0]))
                  );
                  console.log(`📅 Day ${idx + 1} (${dayStr}) - Morning:`, {
                    totalActivities: activities.length,
                    morningCount: morningItems.length,
                    morningItems: morningItems.map((a) => ({
                      title: a.title,
                      date: a.date,
                      slot: a.time_slot,
                    })),
                  });

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
                            (a) =>
                              a.time_slot === "Morning" &&
                              (a.date?.split("T")[0] === dayStr ||
                                (!a.date &&
                                  dayStr === planDays[0].split("T")[0]))
                          )}
                          onDelete={handleDeleteActivity}
                          onAddPlace={() =>
                            handleAddPlaceToSlot(dayStr, "Morning")
                          }
                        />
                        <TimeSlotContainer
                          id={`${dayStr}_Afternoon`}
                          title="Afternoon"
                          icon={<Sunset size={18} className="text-red-400" />}
                          items={activities.filter(
                            (a) =>
                              a.time_slot === "Afternoon" &&
                              (a.date?.split("T")[0] === dayStr ||
                                (!a.date &&
                                  dayStr === planDays[0].split("T")[0]))
                          )}
                          onDelete={handleDeleteActivity}
                          onAddPlace={() =>
                            handleAddPlaceToSlot(dayStr, "Afternoon")
                          }
                        />
                        <TimeSlotContainer
                          id={`${dayStr}_Evening`}
                          title="Evening"
                          icon={<Moon size={18} className="text-purple-400" />}
                          items={activities.filter(
                            (a) =>
                              a.time_slot === "Evening" &&
                              (a.date?.split("T")[0] === dayStr ||
                                (!a.date &&
                                  dayStr === planDays[0].split("T")[0]))
                          )}
                          onDelete={handleDeleteActivity}
                          onAddPlace={() =>
                            handleAddPlaceToSlot(dayStr, "Evening")
                          }
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
              <DragOverlay dropAnimation={dropAnimationConfig}>
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
            <ChatWindow
              onClose={handleToggleChat}
              planId={planId ? Number(planId) : null}
            />
          </div>
        )}

        {/* === MEMBER MANAGEMENT MODAL === */}
        {showMemberModal && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
            <div className="bg-white rounded-3xl p-6 w-full max-w-md shadow-2xl transform transition-all scale-100">
              <div className="flex justify-between items-center mb-6">
                <h2
                  className={`${jost.className} text-2xl font-bold text-gray-800`}
                >
                  Plan Members
                </h2>
                <button
                  onClick={() => setShowMemberModal(false)}
                  className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <X size={24} className="text-gray-500" />
                </button>
              </div>

              {!isOwner && (
                <div className="mb-6 p-4 bg-[#E3F1E4] rounded-2xl border border-[#53B552]/20 flex gap-3 items-start">
                  <div className="p-2 bg-white rounded-full shrink-0">
                    <Users size={16} className="text-[#53B552]" />
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    You are viewing this plan as a member. Only the owner can
                    manage members.
                  </p>
                </div>
              )}

              {/* ❌ REMOVED: Add Member by Email section */}

              <div>
                <h3
                  className={`${jost.className} text-sm font-bold text-gray-700 mb-3 ml-1 flex items-center gap-2`}
                >
                  Current Members{" "}
                  <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs">
                    {members.length}
                  </span>
                </h3>

                <div className="space-y-3 max-h-[300px] overflow-y-auto pr-1 custom-scrollbar">
                  {members.length === 0 ? (
                    <div className="text-center py-8 bg-gray-50 rounded-2xl border border-dashed border-gray-200">
                      <Users size={32} className="mx-auto text-gray-300 mb-2" />
                      <p className="text-sm text-gray-400">
                        No members added yet
                      </p>
                    </div>
                  ) : (
                    members.map((member) => (
                      <div
                        key={member.user_id}
                        className="flex items-center justify-between p-3 bg-white border border-gray-100 rounded-2xl shadow-sm hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-linear-to-br from-gray-100 to-gray-200 rounded-full flex items-center justify-center border-2 border-white shadow-sm">
                            <span
                              className={`${jost.className} font-bold text-gray-500`}
                            >
                              {member.username?.charAt(0).toUpperCase() ||
                                member.user_id.toString().slice(0, 2)}
                            </span>
                          </div>
                          <div>
                            <p
                              className={`${jost.className} font-bold text-gray-800 text-sm`}
                            >
                              {member.username ||
                                member.email ||
                                `User #${member.user_id}`}
                            </p>
                            {member.role === "owner" ? (
                              <span className="text-[10px] font-bold text-[#53B552] bg-[#E3F1E4] px-2 py-0.5 rounded-full inline-block mt-0.5">
                                Owner
                              </span>
                            ) : (
                              <span className="text-[10px] text-gray-400">
                                Member
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Action buttons */}
                        {isOwner && member.role !== "owner" ? (
                          // Owner can kick members
                          <button
                            onClick={async () => {
                              if (!planId) return;
                              if (
                                !confirm(
                                  `Remove ${member.username || "this member"}?`
                                )
                              )
                                return;
                              try {
                                await api.removePlanMembers(Number(planId), [
                                  member.user_id,
                                ]);
                                const membersResponse =
                                  await api.getPlanMembers(Number(planId));
                                setMembers(membersResponse.members || []);
                                alert("Member removed successfully!");
                              } catch (error) {
                                console.error(
                                  "Failed to remove member:",
                                  error
                                );
                                alert("Failed to remove member");
                              }
                            }}
                            className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-all"
                            title="Remove member"
                          >
                            <Trash2 size={18} />
                          </button>
                        ) : !isOwner && member.user_id === currentUser?.id ? (
                          // Member can leave plan (except owner)
                          <button
                            onClick={async () => {
                              if (!planId) return;
                              if (
                                !confirm(
                                  "Are you sure you want to leave this plan?"
                                )
                              )
                                return;
                              try {
                                await api.leavePlan(Number(planId));
                                alert("You have left the plan successfully!");
                                // Redirect back to plans list
                                window.location.href =
                                  "/planning_page/showing_plan_page";
                              } catch (error) {
                                console.error("Failed to leave plan:", error);
                                alert("Failed to leave plan");
                              }
                            }}
                            className="px-3 py-1.5 text-xs font-bold text-red-500 hover:text-white hover:bg-red-500 border border-red-500 rounded-full transition-all"
                            title="Leave plan"
                          >
                            Leave
                          </button>
                        ) : null}
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ==========================================
// WRAPPER WITH SUSPENSE
// ==========================================
export default function ReviewPlanPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center w-full h-screen">
          Loading...
        </div>
      }
    >
      <ReviewPlanContent />
    </Suspense>
  );
}