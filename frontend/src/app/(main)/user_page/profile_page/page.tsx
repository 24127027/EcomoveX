"use client";

import React, { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { ArrowLeft, Home, MapPin, Bot, User, Loader2 } from "lucide-react";
import { Jost, Abhaya_Libre, Knewave } from "next/font/google";
import { useRouter } from "next/navigation";
import { api, UserProfile, UserProfileUpdate } from "@/lib/api";

// Khai báo font chữ
const jost = Jost({ subsets: ["latin"] });
const abhaya_libre = Abhaya_Libre({
  weight: ["400", "500", "600", "800"],
  subsets: ["latin"],
});
const knewave = Knewave({ weight: ["400"], subsets: ["latin"] });

export default function ProfilePage() {
  const router = useRouter();

  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  // State cho chức năng Edit
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // State lưu dữ liệu form (Đã bỏ phone_number)
  const [formData, setFormData] = useState<UserProfileUpdate>({
    username: "",
    email: "",
  });

  // State lưu lỗi validation
  const [errors, setErrors] = useState<{ email?: string }>({});

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const userData = await api.getUserProfile();
        setUser(userData);
        // Khởi tạo formData ban đầu
        setFormData({
          username: userData.username,
          email: userData.email,
        });
      } catch (error) {
        console.error("Failed to fetch user profile:", error);
        router.push("/login");
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, [router]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    // Xóa lỗi khi user nhập lại
    if (errors[name as keyof typeof errors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const validateForm = () => {
    let isValid = true;
    const newErrors: { email?: string } = {};

    // Validate Email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (formData.email && !emailRegex.test(formData.email)) {
      newErrors.email = "Invalid email format.";
      isValid = false;
    }

    // Đã xóa phần validate Phone number

    setErrors(newErrors);
    return isValid;
  };

  const handleEditToggle = async () => {
    // 1. Nếu đang ở chế độ Xem -> Chuyển sang Sửa
    if (!isEditing) {
      setFormData({
        username: user?.username || "",
        email: user?.email || "",
      });
      setIsEditing(true);
      return;
    }

    // 2. Validate trước khi lưu
    if (!validateForm()) {
      return;
    }

    try {
      setIsSaving(true);

      // Gọi API cập nhật (chỉ gửi username và email)
      const updatedUser = await api.updateUserProfile({
        username: formData.username,
        email: formData.email,
      });

      // Cập nhật state hiển thị
      setUser(updatedUser);

      // Tắt chế độ Edit
      setIsEditing(false);
    } catch (error: any) {
      console.error("Update failed:", error);
      // Thông báo lỗi (ví dụ: Email đã tồn tại)
      alert(error.message || "Failed to update profile");
    } finally {
      setIsSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen w-full flex justify-center items-center bg-gray-200">
        <div className="text-green-600 font-bold animate-pulse">
          Loading Profile...
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      <div className="w-full max-w-md bg-[#F5F7F5] h-screen shadow-2xl relative flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-[#E3F1E4] pt-12 pb-24 px-6 rounded-b-[40px] relative z-0">
          <div className="flex items-center gap-4">
            <Link href="/homepage">
              <ArrowLeft
                className="text-gray-600 cursor-pointer hover:text-green-600 transition-colors"
                size={28}
              />
            </Link>
            <h1
              className={`${jost.className} text-2xl font-bold text-gray-600`}
            >
              My Profile
            </h1>
          </div>
        </div>

        {/* Avatar & Name */}
        <div className="relative z-10 -mt-16 flex flex-col items-center">
          <div className="p-1.5 bg-white rounded-full shadow-md">
            <div className="relative w-32 h-32 rounded-full overflow-hidden border-4 border-white shadow-inner bg-gray-100">
              <Image
                src={user?.avatar_url || "/images/default-avatar.png"}
                alt="Profile picture"
                fill
                className="object-cover"
              />
            </div>
          </div>
          <h2
            className={`${abhaya_libre.className} mt-3 text-2xl font-bold text-[#53B552]`}
          >
            {user?.username || "User Name"}
          </h2>
        </div>

        {/* Form Info */}
        <main className="flex-1 overflow-y-auto px-6 mt-6 pb-24 space-y-6">
          {/* Username */}
          <div className="flex flex-col">
            <label
              className={`${abhaya_libre.className} bg-[#6AC66B] text-white px-4 py-1 rounded-t-xl w-fit text-base font-bold tracking-wide shadow-sm z-10 ml-1`}
            >
              Username
            </label>
            <div
              className={`bg-white rounded-xl p-3 shadow-sm border transition-all ${
                isEditing
                  ? "border-green-300 ring-2 ring-green-100"
                  : "border-transparent"
              }`}
            >
              <input
                type="text"
                name="username"
                value={isEditing ? formData.username : user?.username || ""}
                onChange={handleChange}
                readOnly={!isEditing}
                className={`${abhaya_libre.className} w-full text-gray-700 outline-none bg-transparent px-2 font-semibold`}
              />
            </div>
          </div>

          {/* Email */}
          <div className="flex flex-col">
            <label
              className={`${abhaya_libre.className} bg-[#6AC66B] text-white px-4 py-1 rounded-t-xl w-fit text-base font-bold tracking-wide shadow-sm z-10 ml-1`}
            >
              Email
            </label>
            <div
              className={`bg-white rounded-xl p-3 shadow-sm border transition-all ${
                isEditing
                  ? "border-green-300 ring-2 ring-green-100"
                  : "border-transparent"
              } ${errors.email ? "border-red-500 bg-red-50" : ""}`}
            >
              <input
                type="email"
                name="email"
                value={isEditing ? formData.email : user?.email || ""}
                onChange={handleChange}
                readOnly={!isEditing}
                className={`${abhaya_libre.className} w-full text-gray-700 outline-none bg-transparent px-2 font-semibold`}
              />
            </div>
            {isEditing && errors.email && (
              <p className="text-red-500 text-xs mt-1 ml-2">{errors.email}</p>
            )}
          </div>

          {/* Đã xóa phần Phone Number ở đây */}

          {/* Button */}
          <div className="pt-4 flex justify-center">
            <button
              onClick={handleEditToggle}
              disabled={isSaving}
              className={`${jost.className} w-48 ${
                isEditing
                  ? "bg-[#53B552] text-white hover:bg-green-700"
                  : "bg-[#E3F1E4] text-[#5BB95B] hover:bg-[#5BB95B] hover:text-white"
              } font-bold py-3 rounded-full transition-all duration-300 shadow-sm text-lg flex justify-center items-center gap-2 cursor-pointer`}
            >
              {isSaving && <Loader2 className="animate-spin" size={20} />}
              {isEditing ? (isSaving ? "Saving..." : "Save") : "Edit Profile"}
            </button>
          </div>
        </main>

        {/* Footer */}
        <nav className="bg-white shadow-[0_-5px_15px_rgba(0,0,0,0.05)] sticky bottom-0 w-full z-20">
          <div className="h-1 bg-linear-to-r from-transparent via-green-200 to-transparent"></div>
          <div className="flex justify-around items-center py-3">
            <Link
              href="/homepage"
              className="flex flex-col items-center text-gray-400 hover:text-green-600 transition-colors"
            >
              <Home size={24} strokeWidth={2} />
              <span className={`${jost.className} text-xs font-medium mt-1`}>
                Home
              </span>
            </Link>
            <Link
              href="#"
              className="flex flex-col items-center text-gray-400 hover:text-green-600 transition-colors"
            >
              <MapPin size={24} strokeWidth={2} />
              <span className={`${jost.className} text-xs font-medium mt-1`}>
                Planning
              </span>
            </Link>
            <Link
              href="#"
              className="flex flex-col items-center text-gray-400 hover:text-green-600 transition-colors"
            >
              <Bot size={24} strokeWidth={2} />
              <span className={`${jost.className} text-xs font-medium mt-1`}>
                Ecobot
              </span>
            </Link>
            <div className="flex flex-col items-center text-[#53B552]">
              <User size={24} strokeWidth={2.5} />
              <span className={`${jost.className} text-xs font-bold mt-1`}>
                User
              </span>
            </div>
          </div>
        </nav>
      </div>
    </div>
  );
}
