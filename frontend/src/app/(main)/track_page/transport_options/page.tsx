'use client';

import React, { useState, useEffect } from 'react';
import { ArrowLeft, PersonStanding, Bike, Bus, Car, Train, LucideIcon, MapPin, Route, Home, Bot, User, X } from 'lucide-react';
import Link from 'next/link';
import { Jost, Abhaya_Libre } from 'next/font/google';    
import { useRouter } from 'next/navigation';

const jost_medium = Jost({
    subsets: ["latin"],
    weight: ["500"],
    display: 'swap'
});

const jost_semibold = Jost({
    subsets: ["latin"],
    weight: ["600"],
    display: 'swap'
});

const jost_extrabold = Jost({
    subsets: ["latin"],
    weight: ["800"],
    display: 'swap'
});

const abhayaLibre = Abhaya_Libre({
    subsets: ["latin"],
    weight: ["400"],
    display: 'swap'
});

// Types
interface EmissionData {
    carbon_emission_kg: number;
    carbon_saved_kg: number;
}

interface ApiEmissionResponse {
    carbon_emission_kg: number;
}

interface TransportMode {
    id: string;
    name: string;
    icon: LucideIcon;
    time: string;
    apiMode: string;
}

interface TransportOptionProps {
    mode: TransportMode;
    emission: string;
    saved: string;
    time: string;
    distance: number;
    onAccept: (mode: TransportMode, emission: string, saved: string) => void;
}

// Constants
const TRANSPORT_MODES: TransportMode[] = [
    { id: 'walking', name: 'Walk', icon: PersonStanding, time: '20 min', apiMode: 'WALKING' },
    { id: 'motorbike', name: 'Motorbike', icon: Bike, time: '5 min', apiMode: 'MOTORBIKE' },
    { id: 'bus', name: 'Bus', icon: Bus, time: '10 min', apiMode: 'BUS' },
    { id: 'car', name: 'Car', icon: Car, time: '5 min', apiMode: 'CAR' },
    { id: 'metro', name: 'Metro', icon: Train, time: '20 min', apiMode: 'METRO' }
];

const DEFAULT_DISTANCE = 1.4;
const API_ENDPOINT = '/carbon/estimate';

// Confirmation Modal Component
interface ConfirmModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
}

const ConfirmModal: React.FC<ConfirmModalProps> = ({ isOpen, onClose, onConfirm }) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/20 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            {/* Backdrop với blur effect */}
            <div
                className="absolute inset-0 bg-black/30 backdrop-blur-sm"
                onClick={onClose}
            ></div>

            <div className="bg-white rounded-3xl p-6 max-w-xs w-full shadow-2xl relative animate-scale-in">
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
                >
                    <X className="w-5 h-5" />
                </button>

                <h2 className={`${jost_extrabold.className} text-2xl text-green-600 text-center mb-4`}>
                    Confirm!
                </h2>

                <p className={`${jost_semibold.className} text-center text-gray-600 font-medium mb-2`}>
                    You are not saving any CO2 by using this mode of transportation.
                </p>

                <p className={`${abhayaLibre.className} text-center text-gray-600 mb-6`}>
                    Are you sure you want to continue?
                </p>

                <div className="flex gap-3">
                    <button
                        onClick={onClose}
                        className="flex-1 py-2 border-2 border-green-500 text-green-600 font-semibold rounded-lg hover:bg-green-50 transition-colors"
                    >
                        No
                    </button>
                    <button
                        onClick={onConfirm}
                        className="flex-1 py-2 bg-green-500 text-white font-semibold rounded-lg hover:bg-green-600 transition-colors"
                    >
                        Yes
                    </button>
                </div>
            </div>
        </div>
    );
};


// Transport Option Component
const TransportOption: React.FC<TransportOptionProps> = ({ mode, emission, saved, time, distance, onAccept }) => {
    const Icon = mode.icon;

    const handleAccept = () => {
        onAccept(mode, emission, saved);
    };

    return (
        <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                    <Icon className="w-6 h-6 text-black" />
                    <span className={`${jost_medium.className} text-black whitespace-nowrap`}>{mode.name}</span>
                </div>
                <div className="text-right">
                    <div className={`${abhayaLibre.className} text-sm text-black whitespace-nowrap`}>{time}</div>
                    <div className={`${abhayaLibre.className} text-sm text-black whitespace-nowrap`}>{distance}km</div>
                </div>
            </div>
            <div className="flex items-center flex-1">
                <div className="bg-gray-100 rounded-lg border border-gray-400 p-3 px-6 flex gap-10 inline-flex">
                    <div className="flex items-center gap-3">
                        <div className="w-3 h-3 bg-orange-500 rotate-45"></div>
                        <div>
                            <div className={`${jost_semibold.className} text-xs text-black whitespace-nowrap`}>{emission}kg</div>
                            <div className={`${jost_semibold.className} text-xs text-gray-400 whitespace-nowrap`}>CO2 Emission</div>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="w-3 h-3 bg-green-500 rotate-45"></div>
                        <div>
                            <div className={`${jost_semibold.className} text-xs text-black whitespace-nowrap`}>{saved}kg</div>
                            <div className={`${jost_semibold.className} text-xs text-gray-400 whitespace-nowrap`}>CO2 Saved</div>
                        </div>
                    </div>
                </div>
                <div className="text-right flex-1">
                    <button
                        onClick={handleAccept}
                        className={`${jost_semibold.className} bg-green-500 hover:bg-green-600 text-white text-sm px-6 py-2 rounded-full transition-colors whitespace-nowrap`}
                    >
                        Accept
                    </button>
                </div>
            </div>
        </div>
    );
};

