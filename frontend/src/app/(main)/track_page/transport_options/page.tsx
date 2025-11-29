'use client'; 

import React, { useState, useEffect } from 'react';
import { ArrowLeft, PersonStanding, Bike, Bus, Car, Train } from 'lucide-react';

const TransportCO2Page = () => {
    const [fromAddress, setFromAddress] = useState('428 Truong Sa, Ward 2, District Phu Nhuan, HCMC');
    const [toAddress, setToAddress] = useState('227 Nguyen Van Cu, Ward 4, District 5, HCMC');
    const [distance] = useState(1.4); // km
    const [emissions, setEmissions] = useState({});
    const [loading, setLoading] = useState(true);

    const transportModes = [
        {
            id: 'walk',
            name: 'Walk',
            icon: PersonStanding,
            time: '20 min',
            apiMode: 'WALKING'
        },
        {
            id: 'motorbike',
            name: 'Motorbike',
            icon: Bike,
            time: '5 min',
            apiMode: 'MOTORBIKE'
        },
        {
            id: 'bus',
            name: 'Bus',
            icon: Bus,
            time: '10 min',
            apiMode: 'BUS'
        },
        {
            id: 'car',
            name: 'Car',
            icon: Car,
            time: '5 min',
            apiMode: 'CAR'
        },
        {
            id: 'metro',
            name: 'Metro',
            icon: Train,
            time: '20 min',
            apiMode: 'METRO'
        }
    ];

    useEffect(() => {
        fetchEmissions();
    }, []);

    const fetchEmissions = async () => {
        setLoading(true);
        const emissionData = {};

        try {
            for (const mode of transportModes) {
                const response = await fetch(
                    `/api/estimate?transport_mode=${mode.apiMode}&distance_km=${distance}&passengers=1`,
                    { method: 'POST' }
                );
                const data = await response.json();
                emissionData[mode.id] = data;
            }
            setEmissions(emissionData);
        } catch (error) {
            console.error('Error fetching emissions:', error);
            // Fallback mock data for demonstration
            emissionData.walk = { carbon_emission_kg: 0.0, carbon_saved_kg: 8.2 };
            emissionData.motorbike = { carbon_emission_kg: 4.0, carbon_saved_kg: 4.2 };
            emissionData.bus = { carbon_emission_kg: 0.0, carbon_saved_kg: 8.2 };
            emissionData.car = { carbon_emission_kg: 8.2, carbon_saved_kg: 0.0 };
            emissionData.metro = { carbon_emission_kg: 0.0, carbon_saved_kg: 8.2 };
            setEmissions(emissionData);
        }

        setLoading(false);
    };

    const TransportOption = ({ mode, emission, saved, time }) => {
        const Icon = mode.icon;

        return (
            <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                        <Icon className="w-6 h-6" />
                        <span className="font-semibold text-lg">{mode.name}</span>
                    </div>
                    <div className="text-right">
                        <div className="font-semibold">{time}</div>
                        <div className="text-sm text-gray-500">{distance}km</div>
                    </div>
                </div>

                <div className="bg-white rounded-lg border border-gray-200 p-4 flex items-center justify-between">
                    <div className="flex gap-4 flex-1">
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 bg-orange-500 rotate-45"></div>
                            <div>
                                <div className="font-semibold">{emission}kg</div>
                                <div className="text-xs text-gray-500">CO2 Emission</div>
                            </div>
                        </div>

                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 bg-green-500 rotate-45"></div>
                            <div>
                                <div className="font-semibold">{saved}kg</div>
                                <div className="text-xs text-gray-500">CO2 Saved</div>
                            </div>
                        </div>
                    </div>

                    <button className="bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded-full font-semibold transition-colors">
                        Accept
                    </button>
                </div>
            </div>
        );
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <div className="max-w-md mx-auto bg-white min-h-screen">
                {/* Header */}
                <div className="p-4 border-b">
                    <button className="p-2 hover:bg-gray-100 rounded-full transition-colors">
                        <ArrowLeft className="w-6 h-6" />
                    </button>
                </div>

                {/* Route Information */}
                <div className="p-4">
                    <div className="mb-4">
                        <div className="flex items-start gap-3 mb-3">
                            <div className="flex flex-col items-center gap-1 mt-2">
                                <div className="w-4 h-4 bg-green-500 rounded-full"></div>
                                <div className="w-0.5 h-8 bg-green-300 border-dashed border-l-2 border-green-400"></div>
                                <div className="w-4 h-4 border-2 border-green-500 rounded-full bg-white"></div>
                            </div>
                            <div className="flex-1 space-y-3">
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

                {/* Transport Options */}
                <div className="px-4 pb-20">
                    {loading ? (
                        <div className="text-center py-8">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500 mx-auto"></div>
                            <p className="mt-2 text-gray-500">Loading emissions data...</p>
                        </div>
                    ) : (
                        transportModes.map(mode => (
                            <TransportOption
                                key={mode.id}
                                mode={mode}
                                emission={emissions[mode.id]?.carbon_emission_kg?.toFixed(1) || '0.0'}
                                saved={emissions[mode.id]?.carbon_saved_kg?.toFixed(1) || '0.0'}
                                time={mode.time}
                            />
                        ))
                    )}
                </div>

                {/* Bottom Navigation */}
                <div className="fixed bottom-0 left-0 right-0 bg-white border-t">
                    <div className="max-w-md mx-auto flex justify-around py-3">
                        <button className="flex flex-col items-center gap-1 text-gray-400">
                            <div className="w-6 h-6 bg-gray-200 rounded"></div>
                            <span className="text-xs">Home</span>
                        </button>
                        <button className="flex flex-col items-center gap-1 text-green-500">
                            <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center text-white text-xs font-bold">2</div>
                            <span className="text-xs font-semibold">Track</span>
                        </button>
                        <button className="flex flex-col items-center gap-1 text-gray-400">
                            <div className="w-6 h-6 bg-gray-200 rounded"></div>
                            <span className="text-xs">Planning</span>
                        </button>
                        <button className="flex flex-col items-center gap-1 text-gray-400">
                            <div className="w-6 h-6 bg-gray-200 rounded"></div>
                            <span className="text-xs">Ecobot</span>
                        </button>
                        <button className="flex flex-col items-center gap-1 text-gray-400">
                            <div className="w-6 h-6 bg-gray-200 rounded"></div>
                            <span className="text-xs">User</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TransportCO2Page;