"use client";
import { Knewave, Josefin_Sans, Abhaya_Libre, Poppins } from "next/font/google";
import { useState } from "react";
import Link from "next/link";
// Đảm bảo đường dẫn import này đúng
import { Gotu } from "next/font/google";
import { api, ApiValidationError } from "@/lib/api";
import { useRouter } from "next/navigation";
import {
  validateSignupForm,
  ValidationErrors,
  getFriendlyErrorMessage,
} from "@/lib/validation";

const knewave = Knewave({
  subsets: ["latin"],
  weight: ["400"],
});

export const gotu = Gotu({
  subsets: ["latin"],
  weight: ["400"],
});

export const poppins = Poppins({
  subsets: ["latin"],
  weight: ["300"],
});
const abhaya_libre = Abhaya_Libre({
  subsets: ["latin"],
  weight: ["700"],
});

const josefin_sans = Josefin_Sans({
  subsets: ["latin"],
  weight: ["700"],
});

export default function SignupPage() {
  const [form, setForm] = useState({
    username: "",
    password: "",
    authorize: "",
    email: "",
  });
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>(
    {}
  );
  const [loading, setLoading] = useState(false);
  const [serverError, setServerError] = useState("");
  const router = useRouter();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: value,
    }));

    setValidationErrors((prev) => ({
      ...prev,
      [name]: undefined,
    }));

    setServerError("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setServerError("");

    const errors = validateSignupForm(form);
    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      setLoading(false);
      return;
    }

    try {
      const response = await api.signup({
        username: form.username,
        email: form.email,
        password: form.password,
      });
      if (!response?.access_token) {
        throw new Error("Missing access token in response");
      }

      localStorage.setItem("access_token", response.access_token);

      if (response.user_id != null) {
        localStorage.setItem("user_id", response.user_id.toString());
      }

      router.replace("/allow_permission/location_permission");
    } catch (err: any) {
      if (err instanceof ApiValidationError) {
        setValidationErrors({
          [err.field]: err.message,
        });
      } else if (
        err.message?.includes("already exists") ||
        err.message?.includes("Failed to create new user") ||
        err.status === 500
      ) {
        setServerError("Username already exists. Please choose another.");
      } else {
        setServerError(getFriendlyErrorMessage(err));
      }
      console.error("Signup error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    // 1. WRAPPER NGOÀI CÙNG: Nền xám, căn giữa
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      {/* 2. KHUNG APP: max-w-md, nền trắng, đổ bóng */}
      <main className="w-full max-w-md bg-white min-h-screen shadow-2xl flex flex-col items-center justify-center px-6 py-8 overflow-y-auto">
        {/* Header / Logo */}
        <div className="text-center mb-6">
          <h1 className={`${knewave.className} text-5xl text-green-600 mb-2`}>
            Ecomove<span className="text-green-500">X</span>
          </h1>
          <p
            className={`${josefin_sans.className} text-green-600 text-xl leading-relaxed`}
          >
            Your Trip. Your impact. Your choice.
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-full">
          {/* Username Field */}
          <div className="w-full">
            <input
              type="text"
              name="username"
              value={form.username}
              onChange={handleChange}
              placeholder="Enter your username"
              className={`${abhaya_libre.className} w-full border-2 ${
                validationErrors.username
                  ? "border-red-500 bg-red-50"
                  : "bg-green-100 border-transparent focus:border-green-500"
              } text-green-700 rounded-full px-5 py-3 text-lg font-medium outline-none transition-all placeholder:text-green-700/60`}
              required
            />
            {validationErrors.username && (
              <p className="text-red-500 text-sm mt-1 ml-4">
                {validationErrors.username}
              </p>
            )}
          </div>

          {/* Email Field */}
          <div className="w-full">
            <input
              type="email"
              value={form.email}
              onChange={handleChange}
              placeholder="Enter your email"
              name="email"
              className={`${abhaya_libre.className} w-full border-2 ${
                validationErrors.email
                  ? "border-red-500 bg-red-50"
                  : "bg-green-100 border-transparent focus:border-green-500"
              } text-green-700 rounded-full px-5 py-3 text-lg font-medium outline-none transition-all placeholder:text-green-700/60`}
              required
            />
            {validationErrors.email && (
              <p className="text-red-500 text-sm mt-1 ml-4">
                {validationErrors.email}
              </p>
            )}
          </div>

          {/* Password Field */}
          <div className="w-full">
            <input
              type="password"
              value={form.password}
              name="password"
              onChange={handleChange}
              placeholder="Enter your password (min 6 chars)"
              className={`${abhaya_libre.className} w-full border-2 ${
                validationErrors.password
                  ? "border-red-500 bg-red-50"
                  : "bg-green-100 border-transparent focus:border-green-500"
              } text-green-700 rounded-full px-5 py-3 text-lg font-medium outline-none transition-all placeholder:text-green-700/60`}
              required
            />
            {validationErrors.password && (
              <p className="text-red-500 text-sm mt-1 ml-4">
                {validationErrors.password}
              </p>
            )}
          </div>

          {/* Confirm Password Field */}
          <div className="w-full">
            <input
              type="password"
              value={form.authorize}
              name="authorize"
              onChange={handleChange}
              placeholder="Confirm your password"
              className={`${abhaya_libre.className} w-full border-2 ${
                validationErrors.authorize
                  ? "border-red-500 bg-red-50"
                  : "bg-green-100 border-transparent focus:border-green-500"
              } text-green-700 rounded-full px-5 py-3 text-lg font-medium outline-none transition-all placeholder:text-green-700/60`}
              required
              disabled={!form.password}
            />
            {validationErrors.authorize && (
              <p className="text-red-500 text-sm mt-1 ml-4">
                {validationErrors.authorize}
              </p>
            )}
          </div>

          {/* Submit Button */}
          <button
            disabled={
              loading ||
              !form.username ||
              !form.email ||
              !form.password ||
              !form.authorize
            }
            type="submit"
            className={`${abhaya_libre.className} w-full ${
              loading
                ? "bg-gray-400"
                : "bg-green-500 hover:bg-green-600 shadow-md"
            } text-white rounded-full py-3 text-lg font-medium transition-all transform active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed mt-2`}
          >
            {loading ? "Signing up..." : "Sign up"}
          </button>

          {/* Server Error Message */}
          {serverError && (
            <p className="text-red-500 text-sm mt-2 text-center bg-red-50 p-3 rounded-lg border border-red-200">
              {serverError}
            </p>
          )}
        </form>

        {/* Login Link */}
        <div className="mt-8 text-center">
          <p className={`${gotu.className} text-green-500 text-lg`}>
            Have an account?{" "}
            <Link
              href="../login"
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
