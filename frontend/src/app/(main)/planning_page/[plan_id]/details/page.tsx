"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
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
  Sparkles, // Icon chính cho AI
  GripVertical,
  Pencil,
  Sun,
  Sunset,
  Moon,
  Plus,
  Loader2,
  BrainCircuit, 
} from "lucide-react";
import { Jost, Roboto } from "next/font/google";
import { api, PlanActivity } from "@/lib/api";
import Link from "next/link";

// --- FONTS ---
const roboto = Roboto({
  subsets: ["vietnamese"],
  weight: ["400", "500", "700"],
});
const jost = Jost({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

// --- MESSAGES CHO AI LOADING ---
const AI_STEPS = [
  "Analyzing your selected preferences...",
  "Finding optimal routes between locations...",
  "Checking weather conditions...",
  "Finalizing your perfect itinerary...",
];

// --- COMPONENT ITEM ---
interface SortableItemProps {
  activity: PlanActivity;
}

function SortableItem({ activity }: SortableItemProps) {
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
      className={`bg-white p-4 rounded-xl shadow-sm border mb-3 flex gap-3 items-center group touch-none ${
        isDragging
          ? "border-[#53B552] ring-2 ring-[#53B552]/20"
          : "border-gray-100"
      }`}
    >
      <div className="flex-1 min-w-0">
        <h3 className={`${jost.className} font-bold text-gray-800 truncate`}>
          {activity.title}
        </h3>
      </div>
      <div
        {...attributes}
        {...listeners}
        className="cursor-grab text-gray-300 hover:text-gray-500 p-2 border-l border-gray-100 pl-3"
      >
        <GripVertical size={20} />
      </div>
    </div>
  );
}

// --- CONTAINER COMPONENT ---
function TimeSlotContainer({
  id,
  title,
  icon,
  items,
}: {
  id: string;
  title: string;
  icon: React.ReactNode;
  items: PlanActivity[];
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
            <SortableItem key={activity.id} activity={activity} />
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
  const searchParams = useSearchParams();
  const planId = Number(params.plan_id);
  const isNewPlan = searchParams.get("new") === "true";

  // States
  const [isLoading, setIsLoading] = useState(true);
  const [isAiProcessing, setIsAiProcessing] = useState(isNewPlan);
  const [aiStepIndex, setAiStepIndex] = useState(0);
  const [progress, setProgress] = useState(0);

  const [isSaving, setIsSaving] = useState(false);
  const [activities, setActivities] = useState<PlanActivity[]>([]);
  const [activeId, setActiveId] = useState<string | number | null>(null);

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

  useEffect(() => {
    let isMounted = true;

    let textInterval: NodeJS.Timeout;
    let progressInterval: NodeJS.Timeout;
    let finishTimeout: NodeJS.Timeout;

    const initData = async () => {
      try {
        const plans = await api.getPlans();
        const currentPlan = plans.find((p) => p.id === planId);

        if (currentPlan && isMounted) {
          setPlanInfo({
            name: currentPlan.destination,
            date: currentPlan.date,
            end_date: currentPlan.end_date || "",
          });
          setActivities(currentPlan.activities);

          const prevCountStr = sessionStorage.getItem(`plan_${planId}_count`);
          const currentCount = currentPlan.activities.length;

          let shouldRunAI = false;

          if (isNewPlan) {
            shouldRunAI = true;
          } else if (prevCountStr !== null) {
            const prevCount = parseInt(prevCountStr);
            if (currentCount !== prevCount) {
              shouldRunAI = true;
            }
            sessionStorage.removeItem(`plan_${planId}_count`);
          }

          if (shouldRunAI) {
            setIsAiProcessing(true);

            const stepDuration = 800;
            const totalDuration = stepDuration * AI_STEPS.length + 500;

            setAiStepIndex(0);
            setProgress(0);

            textInterval = setInterval(() => {
              setAiStepIndex((prev) => {
                if (prev < AI_STEPS.length - 1) return prev + 1;
                return prev;
              });
            }, stepDuration);

            progressInterval = setInterval(() => {
              setProgress((prev) => {
                if (prev >= 100) return 100;
                return prev + 100 / (totalDuration / 50);
              });
            }, 50);

            finishTimeout = setTimeout(() => {
              clearInterval(textInterval);
              clearInterval(progressInterval);

              if (isMounted) {
                setIsAiProcessing(false);
                setIsLoading(false);
              }
            }, totalDuration);
          } else {
            setIsAiProcessing(false);
            setIsLoading(false);
          }
        }
      } catch (error) {
        console.error("Error fetching plan:", error);
        if (isMounted) setIsLoading(false);
      }
    };

    initData();

    return () => {
      isMounted = false;
      clearInterval(textInterval);
      clearInterval(progressInterval);
      clearTimeout(finishTimeout);
    };
  }, [planId, isNewPlan]);
  const getDaysArray = (start: string, end?: string) => {
    const arr = [];
    const dt = new Date(start);
    const endDate = end ? new Date(end) : new Date(start);

    while (dt <= endDate) {
      arr.push(new Date(dt).toISOString().split("T")[0]);
      dt.setDate(dt.getDate() + 1);
    }
    return arr;
  };
  const planDays = React.useMemo(() => {
    if (!planInfo.date) return [];
    return getDaysArray(planInfo.date, planInfo.end_date);
  }, [planInfo.date, planInfo.end_date]);

  const findContainer = (id: string | number) => {
    if (String(id).includes("_")) return id;
    const item = activities.find((a) => a.id === id);
    if (!item) return null;
    const dateStr = item.date ? item.date.split("T")[0] : planDays[0];
    return `${dateStr}_${item.time_slot}`;
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
      const [newDate, newSlot] = String(overContainer).split("_");

      const newActivities = [...prev];
      newActivities[activeIndex] = {
        ...newActivities[activeIndex],
        time_slot: newSlot as "Morning" | "Afternoon" | "Evening",
        date: newDate,
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

  // --- LOGIC SAVE (Giữ nguyên) ---
  const performSave = async () => {
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
      const realId = activity.original_id;
      if (!realId) return Promise.resolve();
      let dateToSave = planInfo.date.split("T")[0];
      if (activity.date) {
        dateToSave = activity.date.split("T")[0];
      }
      return api.updatePlanDestination(realId, planId, {
        note: activity.title,
        visit_date: dateToSave,
      });
    });

    await Promise.all(updatePromises);
  };

  const handleSavePlan = async () => {
    setIsSaving(true);
    try {
      await performSave();
      alert("Plan saved successfully!");
      router.push("/planning_page/showing_plan_page");
    } catch (error) {
      console.error("Error saving plan:", error);
      alert("Failed to save changes.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveHeader = async () => {
    setIsEditingHeader(false);
  };

  const handleAddPlace = async () => {
    setIsSaving(true);
    try {
      await performSave();
      sessionStorage.setItem(
        `plan_${planId}_count`,
        activities.length.toString()
      );
      router.push(`/planning_page/${planId}`);
    } catch (error) {
      console.error("Save before redirect failed:", error);
      alert("Could not save current changes. Please try again.");
      setIsSaving(false);
    }
  };

  const dropAnimation: DropAnimation = {
    sideEffects: defaultDropAnimationSideEffects({
      styles: { active: { opacity: "0.5" } },
    }),
  };

  // --- MÀN HÌNH AI GENERATING (Loading Screen) ---
  if (isAiProcessing) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center p-8 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-64 h-64 bg-green-100 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2 opacity-50"></div>
        <div className="absolute bottom-0 right-0 w-80 h-80 bg-blue-100 rounded-full blur-3xl translate-x-1/2 translate-y-1/2 opacity-50"></div>

        <div className="relative z-10 flex flex-col items-center max-w-sm w-full">
          {/* Animated Icon */}
          <div className="relative mb-8">
            <div className="w-20 h-20 bg-[#E3F1E4] rounded-full flex items-center justify-center animate-pulse">
              <Sparkles className="text-[#53B552] w-10 h-10 animate-spin-slow" />
            </div>
            <div className="absolute -top-1 -right-1 bg-white p-1 rounded-full shadow-sm animate-bounce">
              <BrainCircuit size={16} className="text-blue-500" />
            </div>
          </div>

          {/* Text Steps */}
          <h2
            className={`${jost.className} text-xl font-bold text-gray-800 text-center mb-2 h-8 transition-all duration-500 ease-in-out`}
          >
            AI Generator
          </h2>
          <p className="text-gray-500 text-sm mb-8 h-6 text-center transition-all duration-300">
            {AI_STEPS[aiStepIndex]}
          </p>

          {/* Progress Bar */}
          <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden relative">
            <div
              className="h-full bg-linear-to-r from-[#53B552] to-emerald-400 transition-all duration-100 ease-out"
              style={{ width: `${progress}%` }}
            ></div>
          </div>

          <div className="flex justify-between w-full mt-2">
            <span className="text-xs text-gray-400 font-medium">
              Processing
            </span>
            <span className="text-xs text-gray-400 font-medium">
              {Math.round(progress)}%
            </span>
          </div>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="flex flex-col items-center gap-2">
          <Loader2 className="w-8 h-8 text-[#53B552] animate-spin" />
          <p className="text-gray-400 text-sm font-medium">
            Loading itinerary...
          </p>
        </div>
      </div>
    );
  }

  // --- GIAO DIỆN CHÍNH (Sau khi load xong) ---
  return (
    <div className="min-h-screen w-full flex justify-center bg-gray-200 animate-in fade-in duration-700">
      <div className="w-full max-w-md bg-[#F5F7F5] h-screen shadow-2xl relative flex flex-col">
        {/* HEADER BAR */}
        <div className="bg-white px-4 py-4 shadow-sm z-10 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Link href={`/planning_page/showing_plan_page`}>
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
              "Saving..."
            ) : (
              <>
                <Save size={16} /> Save
              </>
            )}
          </button>
        </div>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-4 pb-20">
          <div className="mb-4 bg-white p-4 rounded-xl shadow-sm border border-gray-100">
            {isEditingHeader ? (
              <div className="space-y-4">
                <input
                  value={planInfo.name}
                  onChange={(e) =>
                    setPlanInfo({ ...planInfo, name: e.target.value })
                  }
                  className="w-full text-xl font-bold border-b border-[#53B552] outline-none py-1 text-gray-800"
                />
                <button
                  onClick={() => setIsEditingHeader(false)}
                  className="bg-[#53B552] text-white px-3 py-1 rounded text-xs"
                >
                  Done
                </button>
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
                <p className="text-gray-500 text-sm flex items-center gap-2 mt-1">
                  <CalendarDays size={16} />
                  <span>
                    {planInfo.date ? planInfo.date.split("T")[0] : ""}

                    {planInfo.end_date &&
                      planInfo.end_date.split("T")[0] !==
                        planInfo.date.split("T")[0] && (
                        <>
                          <span className="mx-1 text-gray-400">-</span>
                          {planInfo.end_date.split("T")[0]}
                        </>
                      )}
                  </span>
                </p>
              </div>
            )}
          </div>

          {/* Add Place Button */}
          <div className="mb-6 flex justify-end">
            <button
              onClick={handleAddPlace}
              disabled={isSaving}
              className={`flex items-center gap-2 border px-4 py-2 rounded-full font-bold shadow-sm transition text-sm ${
                isSaving
                  ? "bg-gray-50 text-gray-400 border-gray-200 cursor-wait"
                  : "bg-white text-[#53B552] border-[#53B552] hover:bg-green-50"
              }`}
            >
              {isSaving ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <Plus size={18} />
              )}
              {isSaving ? "Saving..." : "Edit Place"}
            </button>
          </div>

          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragStart={handleDragStart}
            onDragOver={handleDragOver}
            onDragEnd={handleDragEnd}
          >
            <div className="space-y-8">
              {planDays.map((day, dayIndex) => (
                <div
                  key={day}
                  className="animate-in fade-in slide-in-from-bottom-4 duration-500"
                >
                  <div className="flex items-center gap-2 mb-4 sticky top-0 bg-[#F5F7F5] z-10 py-2 border-b border-gray-200">
                    <div className="bg-[#53B552] text-white font-bold w-8 h-8 rounded-full flex items-center justify-center shadow-md">
                      {dayIndex + 1}
                    </div>
                    <div>
                      <h3
                        className={`${jost.className} font-bold text-gray-800 text-lg`}
                      >
                        Day {dayIndex + 1}
                      </h3>
                      <p className="text-xs text-gray-400">
                        {new Date(day).toLocaleDateString("en-US", {
                          weekday: "long",
                          month: "short",
                          day: "numeric",
                        })}
                      </p>
                    </div>
                  </div>

                  <div className="space-y-2 pl-2 border-l-2 border-dashed border-gray-200 ml-4">
                    <TimeSlotContainer
                      id={`${day}_Morning`}
                      title="Morning"
                      icon={<Sun size={18} className="text-orange-400" />}
                      items={activities.filter(
                        (a) =>
                          (a.date?.split("T")[0] === day ||
                            (!a.date && dayIndex === 0)) &&
                          a.time_slot === "Morning"
                      )}
                    />
                    <TimeSlotContainer
                      id={`${day}_Afternoon`}
                      title="Afternoon"
                      icon={<Sunset size={18} className="text-red-400" />}
                      items={activities.filter(
                        (a) =>
                          (a.date?.split("T")[0] === day ||
                            (!a.date && dayIndex === 0)) &&
                          a.time_slot === "Afternoon"
                      )}
                    />
                    <TimeSlotContainer
                      id={`${day}_Evening`}
                      title="Evening"
                      icon={<Moon size={18} className="text-purple-400" />}
                      items={activities.filter(
                        (a) =>
                          (a.date?.split("T")[0] === day ||
                            (!a.date && dayIndex === 0)) &&
                          a.time_slot === "Evening"
                      )}
                    />
                  </div>
                </div>
              ))}
            </div>

            <DragOverlay dropAnimation={dropAnimation}>
              {activeId ? (
                <div className="bg-white p-4 rounded-xl shadow-xl border-2 border-[#53B552] opacity-90 cursor-grabbing">
                  {activities.find((a) => a.id === activeId)?.title}
                </div>
              ) : null}
            </DragOverlay>
          </DndContext>
        </main>
      </div>
    </div>
  );
}
