"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { CenteredMobileLoader } from "../components/CenteredMobileLoader";

function EditPlanContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const planId = searchParams.get("id");

  useEffect(() => {
    if (planId) {
      router.replace(`/planning_page/review_plan?id=${planId}`);
    } else {
      router.replace("/homepage");
    }
  }, [planId, router]);

  return <CenteredMobileLoader message="Loading plan..." />;
}
export default function EditPlanPage() {
  return (
    <Suspense fallback={<CenteredMobileLoader message="Loading plan..." />}>
      <EditPlanContent />
    </Suspense>
  );
}
