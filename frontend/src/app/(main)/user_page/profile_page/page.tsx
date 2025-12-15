"use client";

import React, { useEffect, useState, useRef } from "react";
import Image from "next/image";
import { ArrowLeft, Loader2, Camera } from "lucide-react";
import { Jost, Abhaya_Libre } from "next/font/google";
import { useRouter } from "next/navigation";
import { api, UserProfile } from "@/lib/api";

const jost = Jost({ subsets: ["latin"] });
const abhaya_libre = Abhaya_Libre({
  weight: ["400", "500", "600", "800"],
  subsets: ["latin"],
});

export default function ProfilePage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const coverInputRef = useRef<HTMLInputElement>(null);

  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  // UI States
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");

  // Data States
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");

  // Avatar Data
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [previewAvatar, setPreviewAvatar] = useState<string | null>(null);

  //Cover Data
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [previewCover, setPreviewCover] = useState<string | null>(null);

  // Password States
  const [newPassword, setNewPassword] = useState("");
  const [oldPassword, setOldPassword] = useState("");
  const [errors, setErrors] = useState<{ email?: string; password?: string }>(
    {}
  );

  // 1. Fetch Data
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const userData = await api.getUserProfile();
        setUser(userData);
        setUsername(userData.username);
        setEmail(userData.email);
        setPreviewAvatar(userData.avt_url || "/images/default-avatar.png");
        setPreviewCover(userData.cover_url || null);
      } catch (error) {
        console.error(error);
        router.push("/login");
      } finally {
        setLoading(false);
      }
    };
    fetchUserData();
  }, [router]);

  // 2. Handle Avatar Click (Check Permission)
  const handleAvatarClick = () => {
    if (!isEditing) return;

    const hasPermission = localStorage.getItem("photoPermission");
    if (hasPermission !== "granted") {
      router.push("/permission/photo");
    } else {
      fileInputRef.current?.click();
    }
  };

  const handleCoverClick = () => {
    if (!isEditing) return;
    const hasPermission = localStorage.getItem("photoPermission");
    if (hasPermission !== "granted") {
      router.push("/permission/photo");
    } else {
      coverInputRef.current?.click();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 2 * 1024 * 1024) {
        alert("Please choose an image smaller than 2MB.");
        return;
      }
      setAvatarFile(file);
      setPreviewAvatar(URL.createObjectURL(file));
    }
  };

  const handleCoverFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        alert("Please choose a cover image smaller than 5MB.");
        return;
      }
      setCoverFile(file);
      setPreviewCover(URL.createObjectURL(file));
    }
  };

  // 3. Validation logic
  const validateForm = () => {
    let isValid = true;
    const newErrors: { email?: string; password?: string } = {};

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      newErrors.email = "Invalid email format.";
      isValid = false;
    }

    const isEmailChanged = email !== user?.email;
    const isPasswordChanged = newPassword.length > 0;

    if ((isEmailChanged || isPasswordChanged) && !oldPassword) {
      newErrors.password =
        "Current password is required to change Email or Password.";
      isValid = false;
    }

    setErrors(newErrors);
    return isValid;
  };

  // 4. Handle Save
  const handleEditToggle = async () => {
    // A. Enable edit mode (existing behavior)
    if (!isEditing) {
      if (user) {
        setUsername(user.username);
        setEmail(user.email);
        setPreviewAvatar(user.avt_url || "/images/default-avatar.png");
        setAvatarFile(null);
        setPreviewCover(user.cover_url || null);
        setCoverFile(null);
      }
      setNewPassword("");
      setOldPassword("");
      setSuccessMsg("");
      setIsEditing(true);
      return;
    }

    if (!validateForm()) return;

    try {
      setIsSaving(true);
      setSuccessMsg("");

      let newBlobName = null;
      let newAvatarUrl = null;
      if (avatarFile) {
        const uploadResponse = await api.uploadFile(
          avatarFile,
          "profile_avatar"
        );
        newBlobName = uploadResponse.blob_name;
        newAvatarUrl = uploadResponse.url;
      }

      let newCoverBlobName = null;
      let newCoverUrl = null;
      if (coverFile) {
        const uploadResponse = await api.uploadFile(coverFile, "profile_cover");
        newCoverBlobName = uploadResponse.blob_name;
        newCoverUrl = uploadResponse.url;
      }

      const promises = [];

      if (username !== user?.username || newBlobName || newCoverBlobName) {
        promises.push(
          api
            .updateUserProfile({
              username: username,
              ...(newBlobName && { avt_blob_name: newBlobName }),
              ...(newCoverBlobName && { cover_blob_name: newCoverBlobName }),
            })
            .then((res) => {
              setUser((prev) =>
                prev
                  ? {
                      ...prev,
                      username: res.username,
                      avt_url: newAvatarUrl || res.avt_url,
                      cover_url: newCoverUrl || res.cover_url,
                    }
                  : null
              );
              if (newAvatarUrl) {
                setPreviewAvatar(newAvatarUrl);
              } else if (res.avt_url) {
                setPreviewAvatar(res.avt_url);
              }
              if (newCoverUrl) {
                setPreviewCover(newCoverUrl);
              } else if (res.cover_url) {
                setPreviewCover(res.cover_url);
              }
            })
        );
      }

      const isEmailChanged = email !== user?.email;
      const isPasswordChanged = newPassword.length > 0;

      if (isEmailChanged || isPasswordChanged) {
        promises.push(
          api
            .updateCredentials({
              old_password: oldPassword,
              new_email: isEmailChanged ? email : undefined,
              new_password: isPasswordChanged ? newPassword : undefined,
            })
            .then((res) => {
              const updatedEmail = res.email;
              if (typeof updatedEmail === "string") {
                setUser((prev) =>
                  prev ? { ...prev, email: updatedEmail } : null
                );
              }
            })
        );
      }

      await Promise.all(promises);

      setSuccessMsg("Profile updated successfully!");
      setIsEditing(false);
      setNewPassword("");
      setOldPassword("");
      setAvatarFile(null);
      setCoverFile(null);
    } catch (error: unknown) {
      console.error("Update failed:", error);
      const message =
        error instanceof Error && error.message
          ? error.message
          : "Failed to update profile.";

      if (message.toLowerCase().includes("old password")) {
        setErrors((prev) => ({
          ...prev,
          password: "Incorrect current password.",
        }));
      } else {
        alert(message);
      }
    } finally {
      setIsSaving(false);
    }
  };

  if (loading)
    return (
      <div className="flex h-screen justify-center items-center text-green-600">
        Loading...
      </div>
    );

  const needsAuth = email !== user?.email || newPassword.length > 0;
  const avatarSrc = previewAvatar || "/images/default-avatar.png";

  return (
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      <div className="w-full max-w-md bg-[#F5F7F5] h-screen shadow-2xl relative flex flex-col overflow-hidden">
        <div className="relative w-full h-[230px] rounded-b-[40px] overflow-hidden bg-[#E3F1E4]">
          {previewCover ? (
            <Image
              src={previewCover}
              alt="Cover"
              fill
              className="object-cover"
              priority
            />
          ) : (
            <div className="absolute inset-0 bg-linear-to-br from-green-200 via-emerald-100 to-green-300" />
          )}
          <div className="absolute inset-0 bg-linear-to-b from-black/10 via-black/40 to-black/60" />

          <input
            type="file"
            hidden
            ref={coverInputRef}
            accept="image/*"
            onChange={handleCoverFileChange}
          />
          <input
            type="file"
            hidden
            ref={fileInputRef}
            accept="image/*"
            onChange={handleFileChange}
          />

          <div className="relative z-20 h-full flex flex-col px-6 pt-12 pb-8">
            <div className="flex items-center justify-between gap-3">
              <button
                type="button"
                onClick={() => router.back()}
                className="p-2 rounded-full bg-white/20 text-white hover:bg-white/40 transition"
              >
                <ArrowLeft size={20} />
              </button>
              <p
                className={`${jost.className} text-white text-lg font-semibold tracking-wide`}
              >
                My Profile
              </p>
              {isEditing ? (
                <button
                  type="button"
                  onClick={handleCoverClick}
                  className="flex items-center gap-2 bg-white/20 backdrop-blur px-3 py-1.5 rounded-full text-white text-xs font-semibold hover:bg-white/40 transition"
                >
                  <Camera size={16} />
                  Change cover
                </button>
              ) : (
                <div className="w-10" />
              )}
            </div>
          </div>
        </div>

        <div className="relative z-10 flex flex-col items-center -mt-16 px-6 gap-3">
          <div className="p-1.5 bg-white rounded-full shadow-xl">
            <div className="relative w-32 h-32 rounded-full border-4 border-white shadow-lg overflow-hidden bg-gray-100">
              <Image
                src={avatarSrc}
                alt="Avatar"
                fill
                sizes="128px"
                className="object-cover"
                priority
              />

              {isEditing && (
                <button
                  type="button"
                  onClick={handleAvatarClick}
                  className="absolute bottom-2 right-2 bg-white/90 text-[#53B552] p-2 rounded-full shadow-md hover:bg-white"
                >
                  <Camera size={16} />
                </button>
              )}
            </div>
          </div>
        </div>

        <main className="flex-1 overflow-y-auto px-6 mt-6 pb-24 space-y-5">
          <div className="flex flex-col">
            <label
              className={`${abhaya_libre.className} bg-[#6AC66B] text-white px-4 py-1 rounded-t-xl w-fit text-base font-bold ml-1`}
            >
              Username
            </label>
            <div
              className={`bg-white rounded-xl p-3 shadow-sm border transition-all ${
                isEditing ? "border-green-300" : "border-transparent"
              }`}
            >
              <input
                type="text"
                value={isEditing ? username : user?.username || ""}
                onChange={(e) => setUsername(e.target.value)}
                readOnly={!isEditing}
                className={`${abhaya_libre.className} w-full text-gray-700 outline-none bg-transparent px-2 font-semibold`}
              />
            </div>
          </div>

          <div className="flex flex-col">
            <label
              className={`${abhaya_libre.className} bg-[#6AC66B] text-white px-4 py-1 rounded-t-xl w-fit text-base font-bold ml-1`}
            >
              Email
            </label>
            <div
              className={`bg-white rounded-xl p-3 shadow-sm border transition-all ${
                isEditing ? "border-green-300" : "border-transparent"
              } ${errors.email ? "border-red-500 bg-red-50" : ""}`}
            >
              <input
                type="email"
                value={isEditing ? email : user?.email || ""}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (errors.email)
                    setErrors((prev) => ({ ...prev, email: undefined }));
                }}
                readOnly={!isEditing}
                className={`${abhaya_libre.className} w-full text-gray-700 outline-none bg-transparent px-2 font-semibold`}
              />
            </div>
            {isEditing && errors.email && (
              <p className="text-red-500 text-xs mt-1 ml-2">{errors.email}</p>
            )}
          </div>

          <div className="flex flex-col">
            <label
              className={`${abhaya_libre.className} bg-[#6AC66B] text-white px-4 py-1 rounded-t-xl w-fit text-base font-bold ml-1`}
            >
              Password
            </label>
            <div
              className={`bg-white rounded-xl p-3 shadow-sm border transition-all ${
                isEditing ? "border-green-300" : "border-transparent"
              }`}
            >
              <input
                type="password"
                value={isEditing ? newPassword : "dummy_password"}
                onChange={(e) => setNewPassword(e.target.value)}
                readOnly={!isEditing}
                placeholder={isEditing ? "Leave blank to keep current" : ""}
                className={`${abhaya_libre.className} w-full text-gray-700 outline-none bg-transparent px-2 font-semibold tracking-widest`}
              />
            </div>
          </div>

          {isEditing && needsAuth && (
            <div className="flex flex-col animate-in fade-in slide-in-from-top-2 duration-300">
              <label
                className={`${abhaya_libre.className} bg-gray-500 text-white px-4 py-1 rounded-t-xl w-fit text-sm font-bold ml-1`}
              >
                Current Password (Required to save)
              </label>
              <div
                className={`bg-white rounded-xl p-3 shadow-sm border border-gray-300 ${
                  errors.password ? "border-red-500 bg-red-50" : ""
                }`}
              >
                <input
                  type="password"
                  value={oldPassword}
                  onChange={(e) => {
                    setOldPassword(e.target.value);
                    if (errors.password)
                      setErrors((prev) => ({ ...prev, password: undefined }));
                  }}
                  placeholder="Enter current password"
                  className={`${abhaya_libre.className} w-full text-gray-700 outline-none bg-transparent px-2 font-semibold`}
                />
              </div>
              {errors.password && (
                <p className="text-red-500 text-xs mt-1 ml-2">
                  {errors.password}
                </p>
              )}
            </div>
          )}

          <div className="pt-4 flex flex-col items-center pb-8">
            {successMsg && (
              <p
                className={`${jost.className} text-green-600 font-bold mb-3 animate-in fade-in slide-in-from-bottom-2`}
              >
                {successMsg}
              </p>
            )}
            <button
              onClick={handleEditToggle}
              disabled={isSaving}
              className={`${jost.className} w-48 ${
                isEditing
                  ? "bg-[#53B552] text-white hover:bg-green-700"
                  : "bg-[#E3F1E4] text-[#5BB95B] hover:bg-[#5BB95B] hover:text-white"
              } font-bold py-3 rounded-full transition-all duration-300 shadow-sm text-lg flex justify-center items-center gap-2`}
            >
              {isSaving && <Loader2 className="animate-spin" size={20} />}
              {isEditing
                ? isSaving
                  ? "Saving..."
                  : "Save Changes"
                : "Edit Profile"}
            </button>
          </div>
        </main>
      </div>
    </div>
  );
}
