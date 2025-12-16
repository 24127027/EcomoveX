"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import {
  Knewave,
  Josefin_Sans,
  Abhaya_Libre,
} from "next/font/google";

const knewave = Knewave({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--font-knewave",
});

const josefin_sans = Josefin_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-josefin",
});

const abhaya_libre = Abhaya_Libre({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-abhaya",
});

type BudgetLevel = "low" | "mid" | "luxury";
type ClimateType = "warm" | "cool" | "cold" | "any";
type AttractionType = "food" | "beach" | "nature" | "culture" | "shopping" | "nightlife" | "adventure" | "wellness" | "theme_park";

export default function PreferenceOnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState<number>(1);
  const [loading, setLoading] = useState(false);

  // Preference states
  const [budget, setBudget] = useState<BudgetLevel | null>(null);
  const [climate, setClimate] = useState<ClimateType | null>(null);
  const [kidsFriendly, setKidsFriendly] = useState<boolean | null>(null);
  const [attractionTypes, setAttractionTypes] = useState<AttractionType[]>([]);

  const totalSteps = 4;

  const handleNext = () => {
    if (step < totalSteps) {
      setStep(step + 1);
    } else {
      handleComplete();
    }
  };

  const handleSkip = async () => {
    setLoading(true);
    try {
      // Skip: update with no params - backend will use defaults
      await api.updateUserPreferences({});
      router.push("/allow_permission/location_permission");
    } catch (error) {
      console.error("Error skipping preferences:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = async () => {
    setLoading(true);
    try {
      // Build preferences object
      const preferences: any = {};

      if (budget) {
        preferences.budget_range = { level: budget };
      }

      if (climate) {
        preferences.weather_pref = { climate: climate };
      }

      if (kidsFriendly !== null) {
        preferences.kids_friendly = kidsFriendly;
      }

      if (attractionTypes.length > 0) {
        preferences.attraction_types = attractionTypes;
      }

      // Update preferences
      await api.updateUserPreferences(preferences);
      router.push("/allow_permission/location_permission");
    } catch (error) {
      console.error("Error saving preferences:", error);
    } finally {
      setLoading(false);
    }
  };

  const canProceed = () => {
    switch (step) {
      case 1:
        return budget !== null;
      case 2:
        return climate !== null;
      case 3:
        return kidsFriendly !== null;
      case 4:
        return attractionTypes.length > 0;
      default:
        return false;
    }
  };

  const toggleAttractionType = (type: AttractionType) => {
    setAttractionTypes(prev => 
      prev.includes(type) 
        ? prev.filter(t => t !== type)
        : [...prev, type]
    );
  };

  return (
    <div className="min-h-screen w-full flex justify-center bg-gradient-to-br from-green-50 via-white to-green-50">
      <main className="w-full max-w-md bg-white min-h-screen shadow-2xl flex flex-col px-6 py-8">
        {/* Header */}
        <div className="text-center mb-6">
          <h1 className={`${knewave.className} text-4xl text-green-600 mb-2`}>
            Ecomove<span className="text-green-500">X</span>
          </h1>
          <p className={`${josefin_sans.className} text-green-600 text-lg`}>
            Let&apos;s personalize your experience
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-2">
            <span className={`${abhaya_libre.className} text-sm text-gray-600`}>
              Step {step} of {totalSteps}
            </span>
            <span className={`${abhaya_libre.className} text-sm text-gray-600`}>
              {Math.round((step / totalSteps) * 100)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-green-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(step / totalSteps) * 100}%` }}
            />
          </div>
        </div>

        {/* Step Content */}
        <div className="flex-1 flex flex-col">
          {step === 1 && (
            <div className="animate-in fade-in slide-in-from-right-5 duration-500">
              <h2 className={`${abhaya_libre.className} text-2xl font-bold text-gray-800 mb-3`}>
                What&apos;s your daily budget?
              </h2>
              <p className={`${josefin_sans.className} text-gray-600 mb-6`}>
                Help us recommend destinations that fit your budget per day
              </p>

              <div className="space-y-3">
                <button
                  onClick={() => setBudget("low")}
                  className={`w-full p-5 rounded-2xl border-2 transition-all ${
                    budget === "low"
                      ? "border-green-500 bg-green-50 shadow-lg"
                      : "border-gray-200 hover:border-green-300 hover:bg-gray-50"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="text-left">
                      <h3 className={`${abhaya_libre.className} text-xl font-bold text-gray-800`}>
                        💰 Low
                      </h3>
                      <p className={`${josefin_sans.className} text-sm text-gray-600 mt-1`}>
                        Affordable and economical options
                      </p>
                    </div>
                    {budget === "low" && (
                      <div className="bg-green-500 rounded-full p-1">
                        <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                  </div>
                </button>

                <button
                  onClick={() => setBudget("mid")}
                  className={`w-full p-5 rounded-2xl border-2 transition-all ${
                    budget === "mid"
                      ? "border-green-500 bg-green-50 shadow-lg"
                      : "border-gray-200 hover:border-green-300 hover:bg-gray-50"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="text-left">
                      <h3 className={`${abhaya_libre.className} text-xl font-bold text-gray-800`}>
                        💎 Mid-Range
                      </h3>
                      <p className={`${josefin_sans.className} text-sm text-gray-600 mt-1`}>
                        Comfortable balance of value & quality
                      </p>
                    </div>
                    {budget === "mid" && (
                      <div className="bg-green-500 rounded-full p-1">
                        <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                  </div>
                </button>

                <button
                  onClick={() => setBudget("luxury")}
                  className={`w-full p-5 rounded-2xl border-2 transition-all ${
                    budget === "luxury"
                      ? "border-green-500 bg-green-50 shadow-lg"
                      : "border-gray-200 hover:border-green-300 hover:bg-gray-50"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="text-left">
                      <h3 className={`${abhaya_libre.className} text-xl font-bold text-gray-800`}>
                        ✨ Luxury
                      </h3>
                      <p className={`${josefin_sans.className} text-sm text-gray-600 mt-1`}>
                        Premium experiences & top-tier service
                      </p>
                    </div>
                    {budget === "luxury" && (
                      <div className="bg-green-500 rounded-full p-1">
                        <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                  </div>
                </button>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="animate-in fade-in slide-in-from-right-5 duration-500">
              <h2 className={`${abhaya_libre.className} text-2xl font-bold text-gray-800 mb-3`}>
                What&apos;s your ideal climate?
              </h2>
              <p className={`${josefin_sans.className} text-gray-600 mb-6`}>
                We&apos;ll suggest destinations with your preferred weather
              </p>

              <div className="space-y-3">
                <button
                  onClick={() => setClimate("warm")}
                  className={`w-full p-5 rounded-2xl border-2 transition-all ${
                    climate === "warm"
                      ? "border-green-500 bg-green-50 shadow-lg"
                      : "border-gray-200 hover:border-green-300 hover:bg-gray-50"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="text-left">
                      <h3 className={`${abhaya_libre.className} text-xl font-bold text-gray-800`}>
                        ☀️ Warm
                      </h3>
                      <p className={`${josefin_sans.className} text-sm text-gray-600 mt-1`}>
                        Sunny beaches & tropical destinations
                      </p>
                    </div>
                    {climate === "warm" && (
                      <div className="bg-green-500 rounded-full p-1">
                        <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                  </div>
                </button>

                <button
                  onClick={() => setClimate("cool")}
                  className={`w-full p-5 rounded-2xl border-2 transition-all ${
                    climate === "cool"
                      ? "border-green-500 bg-green-50 shadow-lg"
                      : "border-gray-200 hover:border-green-300 hover:bg-gray-50"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="text-left">
                      <h3 className={`${abhaya_libre.className} text-xl font-bold text-gray-800`}>
                        🌤️ Cool
                      </h3>
                      <p className={`${josefin_sans.className} text-sm text-gray-600 mt-1`}>
                        Mild temperatures & pleasant weather
                      </p>
                    </div>
                    {climate === "cool" && (
                      <div className="bg-green-500 rounded-full p-1">
                        <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                  </div>
                </button>

                <button
                  onClick={() => setClimate("cold")}
                  className={`w-full p-5 rounded-2xl border-2 transition-all ${
                    climate === "cold"
                      ? "border-green-500 bg-green-50 shadow-lg"
                      : "border-gray-200 hover:border-green-300 hover:bg-gray-50"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="text-left">
                      <h3 className={`${abhaya_libre.className} text-xl font-bold text-gray-800`}>
                        ❄️ Cold
                      </h3>
                      <p className={`${josefin_sans.className} text-sm text-gray-600 mt-1`}>
                        Snowy mountains & winter wonderlands
                      </p>
                    </div>
                    {climate === "cold" && (
                      <div className="bg-green-500 rounded-full p-1">
                        <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                  </div>
                </button>

                <button
                  onClick={() => setClimate("any")}
                  className={`w-full p-5 rounded-2xl border-2 transition-all ${
                    climate === "any"
                      ? "border-green-500 bg-green-50 shadow-lg"
                      : "border-gray-200 hover:border-green-300 hover:bg-gray-50"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="text-left">
                      <h3 className={`${abhaya_libre.className} text-xl font-bold text-gray-800`}>
                        🌍 Any
                      </h3>
                      <p className={`${josefin_sans.className} text-sm text-gray-600 mt-1`}>
                        I&apos;m flexible with weather conditions
                      </p>
                    </div>
                    {climate === "any" && (
                      <div className="bg-green-500 rounded-full p-1">
                        <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                  </div>
                </button>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="animate-in fade-in slide-in-from-right-5 duration-500">
              <h2 className={`${abhaya_libre.className} text-2xl font-bold text-gray-800 mb-3`}>
                Traveling with kids?
              </h2>
              <p className={`${josefin_sans.className} text-gray-600 mb-6`}>
                We&apos;ll prioritize family-friendly destinations
              </p>

              <div className="space-y-3">
                <button
                  onClick={() => setKidsFriendly(true)}
                  className={`w-full p-5 rounded-2xl border-2 transition-all ${
                    kidsFriendly === true
                      ? "border-green-500 bg-green-50 shadow-lg"
                      : "border-gray-200 hover:border-green-300 hover:bg-gray-50"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="text-left">
                      <h3 className={`${abhaya_libre.className} text-xl font-bold text-gray-800`}>
                        👨‍👩‍👧‍👦 Yes, kids-friendly please
                      </h3>
                      <p className={`${josefin_sans.className} text-sm text-gray-600 mt-1`}>
                        Show only family-friendly destinations
                      </p>
                    </div>
                    {kidsFriendly === true && (
                      <div className="bg-green-500 rounded-full p-1">
                        <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                  </div>
                </button>

                <button
                  onClick={() => setKidsFriendly(false)}
                  className={`w-full p-5 rounded-2xl border-2 transition-all ${
                    kidsFriendly === false
                      ? "border-green-500 bg-green-50 shadow-lg"
                      : "border-gray-200 hover:border-green-300 hover:bg-gray-50"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="text-left">
                      <h3 className={`${abhaya_libre.className} text-xl font-bold text-gray-800`}>
                        🎒 No, adults only or flexible
                      </h3>
                      <p className={`${josefin_sans.className} text-sm text-gray-600 mt-1`}>
                        Show all destinations without restrictions
                      </p>
                    </div>
                    {kidsFriendly === false && (
                      <div className="bg-green-500 rounded-full p-1">
                        <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                  </div>
                </button>
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="animate-in fade-in slide-in-from-right-5 duration-500">
              <h2 className={`${abhaya_libre.className} text-2xl font-bold text-gray-800 mb-3`}>
                What interests you?
              </h2>
              <p className={`${josefin_sans.className} text-gray-600 mb-4`}>
                Select all that apply - we&apos;ll find perfect matches
              </p>

              <div className="grid grid-cols-2 gap-3 max-h-[400px] overflow-y-auto">
                {[
                  { type: "food" as AttractionType, emoji: "🍴", label: "Food" },
                  { type: "beach" as AttractionType, emoji: "🏖️", label: "Beach" },
                  { type: "nature" as AttractionType, emoji: "🌿", label: "Nature" },
                  { type: "culture" as AttractionType, emoji: "🏛️", label: "Culture" },
                  { type: "shopping" as AttractionType, emoji: "🛍️", label: "Shopping" },
                  { type: "nightlife" as AttractionType, emoji: "🌃", label: "Nightlife" },
                  { type: "adventure" as AttractionType, emoji: "🧗", label: "Adventure" },
                  { type: "wellness" as AttractionType, emoji: "🧘", label: "Wellness" },
                  { type: "theme_park" as AttractionType, emoji: "🎢", label: "Theme Park" },
                ].map(({ type, emoji, label }) => (
                  <button
                    key={type}
                    onClick={() => toggleAttractionType(type)}
                    className={`p-4 rounded-xl border-2 transition-all ${
                      attractionTypes.includes(type)
                        ? "border-green-500 bg-green-50 shadow-md"
                        : "border-gray-200 hover:border-green-300 hover:bg-gray-50"
                    }`}
                  >
                    <div className="text-center">
                      <div className="text-3xl mb-2">{emoji}</div>
                      <h3 className={`${abhaya_libre.className} text-base font-bold text-gray-800`}>
                        {label}
                      </h3>
                      {attractionTypes.includes(type) && (
                        <div className="mt-2 flex justify-center">
                          <div className="bg-green-500 rounded-full p-0.5">
                            <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          </div>
                        </div>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="mt-8 space-y-3">
          <button
            onClick={handleNext}
            disabled={!canProceed() || loading}
            className={`${abhaya_libre.className} w-full ${
              canProceed() && !loading
                ? "bg-green-500 hover:bg-green-600 shadow-md hover:shadow-lg"
                : "bg-gray-300 cursor-not-allowed"
            } text-white rounded-full py-4 text-lg font-bold transition-all transform active:scale-[0.98]`}
          >
            {loading ? "Saving..." : step === totalSteps ? "Complete" : "Continue"}
          </button>

          <button
            onClick={handleSkip}
            disabled={loading}
            className={`${abhaya_libre.className} w-full bg-white border-2 border-gray-300 text-gray-700 hover:border-gray-400 hover:bg-gray-50 rounded-full py-4 text-lg font-medium transition-all`}
          >
            Skip for now
          </button>
        </div>

        {/* Skip explanation */}
        <p className={`${josefin_sans.className} text-center text-xs text-gray-500 mt-4`}>
          You can always update your preferences later in settings
        </p>
      </main>
    </div>
  );
}
