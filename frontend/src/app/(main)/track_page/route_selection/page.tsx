'use client';

import React, { useState, useRef, useEffect } from 'react';
import { MapPin, ArrowLeft, Home, Navigation, Calendar, MessageSquare, User, Bot, Route } from 'lucide-react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { PlanDestinationResponse, Plan } from '@/lib/api'; 

interface CurvedArrowWrapperProps {
    fromId: number;
    toId: number;
    direction?: 'down' | 'up';
}

export default function RouteSelectionPage() {
    const [selectedDate, setSelectedDate] = useState('');
    const [selectedTime, setSelectedTime] = useState('');
    const [selectedRoute, setSelectedRoute] = useState<string | null>(null);
    const router = useRouter();
    const searchParams = useSearchParams();

    const [plan, setPlan] = useState<Plan | null>(null);
    const [availableDates, setAvailableDates] = useState<string[]>([]);

    /** Load params từ URL */
    useEffect(() => {
        const params = searchParams;

        try {
            const parsedPlan: Plan = {
                id: Number(params.get("id")),
                place_name: params.get("place_name") ?? "",
                start_date: params.get("start_date") ?? "",
                end_date: params.get("end_date") ?? "",
                budget_limit: params.get("budget_limit")
                    ? Number(params.get("budget_limit"))
                    : null,
                destinations: JSON.parse(params.get("destinations") ?? "[]"),
                route: params.get("route")
                    ? JSON.parse(params.get("route") ?? "[]")
                    : null,
            };

            setPlan(parsedPlan);

            // Generate available dates from start_date to end_date
            if (parsedPlan.start_date && parsedPlan.end_date) {
                const dates: string[] = [];
                const start = new Date(parsedPlan.start_date);
                const end = new Date(parsedPlan.end_date);

                for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
                    dates.push(new Date(d).toISOString().split('T')[0]);
                }

                setAvailableDates(dates);

                // Set first date as default
                if (dates.length > 0) {
                    setSelectedDate(dates[0]);
                }
            }
        } catch (e) {
            console.error("Failed to parse plan", e);
        }
    }, [searchParams]);

    // Filter destinations based on selected date and time
    const destinations = plan?.destinations.filter(dest => {
        if (!selectedDate) return false;
        if (dest.visit_date !== selectedDate) return false;
        if (selectedTime && dest.time_slot !== selectedTime) return false;
        return true;
    }).sort((a, b) => a.order_in_day - b.order_in_day) || [];

   

    // Sample destinations - replace with actual data from params
    //const destinations = [
    //    {
    //        id: 1,
    //        name: "Ben Thanh Market",
    //        address: "Le Loi Street, District 1"
    //    },
    //    {
    //        id: 2,
    //        name: "Notre-Dame Cathedral",
    //        address: "01 Cong xa Paris, District 1"
    //    },
    //    {
    //        id: 3,
    //        name: "War Remnants Museum",
    //        address: "28 Vo Van Tan, District 3"
    //    },
    //    {
    //        id: 4,
    //        name: "Independence Palace",
    //        address: "135 Nam Ky Khoi Nghia, District 1"
    //    }
    //];

    const selectRoute = (fromId: number, toId: number) => {
        const routeKey = `${fromId}-${toId}`;

        if (selectedRoute === routeKey) {
            setSelectedRoute(null);
        } else {
            setSelectedRoute(routeKey);
        }
    };

    const handleCalculateCO2 = () => {
        if (!selectedRoute || !plan) return;

        const [fromIdStr, toIdStr] = selectedRoute.split('-');
        const fromId = Number(fromIdStr);
        const toId = Number(toIdStr);

        const fromDest = destinations.find(d => d.id === fromId);
        const toDest = destinations.find(d => d.id === toId);

        if (!fromDest || !toDest) return;

        const routeData = plan.route?.find(r =>
            r.origin === fromDest.destination_id &&
            r.destination === toDest.destination_id
        );

        const params = new URLSearchParams({
            from: fromDest.destination_id,
            to: toDest.destination_id,
            distance: routeData?.distance_km?.toString() || '0',
            travel_time: routeData?.estimated_travel_time_min?.toString() || '0',
        });

        router.push(`/track_page/transport_selection?${params.toString()}`);
    };

    const isRouteSelected = (fromId: number, toId: number) => {
        return selectedRoute === `${fromId}-${toId}`;
    };

    const CurvedArrow = ({ fromId, toId, direction = 'down' }: CurvedArrowWrapperProps) => {
        const isSelected = isRouteSelected(fromId, toId);
        const color = isSelected ? '#10b981' : '#d1d5db';
        const strokeWidth = isSelected ? 3 : 2;

        return (
            <div
                className="relative cursor-pointer touch-manipulation active:opacity-70"
                onClick={() => selectRoute(fromId, toId)}
                style={{ height: '80px', margin: '0 auto', width: '90%' }}
            >
                <svg width="100%" height="80" style={{ overflow: 'visible' }}>
                    <defs>
                        <marker
                            id={`arrowhead-${fromId}-${toId}`}
                            markerWidth="10"
                            markerHeight="10"
                            refX="9"
                            refY="3"
                            orient="auto"
                        >
                            <polygon points="0 0, 10 3, 0 6" fill={color} />
                        </marker>
                    </defs>
                    {direction === 'down' ? (
                        <path
                            d="M 50 10 Q 200 40, 350 70"
                            stroke={color}
                            strokeWidth={strokeWidth}
                            fill="none"
                            strokeDasharray={isSelected ? "0" : "8 4"}
                            markerEnd={`url(#arrowhead-${fromId}-${toId})`}
                        />
                    ) : (
                        <path
                            d="M 350 10 Q 200 40, 50 70"
                            stroke={color}
                            strokeWidth={strokeWidth}
                            fill="none"
                            strokeDasharray={isSelected ? "0" : "8 4"}
                            markerEnd={`url(#arrowhead-${fromId}-${toId})`}
                        />
                    )}
                </svg>
            </div>
        );
    };

    return (
        <div className="bg-gray-200 flex justify-center border-b shadow-sm h-screen">
            <div className="w-full max-w-md mx-auto bg-gray-50 min-h-screen flex flex-col overflow-y-auto scrollbar-hide">
                {/* Header */}
                <div className="bg-white shadow-sm px-4 py-4 flex items-center gap-4 sticky top-0 z-10">
                    <ArrowLeft className="w-6 h-6 text-gray-700 cursor-pointer" onClick={() => router.back()} />
                    <h1 className="text-lg font-semibold text-gray-900">{plan?.place_name || "Loading..."}</h1>
                </div>

                {/* Main Content */}
                <div className="p-4 space-y-4 pb-24 flex-1">
                    {/* Date Selection */}
                    <div className="bg-white border-2 border-green-500 rounded-xl p-4 touch-manipulation">
                        <select
                            value={selectedDate}
                            onChange={(e) => setSelectedDate(e.target.value)}
                            className="w-full text-green-600 font-medium outline-none bg-transparent text-base"
                        >
                            <option value="">Select a date</option>
                            {availableDates.map((date) => (
                                <option key={date} value={date}>
                                    {new Date(date).toLocaleDateString('en-US', {
                                        weekday: 'short',
                                        year: 'numeric',
                                        month: 'short',
                                        day: 'numeric'
                                    })}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Time Selection */}
                    <div className="bg-white border-2 border-green-500 rounded-xl p-4 touch-manipulation">
                        <select
                            value={selectedTime}
                            onChange={(e) => setSelectedTime(e.target.value)}
                            className="w-full text-green-600 font-medium outline-none bg-transparent text-base"
                        >
                            <option value="">All time slots</option>
                            <option value="morning">Morning☀️ (6am - 12pm)</option>
                            <option value="afternoon">Afternoon🌗 (12pm - 6pm)</option>
                            <option value="evening">Evening🌑 (6pm - 11pm)</option>
                        </select>
                    </div>

                    {/* Destinations with Arrows */}
                    <div className="space-y-0">
                        {destinations.length === 0 ? (
                            <div className="text-center py-8 text-gray-500">
                                <p>No destinations found for selected date/time.</p>
                                <p className="text-sm mt-2">Try selecting a different date or time slot.</p>
                            </div>
                        ) : (
                            destinations.map((dest, index) => (
                                <React.Fragment key={dest.id}>
                                    {/* Destination Card */}
                                    <div className={`flex items-center gap-3 touch-manipulation ${index % 2 === 1 ? 'flex-row-reverse' : ''}`}>
                                        <MapPin className="w-8 h-8 text-green-600 flex-shrink-0" />
                                        <div className="flex-1 bg-gradient-to-r from-green-300 to-green-200 rounded-xl p-4 shadow-sm">
                                            <h3 className="font-semibold text-gray-900 text-base">
                                                {dest.destination_id}
                                            </h3>
                                            <p className="text-sm text-gray-700">
                                                {dest.type} • Order: {dest.order_in_day}
                                            </p>
                                            {dest.estimated_cost && (
                                                <p className="text-xs text-gray-600 mt-1">
                                                    Est. cost: ${dest.estimated_cost}
                                                </p>
                                            )}
                                            {dest.note && (
                                                <p className="text-xs text-gray-600 mt-1 italic">
                                                    {dest.note}
                                                </p>
                                            )}
                                        </div>
                                    </div>

                                    {/* Arrow to next destination */}
                                    {index < destinations.length - 1 && (
                                        <CurvedArrow
                                            fromId={dest.id}
                                            toId={destinations[index + 1].id}
                                            direction={index % 2 === 0 ? 'down' : 'up'}
                                        />
                                    )}
                                </React.Fragment>
                            ))
                        )}
                    </div>

                    {/* Selected Route Info */}
                    {selectedRoute && (
                        <div className="bg-green-50 border border-green-200 rounded-xl p-4 mt-6 space-y-3">
                            <p className="text-sm font-medium text-green-800">
                                Route selected
                            </p>
                            <button
                                onClick={handleCalculateCO2}
                                className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors active:scale-95 transform"
                            >
                                Calculate CO2 Emission
                            </button>
                        </div>
                    )}
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
};