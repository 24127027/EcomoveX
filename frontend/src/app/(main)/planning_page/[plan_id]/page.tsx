"use client";

import React, { useState, useEffect } from "react"; // Thêm useEffect
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
} from "lucide-react";
import { Jost, Roboto } from "next/font/google";
import { api, AutocompletePrediction, DestinationCard } from "@/lib/api";
import Link from "next/link";

// --- FONTS ---
const roboto = Roboto({
  subsets: ["vietnamese"],
  weight: ["400", "500", "700"],
});
const jost = Jost({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export default function AddDestinationsPage() {
  const router = useRouter();
  const params = useParams();
  const planId = Number(params.plan_id);

  const [cards, setCards] = useState<DestinationCard[]>([
    {
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
  ]);
  const [errorMessage, setErrorMessage] = useState("");

  const [suggestions, setSuggestions] = useState<{
    [key: number]: AutocompletePrediction[];
  }>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const pendingCardId = sessionStorage.getItem("picking_for_card_id");
    const pickedPlaceData = sessionStorage.getItem("picked_place_data");

    if (pendingCardId && pickedPlaceData) {
      try {
        const place = JSON.parse(pickedPlaceData); // Dữ liệu từ Map gửi về
        const tempId = Number(pendingCardId);

        setCards((prevCards) =>
          prevCards.map((c) =>
            c.tempId === tempId
              ? {
                  ...c,
                  name: place.name || c.name,
                  destinationId: place.place_id || c.destinationId,
                  type: place.type
                    ? mapGoogleTypeToBackend([place.type])
                    : c.type,
                }
              : c
          )
        );
      } catch (e) {
        console.error("Lỗi parse data từ map:", e);
      } finally {
        sessionStorage.removeItem("picking_for_card_id");
        sessionStorage.removeItem("picked_place_data");
      }
    }
  }, []);

  const handleOpenMap = (tempId: number) => {
    sessionStorage.setItem("picking_for_card_id", tempId.toString());
    router.push("/map_page?mode=picker");
  };

  const showErrorMessage = (msg: string) => {
    setErrorMessage(msg);
    setTimeout(() => setErrorMessage(""), 5000);
  };
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
        [
          "restaurant",
          "food",
          "cafe",
          "bar",
          "bakery",
          "meal_takeaway",
        ].includes(t)
      )
    )
      return "food";
    if (
      googleTypes.some((t) =>
        ["transit_station", "bus_station", "train_station", "airport"].includes(
          t
        )
      )
    )
      return "transportation";
    return "attraction";
  };

  const handleInputChange = async (tempId: number, value: string) => {
    setCards(
      cards.map((c) =>
        c.tempId === tempId ? { ...c, name: value, destinationId: "" } : c
      )
    );
    if (value.length > 2) {
      try {
        const res = await api.autocomplete({ query: value });
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
    setErrorMessage("");
  };

  const handleDateChange = (tempId: number, date: string) => {
    setCards(
      cards.map((c) => (c.tempId === tempId ? { ...c, visitDate: date } : c))
    );
    setErrorMessage("");
  };

  const cycleType = (tempId: number, currentType: string) => {
    const types = ["attraction", "food", "accommodation"];
    const nextIndex = (types.indexOf(currentType) + 1) % types.length;
    setCards(
      cards.map((c) =>
        c.tempId === tempId ? { ...c, type: types[nextIndex] } : c
      )
    );
  };

  const addCard = () => {
    const newId = Math.max(...cards.map((c) => c.tempId)) + 1;
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
    setErrorMessage("");
  };

  const removeCard = (tempId: number) => {
    if (cards.length <= 2) {
      showErrorMessage("You need at least 2 destinations!");
      return;
    }
    setCards(cards.filter((c) => c.tempId !== tempId));
  };

  const handleFinish = async () => {
    const validCards = cards.filter((c) => c.destinationId && c.visitDate);
    if (validCards.length < 2) {
      showErrorMessage("Please add at least 2 valid destinations.");
      return;
    }
    try {
      setLoading(true);
      for (const card of validCards) {
        await api.addDestinationToPlan(planId, {
          destination_id: card.destinationId,
          type: card.type,
          visit_date: card.visitDate,
          note: card.name,
        });
      }
      router.push(`/planning_page/${planId}/details`);
    } catch (error) {
      console.error("Error adding destinations:", error);
      alert("Some destinations failed to save.");
    } finally {
      setLoading(false);
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "food":
        return <Utensils size={14} className="text-orange-500" />;
      case "accommodation":
        return <Hotel size={14} className="text-blue-500" />;
      default:
        return <Camera size={14} className="text-green-500" />;
    }
  };

  return (
    <div className="min-h-screen w-full flex justify-center bg-gray-200">
      <div className="w-full max-w-md bg-[#F5F7F5] h-screen shadow-2xl relative flex flex-col">
        <div className="bg-white px-4 py-4 shadow-sm z-10 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Link href="/planning_page/create_plan">
              <ChevronLeft className="text-gray-400" />
            </Link>
            <h1 className={`${jost.className} text-gray-800 font-bold text-lg`}>
              Add Destinations
            </h1>
          </div>
          <button
            onClick={handleFinish}
            disabled={loading}
            className={`${jost.className} text-[#53B552] font-bold text-sm bg-[#E3F1E4] px-4 py-2 rounded-full hover:bg-green-100 disabled:opacity-50`}
          >
            {loading ? "Saving..." : "Done"}
          </button>
        </div>

        <main className="flex-1 overflow-y-auto p-4 space-y-4 pb-24">
          {errorMessage && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-xl flex items-center gap-2 animate-in fade-in slide-in-from-top-2 duration-300">
              <AlertCircle size={18} />
              <span className={`${jost.className} text-sm font-medium`}>
                {errorMessage}
              </span>
            </div>
          )}
          {cards.map((card, index) => (
            <div
              key={card.tempId}
              className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 relative group transition-all hover:shadow-md"
            >
              <div className="flex justify-between items-start mb-3">
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
                <button
                  onClick={() => removeCard(card.tempId)}
                  className="text-gray-300 hover:text-red-400 p-1"
                >
                  <Trash2 size={16} />
                </button>
              </div>

              <div className="relative mb-3 flex items-center gap-2">
                <div className="relative flex-1">
                  <input
                    type="text"
                    placeholder="Enter location..."
                    value={card.name}
                    onChange={(e) =>
                      handleInputChange(card.tempId, e.target.value)
                    }
                    className={`${jost.className} w-full border-b border-gray-200 focus:border-[#53B552] outline-none py-2 text-gray-700 font-medium pr-8`}
                  />
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
                  className="p-2 bg-blue-50 text-blue-500 rounded-full hover:bg-blue-100 transition-colors"
                  title="Pick on Map"
                >
                  <Map size={18} />
                </button>
              </div>

              <div className="flex items-center gap-2">
                <CalendarDays size={16} className="text-gray-400" />
                <span
                  className={`${jost.className} text-xs text-gray-400 whitespace-nowrap`}
                >
                  Visit Date:
                </span>
                <input
                  type="date"
                  value={card.visitDate}
                  onChange={(e) =>
                    handleDateChange(card.tempId, e.target.value)
                  }
                  onClick={(e) => e.currentTarget.showPicker()}
                  className={`${jost.className} w-full text-sm text-gray-600 outline-none bg-transparent cursor-pointer`}
                />
              </div>
            </div>
          ))}

          <button
            onClick={addCard}
            className="w-full py-4 border-2 border-dashed border-[#53B552] rounded-xl text-[#53B552] font-bold flex flex-col items-center justify-center hover:bg-green-50 transition-colors gap-1"
          >
            <Plus size={24} />
            <span className={`${jost.className} text-sm`}>Add Card</span>
          </button>
        </main>
      </div>
    </div>
  );
}
