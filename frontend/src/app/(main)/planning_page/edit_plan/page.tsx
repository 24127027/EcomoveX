"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";

function EditPlanContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const planId = searchParams.get("id");

  useEffect(() => {
    if (planId) {
      // Redirect to review_plan with the plan ID
      router.replace(`/planning_page/review_plan?id=${planId}`);
    } else {
      // If no ID, go to homepage
      router.replace("/homepage");
    }
  }, [planId, router]);

  return (
    <div className="min-h-screen w-full flex justify-center items-center bg-gray-200">
      <div className="w-full max-w-md bg-white h-screen shadow-2xl relative flex flex-col items-center justify-center">
        <div className="w-16 h-16 border-4 border-green-500 border-t-transparent rounded-full animate-spin mb-4"></div>
        <p className="text-gray-600">Loading plan...</p>
      </div>
    </div>
  );
}
export default function EditPlanPage() {  
return (
    <Suspense >
      <EditPlanContent/>
    </Suspense>
  );
}