'use client';

import {
    Knewave,
    Josefin_Sans,
    Abhaya_Libre,
    Poppins,
    Gotu,
    Jost,
} from "next/font/google";
import React, { useState } from 'react';
import { Home, MapPin, Calendar, MessageCircle, User, Search, Leaf, Bot, Route} from 'lucide-react';
import Link from 'next/link';

const gotu = Gotu({
    subsets: ["latin"],
    weight: ["400"]
});

const jost = Jost({
    subsets: ["latin"],
    weight: ["700"],
    display: 'swap'
});

const abhayaLibre = Abhaya_Libre({
    subsets: ["latin"],
    weight: ["400"],
    display: 'swap'
});

const poppins = Poppins({
    subsets: ["latin"],
    weight: ["300"],
    display: 'swap'
});

const josefinSans = Josefin_Sans({
    subsets: ["latin"],
    weight: ["700"],
    display: 'swap'
});


export default function TrackPage() {
    const [activeTab, setActiveTab] = useState('track');
    const [fromLocation, setFromLocation] = useState('');
    const [toLocation, setToLocation] = useState('');
    const [co2Saved, setCo2Saved] = useState(0);

    const handleCalculate = () => {
        // Placeholder for CO2 calculation logic
        if (fromLocation && toLocation) {
            // Simulate calculation
            const randomSaved = Math.random() * 10;
            setCo2Saved(randomSaved);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col max-w-md mx-auto">
            {/* Main Content */}
            <div className="flex-1 p-6 pb-20">
                {/* Header */}
                <div className="flex items-center gap-2 mb-6">
                    <Leaf className="text-green-600" size={32} />
                    <h1 className="text-3xl font-bold text-green-600">TRACK</h1>
                </div>

                {/* Location Inputs */}
                <div className="space-y-4 mb-8">
                    <div className="relative">
                        <input
                            type="text"
                            placeholder="From location?"
                            value={fromLocation}
                            onChange={(e) => setFromLocation(e.target.value)}
                            className="w-full px-4 py-3 pl-11 text-green-600 border-2 border-green-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 text-base"
                        />
                        <MapPin className="absolute left-3 top-3.5 text-green-600" size={20} />
                    </div>

                    <div className="relative">
                        <input
                            type="text"
                            placeholder="To location?"
                            value={toLocation}
                            onChange={(e) => setToLocation(e.target.value)}
                            className="w-full px-4 py-3 pl-11 text-green-600 border-2 border-green-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 text-base"
                        />
                        <Search className="absolute left-3 top-3.5 text-green-600" size={20} />
                    </div>

                    <button
                        className="w-full bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors"
                        onClick={handleCalculate}
                    >
                        Calculate CO2 Emissions
                    </button>
                </div>

                {/* Helper Text */}
                <p className={`${abhayaLibre.className} text-xs text-green-600 mb-8`}>
                    View CO2 emissions by transportation type between two locations.
                </p>

                {/* CO2 Saved Card */}
                <div className="relative">
                    {/* Plant Icon Circle */}
                    <div className="absolute -top-12 left-1/2 transform -translate-x-1/2 bg-white rounded-full w-24 h-24 flex items-center justify-center shadow-lg z-10">
                        <div className="relative">
                            <div className="text-5xl">🌱</div>
                            <div className="absolute bottom-0 right-0 text-3xl">🌍</div>
                        </div>
                    </div>

                    {/* Green Card */}
                    <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-2xl p-8 pt-16 text-center text-white shadow-lg">
                        <h2 className="text-2xl font-semibold mb-2">CO2 Saved</h2>
                        <p className="text-base mb-6 opacity-90 whitespace-nowrap">
                            Your contribution towards staying green
                        </p>
                        <div className="text-6xl font-bold mb-2">
                            {co2Saved.toFixed(1)} Kg
                        </div>
                    </div>

                    {/* Quick Stats */}
                    <div className="grid grid-cols-2 gap-4 mt-6">
                      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
                        <div className="text-gray-500 text-sm mb-1">Trips</div>
                        <div className="text-2xl font-bold text-gray-800">0</div>
                      </div>
                      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
                        <div className="text-gray-500 text-sm mb-1">Trees Saved</div>
                        <div className="text-2xl font-bold text-green-600">0</div>
                      </div>
                    </div>
                </div>
            </div>

            <footer className="bg-white shadow-[0_-5px_15px_rgba(0,0,0,0.05)] sticky bottom-0 w-full z-20">
                <div className="h-1 bg-linear-to-r from-transparent via-green-200 to-transparent"></div>
                <div className="flex justify-around items-center py-3">
                    <Link
                        href="/homepage"
                        className="flex flex-col items-center justify-center w-1/4 text-gray-400 hover:text-green-600 transition-colors"
                    >
                        <Home className="size-6" strokeWidth={1.5} />
                        <span className={`${jost.className} text-[10px] mt-1`}>Home</span>
                    </Link>

                    <div className="flex flex-col items-center justify-center w-1/4 text-green-600">
                        <Route className="size-6" strokeWidth={2.0} />
                        <span className={`${jost.className} text-[10px] mt-1`}>
                            User
                        </span>
                    </div>

                    <Link
                        href="/planning_page/showing_plan_page"
                        className="flex flex-col items-center justify-center w-1/4 text-gray-400 hover:text-green-600 transition-colors"
                    >
                        <MapPin className="size-6" strokeWidth={1.5} />
                        <span className={`${jost.className} text-[10px] mt-1`}>Planning</span>
                    </Link>
                    <Link
                        href="#"
                        className="flex flex-col items-center justify-center w-1/4 text-gray-400 hover:text-green-600 transition-colors"
                    >
                        <Bot className="size-6" strokeWidth={1.5} />
                        <span className={`${jost.className} text-[10px] mt-1`}>Ecobot</span>
                    </Link>
                    <Link
                        href="/user_page/main_page"
                        className="flex flex-col items-center justify-center w-1/4 text-gray-400 hover:text-green-600 transition-colors relative"
                    >
                        <div className="relative">
                            <User className="size-6" strokeWidth={1.5} />
                        </div>
                        <span className={`${jost.className} text-[10px] mt-1`}>User</span>
                    </Link>
                </div>
            </footer>
        </div>


    );
}

export { jost, abhayaLibre, poppins, josefinSans, gotu };