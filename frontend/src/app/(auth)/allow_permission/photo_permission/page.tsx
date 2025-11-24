"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Image as ImageIcon } from "lucide-react";
import { Knewave, Josefin_Sans, Abhaya_Libre, Jost } from "next/font/google";

const knewave = Knewave({ subsets: ["latin"], weight: ["400"] });
const josefin_sans = Josefin_Sans({ subsets: ["latin"], weight: ["700"] });
const abhaya_libre = Abhaya_Libre({
  subsets: ["latin"],
  weight: ["400", "700"],
});
const jost = Jost({ subsets: ["latin"], weight: ["700"] });

export default function PhotoPermissionPage() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    // Kiểm tra xem đã cho phép chưa
    const hasPermission = localStorage.getItem("photoPermission");

    // Nếu đã cấp quyền rồi -> Chuyển thẳng vào Homepage
    if (hasPermission === "granted") {
      router.push("/homepage");
    } else {
      setIsChecking(false);
    }
  }, [router]);

  const handleAllow = () => {
    // Lưu trạng thái đã cho phép vào LocalStorage
    localStorage.setItem("photoPermission", "granted");
    // Chuyển hướng sang Homepage
    router.push("/homepage");
  };

  const handleSkip = () => {
    // Tùy chọn: Bạn có thể lưu trạng thái 'skipped' nếu muốn lần sau không hỏi lại
    // localStorage.setItem("photoPermission", "skipped");

    // Chuyển hướng sang Homepage
    router.push("/homepage");
  };

  if (isChecking) return null;

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
        </div>

        {/* Icon Section */}
        <div className="flex flex-col items-center justify-center mt-10">
          <div className="w-48 h-48 bg-[#E9F5EB] rounded-full flex items-center justify-center mb-10 shadow-sm relative">
            <ImageIcon size={80} className="text-[#53B552]" />
            <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-12 h-3 bg-green-200 rounded-full opacity-50 blur-sm"></div>
          </div>

          <h2
            className={`${abhaya_libre.className} text-3xl font-bold text-gray-800 mb-3`}
          >
            Photo Access
          </h2>
          <p
            className={`${abhaya_libre.className} text-center text-gray-500 text-lg leading-relaxed max-w-xs`}
          >
            Allow EcomoveX to access your photos to update your profile picture.
          </p>
        </div>

        {/* Button Section */}
        <div className="w-full mt-16">
          <button
            onClick={handleAllow}
            className={`${jost.className} w-full bg-[#53B552] hover:bg-green-600 text-white text-xl font-bold py-3.5 rounded-full shadow-lg transition-all transform active:scale-[0.98]`}
          >
            Allow Access
          </button>

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
