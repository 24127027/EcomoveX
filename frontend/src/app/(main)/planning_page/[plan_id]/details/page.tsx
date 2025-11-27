"use client";

import React, { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
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
  DropAnimation,
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
  Check,
  X,
  Sun,
  Sunset,
  Moon,
  MapPin,
} from "lucide-react";
import { Jost, Roboto } from "next/font/google";
import {
  api,
  PlanActivity,
  TravelPlan,
  AutocompletePrediction,
} from "@/lib/api";
import Link from "next/link";
import router from "next/dist/shared/lib/router/router";

// --- FONTS ---
const roboto = Roboto({
  subsets: ["vietnamese"],
  weight: ["400", "500", "700"],
});
const jost = Jost({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

// --- HELPER: Session Token Generator ---
const generateSessionToken = () => {
  return Math.random().toString(36).substring(2) + Date.now().toString(36);
};

// --- COMPONENT: ITEM KÉO THẢ (Có tích hợp Suggestion) ---
interface SortableItemProps {
  activity: PlanActivity;
  onUpdate: (id: string | number, newTitle: string) => void;
}

function SortableItem({ activity, onUpdate }: SortableItemProps) {
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
    zIndex: isDragging ? 999 : "auto", // Đảm bảo item đang kéo nằm trên cùng
  };

  // --- STATE CHO LOGIC EDIT & SUGGESTION ---
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(activity.title);

  // Logic Autocomplete (Mang từ file AddDestinations sang)
  const [suggestions, setSuggestions] = useState<AutocompletePrediction[]>([]);
  const sessionTokenRef = useRef(generateSessionToken());

  // Reset lại title khi tắt chế độ edit
  const handleCancel = () => {
    setEditTitle(activity.title);
    setSuggestions([]);
    setIsEditing(false);
  };

  // Lưu thông tin
  const handleSave = () => {
    onUpdate(activity.id, editTitle);
    setIsEditing(false);
    sessionTokenRef.current = generateSessionToken(); // Reset token sau khi save
  };

  // Xử lý khi nhập liệu (Tìm kiếm gợi ý)
  const handleInputChange = async (value: string) => {
    setEditTitle(value);

    if (value.length > 2) {
      try {
        const res = await api.autocomplete({
          query: value,
          session_token: sessionTokenRef.current,
        });
        setSuggestions(res.predictions || []);
      } catch (err) {
        console.error(err);
      }
    } else {
      setSuggestions([]);
    }
  };

  // Xử lý khi chọn gợi ý
  const handleSelectSuggestion = (prediction: AutocompletePrediction) => {
    setEditTitle(prediction.description);
    setSuggestions([]);

    // Reset token ngay sau khi chọn xong (Logic của Google Maps)
    sessionTokenRef.current = generateSessionToken();
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`bg-white p-4 rounded-xl shadow-sm border mb-3 flex gap-3 items-center group relative touch-none ${
        isDragging
          ? "border-[#53B552] ring-2 ring-[#53B552]/20"
          : "border-gray-100"
      }`}
    >
      <div className="flex-1 min-w-0 relative">
        {" "}
        {/* Thêm relative để dropdown định vị theo div này */}
        {isEditing ? (
          <div className="flex items-center gap-2 relative">
            <div className="flex-1 relative">
              <input
                value={editTitle}
                onChange={(e) => handleInputChange(e.target.value)}
                className="w-full border-b border-[#53B552] outline-none text-gray-800 font-bold bg-transparent py-1"
                autoFocus
                placeholder="Enter location..."
              />

              {/* --- DROPDOWN GỢI Ý (SUGGESTIONS) --- */}
              {suggestions.length > 0 && (
                <div className="absolute top-full left-0 right-0 bg-white shadow-xl rounded-b-lg z-50 max-h-40 overflow-y-auto border border-gray-100 mt-1">
                  {suggestions.map((pred) => (
                    <div
                      key={pred.place_id}
                      onClick={() => handleSelectSuggestion(pred)}
                      className="p-2 hover:bg-green-50 cursor-pointer text-xs border-b border-gray-50 text-gray-600 truncate flex items-center gap-2"
                    >
                      <MapPin size={12} className="text-gray-400 shrink-0" />
                      {pred.description}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <button
              onClick={handleSave}
              className="text-[#53B552] hover:bg-green-50 p-1 rounded"
            >
              <Check size={16} />
            </button>
            <button
              onClick={handleCancel}
              className="text-gray-400 hover:bg-gray-100 p-1 rounded"
            >
              <X size={16} />
            </button>
          </div>
        ) : (
          <div className="flex justify-between items-center">
            <h3
              className={`${jost.className} font-bold text-gray-800 truncate`}
            >
              {activity.title}
            </h3>
            <button
              onClick={() => setIsEditing(true)}
              className="opacity-0 group-hover:opacity-100 transition-opacity text-gray-400 hover:text-[#53B552] p-1"
            >
              <Pencil size={14} />
            </button>
          </div>
        )}
      </div>

      {!isEditing && (
        <div
          {...attributes}
          {...listeners}
          className="cursor-grab text-gray-300 hover:text-gray-500 p-2 border-l border-gray-100 pl-3"
        >
          <GripVertical size={20} />
        </div>
      )}
    </div>
  );
}

// --- COMPONENT: VÙNG CHỨA (Container) ---
function TimeSlotContainer({
  id,
  title,
  icon,
  items,
  onUpdateItem,
}: {
  id: string;
  title: string;
  icon: React.ReactNode;
  items: PlanActivity[];
  onUpdateItem: any;
}) {
  const { setNodeRef } = useSortable({ id });

  return (
    <div
      ref={setNodeRef}
      className="bg-[#F9FAF9] p-3 rounded-2xl mb-4 border border-gray-200"
    >
      <div className="flex items-center gap-2 mb-3 px-1">
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
              onUpdate={onUpdateItem}
            />
          ))}
        </div>
      </SortableContext>
    </div>
  );
}

// --- MAIN PAGE ---
export default function PlanDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const planId = Number(params.plan_id);

  const [isLoading, setIsLoading] = useState(true);
  const [activities, setActivities] = useState<PlanActivity[]>([]);

  // Header Edit State
  const [isEditingHeader, setIsEditingHeader] = useState(false);
  const [planInfo, setPlanInfo] = useState({
    name: "",
    date: "",
    end_date: "",
  });

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const [activeId, setActiveId] = useState<string | number | null>(null);

  // Load Data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const aiDelay = new Promise((resolve) => setTimeout(resolve, 2000));
        const plans = await api.getPlans();
        const currentPlan = plans.find((p) => p.id === planId);
        await aiDelay;

        if (currentPlan) {
          setPlanInfo({
            name: currentPlan.destination,
            date: currentPlan.date,
            end_date: currentPlan.end_date || "",
          });
          setActivities(currentPlan.activities);
        }
      } catch (error) {
        console.error("Error:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [planId]);

  // --- LOGIC DRAG & DROP ---
  const findContainer = (id: string | number) => {
    if (["Morning", "Afternoon", "Evening"].includes(id as string)) return id;
    return activities.find((a) => a.id === id)?.time_slot;
  };

  const handleDragStart = (event: any) => setActiveId(event.active.id);

  const handleDragOver = (event: DragOverEvent) => {
    const { active, over } = event;
    const overId = over?.id;
    if (!overId || active.id === overId) return;

    const activeContainer = findContainer(active.id);
    const overContainer = findContainer(overId);

    if (
      !activeContainer ||
      !overContainer ||
      activeContainer === overContainer
    ) {
      return;
    }

    setActivities((prev) => {
      const activeIndex = prev.findIndex((i) => i.id === active.id);
      const overIndex = prev.findIndex((i) => i.id === overId);
      let newIndex;
      if (["Morning", "Afternoon", "Evening"].includes(overId as string)) {
        newIndex = prev.length + 1;
      } else {
        const isBelowOverItem =
          over &&
          active.rect.current.translated &&
          active.rect.current.translated.top > over.rect.top + over.rect.height;
        const modifier = isBelowOverItem ? 1 : 0;
        newIndex = overIndex >= 0 ? overIndex + modifier : prev.length + 1;
      }

      const newActivities = [...prev];
      newActivities[activeIndex] = {
        ...newActivities[activeIndex],
        time_slot: overContainer as "Morning" | "Afternoon" | "Evening",
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

  const handleUpdateItem = async (id: string | number, newTitle: string) => {
    setActivities((prev) =>
      prev.map((item) => (item.id === id ? { ...item, title: newTitle } : item))
    );
    try {
      await api.updatePlanDestination(id, { note: newTitle });
    } catch (e) {
      console.error(e);
    }
  };

  const handleSaveHeader = async () => {
    let newStartDate = planInfo.date;
    let newEndDate = planInfo.end_date;

    if (newStartDate && newEndDate) {
      if (newStartDate > newEndDate) {
        const temp = newStartDate;
        newStartDate = newEndDate;
        newEndDate = temp;

        setPlanInfo((prev) => ({
          ...prev,
          date: newStartDate,
          end_date: newEndDate,
        }));
        alert("Start date cannot be after End date. We swapped them for you!");
      }
    }

    setIsEditingHeader(false);
    try {
      await api.updatePlan(planId, {
        place_name: planInfo.name,
        start_date: newStartDate,
        end_date: newEndDate,
      });
      console.log("Header saved!");
    } catch (error) {
      console.error("Failed to save header:", error);
      alert("Could not save trip info.");
    }
  };
  const [isSaving, setIsSaving] = useState(false);
  const handleSavePlan = async () => {
    setIsSaving(true);
    try {
      const cleanStartDate = planInfo.date.split("T")[0];
      const cleanEndDate = planInfo.end_date
        ? planInfo.end_date.split("T")[0]
        : undefined;

      await api.updatePlan(planId, {
        place_name: planInfo.name,
        start_date: cleanStartDate,
        end_date: cleanEndDate,
      });

      const updatePromises = activities.map((activity) => {
        const realId =
          activity.original_id ||
          String(activity.id).substring(
            0,
            String(activity.id).lastIndexOf("-")
          );

        let dateToSave = planInfo.date.split("T")[0];
        if (activity.date) {
          dateToSave = activity.date.split("T")[0];
        }

        return api.updatePlanDestination(realId, {
          note: activity.title,
          visit_date: dateToSave,
        });
      });

      await Promise.all(updatePromises);

      alert("Plan saved successfully!");
      router.push("/planning_page/showing_plan_page");
    } catch (error) {
      console.error("Error saving plan:", error);
      alert("Failed to save changes. Please check inputs.");
    } finally {
      setIsSaving(false);
    }
  };

  const dropAnimation: DropAnimation = {
    sideEffects: defaultDropAnimationSideEffects({
      styles: { active: { opacity: "0.5" } },
    }),
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center p-6 text-center space-y-6">
        <div className="relative">
          <div className="w-16 h-16 border-4 border-[#E3F1E4] border-t-[#53B552] rounded-full animate-spin"></div>
          <Sparkles
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-[#53B552] animate-pulse"
            size={24}
          />
        </div>
        <h2 className={`${jost.className} text-xl font-bold text-gray-800`}>
          AI is optimizing...
        </h2>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      <div className="w-full max-w-md bg-[#F5F7F5] h-screen shadow-2xl relative flex flex-col">
        <div className="bg-white px-4 py-4 shadow-sm z-10 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Link href={`/planning_page/${planId}/add_destinations`}>
              <ChevronLeft className="text-gray-400" />
            </Link>
            <h1 className={`${jost.className} text-gray-800 font-bold text-lg`}>
              Itinerary
            </h1>
          </div>
          <button
            onClick={handleSavePlan}
            disabled={isSaving}
            className={`flex items-center gap-1 font-bold text-sm px-3 py-2 rounded-full transition-colors ${
              isSaving
                ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                : "text-[#53B552] bg-[#E3F1E4] hover:bg-green-100"
            }`}
          >
            {isSaving ? (
              <>
                <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
                <span>Saving...</span>
              </>
            ) : (
              <>
                <Save size={16} />
                <span>Save</span>
              </>
            )}
          </button>
        </div>

        <main className="flex-1 overflow-y-auto p-4 pb-20">
          <div className="mb-6 bg-white p-4 rounded-xl shadow-sm border border-gray-100">
            {isEditingHeader ? (
              <div className="space-y-4">
                <input
                  value={planInfo.name}
                  onChange={(e) =>
                    setPlanInfo({ ...planInfo, name: e.target.value })
                  }
                  className="w-full text-xl font-bold border-b border-[#53B552] outline-none py-1 text-gray-800"
                  placeholder="Trip Name"
                />

                <div className="flex gap-4">
                  <div className="flex-1">
                    <label className="text-xs text-gray-400 mb-1 block">
                      Start Date
                    </label>
                    <input
                      type="date"
                      value={planInfo.date}
                      onChange={(e) =>
                        setPlanInfo({ ...planInfo, date: e.target.value })
                      }
                      className="w-full text-sm border-b border-gray-200 focus:border-[#53B552] py-1 outline-none text-gray-600 bg-transparent"
                    />
                  </div>
                  <div className="flex-1">
                    <label className="text-xs text-gray-400 mb-1 block">
                      End Date
                    </label>
                    <input
                      type="date"
                      value={planInfo.end_date}
                      onChange={(e) =>
                        setPlanInfo({ ...planInfo, end_date: e.target.value })
                      }
                      className="w-full text-sm border-b border-gray-200 focus:border-[#53B552] py-1 outline-none text-gray-600 bg-transparent"
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    onClick={handleSaveHeader}
                    className="bg-[#53B552] text-white px-4 py-1.5 rounded-lg text-xs font-bold shadow-md shadow-green-100"
                  >
                    Done
                  </button>
                </div>
              </div>
            ) : (
              <div className="relative group">
                <button
                  onClick={() => setIsEditingHeader(true)}
                  className="absolute top-0 right-0 text-gray-300 hover:text-[#53B552]"
                >
                  <Pencil size={16} />
                </button>
                <h2
                  className={`${jost.className} text-2xl font-bold text-gray-800`}
                >
                  {planInfo.name}
                </h2>
                <p className="text-gray-500 text-sm flex gap-2 mt-1">
                  <CalendarDays size={16} />
                  {/* Hiển thị ngày tháng */}
                  {planInfo.date}{" "}
                  {planInfo.end_date ? `— ${planInfo.end_date}` : ""}
                </p>
              </div>
            )}
          </div>

          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragStart={handleDragStart}
            onDragOver={handleDragOver}
            onDragEnd={handleDragEnd}
          >
            <div className="space-y-2">
              <TimeSlotContainer
                id="Morning"
                title="Morning"
                icon={<Sun size={18} className="text-orange-400" />}
                items={activities.filter((a) => a.time_slot === "Morning")}
                onUpdateItem={handleUpdateItem}
              />
              <TimeSlotContainer
                id="Afternoon"
                title="Afternoon"
                icon={<Sunset size={18} className="text-red-400" />}
                items={activities.filter((a) => a.time_slot === "Afternoon")}
                onUpdateItem={handleUpdateItem}
              />
              <TimeSlotContainer
                id="Evening"
                title="Evening"
                icon={<Moon size={18} className="text-purple-400" />}
                items={activities.filter((a) => a.time_slot === "Evening")}
                onUpdateItem={handleUpdateItem}
              />
            </div>

            <DragOverlay dropAnimation={dropAnimation}>
              {activeId ? (
                <div className="bg-white p-4 rounded-xl shadow-xl border-2 border-[#53B552] opacity-90 cursor-grabbing">
                  <h3 className="font-bold text-gray-800">
                    {activities.find((a) => a.id === activeId)?.title}
                  </h3>
                </div>
              ) : null}
            </DragOverlay>
          </DndContext>
        </main>
      </div>
    </div>
  );
}
