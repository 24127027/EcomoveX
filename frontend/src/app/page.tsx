"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import {
  Leaf,
  Map,
  Heart,
  ArrowRight,
  Star,
  ShieldCheck,
  Menu,
} from "lucide-react";
import { Knewave, Jost, Poppins } from "next/font/google";

// --- Font Setup ---
const knewave = Knewave({ subsets: ["latin"], weight: ["400"] });
const jost = Jost({ subsets: ["latin"], weight: ["400", "600", "700"] });
const poppins = Poppins({ subsets: ["latin"], weight: ["300", "400", "500"] });

export default function LandingPage() {
  return (
    // 1. Wrapper Desktop (Nền xám, căn giữa)
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      {/* 2. Khung App Mobile (max-w-md) */}
      <div className="w-full max-w-md bg-white h-screen shadow-2xl relative flex flex-col overflow-y-auto overflow-x-hidden scroll-smooth">
        {/* --- NAVBAR (Mobile) --- */}
        <nav className="absolute top-0 left-0 right-0 z-50 px-5 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="bg-green-500/90 p-1.5 rounded-lg backdrop-blur-sm">
              <Leaf className="text-white size-5" fill="white" />
            </div>
            <span
              className={`${knewave.className} text-xl text-white tracking-wider drop-shadow-md`}
            >
              Ecomove<span className="text-green-300">X</span>
            </span>
          </div>

          <div className="flex items-center gap-3">
            <Link href="/signup">
              <button
                className={`${jost.className} text-white text-sm font-semibold drop-shadow-md cursor-pointer`}
              >
                Sign Up
              </button>
            </Link>
            <Link href="/login">
              <button
                className={`${jost.className} bg-white text-green-700 px-4 py-1.5 rounded-full text-xs font-bold shadow-lg cursor-pointer`}
              >
                Sign In
              </button>
            </Link>
          </div>
        </nav>

        {/* --- HERO SECTION --- */}
        <section className="relative h-[85vh] w-full shrink-0">
          {/* Background Image */}
          <div className="absolute inset-0 z-0">
            <Image
              src="https://images.unsplash.com/photo-1469474968028-56623f02e42e?q=80&w=1000&auto=format&fit=crop"
              alt="Nature Background"
              fill
              className="object-cover"
              priority
            />
            <div className="absolute inset-0 bg-linear-to-b from-black/40 via-transparent to-black/80" />
          </div>

          {/* Content */}
          <div className="relative z-10 h-full flex flex-col justify-end px-6 pb-12 text-left">
            <div className="mb-4">
              <span
                className={`${jost.className} bg-green-500/20 backdrop-blur-md border border-green-400/30 text-green-100 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest`}
              >
                #1 Green Travel App
              </span>
            </div>

            <h1
              className={`${jost.className} text-4xl font-bold text-white leading-tight mb-4 drop-shadow-xl`}
            >
              Travel Green.
              <br />
              Live Clean.
            </h1>

            <p
              className={`${poppins.className} text-gray-200 text-sm mb-8 font-light leading-relaxed opacity-90`}
            >
              Discover eco-friendly spots in HCMC, earn points, and reduce your
              carbon footprint with every trip.
            </p>

            <div className="flex flex-col gap-3">
              <Link href="/signup" className="w-full">
                <button
                  className={`${jost.className} w-full bg-green-500 hover:bg-green-400 text-white text-lg py-3.5 rounded-full font-bold shadow-lg transition-all flex justify-center items-center gap-2 group`}
                >
                  Get Started
                  <ArrowRight className="group-hover:translate-x-1 transition-transform size-5" />
                </button>
              </Link>
            </div>
          </div>
        </section>

        {/* --- FEATURES SECTION --- */}
        <section className="py-12 px-6 bg-[#0a2e14] relative overflow-hidden shrink-0">
          {/* Decorative Blob */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-green-500/10 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10">
            <h2
              className={`${jost.className} text-3xl font-bold text-white mb-2`}
            >
              Why EcomoveX?
            </h2>
            <p className={`${poppins.className} text-gray-400 text-sm mb-8`}>
              Your companion for conscious travel.
            </p>

            <div className="space-y-5">
              {/* Feature 1 */}
              <div className="bg-white/5 backdrop-blur-sm border border-white/10 p-5 rounded-2xl flex items-start gap-4">
                <div className="bg-green-500/20 p-2.5 rounded-xl shrink-0">
                  <Map className="text-green-400 size-6" />
                </div>
                <div>
                  <h3
                    className={`${jost.className} text-white font-bold text-lg`}
                  >
                    Green Map
                  </h3>
                  <p className="text-gray-400 text-xs mt-1 leading-relaxed">
                    Find parks, vegan spots, and eco-shops instantly.
                  </p>
                </div>
              </div>

              {/* Feature 2 */}
              <div className="bg-white/5 backdrop-blur-sm border border-white/10 p-5 rounded-2xl flex items-start gap-4">
                <div className="bg-blue-500/20 p-2.5 rounded-xl shrink-0">
                  <Star className="text-blue-400 size-6" />
                </div>
                <div>
                  <h3
                    className={`${jost.className} text-white font-bold text-lg`}
                  >
                    Eco Rewards
                  </h3>
                  <p className="text-gray-400 text-xs mt-1 leading-relaxed">
                    Earn points for every sustainable check-in.
                  </p>
                </div>
              </div>

              {/* Feature 3 */}
              <div className="bg-white/5 backdrop-blur-sm border border-white/10 p-5 rounded-2xl flex items-start gap-4">
                <div className="bg-yellow-500/20 p-2.5 rounded-xl shrink-0">
                  <ShieldCheck className="text-yellow-400 size-6" />
                </div>
                <div>
                  <h3
                    className={`${jost.className} text-white font-bold text-lg`}
                  >
                    Verified Spots
                  </h3>
                  <p className="text-gray-400 text-xs mt-1 leading-relaxed">
                    Trusted locations vetted by our green community.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
