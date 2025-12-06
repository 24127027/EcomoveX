'use client';

import React, { useState, useEffect } from 'react';
import { Home, MapPin, User, Bot, Route, ChevronDown, Check, X, ArrowLeft, Leaf, Trophy, Sparkles, Medal, Crown } from 'lucide-react';

// Types
interface Plan {
  id: number;
  place_name: string;
  budget_limit: number;
}

interface RouteData {
  user_id: number;
  plan_id: number;
  origin_id: number;
  destination_id: number;
  distance_km: number;
  carbon_emission_kg: number;
  origin_name: string;
  destination_name: string;
  visit_date: string;
  time_slot: string;
}

interface TransportOption {
  id: string;
  name: string;
  carbon: number;
  icon: string;
}

// Mock API responses
const mockPlans = {
  plans: [
    { id: 1, place_name: "Ho Chi Minh City Tour", budget_limit: 500 },
    { id: 2, place_name: "Mekong Delta Adventure", budget_limit: 300 },
    { id: 3, place_name: "Cu Chi Tunnels Visit", budget_limit: 150 }
  ]
};

const mockRoutes = [
  {
    user_id: 1,
    plan_id: 1,
    origin_id: 1,
    destination_id: 2,
    distance_km: 5.2,
    carbon_emission_kg: 1.8,
    origin_name: "Ben Thanh Market",
    destination_name: "Notre-Dame Cathedral",
    visit_date: "2024-12-15",
    time_slot: "morning"
  },
  {
    user_id: 1,
    plan_id: 1,
    origin_id: 2,
    destination_id: 3,
    distance_km: 3.8,
    carbon_emission_kg: 1.3,
    origin_name: "Notre-Dame Cathedral",
    destination_name: "War Remnants Museum",
    visit_date: "2024-12-15",
    time_slot: "morning"
  },
  {
    user_id: 1,
    plan_id: 1,
    origin_id: 3,
    destination_id: 4,
    distance_km: 2.5,
    carbon_emission_kg: 0.9,
    origin_name: "War Remnants Museum",
    destination_name: "Independence Palace",
    visit_date: "2024-12-15",
    time_slot: "afternoon"
  },
  {
    user_id: 1,
    plan_id: 1,
    origin_id: 4,
    destination_id: 5,
    distance_km: 4.1,
    carbon_emission_kg: 1.4,
    origin_name: "Independence Palace",
    destination_name: "Bitexco Tower",
    visit_date: "2024-12-15",
    time_slot: "afternoon"
  },
  {
    user_id: 1,
    plan_id: 1,
    origin_id: 5,
    destination_id: 6,
    distance_km: 6.3,
    carbon_emission_kg: 2.2,
    origin_name: "Bitexco Tower",
    destination_name: "Saigon Opera House",
    visit_date: "2024-12-15",
    time_slot: "evening"
  },
  {
    user_id: 1,
    plan_id: 1,
    origin_id: 6,
    destination_id: 7,
    distance_km: 3.2,
    carbon_emission_kg: 1.1,
    origin_name: "Saigon Opera House",
    destination_name: "Bui Vien Street",
    visit_date: "2024-12-16",
    time_slot: "morning"
  }
];

const transportOptions = [
  { id: 'walk', name: 'Walk', carbon: 0, icon: '🚶' },
  { id: 'bike', name: 'Bike', carbon: 0, icon: '🚲' },
  { id: 'motorbike', name: 'Motorbike', carbon: 0.8, icon: '🛵' },
  { id: 'bus', name: 'Bus', carbon: 0.5, icon: '🚌' },
  { id: 'car', name: 'Car', carbon: 1.0, icon: '🚗' }
];

const timeSlots = ['morning', 'afternoon', 'evening'];

