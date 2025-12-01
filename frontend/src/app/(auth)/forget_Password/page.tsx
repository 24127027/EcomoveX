"use client";
import { Knewave, Josefin_Sans, Abhaya_Libre, Poppins } from "next/font/google";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { FiMail } from "react-icons/fi";
const knewave = Knewave({
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

export default function ForgetPassword() {
  const [form, setForm] = useState({
    username: "",
    password: "",
    authorize: "",
    email: "",
  });
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      // Here you would typically make an API call to your
      // For now, we'll just simulate the process
      await new Promise((resolve) => setTimeout(resolve, 1500));

      // Show success message and redirect to login
      alert("Password reset link has been sent to your email");
      router.push("/login");
    } catch (err) {
      setError("Failed to send reset link. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Forgot your password?
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Enter your email address and we'll send you a link to reset your
            password.
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <FiMail className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="appearance-none rounded relative block w-full px-3 py-2 pl-10 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Email address"
              />
            </div>
          </div>

          {error && (
            <div className="text-red-500 text-sm text-center">{error}</div>
          )}

          <div>
            <button
              type="submit"
              disabled={loading}
              className={`group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white ${
                loading
                  ? "bg-blue-400 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              }`}
            >
              {loading ? "Sending..." : "Send reset link"}
            </button>
          </div>
        </form>

        <div className="text-center">
          <Link
            href="/login"
            className="font-medium text-blue-600 hover:text-blue-500"
          >
            Back to login
          </Link>
        </div>
      </div>
    </div>
  );
}
