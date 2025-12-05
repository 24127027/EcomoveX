'use client';

import { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';


interface PlanDestinationResponse {
    id: number;
    destination_id: string;
    type: string;
    order_in_day: number;
    visit_date: string;
    estimated_cost?: number | null;
    url?: string | null;
    note?: string | null;
    time_slot: string;
}

interface TravelPlan {
    id: number;
    place_name: string;
    start_date: string;
    end_date: string;
    budget_limit?: number | null;
    destinations: PlanDestinationResponse[];
    route?: any[] | null;
}

export default function RouteSelectionPage() {
    const location = useLocation();
    const navigate = useNavigate();

    const [plan, setPlan] = useState<TravelPlan | null>(null);

    /** Load params từ URL */
    useEffect(() => {
        const params = new URLSearchParams(location.search);

        try {
            const parsedPlan: TravelPlan = {
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
        } catch (e) {
            console.error("Failed to parse plan", e);
        }
    }, [location.search]);

    /** Tạo danh sách các option (đi từ điểm A → điểm B theo thứ tự thời gian) */
    const routeOptions = useMemo(() => {
        if (!plan) return [];

        // sắp xếp theo visit_date + order_in_day
        const sorted = [...plan.destinations].sort((a, b) => {
            const t1 = new Date(a.visit_date).getTime();
            const t2 = new Date(b.visit_date).getTime();
            if (t1 !== t2) return t1 - t2;
            return a.order_in_day - b.order_in_day;
        });

        const options = [];
        for (let i = 0; i < sorted.length - 1; i++) {
            const from = sorted[i];
            const to = sorted[i + 1];

            options.push({
                label: `${from.note || from.destination_id} → ${to.note || to.destination_id}`,
                from,
                to,
            });
        }

        return options;
    }, [plan]);

    const handleSelect = (option: { from: any; to: any }) => {
        navigate("/transport_options", {
            state: {
                from: option.from,
                to: option.to,
                plan,
            },
        });
    };

    if (!plan) return <div>Loading...</div>;

   
    return (
        <div className= "p-4" >
            <h1 className="text-xl font-bold mb-4" >
                Select a Route in { plan.place_name }
            </h1>

            {routeOptions.length === 0 ? (
                <div>No valid route options found.< /div>
            ) : (
                <ul className= "flex flex-col gap-3" >
                {
                    routeOptions.map((opt, index) => (
                    <li
                        key= { index }
                        className = "cursor-pointer p-3 rounded border bg-gray-100 hover:bg-gray-200"
                        onClick = {() => handleSelect(opt)}
                    >
                        { opt.label }
                    </li>
                }
                </ul>
              )}
        </div>
      );
}