"use client";

import {
  useEffect,
  useState,
  Suspense,
  useMemo,
  useRef,
  useCallback,
} from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api, PlanActivity, RouteLocation, TravelPlan } from "@/lib/api";
import { Jost } from "next/font/google";
import { CenteredMobileLoader } from "../components/CenteredMobileLoader";
import {
  ArrowLeft,
  Calendar,
  MapPin,
  DollarSign,
  Clock,
  Edit,
  Sun,
  Sunset,
  Moon,
  Navigation,
  Car,
  Fuel,
  Loader2,
  AlertTriangle,
  Route,
} from "lucide-react";
import { useGoogleMaps } from "@/lib/useGoogleMaps";

const jost = Jost({ subsets: ["latin"], weight: ["400", "500", "600", "700"] });

const LoadingView = () => <CenteredMobileLoader message="Loading plan..." />;

const TIME_SLOT_ORDER: Record<string, number> = {
  Morning: 0,
  Afternoon: 1,
  Evening: 2,
};

const ROUTE_COLORS = ["#22c55e", "#0ea5e9", "#9333ea", "#f97316"];

const sortActivitiesChronologically = (items: PlanActivity[]) => {
  return [...items].sort((a, b) => {
    const dateA = a.date ? new Date(a.date).getTime() : 0;
    const dateB = b.date ? new Date(b.date).getTime() : 0;
    if (dateA !== dateB) return dateA - dateB;

    const slotA = TIME_SLOT_ORDER[a.time_slot] ?? 99;
    const slotB = TIME_SLOT_ORDER[b.time_slot] ?? 99;
    if (slotA !== slotB) return slotA - slotB;

    return (a.order_in_day ?? 0) - (b.order_in_day ?? 0);
  });
};

type RoutePoint = RouteLocation & {
  label: string;
  order: number;
};

type RouteSegment = {
  from: RoutePoint;
  to: RoutePoint;
  distance: number;
  duration: number;
  polyline: string;
};

type RouteState = {
  points: RoutePoint[];
  segments: RouteSegment[];
  totalDistance: number;
  totalDuration: number;
};

