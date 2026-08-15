"use client";

import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, Legend,
} from "recharts";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { clsx } from "clsx";

interface DataPoint {
  date: string;
  value: number;
  status: string;
}

interface TrendChartProps {
  parameter: string;
  dataPoints: DataPoint[];
  direction?: string | null;
}

const STATUS_COLORS: Record<string, string> = {
  NORMAL: "#10b981",
  HIGH: "#ef4444",
  LOW: "#f59e0b",
  UNKNOWN: "#64748b",
};

function DirectionBadge({ direction }: { direction?: string | null }) {
  if (!direction) return null;
  const icon =
    direction === "increasing" ? <TrendingUp className="w-3.5 h-3.5" /> :
    direction === "decreasing" ? <TrendingDown className="w-3.5 h-3.5" /> :
    <Minus className="w-3.5 h-3.5" />;
  const style =
    direction === "increasing" ? "bg-red-500/10 text-red-400 border-red-500/20" :
    direction === "decreasing" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
    "bg-slate-500/10 text-slate-400 border-slate-500/20";

  return (
    <span className={clsx("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border", style)}>
      {icon} {direction.charAt(0).toUpperCase() + direction.slice(1)}
    </span>
  );
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="glass-card px-3 py-2.5 text-sm min-w-[140px]">
      <p className="text-slate-400 text-xs mb-1">{label}</p>
      <p className="font-semibold text-slate-100">{d.value}</p>
      <span className={clsx("text-xs", {
        "text-emerald-400": d.status === "NORMAL",
        "text-red-400": d.status === "HIGH",
        "text-amber-400": d.status === "LOW",
        "text-slate-400": d.status === "UNKNOWN",
      })}>
        {d.status}
      </span>
    </div>
  );
}

export function TrendChart({ parameter, dataPoints, direction }: TrendChartProps) {
  const chartData = dataPoints.map((dp) => ({
    ...dp,
    date: new Date(dp.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    fill: STATUS_COLORS[dp.status] ?? "#64748b",
  }));

  return (
    <div className="glass-card p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="font-semibold text-slate-200">{parameter}</h3>
          <p className="text-xs text-slate-500">{dataPoints.length} data point{dataPoints.length !== 1 ? "s" : ""}</p>
        </div>
        <DirectionBadge direction={direction} />
      </div>

      {dataPoints.length < 2 ? (
        <div className="text-center py-8 text-slate-500 text-sm">
          Need at least 2 data points to show a trend.
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a3347" />
            <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={{ stroke: "#2a3347" }} tickLine={false} />
            <YAxis tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#3b82f6"
              strokeWidth={2.5}
              dot={(props: any) => {
                const { cx, cy, payload } = props;
                return (
                  <circle
                    key={payload.date}
                    cx={cx}
                    cy={cy}
                    r={5}
                    fill={payload.fill}
                    stroke="#0f1117"
                    strokeWidth={2}
                  />
                );
              }}
              activeDot={{ r: 7, fill: "#3b82f6", stroke: "#0f1117", strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
