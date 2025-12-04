"use client";

import React, { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import {
  ChevronLeft,
  Car,
  Bike,
  Bus,
  Fuel,
  Leaf,
  Check,
  ArrowRight,
  TrendingUp,
  AlertCircle,
} from "lucide-react";
import { Jost } from "next/font/google";
import { api } from "@/lib/api";

const jost = Jost({ subsets: ["latin"], weight: ["400", "500", "600", "700"] });

// Transport types with fuel consumption data
interface TransportOption {
  id: "car" | "motorbike" | "bus";
  name: string;
  icon: typeof Car;
  fuelPerKm: number; // Liters per 100km
  color: string;
  bgColor: string;
}

const TRANSPORT_OPTIONS: TransportOption[] = [
  {
    id: "car",
    name: "Car",
    icon: Car,
    fuelPerKm: 7.5, // 7.5L/100km
    color: "text-blue-600",
    bgColor: "bg-blue-50",
  },
  {
    id: "motorbike",
    name: "Motorbike",
    icon: Bike,
    fuelPerKm: 2.5, // 2.5L/100km
    color: "text-orange-600",
    bgColor: "bg-orange-50",
  },
  {
    id: "bus",
    name: "Bus",
    icon: Bus,
    fuelPerKm: 1.2, // 1.2L/100km per passenger
    color: "text-green-600",
    bgColor: "bg-green-50",
  },
];

interface CarbonData {
  car: number;
  motorbike: number;
  bus: number;
}

function TransportSelectionContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const planId = searchParams.get("id");

  const [selectedTransport, setSelectedTransport] = useState<string | null>(
    null
  );
  const [totalDistance, setTotalDistance] = useState<number>(0);
  const [carbonData, setCarbonData] = useState<CarbonData>({
    car: 0,
    motorbike: 0,
    bus: 0,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Calculate total distance and fetch carbon data
    const loadPlanData = async () => {
      try {
        const activities = sessionStorage.getItem("current_plan_activities");
        if (!activities) {
          setTotalDistance(30); // Default fallback
          await fetchCarbonData(30);
          setIsLoading(false);
          return;
        }

        const parsed = JSON.parse(activities);

        // Calculate distance based on number of transitions
        let totalDist = 0;
        if (parsed.length > 1) {
          const transitions = parsed.length - 1;
          totalDist = transitions * 8;

          const timeSlots = new Set(parsed.map((a: any) => a.time_slot));
          if (timeSlots.size > 1) {
            totalDist += (timeSlots.size - 1) * 5;
          }
        }

        const distance = totalDist > 0 ? totalDist : 30;
        setTotalDistance(distance);

        // Fetch real carbon data from backend
        await fetchCarbonData(distance);
      } catch (error) {
        console.error("Error loading plan data:", error);
        setError("Failed to load carbon data");
        setTotalDistance(50);
      } finally {
        setIsLoading(false);
      }
    };

    loadPlanData();
  }, []);

  const fetchCarbonData = async (distance: number) => {
    try {
      const [carEmission, motorbikeEmission, busEmission] = await Promise.all([
        api.estimateCarbon("car", distance, 1),
        api.estimateCarbon("motorbike", distance, 1),
        api.estimateCarbon("bus", distance, 1),
      ]);

      setCarbonData({
        car: carEmission,
        motorbike: motorbikeEmission,
        bus: busEmission,
      });
    } catch (error) {
      console.error("Error fetching carbon data:", error);
      setError("Failed to fetch carbon emissions data");
      // Set default values as fallback
      setCarbonData({
        car: distance * 0.12,
        motorbike: distance * 0.06,
        bus: distance * 0.03,
      });
    }
  };

  const calculateFuelConsumption = (fuelPerKm: number) => {
    return ((totalDistance * fuelPerKm) / 100).toFixed(2);
  };

  const getCO2Emission = (transportId: "car" | "motorbike" | "bus") => {
    return carbonData[transportId].toFixed(2);
  };

  const handleConfirm = () => {
    if (!selectedTransport) return;

    // Save selected transport to sessionStorage
    const transportData = {
      transportType: selectedTransport,
      totalDistance,
      timestamp: Date.now(),
    };
    sessionStorage.setItem("selected_transport", JSON.stringify(transportData));

    // Navigate back to showing_plan_page
    router.push(`/planning_page/showing_plan_page?refresh=${Date.now()}`);
  };

  const handleBack = () => {
    router.back();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#53B552]"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-linear-to-b from-[#E3F1E4] to-white">
      {/* Header */}
      <div className="bg-[#E3F1E4] px-6 py-4 sticky top-0 z-10 shadow-sm">
        <div className="flex items-center justify-between max-w-2xl mx-auto">
          <button
            onClick={handleBack}
            className="p-2 bg-white rounded-full shadow-sm hover:bg-gray-50 transition"
          >
            <ChevronLeft size={24} className="text-gray-700" />
          </button>
          <h1
            className={`${jost.className} text-xl font-bold text-gray-800 flex items-center gap-2`}
          >
            <Fuel className="text-[#53B552]" size={24} />
            Select Transport
          </h1>
          <div className="w-10"></div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-2xl mx-auto px-6 py-8">
        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-4 mb-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="text-red-600 shrink-0 mt-0.5" size={20} />
              <div>
                <p className="text-sm font-semibold text-red-800 mb-1">
                  Error Loading Data
                </p>
                <p className="text-sm text-red-700">
                  {error}. Using estimated values.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Trip Info */}
        <div className="bg-white rounded-2xl p-6 shadow-sm mb-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">Total Distance</p>
              <p
                className={`${jost.className} text-3xl font-bold text-gray-800`}
              >
                {totalDistance.toFixed(1)} <span className="text-lg">km</span>
              </p>
            </div>
            <div className="w-16 h-16 bg-[#E3F1E4] rounded-full flex items-center justify-center">
              <TrendingUp className="text-[#53B552]" size={32} />
            </div>
          </div>
        </div>

        {/* Transport Options */}
        <div className="space-y-4 mb-6">
          <h2
            className={`${jost.className} text-lg font-semibold text-gray-700 mb-4`}
          >
            Choose Your Transport Method
          </h2>

          {TRANSPORT_OPTIONS.map((transport) => {
            const Icon = transport.icon;
            const isSelected = selectedTransport === transport.id;
            const fuelNeeded = calculateFuelConsumption(transport.fuelPerKm);
            const co2Emission = getCO2Emission(transport.id);

            return (
              <button
                key={transport.id}
                onClick={() => setSelectedTransport(transport.id)}
                className={`w-full bg-white rounded-2xl p-6 shadow-sm transition-all duration-200 ${
                  isSelected
                    ? "ring-2 ring-[#53B552] shadow-lg scale-[1.02]"
                    : "hover:shadow-md hover:scale-[1.01]"
                }`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-4">
                    <div
                      className={`w-14 h-14 ${transport.bgColor} rounded-xl flex items-center justify-center`}
                    >
                      <Icon className={transport.color} size={28} />
                    </div>
                    <div className="text-left">
                      <h3
                        className={`${jost.className} text-xl font-bold text-gray-800`}
                      >
                        {transport.name}
                      </h3>
                      <p className="text-sm text-gray-500">
                        {transport.fuelPerKm}L / 100km
                      </p>
                    </div>
                  </div>
                  {isSelected && (
                    <div className="w-8 h-8 bg-[#53B552] rounded-full flex items-center justify-center">
                      <Check className="text-white" size={20} />
                    </div>
                  )}
                </div>

                {/* Fuel & Emission Stats */}
                <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-100">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Fuel className="text-gray-400" size={16} />
                      <p className="text-xs text-gray-500 font-medium">
                        Total Fuel
                      </p>
                    </div>
                    <p
                      className={`${jost.className} text-lg font-bold text-gray-800`}
                    >
                      {fuelNeeded}{" "}
                      <span className="text-sm font-normal">L</span>
                    </p>
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Leaf className="text-gray-400" size={16} />
                      <p className="text-xs text-gray-500 font-medium">
                        CO₂ Emission
                      </p>
                    </div>
                    <p
                      className={`${jost.className} text-lg font-bold ${
                        transport.id === "bus"
                          ? "text-green-600"
                          : "text-gray-800"
                      }`}
                    >
                      {co2Emission}{" "}
                      <span className="text-sm font-normal">kg</span>
                    </p>
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Eco Tip */}
        <div className="bg-green-50 border border-green-200 rounded-2xl p-4 mb-6">
          <div className="flex items-start gap-3">
            <Leaf className="text-green-600 shrink-0 mt-0.5" size={20} />
            <div>
              <p className="text-sm font-semibold text-green-800 mb-1">
                Eco Tip
              </p>
              <p className="text-sm text-green-700">
                Choosing public transport like buses can reduce your carbon
                footprint by up to 75% compared to private vehicles!
              </p>
            </div>
          </div>
        </div>

        {/* Confirm Button */}
        <button
          onClick={handleConfirm}
          disabled={!selectedTransport}
          className={`w-full py-4 rounded-2xl font-bold text-white transition-all duration-200 flex items-center justify-center gap-2 ${
            selectedTransport
              ? "bg-[#53B552] hover:bg-green-600 shadow-lg hover:shadow-xl"
              : "bg-gray-300 cursor-not-allowed"
          }`}
        >
          Confirm & Continue
          <ArrowRight size={20} />
        </button>
      </div>
    </div>
  );
}

export default function TransportSelectionPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-white flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#53B552]"></div>
        </div>
      }
    >
      <TransportSelectionContent />
    </Suspense>
  );
}
