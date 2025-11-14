"use client";
import {
  Knewave,
  Josefin_Sans,
  Abhaya_Libre,
  Poppins,
  Gotu,
  Jost,
} from "next/font/google";
import { Home, MapPin, Bot, User } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import { Search, Heart, Bookmark, Star } from "lucide-react";
export const gotu = Gotu({
  subsets: ["latin"],
  weight: ["400"],
});
export const jost = Jost({
  subsets: ["latin"],
  weight: ["700"],
});
export const abhaya_libre = Abhaya_Libre({
  subsets: ["latin"],
  weight: ["700"],
});

export const poppins = Poppins({
  subsets: ["latin"],
  weight: ["300"],
});
export const josefin_sans = Josefin_Sans({
  subsets: ["latin"],
  weight: ["700"],
});

export const knewave = Knewave({
  subsets: ["latin"],
  weight: ["400"],
});

export default function HomePage() {
  const handleChange = () => {};
  const [heart, setHeart] = useState(false);
  const [bookMark, setBookMark] = useState(false);
  return (
    <div className="bg-gray-50 min-h-screen">
      <header className="bg-[#53B552] px-4 pt-5 pb-6 shadow-md">
        <div className={`flex justify-between items-center gap-4`}>
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-gray-400" />
            <input
              type="text"
              className={`${abhaya_libre.className} w-full rounded-full py-2 pl-10 pr-3 text-sm
            bg-white text-black focus:outline-none focus:ring-2 focus:ring-green-300 placeholder:text-green-700 placeholder:font-semibold`}
              placeholder="Search for an eco-friendly place"
              onChange={handleChange}
            />
          </div>
          <div
            className={`${knewave.className} text-white font-bold text-2xl select-none`}
          >
            EcomoveX
          </div>
        </div>
        <div className="flex justify-center gap-3 mt-4 flex-wrap">
          {["Café", "Restaurant", "Park", "Hotel", "Shopping"].map((i) => (
            <button
              key={i}
              className={`${jost.className} cursor-pointer  bg-white text-[#53B552] rounded-full px-4 py-1 text-sm font-medium hover:text-white hover:bg-green-500`}
            >
              {i}
            </button>
          ))}
        </div>
      </header>
      <main className={`p-4 flex flex-col gap-5`}>
        <section
          className={`bg-[#F9FFF9] rounded-xl shadow-sm p-4 border border-green-100`}
        >
          <h2
            className={`${jost.className} font-bold text-green-600 uppercase mb-3 text-xl tracking-wide`}
          >
            Most Visited Green Places
          </h2>
          <div className="relative w-full h-48 rounded-lg overflow-hidden">
            <Image
              src="/images/tao-dan-park.png"
              alt="Tao Dan Park"
              layout="fill"
              objectFit="cover"
            />
          </div>
          <div className="flex gap-2 justify-between items-center mt-3">
            <div className="flex gap-3">
              <Heart
                className={`${
                  heart
                    ? "fill-green-600 stroke-green-600 scale-110"
                    : "stroke-green-600"
                } cursor-pointer transition-all size-6 text-green-600 strokeWidth={1.5} hover:fill-green-600 `}
                onClick={() => setHeart(!heart)}
              />
              <Bookmark
                onClick={() => setBookMark(!bookMark)}
                className={`${
                  bookMark
                    ? "fill-green-600 stroke-green-600 scale-110"
                    : "stroke-green-600"
                } cursor-pointer transition-all size-6 text-green-600 strokeWidth={1.5} hover:fill-green-600 `}
              />
            </div>
            <div className="text-right">
              <p
                className={`${abhaya_libre.className} font-semibold text-gray-800`}
              >
                Tao Dan Park
              </p>
              <p className={`${abhaya_libre.className} text-sm text-gray-500`}>
                2km
              </p>
            </div>
          </div>
          <div className="flex justify-center gap-2 mt-4">
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
            <div className="w-2 h-2 rounded-full bg-gray-200"></div>
            <div className="w-2 h-2 rounded-full bg-gray-200"></div>
            <div className="w-2 h-2 rounded-full bg-gray-200"></div>
            <div className="w-2 h-2 rounded-full bg-gray-200"></div>
            <div className="w-2 h-2 rounded-full bg-gray-200"></div>
          </div>
        </section>
        <section className={`grid grid-cols-2 gap-4`}>
          <div className="bg-linear-to-b from-green-500 to-green-50 rounded-xl p-4 text-black flex flex-col shadow-lg">
            <span className={`${abhaya_libre.className} text-xl opacity-90`}>
              Your last trip
            </span>
            <div className="flex items-center justify-between mt-1">
              <h3
                className={`${abhaya_libre.className} text-2xl font-bold mt-1 uppercase`}
              >
                Hoi An{" "}
              </h3>
              <div className={`flex items-center gap-1 mt-1`}>
                <span
                  className={`${abhaya_libre.className} text-xl font-medium`}
                >
                  4.5
                </span>
                <svg
                  className="size-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  {/* Định nghĩa gradient */}
                  <defs>
                    <linearGradient
                      id="starGradient"
                      x1="0%"
                      y1="0%"
                      x2="0%"
                      y2="100%"
                    >
                      {/* Màu vàng ở đỉnh ngôi sao */}
                      <stop offset="0%" stopColor="#FACC15" />{" "}
                      {/* yellow-400 */}
                      {/* Chuyển dần sang trắng ở đáy ngôi sao */}
                      <stop offset="100%" stopColor="#FFFFFF" /> {/* white */}
                    </linearGradient>
                  </defs>

                  {/* Đường viền ngôi sao (màu vàng) */}
                  <path
                    d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"
                    stroke="#FACC15" // yellow-400
                    strokeWidth="1.5"
                    fill="url(#starGradient)" // Áp dụng gradient đã định nghĩa
                  />
                </svg>{" "}
              </div>
            </div>
            <button className="cursor-pointer bg-white text-[#53B552] rounded-full py-2 text-sm font-semibold mt-3 w-full hover:text-white hover:bg-green-600">
              Plan Another Green Trip
            </button>
          </div>
          <div className="bg-linear-to-b from-green-50 to-green-400 rounded-xl p-4 shadow-sm border border-gray-100 flex flex-col items-center justify-center text-center">
            <h3
              className={`${abhaya_libre.className} text-green-700 font-semibold text-xl uppercase leading-tight`}
            >
              Nearby Eco-Friendly Spots
            </h3>
            <button
              className={`${jost.className} bg-green-600 text-white rounded-full px-5 py-2 text-sm font-semibold mt-4 hover:text-green-500 hover:bg-white cursor-pointer`}
            >
              Search Now
            </button>
          </div>
        </section>
        <section
          className={`${jost.className} bg-[#F9FFF9] rounded-xl shadow-sm p-4 border border-green-100 flex justify-between items-center`}
        >
          <div className="flex-1 pr-4">
            <h3 className="text-green-700 font-semibold">
              Explore Local Green Activities
            </h3>
            <p className="text-gray-600 text-sm mt-1">
              Discover eco-friendly experiences near you and make every trip
              meaningful.
            </p>
          </div>
          <button className="border cursor-pointer border-green-500 text-green-500 rounded-full px-5 py-2 text-sm font-semibold hover:bg-green-500 hover:text-white">
            Explore
          </button>
        </section>
      </main>
      <footer
        className={`fixed bottom-0 left-0 right-0 bg-white shadow-[0_-2px_6px_rgba(0,0,0,0.05)] ${poppins.className}`}
      >
        <div className="h-0.5 bg-linear-to-r from-transparent via-green-300 to-transparent opacity-70"></div>
        <div className="flex justify-around items-center px-2 pt-2 pb-3">
          <Link
            href="#"
            className="flex flex-col items-center justify-center w-1/4 text-green-600"
          >
            <Home className="size-6 select-none" strokeWidth={2.0} />
            <span className="text-xs font-medium mt-0.5">Home</span>
          </Link>

          <Link
            href="#"
            className="flex flex-col items-center justify-center w-1/4 text-gray-400"
          >
            <MapPin
              className="size-6 text-gray-400 cursor-pointer transition-all duration-200 hover:text-green-600 hover:scale-110"
              strokeWidth={1.5}
            />
            <span className="text-xs font-medium mt-0.5">Planning</span>
          </Link>

          <Link
            href="#"
            className="flex flex-col items-center justify-center w-1/4 text-gray-400"
          >
            <Bot
              className="size-6 text-gray-400 cursor-pointer transition-all duration-200 hover:text-green-600 hover:scale-110"
              strokeWidth={1.5}
            />
            <span className="text-xs font-medium mt-0.5">Ecobot</span>
          </Link>

          <Link
            href="#"
            className="flex flex-col items-center justify-center w-1/4 text-gray-400"
          >
            <User
              className="size-6 text-gray-400 cursor-pointer transition-all duration-200 hover:text-green-600 hover:scale-110"
              strokeWidth={1.5}
            />
            <span className="text-xs font-medium mt-0.5">User</span>
          </Link>
        </div>
      </footer>
    </div>
  );
}
