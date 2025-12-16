"use client";
import { Knewave, Josefin_Sans, Abhaya_Libre, Gotu } from "next/font/google";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, ApiHttpError } from "@/lib/api";

const knewave = Knewave({
  subsets: ["latin"],
  weight: ["400"],
});

const abhaya_libre = Abhaya_Libre({
  subsets: ["latin"],
  weight: ["700"],
});

const josefin_sans = Josefin_Sans({
  subsets: ["latin"],
  weight: ["700"],
});

const gotu = Gotu({
  subsets: ["latin"],
  weight: ["400"],
});

export default function ForgetPassword() {
  const [form, setForm] = useState({
    username: "",
    email: "",
  });
  const router = useRouter();
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm({
      ...form,
      [name]: value,
    });
    setError("");
    setSuccessMessage("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await api.resetPassword(form.email, form.username);
      
      // Show success message and redirect to login
      setSuccessMessage("A new temporary password has been sent to your email. Please check your inbox. Redirecting to login...");
      setTimeout(() => {
        router.push("/login");
      }, 3000);
    } catch (err: unknown) {
      console.error("Reset password error:", err);
      
      if (err instanceof ApiHttpError) {
        if (err.status === 404) {
          setError("No account found with this email address.");
        } else if (err.status === 400) {
          setError("Username does not match the provided email.");
        } else {
          setError(err.message || "Failed to reset password. Please try again.");
        }
      } else {
        setError("Network error. Please check your connection and try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    // 1. Wrapper nền xám cho Desktop
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      {/* 2. Khung ứng dụng Mobile (max-w-md) */}
      <main className="w-full max-w-md bg-white min-h-screen shadow-2xl flex flex-col items-center justify-center px-6 py-8 overflow-y-auto">
        {/* Logo & Slogan */}
        <div className="text-center mb-8">
          <h1 className={`${knewave.className} text-5xl text-green-600 mb-2`}>
            Ecomove<span className="text-green-500">X</span>
          </h1>
          <p
            className={`${josefin_sans.className} text-green-600 text-xl leading-relaxed`}
          >
            Your Trip. Your impact. Your choice.
          </p>
        </div>

        {/* Header Text */}
        <div className="text-center mb-6">
          <h2 className={`${abhaya_libre.className} text-2xl text-green-700 font-bold mb-2`}>
            Forgot your password?
          </h2>
          <p className={`${gotu.className} text-green-600 text-base`}>
            Enter your username and email to reset your password
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4">
          {/* Username Field */}
          <div className="w-full">
            <input
              type="text"
              name="username"
              value={form.username}
              onChange={handleChange}
              placeholder="Enter your username"
              className={`${abhaya_libre.className} w-full border-2 bg-green-100 border-transparent focus:border-green-500 text-green-700 rounded-full px-5 py-3 text-lg font-medium outline-none transition-all placeholder:text-green-700/60`}
              required
            />
          </div>

          {/* Email Field */}
          <div className="w-full">
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              placeholder="Enter your email"
              className={`${abhaya_libre.className} w-full border-2 bg-green-100 border-transparent focus:border-green-500 text-green-700 rounded-full px-5 py-3 text-lg font-medium outline-none transition-all placeholder:text-green-700/60`}
              required
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !form.username || !form.email}
            className={`${abhaya_libre.className} w-full ${
              loading
                ? "bg-gray-400"
                : "bg-green-500 hover:bg-green-600 shadow-md hover:shadow-lg"
            } text-white rounded-full py-3 text-lg font-medium transition-all transform active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed mt-2`}
          >
            {loading ? "Sending..." : "Reset Password"}
          </button>

          {/* Success Message */}
          {successMessage && (
            <p className="text-green-700 text-sm text-center bg-green-50 p-3 rounded-lg border border-green-200">
              {successMessage}
            </p>
          )}

          {/* Error Message */}
          {error && (
            <p className="text-red-500 text-sm text-center bg-red-50 p-3 rounded-lg border border-red-200">
              {error}
            </p>
          )}
        </form>

        {/* Back to Login Link */}
        <div className="mt-8 text-center">
          <p className={`${gotu.className} text-green-500 text-lg`}>
            Remember your password?{" "}
            <Link
              href="/login"
              className={`${josefin_sans.className} font-bold text-green-600 hover:text-green-800 underline`}
            >
              Login
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}
