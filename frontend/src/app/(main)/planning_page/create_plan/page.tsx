"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Jost, Abhaya_Libre } from "next/font/google";

const jost = Jost({ subsets: ["latin"], weight: ["400", "500", "600", "700"] });
const abhaya_libre = Abhaya_Libre({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export default function CreatePlanPage() {
  const [budget, setBudget] = useState<number>(100000);

  // --- CALENDAR STATE ---
  const [displayDate, setDisplayDate] = useState(new Date(2025, 10, 1));
  const [selectedRange, setSelectedRange] = useState<{
    start: number | null;
    end: number | null;
  }>({
    start: 24,
    end: 27,
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

  const handleDateClick = (day: number) => {
    if (!selectedRange.start || (selectedRange.start && selectedRange.end)) {
      setSelectedRange({ start: day, end: null });
    } else {
      const newStart = Math.min(selectedRange.start, day);
      const newEnd = Math.max(selectedRange.start, day);
      setSelectedRange({ start: newStart, end: newEnd });
    }
  };

  const isSelected = (day: number) => {
    if (!selectedRange.start) return false;
    if (selectedRange.end) {
      return day >= selectedRange.start && day <= selectedRange.end;
    }
    return day === selectedRange.start;
  };

  // Xử lý thay đổi budget từ input (chặn số âm)
  const handleBudgetChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = Number(e.target.value);
    if (val >= 0) setBudget(val);
  };

  return (
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      <div className="w-full max-w-md bg-[#F5F7F5] h-screen shadow-2xl relative flex flex-col overflow-hidden">
        {/* --- HEADER --- */}
        <div className="bg-white px-4 pt-8 pb-4 shadow-sm z-10 flex items-center gap-4">
          <Link href="/planning_page">
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
              className={`${jost.className} w-full outline-none text-[#53B552] font-bold placeholder:text-[#53B552] bg-transparent text-lg`}
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
              {/* Month Nav */}
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
                  const selected = isSelected(day);
                  return (
                    <div key={day} className="flex justify-center items-center">
                      <div
                        onClick={() => handleDateClick(day)}
                        className={`${
                          jost.className
                        } w-8 h-8 flex items-center justify-center rounded-full text-sm cursor-pointer transition-all ${
                          selected
                            ? "bg-[#53B552] text-white font-bold shadow-md scale-110"
                            : "text-gray-800 hover:bg-green-100"
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

              {/* Phần nhập số tiền */}
              <div className="flex items-center justify-end gap-1 w-1/2">
                <input
                  type="number"
                  value={budget.toString()} // Chuyển sang string để tránh lỗi số 0 đầu
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

            {/* Custom Slider */}
            <div className="relative h-4 w-full bg-transparent border border-[#53B552] rounded-full overflow-hidden mt-2">
              <div
                className="absolute top-0 left-0 h-full bg-[#53B552] rounded-full transition-all duration-100 ease-out"
                style={{ width: `${Math.min((budget / 5000000) * 100, 100)}%` }} // Giới hạn thanh hiển thị max 100%
              ></div>
              <input
                type="range"
                min="0"
                max="5000000"
                step="50000"
                value={budget > 5000000 ? 5000000 : budget} // Nếu nhập quá max slider thì slider giữ max
                onChange={handleBudgetChange}
                className="absolute top-0 left-0 w-full h-full opacity-0 cursor-pointer z-10"
              />
            </div>
          </div>

          {/* 5. Category Tags */}
          <div className="flex flex-wrap gap-3">
            {[
              "AdventureTravel",
              "BeachLover",
              "CulturalTravel",
              "Backpacking",
            ].map((tag, idx) => (
              <span
                key={idx}
                className={`${
                  jost.className
                } px-4 py-1.5 rounded-full text-xs font-bold cursor-pointer transition-colors
                    ${
                      tag === "CulturalTravel" || tag === "BeachLover"
                        ? "bg-[#E3F1E4] text-[#53B552] border border-[#53B552]"
                        : "bg-gray-100 text-gray-500 hover:bg-green-50"
                    }`}
              >
                {tag}
              </span>
            ))}
          </div>
        </main>

        {/* --- BOTTOM BUTTON --- */}
        <div className="absolute bottom-20 left-0 right-0 px-5 bg-linear-to-t from-[#F5F7F5] via-[#F5F7F5] to-transparent pt-4 pb-2">
          <button
            className={`${jost.className} w-full bg-[#53B552] text-white text-xl font-bold py-3.5 rounded-xl shadow-lg hover:bg-green-600 transition-all active:scale-[0.98]`}
          >
            Create New Plan
          </button>
        </div>

        {/* --- FOOTER --- */}
        <div className="bg-white shadow-[0_-5px_15px_rgba(0,0,0,0.05)] sticky bottom-0 w-full z-20 shrink-0 h-[60px]"></div>
      </div>
    </div>
  );
}