export default function RouteTracker() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const [routes, setRoutes] = useState<RouteData[]>([]);
  const [currentRouteIndex, setCurrentRouteIndex] = useState(0);
  const [totalCarbon, setTotalCarbon] = useState(0);
  const [showTransportOptions, setShowTransportOptions] = useState(false);
  const [selectedDate, setSelectedDate] = useState('2024-12-15');
  const [selectedTimeSlot, setSelectedTimeSlot] = useState('morning');
  const [availableDates, setAvailableDates] = useState(['2024-12-15', '2024-12-16', '2024-12-17']);
  const [filteredRoutes, setFilteredRoutes] = useState<RouteData[]>([]);
  const [isCompleted, setIsCompleted] = useState(false);
  const [co2Saved, setCo2Saved] = useState(0);

  useEffect(() => {
    setPlans(mockPlans.plans);
    
    // Get CO2 from URL parameter or use mock data
    const params = new URLSearchParams(window.location.search);
    const savedParam = params.get('saved');
    if (savedParam) {
      const savedValue = parseFloat(savedParam);
      if (!isNaN(savedValue)) {
        setCo2Saved(savedValue);
      }
    } else {
      // Mock number for demonstration
      setCo2Saved(12.5);
    }
  }, []);

  useEffect(() => {
    if (selectedPlan) {
      const planRoutes = mockRoutes.filter(r => r.plan_id === selectedPlan.id);
      setRoutes(planRoutes);
    }
  }, [selectedPlan]);

  useEffect(() => {
    if (routes.length > 0) {
      const filtered = routes.filter(r => 
        r.visit_date === selectedDate && r.time_slot === selectedTimeSlot
      );
      setFilteredRoutes(filtered);
      setCurrentRouteIndex(0);
    }
  }, [routes, selectedDate, selectedTimeSlot]);

  const currentRoute = filteredRoutes[currentRouteIndex];

  const handlePlanSelect = (plan: Plan) => {
    setSelectedPlan(plan);
    setShowDropdown(false);
    setTotalCarbon(0);
    setCurrentRouteIndex(0);
    setSelectedDate('2024-12-15');
    setSelectedTimeSlot('morning');
    setIsCompleted(false);
  };

  const handleFollowingRoute = (isFollowing: boolean) => {
    if (isFollowing && currentRoute) {
      setTotalCarbon(prev => prev + currentRoute.carbon_emission_kg);
      moveToNextRoute();
    } else {
      setShowTransportOptions(true);
    }
  };

  const handleTransportSelect = (transport: TransportOption) => {
    if (currentRoute) {
      const carbonMultiplier = transport.carbon;
      const carbon = currentRoute.distance_km * carbonMultiplier;
      setTotalCarbon(prev => prev + carbon);
      setShowTransportOptions(false);
      moveToNextRoute();
    }
  };

  const moveToNextRoute = () => {
    // Check if there are more routes in current time slot
    if (currentRouteIndex < filteredRoutes.length - 1) {
      setCurrentRouteIndex(prev => prev + 1);
      return;
    }

    // Try to find next time slot with routes
    const currentTimeIndex = timeSlots.indexOf(selectedTimeSlot);
    for (let i = currentTimeIndex + 1; i < timeSlots.length; i++) {
      const nextSlotRoutes = routes.filter(r => 
        r.visit_date === selectedDate && r.time_slot === timeSlots[i]
      );
      if (nextSlotRoutes.length > 0) {
        setSelectedTimeSlot(timeSlots[i]);
        return;
      }
    }

    // Try to find next date with routes
    const currentDateIndex = availableDates.indexOf(selectedDate);
    for (let i = currentDateIndex + 1; i < availableDates.length; i++) {
      const nextDateRoutes = routes.filter(r => r.visit_date === availableDates[i]);
      if (nextDateRoutes.length > 0) {
        setSelectedDate(availableDates[i]);
        setSelectedTimeSlot('morning');
        return;
      }
    }

    // No more routes - Plan completed! Show summary
    setSelectedPlan(null);
    setCurrentRouteIndex(0);
    setSelectedDate('2024-12-15');
    setSelectedTimeSlot('morning');
  };

  const handleBackToOverview = () => {
    setSelectedPlan(null);
    setCurrentRouteIndex(0);
  };

  return (
    <div className="w-full h-screen flex justify-center bg-gray-50 overflow-hidden">
      <div className="w-full max-w-md mx-auto bg-white flex flex-col h-screen relative">
        {/* Header */}
        <div className="bg-white px-4 py-3 flex items-center justify-between border-b sticky top-0 z-20">
          <div className="flex items-center gap-2">
            <Leaf className="text-green-600" size={24} />
            <h1 className="text-xl font-extrabold text-green-600">ROUTE TRACK</h1>
          </div>
          {selectedPlan && (
            <div className="bg-green-100 px-3 py-1 rounded-full">
              <span className="text-sm font-bold text-green-700">{totalCarbon.toFixed(1)} kg CO₂</span>
            </div>
          )}
        </div>

        {/* Main Content */}
        <div className="flex-1 overflow-y-auto p-4 pb-20">
          {/* Plan Selection */}
          <div className="mb-3">
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              className="w-full px-4 py-3 text-left text-green-600 border-2 border-green-500 rounded-lg bg-white flex items-center justify-between font-medium"
            >
              <span>
                {selectedPlan ? selectedPlan.place_name : 'Select a plan'}
              </span>
              <ChevronDown
                className={`text-green-600 transition-transform ${showDropdown ? 'rotate-180' : ''}`}
                size={20}
              />
            </button>

            {showDropdown && (
              <div className="absolute z-30 w-full max-w-md mt-2 bg-white border-2 border-green-500 rounded-lg shadow-lg max-h-60 overflow-y-auto left-1/2 -translate-x-1/2">
                {plans.map((plan) => (
                  <button
                    key={plan.id}
                    onClick={() => handlePlanSelect(plan)}
                    className="w-full px-4 py-3 text-left hover:bg-green-50 transition-colors border-b border-gray-100 last:border-b-0"
                  >
                    <div className="font-semibold text-green-600">{plan.place_name}</div>
                    {plan.budget_limit && (
                      <div className="text-xs text-gray-500 mt-1">Budget: ${plan.budget_limit}</div>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {!selectedPlan ? (
            <>
              {/* Helper Text */}
              <p className="text-xs text-green-600 mb-8 text-center">
                Select a plan above to start tracking your carbon footprint
              </p>

              {/* LARGE CO2 PANEL - THE MAIN FEATURE */}
              <div className="mb-8">
                {/* Decorative Earth Image Above Panel */}
                <div className="relative mb-[-40px] z-10 flex justify-center">
                  <div className="bg-white rounded-full w-20 h-20 flex items-center justify-center shadow-lg">
                    <img
                      src="https://img.freepik.com/free-vector/pixel-art-design-earth-vector-illustration-colorful-planet-earth-pixel-style-isolated_118339-977.jpg?w=2000"
                      alt="Protected Earth"
                      className="w-16 h-16 object-contain rounded-full"
                    />
                  </div>
                </div>

                {/* Large Carbon Display Panel */}
                <div className="bg-gradient-to-br from-green-500 via-green-600 to-green-700 rounded-3xl p-8 pt-20 shadow-2xl">
                  <div className="text-center">
                    <h2 className="text-3xl font-bold text-white mb-2">CO₂ Saved</h2>
                    <p className="text-lg text-green-100 mb-6 font-medium">
                      Your contribution towards staying green
                    </p>
                    
                    {/* The Main CO2 Number - VERY LARGE */}
                    <div className="text-8xl font-extrabold text-white mb-3 leading-none">
                      {co2Saved.toFixed(1)}
                    </div>
                    <div className="text-4xl text-green-100 font-bold mb-2">Kg</div>
                    
                    {/* Additional Info */}
                    <div className="mt-6 pt-6 border-t border-green-400/30">
                      <div className="flex items-center justify-center gap-2 text-green-100">
                        <Trophy size={20} />
                        <span className="text-sm font-medium">Keep up the great work!</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Additional Stats or Info */}
              <div className="bg-white rounded-xl p-4 border-2 border-green-200 shadow-sm">
                <div className="text-center">
                  <div className="text-sm text-gray-600 mb-2">Carbon Tracking Status</div>
                  <div className="flex items-center justify-center gap-4">
                    <div>
                      <div className="text-2xl font-bold text-green-600">
                        {(co2Saved / 2.5).toFixed(0)}
                      </div>
                      <div className="text-xs text-gray-500">Trees Saved</div>
                    </div>
                    <div className="w-px h-10 bg-gray-200"></div>
                    <div>
                      <div className="text-2xl font-bold text-green-600">
                        {(co2Saved * 0.8).toFixed(1)}
                      </div>
                      <div className="text-xs text-gray-500">Miles Offset</div>
                    </div>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <>
              {/* Date & Time Selection */}
              <div className="grid grid-cols-2 gap-3 mb-4">
                <select
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  className="px-3 py-2.5 text-green-600 border-2 border-green-500 rounded-lg bg-white font-medium text-sm"
                >
                  {availableDates.map((date) => (
                    <option key={date} value={date}>
                      {new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </option>
                  ))}
                </select>

                <select
                  value={selectedTimeSlot}
                  onChange={(e) => setSelectedTimeSlot(e.target.value)}
                  className="px-3 py-2.5 text-green-600 border-2 border-green-500 rounded-lg bg-white font-medium text-sm"
                >
                  <option value="">All times</option>
                  <option value="morning">Morning</option>
                  <option value="afternoon">Afternoon</option>
                  <option value="evening">Evening</option>
                </select>
              </div>

              {/* Current Route Display */}
              {currentRoute ? (
                <div className="space-y-4">
                  {/* Route Card */}
                  <div className="bg-green-50 border-2 border-green-200 rounded-xl p-5">
                    <div className="text-sm text-green-600 font-semibold mb-4">
                      Route {currentRouteIndex + 1} of {filteredRoutes.length}
                    </div>

                    {/* Origin */}
                    <div className="flex items-start gap-3 mb-3">
                      <div className="w-3 h-3 bg-green-500 rounded-full mt-1.5 flex-shrink-0"></div>
                      <div className="flex-1">
                        <div className="font-semibold text-gray-900 text-base">{currentRoute.origin_name}</div>
                        <div className="text-sm text-gray-500">Starting point</div>
                      </div>
                    </div>

                    {/* Route Info */}
                    <div className="flex items-center gap-3 ml-1.5 mb-3">
                      <div className="w-0.5 h-10 bg-green-300 border-l-2 border-dashed border-green-400"></div>
                      <div className="text-sm text-gray-600">
                        <div className="flex items-center gap-1.5">
                          <span>🚗</span>
                          <span>{currentRoute.distance_km} km</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <span>🌿</span>
                          <span>{currentRoute.carbon_emission_kg.toFixed(1)} kg CO₂</span>
                        </div>
                      </div>
                    </div>

                    {/* Destination */}
                    <div className="flex items-start gap-3">
                      <MapPin className="w-4 h-4 text-green-600 mt-1.5 flex-shrink-0" />
                      <div className="flex-1">
                        <div className="font-semibold text-gray-900 text-base">{currentRoute.destination_name}</div>
                        <div className="text-sm text-gray-500">Destination</div>
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  {!showTransportOptions ? (
                    <div className="space-y-3">
                      <p className="text-center text-gray-700 font-medium">
                        Are you following this route?
                      </p>
                      <div className="grid grid-cols-2 gap-3">
                        <button
                          onClick={() => handleFollowingRoute(true)}
                          className="flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white font-semibold py-3 rounded-lg transition-colors"
                        >
                          <Check size={18} />
                          Yes
                        </button>
                        <button
                          onClick={() => handleFollowingRoute(false)}
                          className="flex items-center justify-center gap-2 bg-gray-500 hover:bg-gray-600 text-white font-semibold py-3 rounded-lg transition-colors"
                        >
                          <X size={18} />
                          No
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <p className="text-center text-gray-700 font-medium">
                        Select your transport mode:
                      </p>
                      <div className="space-y-2">
                        {transportOptions.map((transport) => (
                          <button
                            key={transport.id}
                            onClick={() => handleTransportSelect(transport)}
                            className="w-full flex items-center justify-between p-3 bg-white border-2 border-gray-200 hover:border-green-500 rounded-lg transition-all"
                          >
                            <div className="flex items-center gap-3">
                              <span className="text-xl">{transport.icon}</span>
                              <span className="font-semibold text-gray-800">{transport.name}</span>
                            </div>
                            <div className="text-right">
                              <div className="text-sm font-medium text-gray-700">
                                {(currentRoute.distance_km * transport.carbon).toFixed(1)} kg
                              </div>
                              <div className="text-xs text-gray-500">CO₂</div>
                            </div>
                          </button>
                        ))}
                      </div>
                      <button
                        onClick={() => setShowTransportOptions(false)}
                        className="w-full py-2 text-gray-600 hover:text-gray-800 font-medium text-sm"
                      >
                        Cancel
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-4xl mb-4">🎉</div>
                  <p className="text-gray-600 font-medium mb-2">No routes available</p>
                  <p className="text-sm text-gray-500">Try selecting a different date or time slot</p>
                </div>
              )}

              {/* Back to Overview Button */}
              <button
                onClick={handleBackToOverview}
                className="w-full mt-6 flex items-center justify-center gap-2 bg-white border-2 border-green-500 text-green-600 font-semibold py-3 rounded-lg hover:bg-green-50 transition-colors"
              >
                <ArrowLeft size={20} />
                Back to Overview
              </button>
            </>
          )}
        </div>

        {/* Footer Navigation */}
        <footer className="bg-white shadow-[0_-5px_15px_rgba(0,0,0,0.05)] sticky bottom-0 w-full z-20">
          <div className="h-1 bg-gradient-to-r from-transparent via-green-200 to-transparent"></div>
          <div className="flex justify-around items-center py-3">
            <a href="/homepage" className="flex flex-col items-center justify-center w-1/5 text-gray-400 hover:text-green-600 transition-colors">
              <Home className="w-6 h-6" strokeWidth={1.5} />
              <span className="text-[10px] font-bold mt-1">Home</span>
            </a>
            <div className="flex flex-col items-center justify-center w-1/5 text-green-600">
              <Route className="w-6 h-6" strokeWidth={2.0} />
              <span className="text-[10px] font-bold mt-1">Track</span>
            </div>
            <a href="/planning_page/showing_plan_page" className="flex flex-col items-center justify-center w-1/5 text-gray-400 hover:text-green-600 transition-colors">
              <MapPin className="w-6 h-6" strokeWidth={1.5} />
              <span className="text-[10px] font-bold mt-1">Planning</span>
            </a>
            <a href="#" className="flex flex-col items-center justify-center w-1/5 text-gray-400 hover:text-green-600 transition-colors">
              <Bot className="w-6 h-6" strokeWidth={1.5} />
              <span className="text-[10px] font-bold mt-1">Ecobot</span>
            </a>
            <a href="/user_page/main_page" className="flex flex-col items-center justify-center w-1/5 text-gray-400 hover:text-green-600 transition-colors">
              <User className="w-6 h-6" strokeWidth={1.5} />
              <span className="text-[10px] font-bold mt-1">User</span>
            </a>
          </div>
        </footer>
      </div>
    </div>
  );
}