"use client";

import React, { useState, useEffect } from "react"; // Thêm useEffect
import { useRouter } from "next/navigation";
import { MapPin } from "lucide-react";
import { Knewave, Josefin_Sans, Abhaya_Libre, Jost } from "next/font/google";

// --- Khai báo Font ---
const knewave = Knewave({ subsets: ["latin"], weight: ["400"] });
const josefin_sans = Josefin_Sans({ subsets: ["latin"], weight: ["700"] });
const abhaya_libre = Abhaya_Libre({
  subsets: ["latin"],
  weight: ["400", "700"],
});
const jost = Jost({ subsets: ["latin"], weight: ["700"] });

export default function LocationPermissionPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  // State để kiểm tra xem đã check xong localStorage chưa (tránh nháy màn hình)
  const [isChecking, setIsChecking] = useState(true);

  // 1. KIỂM TRA TRẠNG THÁI KHI COMPONENT MOUNT
  useEffect(() => {
    const hasLocation = localStorage.getItem("userLocation");
    const hasSkipped = localStorage.getItem("locationSkipped");

    // Nếu đã có vị trí HOẶC người dùng đã từng bấm bỏ qua -> Vào thẳng Homepage
    if (hasLocation || hasSkipped) {
      router.push("/homepage");
    } else {
      // Nếu chưa có gì -> Hiển thị giao diện xin phép
      setIsChecking(false);
    }
  }, [router]);

  const handleAllowLocation = () => {
    setLoading(true);
    setErrorMsg("");

    if (!("geolocation" in navigator)) {
      setErrorMsg("Geolocation is not supported by your browser");
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        console.log("User location:", latitude, longitude);

        // Lưu toạ độ (Đánh dấu là đã xin phép thành công)
        localStorage.setItem(
          "userLocation",
          JSON.stringify({ lat: latitude, lng: longitude })
        );

        // Xóa cờ skip nếu có (để đảm bảo dữ liệu sạch)
        localStorage.removeItem("locationSkipped");

        router.push("/homepage");
      },
      (error) => {
        console.error("Error getting location:", error);
        setErrorMsg("Location access denied. Please enable it in settings.");
        setLoading(false);

        // Tùy chọn: Nếu lỗi/từ chối, bạn có muốn coi như là "đã hỏi xong" không?
        // Nếu muốn lần sau không hỏi lại khi user đã Block, hãy uncomment dòng dưới:
        // localStorage.setItem("locationSkipped", "true");
        // router.push("/homepage");
      }
    );
  };

  // 2. XỬ LÝ KHI BẤM "NOT NOW"
  const handleSkip = () => {
    // Lưu cờ đánh dấu là người dùng đã từ chối cung cấp lần đầu
    localStorage.setItem("locationSkipped", "true");
    router.push("/homepage");
  };

  // Nếu đang kiểm tra localStorage thì không render gì cả (hoặc hiện loading spinner)
  if (isChecking) {
    return null; // Hoặc return <div className="min-h-screen bg-white"></div>;
  }

  return (
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      <main className="w-full max-w-md bg-white h-screen shadow-2xl flex flex-col items-center justify-center px-8 relative overflow-hidden">
        {/* Logo Section */}
        <div className="text-center absolute top-20 w-full">
          <h1
            className={`${knewave.className} text-5xl text-[#53B552] mb-2 tracking-wide`}
          >
            EcomoveX
          </h1>
          <p
            className={`${josefin_sans.className} text-[#53B552] text-lg tracking-tight`}
          >
            Your Trip. Your Impact. Your Choice.
          </p>
        </div>

        {/* Center Icon */}
        <div className="flex flex-col items-center justify-center mt-10">
          <div className="w-48 h-48 bg-[#E9F5EB] rounded-full flex items-center justify-center mb-10 shadow-sm">
            <div className="relative">
              <MapPin
                size={80}
                className="text-[#53B552] fill-[#53B552] stroke-white stroke-[1.5]"
              />
              <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-12 h-3 bg-green-200 rounded-full opacity-50 blur-sm"></div>
            </div>
          </div>

          <h2
            className={`${abhaya_libre.className} text-3xl font-bold text-gray-800 mb-3`}
          >
            Allow Location
          </h2>
          <p
            className={`${abhaya_libre.className} text-center text-gray-500 text-lg leading-relaxed max-w-xs`}
          >
            Allow EcomoveX to access your location for a better experience.
          </p>
        </div>

        {/* Button Section */}
        <div className="w-full mt-16">
          {errorMsg && (
            <p className="text-red-500 text-sm text-center mb-3">{errorMsg}</p>
          )}

          <button
            onClick={handleAllowLocation}
            disabled={loading}
            className={`${jost.className} w-full bg-[#53B552] hover:bg-green-600 text-white text-xl font-bold py-3.5 rounded-full shadow-lg transition-all transform active:scale-[0.98] disabled:opacity-70`}
          >
            {loading ? "Locating..." : "Allow"}
          </button>

          {/* Cập nhật hàm onClick cho nút Not now */}
          <button
            onClick={handleSkip}
            className={`${jost.className} w-full text-gray-400 text-sm font-medium mt-4 hover:text-gray-600 transition-colors`}
          >
            Not now
          </button>
        </div>
      </main>
    </div>
  );
}
