"use client";

import { useState } from "react";
import Link from "next/link";
import { FiMail, FiLock } from "react-icons/fi";
import { useRouter } from "next/navigation";
import {
  Poppins,
  Knewave,
  Josefin_Sans,
  Gotu,
  Abhaya_Libre,
} from "next/font/google";

export const poppins = Poppins({ subsets: ["latin"], weight: ["400", "500", "600", "700"], variable: "--font-poppins" });
export const knewave = Knewave({ subsets: ["latin"], weight: ["400"], variable: "--font-knewave" });
export const josefin_sans = Josefin_Sans({ subsets: ["latin"], weight: ["400", "500", "600", "700"], variable: "--font-josefin" });
export const gotu = Gotu({ subsets: ["latin"], weight: ["400"], variable: "--font-gotu" });
export const abhaya_libre = Abhaya_Libre({ subsets: ["latin"], weight: ["400", "500", "600", "700", "800"], variable: "--font-abhaya" });

export default function ForgetPasswordPage() {
  const [mode, setMode] = useState<"forget" | "change">("forget");
  const [email, setEmail] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleForgetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/forgetpassword/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || "Failed to send reset link. Please try again.");
        return;
      }

      alert(data.message);
      router.push("/login");
    } catch (err) {
      console.error(err);
      setError("Failed to send reset link. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (newPassword !== confirmPassword) {
      setError("New passwords do not match");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/forgetpassword/changepassword/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || "Failed to change password");
        return;
      }

      alert(data.message || "Password changed successfully!");
      router.push("/login");
    } catch (err) {
      console.error(err);
      setError("Failed to change password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex justify-center bg-green-100">
      <main className="w-full max-w-md bg-white min-h-screen shadow-2xl flex flex-col items-center justify-center px-6 py-8 overflow-hidden relative">
        {/* Logo & Slogan */}
        <div className="text-center mb-8">
          <h1 className={`${knewave.className} text-5xl text-green-600 mb-2`}>EcomoveX</h1>
          <p className={`${josefin_sans.className} text-green-600 text-xl leading-relaxed`}>
            {mode === "forget" ? "Reset your password" : "Change your password"}
          </p>
        </div>

        {/* FORM */}
        {mode === "forget" && (
          <form onSubmit={handleForgetPassword} className="w-full flex flex-col gap-5">
            <div className="w-full relative">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                className={`${abhaya_libre.className} w-full border-2 bg-green-100 border-transparent focus:border-green-500 text-green-700 rounded-full px-5 py-3 text-lg font-medium outline-none transition-all placeholder:text-green-700/60 pl-12`}
                required
              />
              <FiMail className="absolute left-4 top-1/2 -translate-y-1/2 text-green-700" size={22} />
            </div>

            {error && <p className="text-red-500 text-sm text-center bg-red-50 p-3 rounded-lg border border-red-200">{error}</p>}

            <button
              type="submit"
              disabled={loading || !email}
              className={`${abhaya_libre.className} w-full ${loading ? "bg-gray-400" : "bg-green-500 hover:bg-green-600 shadow-md hover:shadow-lg"} text-white rounded-full py-3 text-lg font-medium transition-all transform active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {loading ? "Sending..." : "Send reset link"}
            </button>

            <div className="text-center px-2 mt-2">
              <button
                type="button"
                onClick={() => setMode("change")}
                className={`${abhaya_libre.className} text-lg text-green-600 hover:text-green-800 underline-offset-2 hover:underline transition-all`}
              >
                I already have a password / Change password
              </button>
            </div>
          </form>
        )}

        {mode === "change" && (
          <form onSubmit={handleChangePassword} className="w-full flex flex-col gap-5">
            <div className="w-full relative">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Your email"
                className={`${abhaya_libre.className} w-full border-2 bg-green-100 border-transparent focus:border-green-500 text-green-700 rounded-full px-5 py-3 text-lg font-medium outline-none transition-all placeholder:text-green-700/60 pl-12`}
                required
              />
              <FiMail className="absolute left-4 top-1/2 -translate-y-1/2 text-green-700" size={22} />
            </div>

            <div className="w-full relative">
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="Current password"
                className={`${abhaya_libre.className} w-full border-2 bg-green-100 border-transparent focus:border-green-500 text-green-700 rounded-full px-5 py-3 text-lg font-medium outline-none transition-all placeholder:text-green-700/60 pl-12`}
                required
              />
              <FiLock className="absolute left-4 top-1/2 -translate-y-1/2 text-green-700" size={22} />
            </div>

            <div className="w-full relative">
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="New password"
                className={`${abhaya_libre.className} w-full border-2 bg-green-100 border-transparent focus:border-green-500 text-green-700 rounded-full px-5 py-3 text-lg font-medium outline-none transition-all placeholder:text-green-700/60 pl-12`}
                required
              />
              <FiLock className="absolute left-4 top-1/2 -translate-y-1/2 text-green-700" size={22} />
            </div>

            <div className="w-full relative">
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm new password"
                className={`${abhaya_libre.className} w-full border-2 bg-green-100 border-transparent focus:border-green-500 text-green-700 rounded-full px-5 py-3 text-lg font-medium outline-none transition-all placeholder:text-green-700/60 pl-12`}
                required
              />
              <FiLock className="absolute left-4 top-1/2 -translate-y-1/2 text-green-700" size={22} />
            </div>

            {error && <p className="text-red-500 text-sm text-center bg-red-50 p-3 rounded-lg border border-red-200">{error}</p>}

            <button
              type="submit"
              disabled={loading || !email || !currentPassword || !newPassword || !confirmPassword}
              className={`${abhaya_libre.className} w-full ${loading ? "bg-gray-400" : "bg-green-500 hover:bg-green-600 shadow-md hover:shadow-lg"} text-white rounded-full py-3 text-lg font-medium transition-all transform active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {loading ? "Changing..." : "Change password"}
            </button>

            <div className="text-center px-2 mt-2">
              <button
                type="button"
                onClick={() => setMode("forget")}
                className={`${abhaya_libre.className} text-lg text-green-600 hover:text-green-800 underline-offset-2 hover:underline transition-all`}
              >
                Back to forget password
              </button>
            </div>
          </form>
        )}
      </main>
    </div>
  );
}
