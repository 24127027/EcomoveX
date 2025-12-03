'use client';

import { Home, MapPin, Calendar, MessageSquare, User, Route, Bot } from 'lucide-react';
import Link from 'next/link';
import { Jost } from 'next/font/google';

const jost_medium = Jost({
    subsets: ["latin"],
    weight: ["500"],
    display: 'swap'
});

const jost_bold = Jost({
    subsets: ["latin"],
    weight: ["700"],
    display: 'swap'
});

const jost_extrabold = Jost({
    subsets: ["latin"],
    weight: ["800"],
    display: 'swap'
});

const jost_semibold = Jost({
    subsets: ["latin"],
    weight: ["600"],
    display: 'swap'
});


export default function EcoTripResult_NotSaveCO2() {
    return (
        <div className="w-full min-h-screen bg-gray-200 flex justify-center">
            <div className="w-full max-w-[430px] min-h-screen bg-white flex flex-col relative shadow-xl">
                {/* Header */}
                <div className="bg-white sticky top-0 z-10 w-full">
                    <div className="p-4">
                        <h1 className={`${jost_extrabold.className} text-2xl font-bold text-green-600`}>RESULT</h1>
                    </div>
                </div>

                {/* Main Content */}
                <div className="flex-1">
                    <div className="flex flex-col items-center justify-center px-6 py-8 min-h-full">
                        {/* Earth with Trees Illustration */}
                        <div className="mb-8">
                            <img
                                src="/images/smoke.png"
                                alt="Earth with cars"
                                className="w-56 h-56 object-contain"
                            />
                        </div>

                        {/* Congratulations Text */}
                        <h2 className={`${jost_bold.className} text-3xl text-green-600 mb-4`}>
                            No CO2 saved!
                        </h2>

                        <p className={`${jost_bold.className} text-black  mb-8`}>
                            You did not save any CO2 on this trip.
                        </p>

                        {/* Stats Card */}
                        <div className="bg-white rounded-lg shadow-sm border border-gray-200 px-6 py-4 w-full max-w-sm mb-3">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="w-4 h-4 bg-orange-500 rotate-45"></div>
                                    <div className="min-w-0">
                                        <div className={`${jost_semibold.className} text-sm text-black`}>0.0kg</div>
                                        <div className={`${jost_semibold.className} text-sm text-gray-400`}>CO2 Emission</div>
                                    </div>
                                </div>

                                <div className="flex items-center gap-3">
                                    <div className="w-4 h-4 bg-green-500 rotate-45"></div>
                                    <div className="min-w-0">
                                        <div className={`${jost_semibold.className} text-sm text-black`}>8.2kg</div>
                                        <div className={`${jost_semibold.className} text-sm text-gray-400`}>CO2 Saved</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="w-full max-w-sm flex flex-col gap-3">
                            <Link href="/track_page/leaderboard">
                                <button className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 rounded-xl border-2 border-green-600 transition-colors">
                                    Go to Track
                                </button>
                            </Link>

                            <button className="w-full bg-white hover:bg-gray-50 text-green-600 font-semibold py-3 rounded-xl border-2 border-green-600 transition-colors">
                                Open Google Maps
                            </button>
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
                            <span className="text-[10px] font-bold mt-1">Home</span>
                        </Link>

                        <Link
                            href="/track_page/leaderboard"
                            className="flex flex-col items-center justify-center w-1/4 text-green-600"
                        >
                            <Route className="size-6" strokeWidth={2.0} />
                            <span className="text-[10px] font-bold mt-1">Track</span>
                        </Link>

                        <Link
                            href="/planning_page/showing_plan_page"
                            className="flex flex-col items-center justify-center w-1/4 text-gray-400 hover:text-green-600 transition-colors"
                        >
                            <MapPin className="size-6" strokeWidth={1.5} />
                            <span className="text-[10px] font-bold mt-1">Planning</span>
                        </Link>
                        <Link
                            href="#"
                            className="flex flex-col items-center justify-center w-1/4 text-gray-400 hover:text-green-600 transition-colors"
                        >
                            <Bot className="size-6" strokeWidth={1.5} />
                            <span className="text-[10px] font-bold mt-1">Ecobot</span>
                        </Link>
                        <Link
                            href="/user_page/main_page"
                            className="flex flex-col items-center justify-center w-1/4 text-gray-400 hover:text-green-600 transition-colors relative"
                        >
                            <div className="relative">
                                <User className="size-6" strokeWidth={1.5} />
                            </div>
                            <span className="text-[10px] font-bold mt-1">User</span>
                        </Link>
                    </div>
                </footer>
            </div>
        </div>
    );
}

export { jost_medium, jost_bold, jost_extrabold, jost_semibold }; 