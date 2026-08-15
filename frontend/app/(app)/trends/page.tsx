import { redirect } from "next/navigation";
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { TrendChart } from "@/components/TrendChart";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Health Trends — Clinexa",
  description: "Track changes in your lab values over time with interactive trend charts.",
};

export default async function TrendsPage() {
  let session = null;
  let trends: any[] = [];

  try {
    const url = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
    const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";
    if (url && key && !url.includes("placeholder")) {
      const cookieStore = cookies();
      const supabase = createServerClient(url, key, {
        cookies: { get: (name) => cookieStore.get(name)?.value }
      });
      const { data } = await supabase.auth.getSession();
      session = data?.session ?? null;

      if (session) {
        const { data: trendData } = await supabase
          .from("health_trends")
          .select("parameter, data_points, direction");
        trends = trendData ?? [];
      }
    }
  } catch (err) {
    session = null;
  }

  if (!session) redirect("/login");

  return (
    <div className="px-8 py-8 max-w-5xl mx-auto animate-fade-in">
      <div className="mb-8">
        <h1 className="section-title">Health Trends</h1>
        <p className="section-subtitle">Track changes in your key parameters over time.</p>
      </div>

      {!trends || trends.length === 0 ? (
        <div className="glass-card text-center py-20 text-slate-500">
          <p className="font-medium mb-1">No trend data available yet.</p>
          <p className="text-sm">Upload multiple reports with the same parameters to see trends.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {trends.map((trend) => (
            <TrendChart
              key={trend.parameter}
              parameter={trend.parameter}
              dataPoints={trend.data_points}
              direction={trend.direction}
            />
          ))}
        </div>
      )}
    </div>
  );
}
