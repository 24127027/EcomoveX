"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation"; // Import router để chuyển trang
import { ChevronLeft, ChevronRight, MapPin, Loader2 } from "lucide-react"; // Thêm icon Loader2
import { Jost, Abhaya_Libre } from "next/font/google";
import { api } from "@/lib/api"; // Import API client từ thư mục lib

const jost = Jost({ subsets: ["latin"], weight: ["400", "500", "600", "700"] });
const abhaya_libre = Abhaya_Libre({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const LOCATIONS = [
  {
    city: "Ho Chi Minh City",
    districts: [
      "District 1",
      "District 2",
      "District 3",
      "District 4",
      "District 5",
      "District 6",
      "District 7",
      "District 8",
      "District 10",
      "District 11",
      "District 12",
      "Binh Thanh District",
      "Binh Tan District",
      "Tan Binh District",
      "Tan Phu District",
      "Go Vap District",
      "Phu Nhuan District",
      "Thu Duc City",
      "Cu Chi District",
      "Hoc Mon District",
      "Binh Chanh District",
      "Nha Be District",
      "Can Gio District",
    ],
  },
];

const STORAGE_KEY_INFO = "temp_plan_info";

export default function CreatePlanPage() {
  const router = useRouter(); // Khởi tạo router
  const [budget, setBudget] = useState<string>("100000"); // Đổi thành string để format dễ hơn
  const [destination, setDestination] = useState<string>("");
  const [selectedDistrict, setSelectedDistrict] = useState<string>(""); // NEW: Lưu district để truyền sang map
  const [showDropdown, setShowDropdown] = useState<boolean>(false);

  // Thêm state loading để chặn click nhiều lần
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const dropdownRef = useRef<HTMLDivElement>(null);

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  // --- 1. DROPDOWN LOGIC ---
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setShowDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelectLocation = (district: string) => {
    setDestination(`${district}, ${LOCATIONS[0].city}`);
    setSelectedDistrict(district); // Lưu district để truyền sang map
    setShowDropdown(false);
  };

  const [displayDate, setDisplayDate] = useState(new Date());
  const [selectedRange, setSelectedRange] = useState<{
    start: Date | null;
    end: Date | null;
  }>({
    start: null,
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

  const handleDateClick = (day: number) => {
    const clickedDate = new Date(year, month, day);
    clickedDate.setHours(0, 0, 0, 0);

    if (clickedDate < today) return;

    if (!selectedRange.start || (selectedRange.start && selectedRange.end)) {
      setSelectedRange({ start: clickedDate, end: null });
    } else {
      if (clickedDate.getTime() < selectedRange.start.getTime()) {
        setSelectedRange({ start: clickedDate, end: null });
      } else {
        setSelectedRange({ ...selectedRange, end: clickedDate });
      }
    }
  };

  const getDayStatus = (day: number) => {
    const currentDayDate = new Date(year, month, day);
    currentDayDate.setHours(0, 0, 0, 0);
    const currentTime = currentDayDate.getTime();

    if (currentDayDate < today) return "disabled";

    const startTime = selectedRange.start
      ? selectedRange.start.getTime()
      : null;
    const endTime = selectedRange.end ? selectedRange.end.getTime() : null;

    if (currentTime === startTime || currentTime === endTime) return "selected";
    if (
      startTime &&
      endTime &&
      currentTime > startTime &&
      currentTime < endTime
    ) {
      return "in-range";
    }
    return "normal";
  };

  const handleBudgetChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const rawValue = e.target.value;
    // Chỉ cho phép số
    const numericValue = rawValue.replace(/[^0-9]/g, "");
    setBudget(numericValue);
  };

  // Format budget cho hiển thị (thêm dấu phẩy)
  const formatBudget = (value: string) => {
    if (!value) return "";
    return Number(value).toLocaleString("vi-VN");
  };

  const formatDate = (date: Date) => {
    return `${date.getDate()}/${date.getMonth() + 1}/${date.getFullYear()}`;
  };
  const formatDateForAPI = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0"); // Tháng bắt đầu từ 0 nên phải +1
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  };

  // --- XỬ LÝ SỰ KIỆN TẠO PLAN ---
  const handleCreatePlan = () => {
    // Bỏ async vì không gọi API nữa
    // Validate dữ liệu cơ bản
    if (!destination || !selectedRange.start) return;

    setIsLoading(true); // Vẫn có thể để loading nhẹ để UX mượt hơn

    try {
      // 1. CHUẨN BỊ DỮ LIỆU
      const planInfo = {
        name: `Trip to ${destination.split(",")[0]}`, // Tên mặc định: "Trip to District 1"
        destination: destination,
        district: selectedDistrict, // NEW: Lưu district để map biết khu vực
        // Format ngày chuẩn để sau này gửi API
        start_date: formatDateForAPI(selectedRange.start),
        end_date: selectedRange.end
          ? formatDateForAPI(selectedRange.end)
          : formatDateForAPI(selectedRange.start),
        budget: Number(budget) || 0, // Convert string về number
      };

      // 2. LƯU VÀO SESSION STORAGE (Thay vì gọi API)
      sessionStorage.setItem(STORAGE_KEY_INFO, JSON.stringify(planInfo));

      // Lưu ý: Có thể cần xóa dữ liệu cũ của các bước sau để tránh bị trộn lẫn plan cũ
      sessionStorage.removeItem("temp_plan_destinations");
      sessionStorage.removeItem("current_plan_activities");
      sessionStorage.removeItem("has_shown_ai_gen");
      sessionStorage.removeItem("EDITING_PLAN_ID"); // ✅ Clear old plan ID to ensure CREATE mode

      // 3. CHUYỂN HƯỚNG
      console.log(
        "Saved info to storage, moving to Add Destinations:",
        planInfo
      );
      router.push("/planning_page/add_destinations");
    } catch (error) {
      console.error("Error:", error);
      alert("There was an error while creating the plan. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      <div className="w-full max-w-md bg-[#F5F7F5] h-screen shadow-2xl relative flex flex-col overflow-hidden">
        {/* HEADER */}
        <div className="bg-white px-4 pt-8 pb-4 shadow-sm z-10 flex items-center gap-4">
          <Link href="/planning_page/showing_plan_page">
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

        {/* SCROLLABLE FORM */}
        <main className="flex-1 overflow-y-auto px-5 py-6 space-y-6 pb-32">
          {/* 1. WHERE TO */}
          <div className="relative" ref={dropdownRef}>
            <div
              className="bg-white border border-[#53B552] rounded-xl p-4 shadow-sm cursor-pointer flex items-center justify-between"
              onClick={() => setShowDropdown(!showDropdown)}
            >
              <input
                type="text"
                readOnly
                value={destination}
                placeholder="Where to in Ho Chi Minh City?"
                className={`${jost.className} w-full outline-none text-[#53B552] font-bold placeholder:text-[#53B552]/70 bg-transparent text-lg cursor-pointer`}
              />
              <MapPin size={20} className="text-[#53B552]" />
            </div>

            {showDropdown && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-xl shadow-lg max-h-60 overflow-y-auto z-50">
                {LOCATIONS[0].districts.map((district, idx) => (
                  <div
                    key={idx}
                    onClick={() => handleSelectLocation(district)}
                    className={`${jost.className} px-4 py-3 hover:bg-green-50 text-[#53B552] font-medium cursor-pointer border-b last:border-0 border-gray-100 transition-colors`}
                  >
                    {district}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 2. CALENDAR */}
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
                  const status = getDayStatus(day);

                  let className = `${jost.className} w-8 h-8 flex items-center justify-center rounded-full text-sm transition-all `;

                  if (status === "disabled") {
                    className += "text-gray-300 cursor-not-allowed";
                  } else if (status === "selected") {
                    className +=
                      "bg-[#53B552] text-white font-bold shadow-md scale-110 cursor-pointer";
                  } else if (status === "in-range") {
                    className +=
                      "bg-[#E3F1E4] text-[#53B552] font-bold cursor-pointer";
                  } else {
                    className +=
                      "text-gray-800 hover:bg-green-100 cursor-pointer";
                  }

                  return (
                    <div key={day} className="flex justify-center items-center">
                      <div
                        onClick={() =>
                          status !== "disabled" && handleDateClick(day)
                        }
                        className={className}
                      >
                        {day}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {selectedRange.start && (
              <div
                className={`${jost.className} mt-4 text-center text-[#53B552] font-medium`}
              >
                Selected: {formatDate(selectedRange.start)}
                {selectedRange.end ? ` - ${formatDate(selectedRange.end)}` : ""}
              </div>
            )}
          </div>

          {/* 3. PEOPLE COUNT */}
          <div className="bg-white border border-[#53B552] rounded-xl p-4 shadow-sm">
            <input
              type="number"
              placeholder="How many people joining this trip?"
              className={`${jost.className} w-full outline-none text-[#53B552] font-bold placeholder:text-[#53B552]/70 bg-transparent text-sm`}
            />
          </div>

          {/* 4. BUDGET */}
          <div className="bg-white border border-[#53B552] rounded-xl p-5 shadow-sm">
            <div className="flex justify-between items-center mb-2">
              <span
                className={`${jost.className} text-[#53B552] font-bold text-lg`}
              >
                Budget
              </span>
              <div className="flex items-center justify-end gap-2 w-3/5">
                <input
                  type="text"
                  value={formatBudget(budget)}
                  onChange={handleBudgetChange}
                  placeholder="0"
                  className={`${jost.className} text-[#53B552] font-medium text-sm text-right outline-none bg-transparent border-b border-gray-300 focus:border-[#53B552] w-full px-2 py-1 transition-colors`}
                />
                <span
                  className={`${jost.className} text-[#53B552] font-medium text-sm whitespace-nowrap`}
                >
                  VND
                </span>
              </div>
            </div>
            <p
              className={`${jost.className} text-xs text-gray-400 mt-2 text-right`}
            >
              {budget ? `≈ $${(Number(budget) / 25000).toFixed(0)} USD` : ""}
            </p>
          </div>
        </main>

        {/* BOTTOM BUTTON */}
        <div className="absolute bottom-20 left-0 right-0 px-5 bg-linear-to-t from-[#F5F7F5] via-[#F5F7F5] to-transparent pt-4 pb-2">
          <button
            onClick={handleCreatePlan} // Gắn sự kiện click
            disabled={!destination || !selectedRange.start || isLoading} // Disable khi đang load
            className={`${jost.className} w-full bg-[#53B552] text-white text-xl font-bold py-3.5 rounded-xl shadow-lg 
            hover:bg-green-600 transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2`}
          >
            {isLoading ? (
              <>
                <Loader2 className="animate-spin" /> Creating...
              </>
            ) : (
              "Create New Plan"
            )}
          </button>
        </div>

        {/* FOOTER */}
        <div className="bg-white shadow-[0_-5px_15px_rgba(0,0,0,0.05)] sticky bottom-0 w-full z-20 shrink-0 h-[60px]"></div>
      </div>
    </div>
  );
}
