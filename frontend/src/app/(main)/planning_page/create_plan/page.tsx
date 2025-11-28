"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { Jost, Abhaya_Libre, Roboto } from "next/font/google";
import { api } from "@/lib/api";

// --- FONTS ---
const roboto = Roboto({
  subsets: ["vietnamese"],
  weight: ["400", "500", "700"],
});
const jost = Jost({
  subsets: ["latin", "latin-ext"],
  weight: ["400", "500", "600", "700"],
});
const abhaya_libre = Abhaya_Libre({
  subsets: ["latin", "latin-ext"],
  weight: ["400", "500", "600", "700"],
});

export default function CreatePlanPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  // --- FORM STATE ---
  const [placeName, setPlaceName] = useState<string>("");
  const [budget, setBudget] = useState<number>(100000);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  // --- CALENDAR STATE ---
  const [displayDate, setDisplayDate] = useState(new Date());

  const [selectedRange, setSelectedRange] = useState<{
    start: Date | null;
    end: Date | null;
  }>({
    start: new Date(),
    end: null,
  });

  // --- CALENDAR LOGIC ---
  const year = displayDate.getFullYear();
  const month = displayDate.getMonth();
  const firstDayOfMonth = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const monthNames = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];

  const handlePrevMonth = () => setDisplayDate(new Date(year, month - 1, 1));
  const handleNextMonth = () => setDisplayDate(new Date(year, month + 1, 1));

  const isSameDay = (d1: Date, d2: Date) => {
    return (
      d1.getFullYear() === d2.getFullYear() &&
      d1.getMonth() === d2.getMonth() &&
      d1.getDate() === d2.getDate()
    );
  };

  const handleDateClick = (day: number) => {
    const clickedDate = new Date(year, month, day);
    clickedDate.setHours(0, 0, 0, 0);

    if (!selectedRange.start || (selectedRange.start && selectedRange.end)) {
      setSelectedRange({ start: clickedDate, end: null });
    } else {
      if (clickedDate < selectedRange.start) {
        setSelectedRange({ start: clickedDate, end: selectedRange.start });
      } else if (isSameDay(clickedDate, selectedRange.start)) {
        setSelectedRange({ start: null, end: null });
      } else {
        setSelectedRange({ ...selectedRange, end: clickedDate });
      }
    }
  };

  const getDayStatus = (day: number) => {
    if (!selectedRange.start) return "none";

    const currentCellDate = new Date(year, month, day);
    currentCellDate.setHours(0, 0, 0, 0);
    const start = selectedRange.start;
    const end = selectedRange.end;

    // Reset giờ cho start/end để so sánh
    const sTime = new Date(start).setHours(0, 0, 0, 0);
    const cTime = currentCellDate.getTime();

    if (end) {
      const eTime = new Date(end).setHours(0, 0, 0, 0);
      if (cTime === sTime || cTime === eTime) return "selected";
      if (cTime > sTime && cTime < eTime) return "in-range";
    } else {
      if (cTime === sTime) return "selected";
    }

    return "none";
  };

  const toggleTag = (tag: string) => {
    if (selectedTags.includes(tag)) {
      setSelectedTags(selectedTags.filter((t) => t !== tag));
    } else {
      setSelectedTags([...selectedTags, tag]);
    }
  };

  const handleBudgetChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = Number(e.target.value);
    if (val >= 0) setBudget(val);
    else if (val < 0) setBudget(0);
  };

  const handlePeopleCountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = Number(e.target.value);
    if (val <= 0) {
      e.target.value = "1";
    }
  };

  const handleCreatePlan = async () => {
    if (!placeName.trim()) {
      alert("Please enter where you want to go!");
      return;
    }
    if (!selectedRange.start) {
      alert("Please select at least one date for your trip!");
      return;
    }

    try {
      setIsLoading(true);

      const startDate = selectedRange.start;
      const endDate = selectedRange.end ? selectedRange.end : startDate;

      const formatDateLocal = (date: Date) => {
        const offset = date.getTimezoneOffset();
        const localDate = new Date(date.getTime() - offset * 60 * 1000);
        return localDate.toISOString().split("T")[0];
      };

      const newPlan = await api.createPlan({
        place_name: placeName,
        start_date: formatDateLocal(startDate),
        end_date: formatDateLocal(endDate),
        budget_limit: budget,
      });
      router.push(`/planning_page/${newPlan.id}`);
    } catch (error) {
      console.error("Error creating plan:", error);
      alert("There was an error creating your plan. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      <div className="w-full max-w-md bg-[#F5F7F5] h-screen shadow-2xl relative flex flex-col overflow-hidden">
        {/* --- HEADER --- */}
        <div className="bg-white px-4 pt-8 pb-4 shadow-sm z-10 flex items-center gap-4">
          <Link href="/homepage">
            <ChevronLeft
              className="text-[#53B552] cursor-pointer"
              size={32}
              strokeWidth={2.5}
            />
          </Link>
          <h1
            className={`${jost.className} text-[#53B552] text-2xl font-bold uppercase tracking-wide`}
          >
            Planning
          </h1>
        </div>

        {/* --- SCROLLABLE FORM --- */}
        <main className="flex-1 overflow-y-auto px-5 py-6 space-y-6 pb-32">
          {/* 1. Where to? */}
          <div className="bg-white border border-[#53B552] rounded-xl p-4 shadow-sm">
            <input
              type="text"
              placeholder="Where to?"
              value={placeName}
              onChange={(e) => setPlaceName(e.target.value)}
              className={`${roboto.className} w-full outline-none text-[#53B552] font-bold placeholder:text-[#53B552] bg-transparent text-lg`}
            />
          </div>

          {/* 2. When to? (Calendar) */}
          <div className="bg-white border border-[#53B552] rounded-xl p-5 shadow-sm">
            <h3
              className={`${jost.className} text-[#53B552] font-bold mb-4 text-lg`}
            >
              When to?
            </h3>

            <div className="bg-[#F1F8F1] rounded-xl p-4 select-none">
              <div className="flex justify-between items-center mb-4 px-2">
                <ChevronLeft
                  size={24}
                  className="text-gray-600 cursor-pointer hover:text-green-600"
                  onClick={handlePrevMonth}
                />
                <span
                  className={`${abhaya_libre.className} font-bold text-lg text-black`}
                >
                  {monthNames[month]} {year}
                </span>
                <ChevronRight
                  size={24}
                  className="text-black cursor-pointer hover:text-green-600"
                  onClick={handleNextMonth}
                />
              </div>
              <div className="h-px bg-gray-300 w-full mb-4"></div>

              {/* Calendar Grid */}
              <div className="grid grid-cols-7 mb-2 text-center">
                {["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"].map((d) => (
                  <span
                    key={d}
                    className={`${jost.className} text-xs text-gray-400 font-bold`}
                  >
                    {d}
                  </span>
                ))}
              </div>

              <div className="grid grid-cols-7 gap-y-3 text-center">
                {Array.from({ length: firstDayOfMonth }).map((_, index) => (
                  <div key={`empty-${index}`} />
                ))}
                {Array.from({ length: daysInMonth }).map((_, index) => {
                  const day = index + 1;

                  const dateToCheck = new Date(year, month, day);
                  const today = new Date();
                  today.setHours(0, 0, 0, 0);
                  const isPast = dateToCheck < today;

                  const status = getDayStatus(day);

                  return (
                    <div key={day} className="flex justify-center items-center">
                      <div
                        onClick={() => !isPast && handleDateClick(day)}
                        className={`${
                          jost.className
                        } w-8 h-8 flex items-center justify-center rounded-full text-sm transition-all 
                        ${
                          isPast
                            ? "text-gray-300 cursor-not-allowed"
                            : "cursor-pointer text-gray-800 hover:bg-green-100"
                        }
                        ${
                          status === "selected" && !isPast
                            ? "bg-[#53B552] text-white font-bold shadow-md scale-110 hover:bg-[#53B552]"
                            : ""
                        }
                        ${
                          status === "in-range" && !isPast
                            ? "bg-[#E3F1E4] text-[#53B552] font-semibold"
                            : ""
                        }`}
                      >
                        {day}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* 3. People count */}
          <div className="bg-white border border-[#53B552] rounded-xl p-4 shadow-sm">
            <input
              type="number"
              onChange={handlePeopleCountChange}
              min={1}
              placeholder="How many people joining this trip?"
              className={`${jost.className} w-full outline-none text-[#53B552] font-bold placeholder:text-[#53B552] bg-transparent text-sm`}
            />
          </div>

          {/* 4. Budget Slider & Input */}
          <div className="bg-white border border-[#53B552] rounded-xl p-5 shadow-sm">
            <div className="flex justify-between items-center mb-2">
              <span
                className={`${jost.className} text-[#53B552] font-bold text-lg`}
              >
                Budget
              </span>

              <div className="flex items-center justify-end gap-1 w-1/2">
                <input
                  type="number"
                  value={budget.toString()}
                  onChange={handleBudgetChange}
                  className={`${jost.className} text-[#53B552] font-medium text-sm text-right outline-none bg-transparent border-b border-gray-200 focus:border-[#53B552] w-full`}
                />
                <span
                  className={`${jost.className} text-[#53B552] font-medium text-sm`}
                >
                  VND
                </span>
              </div>
            </div>
          </div>

          {/* 5. Category Tags */}
          <div className="flex flex-wrap gap-3">
            {[
              "AdventureTravel",
              "BeachLover",
              "CulturalTravel",
              "Backpacking",
              "Foodie",
              "Relaxation",
              "NatureExplorer",
              "LuxuryTravel",
              "FamilyTrip",
              "SoloTravel",
            ].map((tag, idx) => {
              const isActive = selectedTags.includes(tag);
              return (
                <span
                  key={idx}
                  onClick={() => toggleTag(tag)}
                  className={`${
                    jost.className
                  } px-4 py-1.5 rounded-full text-xs font-bold cursor-pointer transition-colors border select-none
                    ${
                      isActive
                        ? "bg-[#E3F1E4] text-[#53B552] border-[#53B552]"
                        : "bg-gray-100 text-gray-500 border-transparent hover:bg-green-50"
                    }`}
                >
                  {tag}
                </span>
              );
            })}
          </div>
        </main>

        {/* --- BOTTOM BUTTON --- */}
        <div className="absolute bottom-0 left-0 right-0 px-5 bg-[#F5F7F5] pt-4 pb-8 z-30">
          <button
            onClick={handleCreatePlan}
            disabled={isLoading}
            className={`${jost.className} w-full bg-[#53B552] text-white text-xl font-bold py-3.5 rounded-xl shadow-lg hover:bg-green-600 transition-all flex justify-center items-center gap-2`}
          >
            {isLoading ? (
              <Loader2 className="animate-spin" />
            ) : (
              "Create New Plan"
            )}
          </button>
        </div>

        {/* --- FOOTER --- */}
        <div className="bg-white shadow-[0_-5px_15px_rgba(0,0,0,0.05)] sticky bottom-0 w-full z-20 shrink-0 h-[60px]"></div>
      </div>
    </div>
  );
}