const RouteOverviewMap = ({ activities }: { activities: PlanActivity[] }) => {
  const orderedActivities = useMemo(
    () => sortActivitiesChronologically(activities),
    [activities]
  );
  const { isLoaded, loadError } = useGoogleMaps();
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<google.maps.Map | null>(null);
  const markersRef = useRef<google.maps.Marker[]>([]);
  const polylinesRef = useRef<google.maps.Polyline[]>([]);
  const locationCacheRef = useRef<Record<string, RouteLocation>>({});
  const [routeState, setRouteState] = useState<RouteState>({
    points: [],
    segments: [],
    totalDistance: 0,
    totalDuration: 0,
  });
  const [routeLoading, setRouteLoading] = useState(false);
  const [routeError, setRouteError] = useState<string | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);

  const clearMapShapes = useCallback(() => {
    markersRef.current.forEach((marker) => marker.setMap(null));
    markersRef.current = [];
    polylinesRef.current.forEach((polyline) => polyline.setMap(null));
    polylinesRef.current = [];
  }, []);

  const decodePolyline = useCallback((encoded: string): RouteLocation[] => {
    if (!encoded) return [];
    const coordinates: RouteLocation[] = [];
    let index = 0;
    let lat = 0;
    let lng = 0;

    while (index < encoded.length) {
      let result = 0;
      let shift = 0;
      let b: number;

      do {
        b = encoded.charCodeAt(index++) - 63;
        result |= (b & 0x1f) << shift;
        shift += 5;
      } while (b >= 0x20);
      const deltaLat = (result & 1) !== 0 ? ~(result >> 1) : result >> 1;
      lat += deltaLat;

      result = 0;
      shift = 0;

      do {
        b = encoded.charCodeAt(index++) - 63;
        result |= (b & 0x1f) << shift;
        shift += 5;
      } while (b >= 0x20);
      const deltaLng = (result & 1) !== 0 ? ~(result >> 1) : result >> 1;
      lng += deltaLng;

      coordinates.push({ lat: lat / 1e5, lng: lng / 1e5 });
    }

    return coordinates;
  }, []);

  const fetchPointForActivity = useCallback(
    async (
      activity: PlanActivity,
      index: number
    ): Promise<RoutePoint | null> => {
      const label = activity.title || `Stop ${index + 1}`;

      if (
        typeof activity.lat === "number" &&
        typeof activity.lng === "number"
      ) {
        return {
          lat: activity.lat,
          lng: activity.lng,
          label,
          order: index + 1,
        };
      }

      const placeId =
        activity.destination_id ||
        (typeof activity.original_id === "string"
          ? activity.original_id
          : undefined);

      if (placeId) {
        const cached = locationCacheRef.current[placeId];
        if (cached) {
          return { ...cached, label, order: index + 1 };
        }
        try {
          const details = await api.getPlaceDetails(placeId, null, ["basic"]);
          const coords = {
            lat: details.geometry.location.lat,
            lng: details.geometry.location.lng,
          };
          locationCacheRef.current[placeId] = coords;
          return { ...coords, label, order: index + 1 };
        } catch (error) {
          console.error(`Failed to fetch place details for ${placeId}`, error);
        }
      }

      if (activity.address) {
        try {
          const geocode = await api.geocodeAddress(activity.address);
          const best = geocode.results?.[0]?.geometry?.location;
          if (best) {
            return { lat: best.lat, lng: best.lng, label, order: index + 1 };
          }
        } catch (error) {
          console.error("Failed to geocode address", error);
        }
      }

      return null;
    },
    []
  );

  useEffect(() => {
    if (
      !isLoaded ||
      mapRef.current ||
      !mapContainerRef.current ||
      !window.google
    ) {
      return;
    }

    mapRef.current = new window.google.maps.Map(mapContainerRef.current, {
      center: { lat: 21.028511, lng: 105.804817 },
      zoom: 12,
      disableDefaultUI: true,
      gestureHandling: "greedy",
      backgroundColor: "#EEF6EF",
    });
  }, [isLoaded]);

  useEffect(() => {
    if (!isLoaded || !mapRef.current || !window.google) return;

    clearMapShapes();
    if (routeState.points.length === 0) {
      return;
    }

    const bounds = new window.google.maps.LatLngBounds();

    routeState.points.forEach((point, index) => {
      const marker = new window.google.maps.Marker({
        map: mapRef.current!,
        position: { lat: point.lat, lng: point.lng },
        label: {
          text: `${index + 1}`,
          color: "#ffffff",
          fontSize: "12px",
          fontWeight: "600",
        },
        icon: {
          path: window.google.maps.SymbolPath.CIRCLE,
          scale: 14,
          fillColor: index === 0 ? "#16a34a" : "#0ea5e9",
          fillOpacity: 1,
          strokeWeight: 2,
          strokeColor: "#ffffff",
        },
      });
      markersRef.current.push(marker);
      const position = marker.getPosition();
      if (position) bounds.extend(position);
    });

    routeState.segments.forEach((segment, idx) => {
      const path = decodePolyline(segment.polyline);
      if (!path.length) return;

      const strokeColor = ROUTE_COLORS[idx % ROUTE_COLORS.length];
      const polyline = new window.google.maps.Polyline({
        map: mapRef.current!,
        path,
        strokeColor,
        strokeOpacity: 0.9,
        strokeWeight: 4,
        icons: [
          {
            icon: {
              path: window.google.maps.SymbolPath.FORWARD_CLOSED_ARROW,
              strokeOpacity: 0.9,
              strokeColor,
              scale: 2,
            },
            offset: "50%",
            repeat: "120px",
          },
        ],
      });
      polylinesRef.current.push(polyline);

      path.forEach((point) => {
        if (point instanceof window.google.maps.LatLng) {
          bounds.extend(point);
        } else {
          bounds.extend(new window.google.maps.LatLng(point.lat, point.lng));
        }
      });
    });

    if (
      routeState.segments.length === 0 &&
      routeState.points.length >= 2 &&
      window.google?.maps
    ) {
      const path = routeState.points.map(
        (point) => new window.google.maps.LatLng(point.lat, point.lng)
      );

      const polyline = new window.google.maps.Polyline({
        map: mapRef.current!,
        path,
        strokeColor: "#10b981",
        strokeOpacity: 0.9,
        strokeWeight: 4,
      });
      polylinesRef.current.push(polyline);
      path.forEach((latLng) => bounds.extend(latLng));
    }

    if (!bounds.isEmpty()) {
      mapRef.current.fitBounds(bounds, 48);
    }
  }, [routeState, decodePolyline, clearMapShapes, isLoaded]);

  useEffect(() => {
    return () => {
      clearMapShapes();
    };
  }, [clearMapShapes]);

  useEffect(() => {
    if (orderedActivities.length < 2) {
      setRouteState({
        points: [],
        segments: [],
        totalDistance: 0,
        totalDuration: 0,
      });
      setRouteError(null);
      setRouteLoading(false);
      return;
    }

    let shouldCancel = false;

    const buildRoutes = async () => {
      setRouteLoading(true);
      setRouteError(null);
      try {
        const resolvedPoints: RoutePoint[] = [];
        for (let i = 0; i < orderedActivities.length; i++) {
          const point = await fetchPointForActivity(orderedActivities[i], i);
          if (point) {
            resolvedPoints.push(point);
          }
        }

        if (shouldCancel) return;

        if (resolvedPoints.length < 2) {
          setRouteState({
            points: resolvedPoints,
            segments: [],
            totalDistance: 0,
            totalDuration: 0,
          });
          setRouteError(
            "Need at least two stops with coordinates to draw a route."
          );
          return;
        }

        if (shouldCancel) return;

        setRouteState({
          points: resolvedPoints,
          segments: [],
          totalDistance: 0,
          totalDuration: 0,
        });
      } catch (error) {
        if (!shouldCancel) {
          console.error("Failed to build plan route", error);
          setRouteError("Unable to prepare the map preview. Please try again.");
        }
      } finally {
        if (!shouldCancel) {
          setRouteLoading(false);
        }
      }
    };

    buildRoutes();

    return () => {
      shouldCancel = true;
    };
  }, [orderedActivities, fetchPointForActivity, refreshTick]);

  const handleRefresh = () => {
    setRefreshTick((prev) => prev + 1);
  };

  return (
    <div className="px-4 mb-6">
      <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-5 py-4 flex items-center justify-between gap-3">
          <div>
            <p
              className={`${jost.className} text-base font-semibold text-gray-900 flex items-center gap-2`}
            >
              <Route size={18} className="text-green-600" />
              Route overview
            </p>
            <p className="text-xs text-gray-500">
              Connect the stops in your plan
            </p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={routeLoading || orderedActivities.length < 2}
            className={`text-xs font-semibold px-3 py-1.5 rounded-full border transition-colors ${
              routeLoading || orderedActivities.length < 2
                ? "border-gray-200 text-gray-400"
                : "border-green-200 text-green-600 hover:bg-green-50"
            }`}
          >
            Refresh
          </button>
        </div>

        <div className="relative h-64 mx-4 mb-4 rounded-2xl overflow-hidden bg-gradient-to-br from-green-50 to-blue-50">
          <div ref={mapContainerRef} className="absolute inset-0" />
          {(!isLoaded || routeLoading) && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-white/80 text-sm text-gray-600">
              <Loader2 className="h-6 w-6 animate-spin text-green-600" />
              Loading route...
            </div>
          )}
          {(routeError || loadError) && !routeLoading && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 px-6 text-center text-sm text-red-600 bg-white/90">
              <AlertTriangle className="h-5 w-5" />
              {routeError || loadError?.message}
            </div>
          )}
          {orderedActivities.length < 2 && !routeLoading && !routeError && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-1 px-6 text-center text-sm text-gray-600 bg-white/70">
              <MapPin className="h-5 w-5 text-gray-500" />
              Add at least two stops to see the route.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

function PreviewPlanContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const planId = searchParams.get("id");

  const [plan, setPlan] = useState<TravelPlan | null>(null);
  const [activities, setActivities] = useState<PlanActivity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!planId) {
      return;
    }

    const loadPlan = async () => {
      try {
        const allPlans = await api.getPlans();
        const currentPlan = allPlans.find((p) => p.id === Number(planId));

        if (currentPlan) {
          console.log("Preview Plan - Full plan data:", currentPlan);
          console.log(
            "Preview Plan - Budget value:",
            currentPlan.budget_limit || currentPlan.budget
          );
          setPlan(currentPlan);
          setActivities(currentPlan.activities || []);
        } else {
          router.push("/homepage");
        }
      } catch (error) {
        console.error("Failed to load plan:", error);
      } finally {
        setLoading(false);
      }
    };

    loadPlan();
  }, [planId, router]);

  const groupActivitiesByDay = () => {
    if (!plan) return {};

    const grouped: { [key: string]: PlanActivity[] } = {};
    activities.forEach((activity) => {
      const dayKey = activity.date?.split("T")[0] || "No Date";
      if (!grouped[dayKey]) grouped[dayKey] = [];
      grouped[dayKey].push(activity);
    });

    // Sort activities within each day by time_slot and order_in_day
    Object.keys(grouped).forEach((day) => {
      grouped[day].sort((a, b) => {
        const slotA = TIME_SLOT_ORDER[a.time_slot] ?? 3;
        const slotB = TIME_SLOT_ORDER[b.time_slot] ?? 3;
        if (slotA !== slotB) return slotA - slotB;
        return (a.order_in_day ?? 0) - (b.order_in_day ?? 0);
      });
    });

    return grouped;
  };

  const getTimeSlotIcon = (slot: string) => {
    if (slot === "Morning")
      return <Sun size={18} className="text-orange-400" />;
    if (slot === "Afternoon")
      return <Sunset size={18} className="text-red-400" />;
    if (slot === "Evening")
      return <Moon size={18} className="text-indigo-400" />;
    return <Clock size={18} className="text-gray-400" />;
  };

  if (loading) {
    return <LoadingView />;
  }

  if (!plan) {
    return null;
  }

  const groupedActivities = groupActivitiesByDay();
  const sortedDays = Object.keys(groupedActivities).sort();

  return (
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      <div className="w-full max-w-md bg-[#F5F7F5] h-screen shadow-2xl relative flex flex-col overflow-hidden">
        {/* Header - Fixed */}
        <div className="bg-white shadow-sm shrink-0 border-b border-gray-100">
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <button
                onClick={() => router.push("/planning_page/showing_plan_page")}
                className="flex items-center gap-2 text-gray-600 hover:text-green-600 transition-colors"
              >
                <ArrowLeft size={20} />
                <span className={`${jost.className} font-semibold`}>Back</span>
              </button>
              <button
                onClick={() =>
                  router.push(`/planning_page/review_plan?id=${planId}`)
                }
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-full hover:bg-green-700 transition-colors shadow-md"
              >
                <Edit size={18} />
                <span className={`${jost.className} font-semibold`}>
                  Edit Plan
                </span>
              </button>
            </div>
          </div>
        </div>

        {/* Main Content - Scrollable */}
        <main className="flex-1 overflow-y-auto px-4 pb-6">
          {/* Hero Section */}
          <div className="py-4">
            <div className="bg-linear-to-r from-green-600 to-blue-600 rounded-3xl p-6 text-white shadow-2xl mb-6">
              <h1 className={`${jost.className} text-3xl font-bold mb-4`}>
                {plan.destination}
              </h1>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {/* Duration */}
                <div className="flex items-center gap-3 bg-white/10 backdrop-blur-sm rounded-xl p-3">
                  <Calendar size={20} />
                  <div>
                    <p className="text-xs opacity-80">Duration</p>
                    <p className={`${jost.className} font-semibold text-sm`}>
                      {new Date(plan.date).toLocaleDateString("en-US", {
                        month: "numeric",
                        day: "numeric",
                      })}{" "}
                      -{" "}
                      {plan.end_date
                        ? new Date(plan.end_date).toLocaleDateString("en-US", {
                            month: "numeric",
                            day: "numeric",
                          })
                        : new Date(plan.date).toLocaleDateString("en-US", {
                            month: "numeric",
                            day: "numeric",
                          })}
                    </p>
                  </div>
                </div>

                {/* Budget */}
                <div className="flex items-center gap-3 bg-white/10 backdrop-blur-sm rounded-xl p-3">
                  <DollarSign size={20} />
                  <div>
                    <p className="text-xs opacity-80">Budget</p>
                    <p className={`${jost.className} font-semibold text-sm`}>
                      {plan.budget_limit
                        ? `$${plan.budget_limit.toLocaleString()}`
                        : plan.budget
                        ? `$${plan.budget.toLocaleString()}`
                        : "N/A"}
                    </p>
                  </div>
                </div>

                {/* Destinations */}
                <div className="flex items-center gap-3 bg-white/10 backdrop-blur-sm rounded-xl p-3">
                  <MapPin size={20} />
                  <div>
                    <p className="text-xs opacity-80">Destinations</p>
                    <p className={`${jost.className} font-semibold text-sm`}>
                      {activities.length} places
                    </p>
                  </div>
                </div>

                {/* Transport - Coming Soon */}
                <div className="flex items-center gap-3 bg-white/10 backdrop-blur-sm rounded-xl p-3">
                  <Car size={20} />
                  <div>
                    <p className="text-xs opacity-80">Transport</p>
                    <p className={`${jost.className} font-semibold text-xs`}>
                      Not selected
                    </p>
                  </div>
                </div>

                {/* Fuel Saved - Coming Soon */}
                <div className="flex items-center gap-3 bg-white/10 backdrop-blur-sm rounded-xl p-3 md:col-span-2 lg:col-span-1">
                  <Fuel size={20} />
                  <div>
                    <p className="text-xs opacity-80">Fuel Saved</p>
                    <p className={`${jost.className} font-semibold text-xs`}>
                      To be calculated
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <RouteOverviewMap activities={activities} />

          {/* Itinerary */}
          <div className="space-y-4">
            <h2
              className={`${jost.className} text-xl font-bold text-gray-800 mb-4`}
            >
              Your Itinerary
            </h2>

            {sortedDays.length === 0 ? (
              <div className="bg-white rounded-xl p-8 text-center shadow-sm">
                <MapPin size={40} className="mx-auto text-gray-300 mb-3" />
                <p className={`${jost.className} text-gray-500`}>
                  No destinations added yet
                </p>
              </div>
            ) : (
              sortedDays.map((day, dayIndex) => (
                <div
                  key={day}
                  className="bg-white rounded-xl shadow-sm overflow-hidden border border-gray-100"
                >
                  {/* Day Header */}
                  <div className="bg-linear-to-r from-green-500 to-blue-500 p-4 text-white">
                    <div className="flex items-center gap-3">
                      <div className="bg-white text-green-600 font-bold w-10 h-10 rounded-full flex items-center justify-center shadow-md text-sm">
                        {dayIndex + 1}
                      </div>
                      <div>
                        <h3 className={`${jost.className} text-lg font-bold`}>
                          Day {dayIndex + 1}
                        </h3>
                        <p className="text-xs opacity-90">
                          {new Date(day).toLocaleDateString("en-US", {
                            weekday: "long",
                            year: "numeric",
                            month: "long",
                            day: "numeric",
                          })}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Activities */}
                  <div className="p-4 space-y-3">
                    {groupedActivities[day].map((activity) => (
                      <div
                        key={activity.id}
                        className="flex gap-3 p-3 rounded-lg bg-gray-50 border border-gray-100"
                      >
                        {/* Time Badge */}
                        <div className="shrink-0">
                          <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-white rounded-lg shadow-sm border border-gray-200">
                            {getTimeSlotIcon(activity.time_slot)}
                            <span
                              className={`${jost.className} text-xs font-semibold text-gray-700`}
                            >
                              {activity.time_slot}
                            </span>
                          </div>
                        </div>

                        {/* Activity Details */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex-1 min-w-0">
                              <h4
                                className={`${jost.className} font-bold text-gray-800 text-base mb-1 truncate`}
                              >
                                {activity.title}
                              </h4>
                              {activity.address && (
                                <p className="text-gray-600 text-xs flex items-center gap-1 truncate">
                                  <MapPin size={12} />
                                  {activity.address}
                                </p>
                              )}
                            </div>
                            {activity.image_url && (
                              <img
                                src={activity.image_url}
                                alt={activity.title}
                                className="w-16 h-16 rounded-lg object-cover shadow-sm shrink-0"
                              />
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Call to Action */}
          <div className="mt-6 mb-4 bg-linear-to-r from-green-100 to-blue-100 rounded-xl p-6 text-center border border-green-200">
            <Navigation size={36} className="mx-auto text-green-600 mb-3" />
            <h3
              className={`${jost.className} text-lg font-bold text-gray-800 mb-1`}
            >
              Ready to Go?
            </h3>
            <p className="text-gray-600 text-sm mb-4">Your adventure awaits!</p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={() =>
                  router.push(`/planning_page/review_plan?id=${planId}`)
                }
                className="flex items-center gap-2 px-5 py-2.5 bg-green-600 text-white rounded-full hover:bg-green-700 transition-colors shadow-md text-sm"
              >
                <Edit size={16} />
                <span className={`${jost.className} font-semibold`}>
                  Edit Plan
                </span>
              </button>
              <button
                onClick={() => router.push("/planning_page/showing_plan_page")}
                className="px-5 py-2.5 bg-white text-gray-700 rounded-full hover:bg-gray-100 transition-colors shadow-md border border-gray-200 text-sm"
              >
                <span className={`${jost.className} font-semibold`}>
                  Back to Plans
                </span>
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default function PreviewPlanPage() {
  return (
    <Suspense fallback={<LoadingView />}>
      <PreviewPlanContent />
    </Suspense>
  );
}
