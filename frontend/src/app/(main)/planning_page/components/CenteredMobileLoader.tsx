import React from "react";

interface CenteredMobileLoaderProps {
  message?: string;
}

export function CenteredMobileLoader({
  message = "Loading...",
}: CenteredMobileLoaderProps) {
  return (
    <div className="min-h-screen w-full flex justify-center items-center bg-gray-200">
      <div className="w-full max-w-md bg-white h-screen shadow-2xl relative flex flex-col items-center justify-center">
        <div className="w-16 h-16 border-4 border-green-500 border-t-transparent rounded-full animate-spin mb-4"></div>
        <p className="text-gray-600">{message}</p>
      </div>
    </div>
  );
}