// Main Component
const TransportCO2Page = () => {
    const router = useRouter();
    const [emissions, setEmissions] = useState<Record<string, EmissionData>>({});
    const [fromAddress, setFromAddress] = useState('428 Truong Sa, Ward 2, District Phu Nhuan, HCMC');
    const [toAddress, setToAddress] = useState('227 Nguyen Van Cu, Ward 4, District 5, HCMC');
    const [distance] = useState(DEFAULT_DISTANCE);
    const [loading, setLoading] = useState(true);
    const [showConfirmModal, setShowConfirmModal] = useState(false);
    const [selectedMode, setSelectedMode] = useState<TransportMode | null>(null);
    const [selectedEmission, setSelectedEmission] = useState('0.0');
    const [selectedSaved, setSelectedSaved] = useState('0.0');

    useEffect(() => {
        const fetchEmissions = async () => {
            setLoading(true);
            const emissionData: Record<string, EmissionData> = {};

            try {
                // Bước 1: Fetch tất cả emission data
                const rawEmissions: Record<string, number> = {};

                for (const mode of TRANSPORT_MODES) {
                    try {
                        const url = `${API_ENDPOINT}?transport_mode=${mode.apiMode}&distance_km=${distance}&passengers=1`;
                        console.log(`Fetching: ${url}`);

                        const response = await fetch(url, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            }
                        });

                        // Kiểm tra response status
                        if (!response.ok) {
                            const text = await response.text();
                            console.error(`API Error for ${mode.id}:`, {
                                status: response.status,
                                statusText: response.statusText,
                                body: text
                            });
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }

                        // Kiểm tra Content-Type
                        const contentType = response.headers.get('content-type');
                        console.log(`Content-Type for ${mode.id}:`, contentType);

                        if (!contentType || !contentType.includes('application/json')) {
                            const text = await response.text();
                            console.error(`Non-JSON response for ${mode.id}:`, text);
                            throw new Error('Response is not JSON');
                        }

                        // Parse JSON
                        const data = await response.json();
                        console.log(`Data for ${mode.id}:`, data);

                        // Backend có thể trả về object hoặc số
                        const emissionValue = typeof data === 'number'
                            ? data
                            : data.carbon_emission_kg || data.carbon_emission || 0;

                        rawEmissions[mode.id] = emissionValue;

                    } catch (fetchError) {
                        console.error(`Error fetching emission for ${mode.id}:`, fetchError);
                        // Nếu 1 mode fail, vẫn tiếp tục với mode khác
                        rawEmissions[mode.id] = 0;
                    }
                }

                console.log('All raw emissions:', rawEmissions);

                // Bước 2: Lấy baseline emission (car)
                const carEmission = rawEmissions['car'] || 0;
                console.log('Car baseline emission:', carEmission);

                // Bước 3: Tính carbon_saved cho mỗi phương tiện
                for (const mode of TRANSPORT_MODES) {
                    const emission = rawEmissions[mode.id] || 0;
                    const saved = Math.max(0, carEmission - emission);

                    emissionData[mode.id] = {
                        carbon_emission_kg: emission,
                        carbon_saved_kg: saved
                    };
                }

                console.log('Final emission data:', emissionData);
                setEmissions(emissionData);

            } catch (error) {
                console.error('Critical error in fetchEmissions:', error);

                // Fallback data với tính toán carbon_saved
                console.log('Using fallback data');
                const fallbackRaw = {
                    walk: 0.0,
                    motorbike: 4.0,
                    bus: 0.0,
                    car: 8.2,
                    metro: 0.0
                };

                const carEmission = fallbackRaw.car;

                Object.keys(fallbackRaw).forEach(key => {
                    const emission = fallbackRaw[key as keyof typeof fallbackRaw];
                    emissionData[key] = {
                        carbon_emission_kg: emission,
                        carbon_saved_kg: Math.max(0, carEmission - emission)
                    };
                });

                setEmissions(emissionData);
            } finally {
                setLoading(false);
            }
        };

        fetchEmissions();
    }, [distance]);

    const handleAccept = (mode: TransportMode, emission: string, saved: string) => {
        setSelectedMode(mode);
        setSelectedEmission(emission);
        setSelectedSaved(saved);

        // Nếu chọn car (saved = 0), hiện modal confirmation
        if (mode.id === 'car' || parseFloat(saved) === 0) {
            setShowConfirmModal(true);
        } else {
            // Chuyển trang trực tiếp cho các phương tiện khác
            navigateToNextPage(mode, emission, saved);
        }
    };

    const handleConfirmCar = () => {
        setShowConfirmModal(false);
        if (selectedMode) {
            navigateToNextPage(selectedMode, selectedEmission, selectedSaved);
        }
    };

    const handleCancelCar = () => {
        setShowConfirmModal(false);
        setSelectedMode(null);
    };

    const navigateToNextPage = (mode: TransportMode, emission: string, saved: string) => {
        // Lưu data vào localStorage (optional)
        const tripData = {
            mode: mode.name,
            emission,
            saved,
            fromAddress,
            toAddress,
            distance
        };
        localStorage.setItem('selectedTrip', JSON.stringify(tripData));

        // Chuyển trang với query params
        const params = new URLSearchParams({
            mode: mode.id,
            modeName: mode.name,
            emission,
            saved,
            time: mode.time,
            distance: distance.toString(),
            from: fromAddress,
            to: toAddress,
        });
        if (mode.id === 'car') {
            router.push(`/track_page/result/not_save_CO2?${params.toString()}`);
        }
        else 
            router.push(`/track_page/result/save_CO2?${params.toString()}`);
    };

    const handleBackClick = () => {
        router.push("/track_page/leaderboard");
    };

    return (
        <div className="bg-gray-200 flex justify-center border-b shadow-sm h-screen overflow-hidden">
        <div className="w-full max-w-md mx-auto bg-gray-50 min-h-screen overflow-y-auto scrollbar-hide">
                <header className="bg-white border-b shadow-sm sticky top-0 z-10">
                    <div className="p-4">
                        <div className="mb-4">
                            {/* Back Button */}
                            <button
                                onClick={handleBackClick}
                                className="p-2 hover:bg-gray-200 rounded-full transition-colors"
                            >
                                <ArrowLeft className="w-6 h-6 text-gray-700" />
                            </button>

                            {/* Route Information */}
                            <div className="flex items-start gap-3 mb-3">
                                <div className="flex flex-col items-center gap-1 mt-2">
                                    <div className="w-4 h-4 bg-green-500 rounded-full"></div>
                                    <div className="w-0.5 h-8 bg-green-300 border-dashed border-l-2 border-green-400"></div>
                                    <div className="w-4 h-4 border-2 border-green-500 rounded-full bg-white"></div>
                                </div>
                                <div className={`${abhayaLibre.className} flex-1 space-y-3 text-black text-sm`}>
                                    <input
                                        type="text"
                                        value={fromAddress}
                                        onChange={(e) => setFromAddress(e.target.value)}
                                        className="w-full p-3 border border-gray-300 rounded-lg"
                                    />
                                    <input
                                        type="text"
                                        value={toAddress}
                                        onChange={(e) => setToAddress(e.target.value)}
                                        className="w-full p-3 border border-gray-300 rounded-lg"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </header>

                {/* Transport Options */}
                <div className="px-4 pt-4 pb-20">
                    {loading ? (
                        <div className="text-center py-8">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500 mx-auto"></div>
                            <p className="mt-2 text-gray-500">Loading emissions data...</p>
                        </div>
                    ) : (
                        TRANSPORT_MODES.map(mode => (
                            <TransportOption
                                key={mode.id}
                                mode={mode}
                                emission={emissions[mode.id]?.carbon_emission_kg?.toFixed(1) || '0.0'}
                                saved={emissions[mode.id]?.carbon_saved_kg?.toFixed(1) || '0.0'}
                                time={mode.time}
                                distance={distance}
                                onAccept={handleAccept}
                            />
                        ))
                    )}
                </div>

                {/* Confirmation Modal */}
                <ConfirmModal
                    isOpen={showConfirmModal}
                    onClose={handleCancelCar}
                    onConfirm={handleConfirmCar}
                />

                <style jsx global>{`
                    @keyframes scale-in {
                    from {
                        transform: scale(0.95);
                        opacity: 0;
                    }
                    to {
                        transform: scale(1);
                        opacity: 1;
                    }
                    }
  
                    @keyframes fade-in {
                    from {
                        opacity: 0;
                    }
                    to {
                        opacity: 1;
                    }
                    }
  
                    .animate-scale-in {
                    animation: scale-in 0.2s ease-out;
                    }
  
                    .animate-fade-in {
                    animation: fade-in 0.2s ease-out;
                    }
                `}</style>

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

export { jost_medium, jost_semibold, abhayaLibre }; 
export default TransportCO2Page;