'use client';

import {
    Abhaya_Libre,
    Jost,
    Lalezar,
} from "next/font/google";
import React, { useState, useEffect } from 'react';
import { Home, MapPin, Calendar, MessageCircle, User, Search, Leaf, Bot, Route, ChevronDown } from 'lucide-react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api, TravelPlan } from "@/lib/api"; 

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

const abhayaLibre = Abhaya_Libre({
    subsets: ["latin"],
    weight: ["400"],
    display: 'swap'
});

const lalezar = Lalezar({
    subsets: ["latin"],
    weight: ["400"],
    display: 'swap'
}); 
export default function TrackPage() {
    const router = useRouter();
    const [plans, setPlans] = useState<TravelPlan[]>([]);
    const [selectedPlan, setSelectedPlan] = useState<TravelPlan | null>(null);
    const [showDropdown, setShowDropdown] = useState(false);
    const [loading, setLoading] = useState(true);
    const [co2Saved, setCo2Saved] = useState(0);
    const [error, setError] = useState<string>("");

    useEffect(() => {
        const fetchPlans = async () => {
            try {
                setLoading(true);
                const data = await api.getPlans();   // ← gọi hàm bạn đã viết
                setPlans(data);
            } catch (err: any) {
                console.error(err);
                setError("Failed to load plans");
            } finally {
                setLoading(false);
            }
        };

        fetchPlans();
    }, []);

    const handlePlanSelect = (plan: TravelPlan) => {
        setSelectedPlan(plan);
        setShowDropdown(false);
    };

    const handleCalculate = () => {
        if (!selectedPlan) {
            alert('Please select a plan first!');
            return;
        }

        const params = new URLSearchParams({
            planId: selectedPlan.id.toString(),
            planName: selectedPlan.destination,
            startDate: selectedPlan.date,
            endDate: selectedPlan.end_date ?? "",
        });

        router.push(`/track_page/transport_options?${params.toString()}`);
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    };

    return (
        <div className="w-full h-screen flex justify-center bg-gray-200 overflow-hidden">
            <div className="w-full min-h-screen bg-gray-50 flex flex-col max-w-md mx-auto relative">
                {/* Main Content */}
                <div className="flex-1 p-6 pb-20 overflow-y-auto scrollbar-hide">

                    <div className="flex items-center gap-2 mb-6">
                        <Leaf className="text-green-600" size={32} />
                        <h1 className={`${jost_extrabold.className} text-2xl text-green-600`}>TRACK</h1>
                    </div>

                    <div className="space-y-3 mb-2">
                        <div className="relative">
                            <button
                                onClick={() => setShowDropdown(!showDropdown)}
                                className="w-full px-4 py-3 pl-11 text-left text-green-600 border-2 border-green-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 text-sm bg-white flex items-center justify-between"
                            >
                                <span>
                                    {selectedPlan
                                        ? selectedPlan.destination
                                        : loading
                                            ? 'Loading plans...'
                                            : 'Select a plan'}
                                </span>
                                <ChevronDown
                                    className={`text-green-600 transition-transform ${showDropdown ? 'rotate-180' : ''}`}
                                    size={20}
                                />
                            </button>
                            <Calendar className="absolute left-3 top-3.5 text-green-600" size={20} />

                            {showDropdown && (
                                <div className="absolute z-20 w-full mt-2 bg-white border-2 border-green-500 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                                    {plans.length === 0 ? (
                                        <div className="px-4 py-3 text-gray-500 text-center">
                                            No plans found. Create a plan first!
                                        </div>
                                    ) : (
                                        plans.map((plan) => (
                                            <button
                                                key={plan.id}
                                                onClick={() => handlePlanSelect(plan)}
                                                className="w-full px-4 py-3 text-left hover:bg-green-50 transition-colors border-b border-gray-100 last:border-b-0"
                                            >
                                                <div className="font-semibold text-green-600">
                                                    {plan.destination}
                                                </div>
                                                <div className="text-xs text-gray-500 mt-1">
                                                    {formatDate(plan.date)} - {plan.end_date ? formatDate(plan.end_date) : "?"}
                                                </div>
                                            </button>
                                        ))
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Display selected plan details */}
                        {selectedPlan && (
                            <div className="bg-white border-2 border-green-200 rounded-lg p-4">
                                <div className="space-y-2">
                                    <div>
                                        <div className="text-xs text-gray-500 mb-1">Destination</div>
                                        <div className="font-semibold text-gray-800">{selectedPlan.destination}</div>
                                    </div>

                                    <div className="flex gap-4">
                                        <div className="flex-1">
                                            <div className="text-xs text-gray-500 mb-1">Start Date</div>
                                            <div className="text-sm text-gray-800">{formatDate(selectedPlan.date)}</div>
                                        </div>
                                        <div className="flex-1">
                                            <div className="text-xs text-gray-500 mb-1">End Date</div>
                                            <div className="text-sm text-gray-800">
                                                {selectedPlan.end_date ? formatDate(selectedPlan.end_date) : "?"}
                                            </div>
                                        </div>
                                    </div>

                                </div>
                            </div>
                        )}

                        <button
                            className="w-full bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                            onClick={handleCalculate}
                            disabled={!selectedPlan || loading}
                        >
                            Calculate CO2 Emissions
                        </button>
                    </div>

                    {/* Helper Text */}
                    <p className={`${abhayaLibre.className} text-xs text-green-600 mb-24`}>
                        View CO2 emissions by transportation type between two locations.
                    </p>

                    {/* CO2 Saved Card */}
                    <div className="relative">
                        {/* Plant Icon Circle */}
                        <div className="absolute -top-20 left-1/2 transform -translate-x-1/2 bg-white rounded-full w-40 h-40 flex items-center justify-center shadow-lg z-10">
                            <div className="relative mt-4 mb-4">
                                <img
                                    src="/images/gaia.png"
                                    alt="Protected Earth"
                                    className="w-32 h-32 object-contain"
                                />
                            </div>
                        </div>

                        {/* Green Card */}
                        <div className="bg-gradient-to-br from-green-600 to-green-400 rounded-2xl p-8 pt-16 text-center text-white shadow-lg">
                            <h2 className={`${jost_semibold.className} text-3xl mt-8 mb-2`}>CO2 Saved</h2>
                            <p className={`${jost_bold.className} text-lg mb-6 opacity-90 whitespace-nowrap`}>
                                Your contribution towards staying green
                            </p>
                            <div className={`${lalezar.className} text-7xl  mb-2`}>
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
                            <span className="text-[10px] font-bold mt-1">Home</span>
                        </Link>

                        <div className="flex flex-col items-center justify-center w-1/4 text-green-600">
                            <Route className="size-6" strokeWidth={2.0} />
                            <span className="text-[10px] font-bold mt-1">User</span>
                        </div>

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

export { jost_bold, jost_semibold, jost_extrabold , abhayaLibre, lalezar };