"use client";

import { CheckCircle2, AlertCircle, TrendingDown, HelpCircle } from "lucide-react";
import { clsx } from "clsx";

interface HealthCardProps {
  id?: string;
  label: string;
  count: number;
  tone: "normal" | "review" | "abnormal";
  description?: string;
}

const TONE_CONFIG = {
  normal: {
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
    text: "text-emerald-400",
    icon: CheckCircle2,
    glow: "shadow-[0_0_20px_rgba(16,185,129,0.1)]",
    countColor: "text-emerald-300",
  },
  review: {
    bg: "bg-amber-500/10",
    border: "border-amber-500/20",
    text: "text-amber-400",
    icon: HelpCircle,
    glow: "shadow-[0_0_20px_rgba(245,158,11,0.1)]",
    countColor: "text-amber-300",
  },
  abnormal: {
    bg: "bg-red-500/10",
    border: "border-red-500/20",
    text: "text-red-400",
    icon: AlertCircle,
    glow: "shadow-[0_0_20px_rgba(239,68,68,0.1)]",
    countColor: "text-red-300",
  },
};

export function HealthCard({ id, label, count, tone, description }: HealthCardProps) {
  const cfg = TONE_CONFIG[tone];
  const Icon = cfg.icon;

  return (
    <div
      id={id}
      className={clsx(
        "glass-card p-6 relative overflow-hidden transition-all duration-200 hover:scale-[1.02]",
        cfg.border,
        cfg.glow
      )}
    >
      {/* Background accent */}
      <div className={clsx("absolute top-0 right-0 w-24 h-24 rounded-full blur-2xl opacity-30 -translate-y-8 translate-x-8", cfg.bg)} />

      <div className="relative">
        <div className={clsx("flex items-center gap-2 mb-4", cfg.text)}>
          <div className={clsx("w-8 h-8 rounded-lg flex items-center justify-center", cfg.bg)}>
            <Icon className="w-4 h-4" />
          </div>
          <span className="text-sm font-medium">{label}</span>
        </div>

        <div className={clsx("text-4xl font-bold mb-1 tabular-nums", cfg.countColor)}>
          {count}
        </div>

        {description && (
          <p className="text-xs text-slate-500">{description}</p>
        )}
      </div>
    </div>
  );
}
