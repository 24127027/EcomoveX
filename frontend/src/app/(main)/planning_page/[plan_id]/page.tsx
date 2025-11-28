"use client";

import React, { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ChevronLeft,
  Plus,
  Trash2,
  Map,
  Hotel,
  Utensils,
  Camera,
  CalendarDays,
  AlertCircle,
  CheckCircle2,
  Clock,
  Sparkles,
} from "lucide-react";
import { Jost, Roboto } from "next/font/google";
import {
  api,
  AutocompletePrediction,
  DestinationCard,
  PlanActivity,
} from "@/lib/api";

const roboto = Roboto({
  subsets: ["vietnamese"],
  weight: ["400", "500", "700"],
});
const jost = Jost({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

// Interface for Error Object
interface CardErrors {
  [key: number]: {
    location?: boolean;
    date?: boolean;
  };
}

export default function AddDestinationsPage() {
  const router = useRouter();
  const params = useParams();
  const planId = Number(params.plan_id);

  const sessionTokenRef = useRef(Math.random().toString(36).substring(2));

  // --- STATE ---
  const [existingActivities, setExistingActivities] = useState<PlanActivity[]>(
    []
  );
  const [isFetching, setIsFetching] = useState(true);

  const [cards, setCards] = useState<DestinationCard[]>([
    {
      tempId: 1,
      destinationId: "",
      name: "",
      visitDate: "",
      type: "attraction",
    },
  ]);

  // State to store errors for each card (to highlight UI)
  const [errors, setErrors] = useState<CardErrors>({});

  const [errorMessage, setErrorMessage] = useState("");
  const [suggestions, setSuggestions] = useState<{
    [key: number]: AutocompletePrediction[];
  }>({});
  const [loading, setLoading] = useState(false);
  const [dateLimits, setDateLimits] = useState<{ min: string; max: string }>({
    min: new Date().toISOString().split("T")[0],
    max: "",
  });

  // --- FETCH DATA ---
  useEffect(() => {
    const fetchPlanDetails = async () => {
      try {
        setIsFetching(true);
        const plans = await api.getPlans();
        const currentPlan = plans.find((p) => p.id === planId);

        if (currentPlan) {
          const startDate = currentPlan.date.split("T")[0];
          const endDate = currentPlan.end_date
            ? currentPlan.end_date.split("T")[0]
            : startDate;
          setDateLimits({ min: startDate, max: endDate });

          const isReturningFromMap = sessionStorage.getItem(
            "picking_for_card_id"
          );

          if (currentPlan.activities && currentPlan.activities.length > 0) {
            setExistingActivities(currentPlan.activities);
          } else {
            if (!isReturningFromMap) {
              setCards((prev) => {
                if (prev.length >= 2) return prev;
                return [
                  prev[0] || {
                    tempId: 1,
                    destinationId: "",
                    name: "",
                    visitDate: "",
                    type: "attraction",
                  },
                  {
                    tempId: 2,
                    destinationId: "",
                    name: "",
                    visitDate: "",
                    type: "attraction",
                  },
                ];
              });
            }
          }
        }
      } catch (error) {
        console.error("Failed to fetch plan details:", error);
      } finally {
        setIsFetching(false);
      }
    };

    if (planId) fetchPlanDetails();
  }, [planId]);
  // --- RESTORE SESSION (IF ANY) ---
  useEffect(() => {
    const savedCardsStr = sessionStorage.getItem("current_cards_state");
    let restoredCards: DestinationCard[] = [];

    if (savedCardsStr) {
      try {
        restoredCards = JSON.parse(savedCardsStr);
      } catch (e) {
        console.error("Error restoring cards:", e);
      }
    }

    if (restoredCards.length === 0) return;

    const pickingForIdStr = sessionStorage.getItem("picking_for_card_id");
    const pickedName = sessionStorage.getItem("picked_location_name");
    const pickedId = sessionStorage.getItem("picked_location_id");
    const pickedTypesStr = sessionStorage.getItem("picked_location_types");

    if (pickingForIdStr && pickedName && pickedId) {
      const targetTempId = parseInt(pickingForIdStr);

      let detectedType = "attraction";
      if (pickedTypesStr) {
        try {
          const typesArr = JSON.parse(pickedTypesStr);
          if (
            typesArr.some((t: string) =>
              ["lodging", "hotel", "resort", "guest_house"].includes(t)
            )
          )
            detectedType = "accommodation";
          else if (
            typesArr.some((t: string) =>
              ["restaurant", "food", "cafe", "bar", "bakery"].includes(t)
            )
          )
            detectedType = "restaurant";
          else if (
            typesArr.some((t: string) =>
              [
                "transit_station",
                "bus_station",
                "train_station",
                "airport",
              ].includes(t)
            )
          )
            detectedType = "transport";
        } catch (e) {
          console.error("Error parsing types", e);
        }
      }

      const updatedCards = restoredCards.map((card) => {
        if (card.tempId === targetTempId) {
          return {
            ...card,
            name: pickedName,
            destinationId: pickedId,
            type: detectedType,
          };
        }
        return card;
      });

      setCards(updatedCards);

      setErrors((prev) => {
        const newErr = { ...prev };
        delete newErr[targetTempId];
        return newErr;
      });

      sessionStorage.removeItem("picking_for_card_id");
      sessionStorage.removeItem("picked_location_name");
      sessionStorage.removeItem("picked_location_id");
      sessionStorage.removeItem("picked_location_types");
      sessionStorage.removeItem("current_cards_state");
    } else {
      setCards(restoredCards);
    }
  }, []);

  // --- HELPER FUNCTIONS ---
  const mapGoogleTypeToBackend = (googleTypes: string[]): string => {
    if (!googleTypes || googleTypes.length === 0) return "attraction";
    if (
      googleTypes.some((t) =>
        ["lodging", "hotel", "resort", "guest_house"].includes(t)
      )
    )
      return "accommodation";
    if (
      googleTypes.some((t) =>
        ["restaurant", "food", "cafe", "bar", "bakery"].includes(t)
      )
    )
      return "restaurant";
    if (
      googleTypes.some((t) =>
        ["transit_station", "bus_station", "train_station", "airport"].includes(
          t
        )
      )
    )
      return "transport";
    return "attraction";
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "restaurant":
        return <Utensils size={14} className="text-orange-500" />;
      case "accommodation":
        return <Hotel size={14} className="text-blue-500" />;
      default:
        return <Camera size={14} className="text-green-500" />;
    }
  };

  // --- HANDLERS ---
  const handleInputChange = async (tempId: number, value: string) => {
    // Clear error for this card when user types again
    setErrors((prev) => {
      const newErrors = { ...prev };
      delete newErrors[tempId];
      return newErrors;
    });

    setCards(
      cards.map((c) =>
        c.tempId === tempId ? { ...c, name: value, destinationId: "" } : c
      )
    );

    if (value.length > 2) {
      try {
        const res = await api.autocomplete({
          query: value,
          session_token: sessionTokenRef.current,
        });
        setSuggestions((prev) => ({ ...prev, [tempId]: res.predictions }));
      } catch (err) {
        console.error(err);
      }
    } else {
      setSuggestions((prev) => ({ ...prev, [tempId]: [] }));
    }
  };

  const handleSelectSuggestion = (
    tempId: number,
    prediction: AutocompletePrediction
  ) => {
    const detectedType = mapGoogleTypeToBackend(prediction.types);
    setCards(
      cards.map((c) =>
        c.tempId === tempId
          ? {
              ...c,
              name: prediction.description,
              destinationId: prediction.place_id,
              type: detectedType,
            }
          : c
      )
    );
    setSuggestions((prev) => ({ ...prev, [tempId]: [] }));

    // Clear location error if exists
    setErrors((prev) => ({
      ...prev,
      [tempId]: { ...prev[tempId], location: false },
    }));
  };

  const handleDateChange = (tempId: number, date: string) => {
    setCards(
      cards.map((c) => (c.tempId === tempId ? { ...c, visitDate: date } : c))
    );
    // Clear date error
    setErrors((prev) => ({
      ...prev,
      [tempId]: { ...prev[tempId], date: false },
    }));
  };

  const cycleType = (tempId: number, currentType: string) => {
    const types = ["attraction", "transport", "restaurant", "accommodation"];
    const nextIndex = (types.indexOf(currentType) + 1) % types.length;
    setCards(
      cards.map((c) =>
        c.tempId === tempId ? { ...c, type: types[nextIndex] } : c
      )
    );
  };

  const addCard = () => {
    const newId = Math.max(...cards.map((c) => c.tempId), 0) + 1;
    setCards([
      ...cards,
      {
        tempId: newId,
        destinationId: "",
        name: "",
        visitDate: "",
        type: "attraction",
      },
    ]);
  };

  const handleRemoveExisting = async (activityId: number | undefined) => {
    if (!activityId) return;

    // Xác nhận trước khi xóa
    const confirmDelete = window.confirm(
      "Are you sure you want to remove this destination from your plan?"
    );
    if (!confirmDelete) return;

    try {
      // 1. Gọi API xóa
      await api.deletePlanDestination(activityId);

      // 2. Cập nhật State để UI tự biến mất ngay lập tức
      setExistingActivities((prev) =>
        prev.filter((item) => item.original_id !== activityId)
      );
    } catch (error) {
      console.error("Failed to delete destination:", error);
      alert("Failed to delete. Please try again.");
    }
  };

  const removeCard = (tempId: number) => {
    if (existingActivities.length + cards.length <= 2) {
      setErrorMessage("Plan requires at least 2 destinations total.");
      setTimeout(() => setErrorMessage(""), 3000);
      return;
    }

    setCards(cards.filter((c) => c.tempId !== tempId));

    setErrors((prev) => {
      const newErr = { ...prev };
      delete newErr[tempId];
      return newErr;
    });
  };
  const handleOpenMap = (tempId: number) => {
    sessionStorage.setItem("picking_for_card_id", String(tempId));
    sessionStorage.setItem("current_cards_state", JSON.stringify(cards));
    router.push("/map_page?mode=picker");
  };

  const handleFinish = async () => {
    if (loading) return;
    setErrorMessage("");

    const newErrors: CardErrors = {};
    let hasError = false;
    let validCount = 0;

    cards.forEach((card) => {
      const isTouched = card.name.trim() !== "" || card.visitDate !== "";
      const hasId = !!card.destinationId;
      const hasDate = !!card.visitDate;

      let shouldValidate = false;

      if (existingActivities.length === 0) {
        if (isTouched || cards.indexOf(card) < 2) {
          shouldValidate = true;
        }
      } else {
        if (isTouched) {
          shouldValidate = true;
        }
      }

      if (shouldValidate) {
        if (!hasId) {
          newErrors[card.tempId] = {
            ...newErrors[card.tempId],
            location: true,
          };
          hasError = true;
        }
        if (!hasDate) {
          newErrors[card.tempId] = { ...newErrors[card.tempId], date: true };
          hasError = true;
        }
        if (hasId && hasDate) {
          validCount++;
        }
      }
    });

    setErrors(newErrors);

    if (hasError) {
      setErrorMessage(
        "Please add at least 2 valid destinations for AI to generate the itinerary!"
      );
      return;
    }

    if (existingActivities.length === 0 && validCount < 2) {
      setErrorMessage(
        "You need at least 2 valid destinations to create an itinerary."
      );
      return;
    }

    const validCards = cards.filter((c) => c.destinationId && c.visitDate);

    if (existingActivities.length > 0 && validCards.length === 0) {
      router.push(`/planning_page/${planId}/details`);
      return;
    }

    try {
      setLoading(true);
      for (const card of validCards) {
        await api.addDestinationToPlan(planId, {
          id: card.tempId,
          destination_id: card.destinationId,
          destination_type: card.type.toLowerCase(),
          visit_date: card.visitDate,
          note: card.name,
        });
      }
      if (existingActivities.length === 0) {
        router.push(`/planning_page/${planId}/details?new=true`);
      } else {
        router.push(`/planning_page/${planId}/details`);
      }
    } catch (error) {
      console.error("Error adding destinations:", error);
      alert("Error saving destinations. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const isInitialSetup = existingActivities.length === 0;

  return (
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      <div className="w-full max-w-md bg-[#F5F7F5] h-screen shadow-2xl relative flex flex-col">
        {/* Header */}
        <div className="bg-white px-4 py-4 shadow-sm z-10 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <button
              onClick={() => router.back()}
              className="text-gray-400 hover:text-gray-600"
            >
              <ChevronLeft size={24} />
            </button>
            <h1 className={`${jost.className} text-gray-800 font-bold text-lg`}>
              {isInitialSetup ? "Setup Itinerary" : "Add Places"}
            </h1>
          </div>
          <button
            onClick={handleFinish}
            disabled={loading}
            className={`${jost.className} flex items-center gap-1 font-bold text-sm bg-[#E3F1E4] px-4 py-2 rounded-full hover:bg-green-100 disabled:opacity-50 transition-colors text-[#53B552]`}
          >
            {loading ? (
              "Saving..."
            ) : isInitialSetup ? (
              <>
                <Sparkles size={16} /> Generate
              </>
            ) : (
              "Done"
            )}
          </button>
        </div>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-4 space-y-4 pb-24">
          {/* List Existing (Read Only but Deletable) */}
          {!isInitialSetup && existingActivities.length > 0 && (
            <div className="mb-6 animate-in fade-in slide-in-from-top-2 duration-500">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle2 size={16} className="text-[#53B552]" />
                <h2
                  className={`${jost.className} text-sm font-bold text-gray-500 uppercase tracking-wide`}
                >
                  Existing Destinations ({existingActivities.length})
                </h2>
              </div>
              <div className="flex flex-col gap-2">
                {existingActivities.map((act) => (
                  <div
                    key={act.id}
                    // Sửa class: bỏ opacity-80 để nhìn rõ hơn, thêm group để hover hiện nút xóa
                    className="bg-white border border-gray-200 p-3 rounded-lg flex items-center justify-between group shadow-sm transition-all hover:border-red-200"
                  >
                    <div className="flex items-center gap-3 overflow-hidden">
                      <div className="bg-gray-50 p-1.5 rounded-full shadow-sm">
                        {getTypeIcon(act.type || "attraction")}
                      </div>
                      <div className="min-w-0">
                        <p
                          className={`${jost.className} font-bold text-gray-700 text-sm truncate`}
                        >
                          {act.title}
                        </p>
                        <p className="text-xs text-gray-400 flex items-center gap-1">
                          <Clock size={10} />{" "}
                          {act.date ? act.date.split("T")[0] : "No date"}
                        </p>
                      </div>
                    </div>

                    <button
                      onClick={() => handleRemoveExisting(act.original_id)}
                      className="text-gray-300 hover:text-red-500 hover:bg-red-50 p-2 rounded-full transition-all opacity-0 group-hover:opacity-100"
                      title="Remove this place"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
              <div className="border-b border-gray-200 my-4 border-dashed"></div>
            </div>
          )}

          {/* Alert Error */}
          {errorMessage && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-xl flex items-center gap-2 animate-pulse sticky top-0 z-20 shadow-sm">
              <AlertCircle size={18} />
              <span className={`${jost.className} text-sm font-medium`}>
                {errorMessage}
              </span>
            </div>
          )}

          {!isInitialSetup && (
            <div className="flex items-center gap-2 mb-2">
              <Plus size={16} className="text-[#53B552]" />
              <h2
                className={`${jost.className} text-sm font-bold text-gray-500 uppercase tracking-wide`}
              >
                Add New Places
              </h2>
            </div>
          )}

          {cards.map((card, index) => {
            const cardErr = errors[card.tempId];
            return (
              <div
                key={card.tempId}
                className={`bg-white p-4 rounded-xl shadow-sm border relative group transition-all hover:shadow-md ${
                  cardErr
                    ? "border-red-300 ring-1 ring-red-100"
                    : "border-gray-100"
                }`}
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center gap-2">
                    <span className="bg-gray-100 text-gray-500 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold">
                      {index + 1}
                    </span>
                    <div
                      onClick={() => cycleType(card.tempId, card.type)}
                      className="flex items-center gap-1 bg-gray-50 px-2 py-1 rounded-md cursor-pointer hover:bg-gray-100 border border-gray-100 select-none"
                    >
                      {getTypeIcon(card.type)}
                      <span
                        className={`${jost.className} text-xs font-bold text-gray-500 uppercase`}
                      >
                        {card.type}
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => removeCard(card.tempId)}
                    className="text-gray-300 hover:text-red-400 p-1"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>

                {/* Input Location */}
                <div className="relative mb-3">
                  <div className="flex items-center gap-2">
                    <div className="relative flex-1">
                      <input
                        type="text"
                        placeholder="Enter location (select from dropdown)..."
                        value={card.name}
                        onChange={(e) =>
                          handleInputChange(card.tempId, e.target.value)
                        }
                        className={`${jost.className} w-full border-b ${
                          cardErr?.location
                            ? "border-red-500 placeholder-red-300"
                            : "border-gray-200 focus:border-[#53B552]"
                        } outline-none py-2 text-gray-700 font-medium pr-8 transition-colors`}
                      />
                      {/* Dropdown Suggestions */}
                      {suggestions[card.tempId] &&
                        suggestions[card.tempId].length > 0 && (
                          <div className="absolute top-full left-0 right-0 bg-white shadow-xl rounded-b-lg z-20 max-h-40 overflow-y-auto border border-gray-100">
                            {suggestions[card.tempId].map((pred) => (
                              <div
                                key={pred.place_id}
                                onClick={() =>
                                  handleSelectSuggestion(card.tempId, pred)
                                }
                                className="p-2 hover:bg-green-50 cursor-pointer text-xs border-b border-gray-50 text-gray-600 truncate"
                              >
                                {pred.description}
                              </div>
                            ))}
                          </div>
                        )}
                    </div>
                    <button
                      onClick={() => handleOpenMap(card.tempId)}
                      className={`p-2 rounded-full transition-colors ${
                        cardErr?.location
                          ? "bg-red-50 text-red-500"
                          : "bg-blue-50 text-blue-500 hover:bg-blue-100"
                      }`}
                    >
                      <Map size={18} />
                    </button>
                  </div>
                  {/* Error Text Location */}
                  {cardErr?.location && (
                    <p className="text-[10px] text-red-500 mt-1 pl-1 font-medium">
                      * Please select a location from the suggestions
                    </p>
                  )}
                </div>

                {/* Date Input */}
                <div>
                  <div className="flex items-center gap-2">
                    <CalendarDays
                      size={16}
                      className={
                        cardErr?.date ? "text-red-400" : "text-gray-400"
                      }
                    />
                    <span
                      className={`${jost.className} text-xs ${
                        cardErr?.date ? "text-red-500" : "text-gray-400"
                      } whitespace-nowrap`}
                    >
                      Visit Date:
                    </span>
                    <input
                      type="date"
                      value={card.visitDate}
                      min={dateLimits.min}
                      max={dateLimits.max}
                      onChange={(e) =>
                        handleDateChange(card.tempId, e.target.value)
                      }
                      onClick={(e) => e.currentTarget.showPicker()}
                      className={`${
                        jost.className
                      } w-full text-sm outline-none bg-transparent cursor-pointer ${
                        cardErr?.date
                          ? "text-red-600 font-bold"
                          : "text-gray-600"
                      }`}
                    />
                  </div>
                  {cardErr?.date && (
                    <p className="text-[10px] text-red-500 mt-1 pl-6 font-medium">
                      * Please select a date
                    </p>
                  )}
                </div>
              </div>
            );
          })}

          <button
            onClick={addCard}
            className="w-full py-4 border-2 border-dashed border-[#53B552] rounded-xl text-[#53B552] font-bold flex flex-col items-center justify-center hover:bg-green-50 transition-colors gap-1"
          >
            <Plus size={24} />
            <span className={`${jost.className} text-sm`}>
              Add Another Place
            </span>
          </button>
        </main>
      </div>
    </div>
  );
}
