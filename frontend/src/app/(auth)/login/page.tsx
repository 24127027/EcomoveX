"use client";
import { useState } from "react";
import Link from "next/link";
import { Eye, EyeOff } from "lucide-react";
import { api, ApiHttpError, ApiValidationError } from "@/lib/api";
import { useRouter } from "next/navigation";
import {
  validateLoginForm,
  ValidationErrors,
  getFriendlyErrorMessage,
} from "@/lib/validation";
import {
  Poppins,
  Knewave,
  Josefin_Sans,
  Gotu,
  Abhaya_Libre,
} from "next/font/google";

export const poppins = Poppins({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-poppins",
});

export const knewave = Knewave({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--font-knewave",
});

export const josefin_sans = Josefin_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-josefin",
});

export const gotu = Gotu({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--font-gotu",
});

export const abhaya_libre = Abhaya_Libre({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-abhaya",
});

export default function SigninPage() {
  const [form, setForm] = useState({
    username: "",
    password: "",
    email: "",
  });
  const [validationErrors, setValidationErrors] = useState<
    Pick<ValidationErrors, "email" | "password">
  >({});
  const [loading, setLoading] = useState(false);
  const [serverError, setServerError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const router = useRouter();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm({
      ...form,
      [name]: value,
    });

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

    const errors = validateLoginForm({
      email: form.email,
      password: form.password,
    });
    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      setLoading(false);
      return;
    }

    try {
      const response = await api.login({
        email: form.email,
        password: form.password,
      });

      if (!response?.access_token) {
        throw new Error("Missing access token in response");
      }

      localStorage.setItem("access_token", response.access_token);
      localStorage.setItem("user_id", response.user_id.toString());
      localStorage.setItem("user_role", response.role || "");

      let role = response.role;
      if (!role) {
        try {
          const profile = await api.getUserProfile();
          role = profile.role || "";
        } catch (profileError) {
          console.warn("Failed to fetch user profile for role", profileError);
        }
      }

      if (role) {
        localStorage.setItem("user_role", role);
      }

      const isAdmin = (role || "").toLowerCase() === "admin";
      if (isAdmin) {
        router.push("/admin");
      } else {
        router.push("/allow_permission/location_permission");
      }
    } catch (err: unknown) {
      console.error("Login error:", err);

      if (err instanceof ApiHttpError) {
        if (err.status === 401) {
          setServerError("Incorrect email or password. Please check again.");
        } else if (err.status === 404) {
          setServerError("Account does not exist.");
        } else {
          setServerError(err.message);
        }
      }
      // Kiểm tra lỗi Validation (giữ nguyên logic cũ)
      else if (err instanceof ApiValidationError) {
        setValidationErrors({
          [err.field]: err.message,
        } as Pick<ValidationErrors, "email" | "password">);
      }
      // Lỗi không xác định (mất mạng, code lỗi...)
      else {
        const msg = getFriendlyErrorMessage(err);
        setServerError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    // 1. Wrapper nền xám cho Desktop
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      {/* 2. Khung ứng dụng Mobile (max-w-md) */}
      <main className="w-full max-w-md bg-white min-h-screen shadow-2xl flex flex-col items-center justify-center px-6 py-8 overflow-hidden relative">
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

        {/* Form Login */}
        <form onSubmit={handleSubmit} className="w-full flex flex-col gap-5">
          {/* Email Field */}
          <div className="w-full">
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              placeholder="Enter your email"
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
          <div className="w-full relative">
            <input
              type={showPassword ? "text" : "password"}
              value={form.password}
              name="password"
              onChange={handleChange}
              placeholder="Enter your password"
              className={`${abhaya_libre.className} w-full border-2 ${
                validationErrors.password
                  ? "border-red-500 bg-red-50"
                  : "bg-green-100 border-transparent focus:border-green-500"
              } text-green-700 rounded-full px-5 py-3 text-lg font-medium outline-none transition-all pr-12 placeholder:text-green-700/60`}
              required
            />

            {/* Nút ẩn hiện password: Dùng absolute để căn phải */}
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-green-700 hover:text-green-900 transition-colors"
            >
              {showPassword ? <EyeOff size={22} /> : <Eye size={22} />}
            </button>

            {validationErrors.password && (
              <p className="text-red-500 text-sm mt-1 ml-4">
                {validationErrors.password}
              </p>
            )}
          </div>

          {/* Forgot Password Link */}
          <div className="text-right px-2">
            <Link
              href="../forget_Password"
              className={`${abhaya_libre.className} text-lg text-green-600 hover:text-green-800 underline-offset-2 hover:underline transition-all`}
            >
              Forgot Password?
            </Link>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !form.email || !form.password}
            className={`${abhaya_libre.className} w-full ${
              loading
                ? "bg-gray-400"
                : "bg-green-500 hover:bg-green-600 shadow-md hover:shadow-lg"
            } text-white rounded-full py-3 text-lg font-medium transition-all transform active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed mt-2`}
          >
            {loading ? "Logging in..." : "Login"}
          </button>

          {/* Server Error Message */}
          {serverError && (
            <p className="text-red-500 text-sm text-center bg-red-50 p-3 rounded-lg border border-red-200">
              {serverError}
            </p>
          )}
        </form>

        {/* Sign Up Link */}
        <div className="mt-10 text-center">
          <p className={`${gotu.className} text-green-500 text-lg`}>
            Not a member?{" "}
            <Link
              href="../signup"
              className={`${josefin_sans.className} font-bold text-green-600 hover:text-green-800 underline`}
            >
              Sign up
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}
