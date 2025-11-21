"use client";

import React from "react";
import Link from "next/link";
import { Search, Home, MapPin, Bot, User, ChevronLeft } from "lucide-react";
import { Poppins, Jost, Abhaya_Libre } from "next/font/google";

// --- Font Setup ---
const poppins = Poppins({ subsets: ["latin"], weight: ["300"] });
const jost = Jost({ subsets: ["latin"], weight: ["700"] });
const abhaya_libre = Abhaya_Libre({ subsets: ["latin"], weight: ["700"] });

export default function MapPage() {
  return (
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      <div className="w-full max-w-md bg-gray-50 h-screen shadow-2xl relative flex flex-col overflow-hidden">
        <div className="flex-1 relative bg-[#E9F5EB] w-full overflow-hidden group">
          {/* Search Bar  */}
          <div className="absolute top-5 left-4 right-4 z-10">
            <div className="bg-white rounded-full shadow-md flex items-center p-3 transition-transform active:scale-95">
              <Link href="/homepage">
                <ChevronLeft className="text-gray-500 mr-2 cursor-pointer hover:text-green-600" />
              </Link>
              <Search size={18} className="text-green-600 mr-2" />
              <input
                type="text"
                placeholder="Search for a location..."
                className={`${abhaya_libre.className} flex-1 outline-none text-gray-700 placeholder:text-gray-400 bg-transparent`}
              />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-t-3xl shadow-[0_-5px_15px_rgba(0,0,0,0.1)] p-6 z-10 shrink-0 relative">
          {/* Address Card */}
          <div className="bg-[#F9FFF9] border border-green-100 rounded-xl p-4 mb-5 flex items-start gap-3 shadow-sm">
            <div className="bg-green-100 p-2.5 rounded-full shrink-0 mt-0.5">
              <MapPin size={20} className="text-green-600" />
            </div>
            <div>
              <p
                className={`${jost.className} text-green-700 text-sm font-bold mb-1 uppercase tracking-wide`}
              >
                Selected Location
              </p>
              <p
                className={`${abhaya_libre.className} text-gray-700 text-lg leading-tight`}
              >
                123 Green Street, Eco District, Ho Chi Minh City
              </p>
            </div>
          </div>

          {/* Select Button */}
          <button
            className={`${jost.className} w-full bg-[#53B552] hover:bg-green-600 text-white text-xl font-bold py-3.5 rounded-full shadow-lg transition-all transform active:scale-[0.98]`}
          >
            Select Location
          </button>
        </div>

        {/* --- FOOTER --- */}
        <footer
          className={`bg-white shadow-[0_-2px_6px_rgba(0,0,0,0.05)] ${poppins.className} shrink-0 z-10`}
        >
          <div className="h-0.5 bg-linear-to-r from-transparent via-green-300 to-transparent opacity-70"></div>
          <div className="flex justify-around items-center px-2 pt-2 pb-3">
            <Link
              href="/homepage"
              className="flex flex-col items-center justify-center w-1/4 text-green-600"
            >
              <Home className="size-6 select-none" strokeWidth={2.0} />
              <span className="text-xs font-medium mt-0.5">Home</span>
            </Link>

            <Link
              href="/planning_page/showing_plan_page"
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
              href="user_page/main_page"
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
    </div>
  );
}
