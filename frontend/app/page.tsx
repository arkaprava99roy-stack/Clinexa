"use client";

import React, { useState } from "react";
import { LandingHero } from "@/components/LandingHero";
import { ClinexaApp } from "@/components/ClinexaApp";

export default function Home() {
  const [view, setView] = useState<"hero" | "dashboard">("hero");

  if (view === "hero") {
    return <LandingHero onLaunchDashboard={() => setView("dashboard")} />;
  }

  return <ClinexaApp onReturnToHero={() => setView("hero")} />;
}
