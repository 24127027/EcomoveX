import { useState, useEffect } from "react";

export const useGoogleMaps = () => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [loadError, setLoadError] = useState<Error | null>(null);

  useEffect(() => {
    const markLoaded = () => setIsLoaded(true);
    const markError = () =>
      setLoadError(new Error("Failed to load Google Maps"));

    const ensureGeometryLoaded = () => {
      if (window.google?.maps?.geometry) {
        setIsLoaded(true);
        return true;
      }

      if (window.google?.maps) {
        const mapsWithImport = window.google
          .maps as typeof window.google.maps & {
          importLibrary?: (name: string) => Promise<unknown>;
        };

        if (typeof mapsWithImport.importLibrary === "function") {
          mapsWithImport
            .importLibrary("geometry")
            .then(markLoaded)
            .catch(markError);
          return true;
        }
      }

      return false;
    };

    if (ensureGeometryLoaded()) {
      return;
    }

    const existingScript = document.querySelector(
      'script[src*="maps.googleapis.com"]'
    );
    if (existingScript) {
      const onLoad = () => ensureGeometryLoaded();
      existingScript.addEventListener("load", onLoad);
      existingScript.addEventListener("error", markError);
      return () => {
        existingScript.removeEventListener("load", onLoad);
        existingScript.removeEventListener("error", markError);
      };
    }

    const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
    if (!apiKey) {
      Promise.resolve().then(() =>
        setLoadError(new Error("Google Maps API key not configured"))
      );
      return;
    }

    const script = document.createElement("script");
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places,geometry`;
    script.async = true;
    script.defer = true;

    const onLoad = () => ensureGeometryLoaded();
    script.addEventListener("load", onLoad);
    script.addEventListener("error", markError);

    document.head.appendChild(script);

    return () => {
      script.removeEventListener("load", onLoad);
      script.removeEventListener("error", markError);
    };
  }, []);

  return { isLoaded, loadError };
};
