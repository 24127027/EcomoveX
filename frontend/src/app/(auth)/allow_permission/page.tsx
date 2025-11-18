"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { MapPin } from "lucide-react";
import { Knewave, Josefin_Sans, Abhaya_Libre, Jost } from "next/font/google";

// --- Khai báo Font (Copy từ các file trước để đồng bộ) ---
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

  const handleAllowLocation = () => {
    setLoading(true);
    setErrorMsg("");

    // Kiểm tra trình duyệt có hỗ trợ Geolocation không
    if (!("geolocation" in navigator)) {
      setErrorMsg("Geolocation is not supported by your browser");
      setLoading(false);
      return;
    }

    // Gọi API xin quyền vị trí của trình duyệt
    navigator.geolocation.getCurrentPosition(
      (position) => {
        // 1. THÀNH CÔNG:
        const { latitude, longitude } = position.coords;
        console.log("User location:", latitude, longitude);

        // Lưu toạ độ vào localStorage để dùng cho các trang khác (Map, Home)
        localStorage.setItem(
          "userLocation",
          JSON.stringify({ lat: latitude, lng: longitude })
        );

        // Chuyển hướng về Homepage
        router.push("/homepage");
      },
      (error) => {
        // 2. THẤT BẠI (Người dùng từ chối hoặc lỗi):
        console.error("Error getting location:", error);
        setErrorMsg("Location access denied. Please enable it in settings.");
        setLoading(false);
        // Tùy chọn: Vẫn cho vào trang chủ nhưng ở chế độ mặc định
        router.push("/homepage");
      }
    );
  };

  return (
    // 1. Wrapper Desktop (Nền xám)
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      {/* 2. Khung App Mobile (Trắng, bo góc, đổ bóng) */}
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
          {/* Vòng tròn nền xanh nhạt */}
          <div className="w-48 h-48 bg-[#E9F5EB] rounded-full flex items-center justify-center mb-10 shadow-sm">
            {/* Icon MapPin mô phỏng hình trong ảnh */}
            <div className="relative">
              <MapPin
                size={80}
                className="text-[#53B552] fill-[#53B552] stroke-white stroke-[1.5]"
              />
              {/* Tạo hiệu ứng bóng đổ dưới chân pin một chút cho giống ảnh 3D */}
              <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-12 h-3 bg-green-200 rounded-full opacity-50 blur-sm"></div>
            </div>
          </div>

          {/* Text Content */}
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
          {/* Hiển thị lỗi nếu có */}
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

          {/* Nút bỏ qua (Optional - thường nên có) */}
          <button
            onClick={() => router.push("/homepage")}
            className={`${jost.className} w-full text-gray-400 text-sm font-medium mt-4 hover:text-gray-600 transition-colors`}
          >
            Not now
          </button>
        </div>
      </main>
    </div>
  );
}
