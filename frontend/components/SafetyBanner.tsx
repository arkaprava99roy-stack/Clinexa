"use client";

import { AlertTriangle, ShieldAlert, Phone } from "lucide-react";

interface SafetyBannerProps {
  riskLevel: "low" | "medium" | "high";
}

export function SafetyBanner({ riskLevel }: SafetyBannerProps) {
  if (riskLevel === "low") return null;

  if (riskLevel === "medium") {
    return (
      <div className="flex items-start gap-2.5 px-3 py-2 rounded-lg bg-amber-500/10 border border-amber-500/20 mt-2">
        <AlertTriangle className="w-3.5 h-3.5 text-amber-400 mt-0.5 flex-shrink-0" />
        <p className="text-xs text-amber-300">
          This information is for educational purposes only. Consult a healthcare professional for personalized advice.
        </p>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-2.5 px-3 py-3 rounded-lg bg-red-500/10 border border-red-500/20 mt-2">
      <ShieldAlert className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
      <div>
        <p className="text-xs font-semibold text-red-400 mb-1">Medical Consultation Required</p>
        <p className="text-xs text-red-300">
          This question requires personalized medical guidance. Please consult a licensed healthcare provider.
          If you are experiencing a medical emergency, call emergency services immediately.
        </p>
        <a
          href="tel:911"
          className="inline-flex items-center gap-1 mt-2 text-xs font-medium text-red-300 hover:text-red-200 transition-colors"
        >
          <Phone className="w-3 h-3" /> Emergency: 911
        </a>
      </div>
    </div>
  );
}
