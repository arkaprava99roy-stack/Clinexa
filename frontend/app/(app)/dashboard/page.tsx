import { redirect } from "next/navigation";
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { HealthCard } from "@/components/HealthCard";
import { FileText, TrendingUp, MessageSquare, ArrowRight, Activity } from "lucide-react";
import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Dashboard — Clinexa",
  description: "Your health overview: report statuses, recent activity, and health trends.",
};

export default async function DashboardPage() {
  let session = null;
  let allReports: any[] = [];
  let allParams: any[] = [];

  try {
    const url = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
    const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";
    if (url && key && !url.includes("placeholder")) {
      const cookieStore = cookies();
      const supabase = createServerClient(url, key, {
        cookies: { get: (name) => cookieStore.get(name)?.value },
      });
      const { data } = await supabase.auth.getSession();
      session = data?.session ?? null;

      if (session) {
        const { data: repData } = await supabase.from("reports").select("status");
        allReports = repData ?? [];

        const { data: paramData } = await supabase.from("health_parameters").select("status");
        allParams = paramData ?? [];
      }
    }
  } catch (err) {
    session = null;
  }

  if (!session) {
    redirect("/login");
  }

  const normalCount = allReports.filter((r) => r.status === "ready").length;
  const processingCount = allReports.filter((r) => r.status === "processing").length;
  const failedCount = allReports.filter((r) => r.status === "failed").length;

  const paramNormal = allParams.filter((p) => p.status === "NORMAL").length;
  const paramHigh = allParams.filter((p) => p.status === "HIGH").length;
  const paramLow = allParams.filter((p) => p.status === "LOW").length;
  const abnormal = paramHigh + paramLow;

  const userName = session.user.user_metadata?.full_name?.split(" ")[0] || "there";

  return (
    <div className="px-8 py-8 max-w-6xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-100">
          Hello, {userName} 👋
        </h1>
        <p className="text-slate-400 mt-1">
          Here's your health overview at a glance.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
        <HealthCard
          id="card-normal"
          label="Normal Results"
          count={paramNormal}
          tone="normal"
          description="Parameters within healthy range"
        />
        <HealthCard
          id="card-review"
          label="Under Review"
          count={processingCount}
          tone="review"
          description="Reports still processing"
        />
        <HealthCard
          id="card-abnormal"
          label="Needs Attention"
          count={abnormal}
          tone="abnormal"
          description="Parameters outside normal range"
        />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
        <Link
          href="/reports"
          id="quick-upload"
          className="glass-card p-6 group hover:border-brand-500/40 transition-all duration-200"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="w-11 h-11 rounded-xl bg-brand-600/15 border border-brand-500/20 flex items-center justify-center group-hover:bg-brand-600/25 transition-colors">
              <FileText className="w-5 h-5 text-brand-400" />
            </div>
            <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-brand-400 group-hover:translate-x-1 transition-all" />
          </div>
          <h3 className="font-semibold text-slate-200 mb-1">Upload Report</h3>
          <p className="text-sm text-slate-400">Add a new blood test or medical report</p>
        </Link>

        <Link
          href="/chat"
          id="quick-chat"
          className="glass-card p-6 group hover:border-brand-500/40 transition-all duration-200"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="w-11 h-11 rounded-xl bg-emerald-600/15 border border-emerald-500/20 flex items-center justify-center group-hover:bg-emerald-600/25 transition-colors">
              <MessageSquare className="w-5 h-5 text-emerald-400" />
            </div>
            <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-emerald-400 group-hover:translate-x-1 transition-all" />
          </div>
          <h3 className="font-semibold text-slate-200 mb-1">Ask the AI</h3>
          <p className="text-sm text-slate-400">Get plain-language explanations of results</p>
        </Link>

        <Link
          href="/trends"
          id="quick-trends"
          className="glass-card p-6 group hover:border-brand-500/40 transition-all duration-200"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="w-11 h-11 rounded-xl bg-purple-600/15 border border-purple-500/20 flex items-center justify-center group-hover:bg-purple-600/25 transition-colors">
              <TrendingUp className="w-5 h-5 text-purple-400" />
            </div>
            <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-purple-400 group-hover:translate-x-1 transition-all" />
          </div>
          <h3 className="font-semibold text-slate-200 mb-1">View Trends</h3>
          <p className="text-sm text-slate-400">Track changes in your key parameters over time</p>
        </Link>
      </div>

      {/* Recent Reports */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold text-slate-200">Recent Reports</h2>
          <Link href="/reports" className="text-sm text-brand-400 hover:text-brand-300 transition-colors">
            View all →
          </Link>
        </div>

        {allReports.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 rounded-2xl bg-surface-elevated border border-surface-border flex items-center justify-center mx-auto mb-4">
              <Activity className="w-8 h-8 text-slate-600" />
            </div>
            <p className="text-slate-400 font-medium mb-1">No reports yet</p>
            <p className="text-slate-500 text-sm">Upload your first medical report to get started.</p>
            <Link href="/reports" id="empty-upload-cta" className="btn-primary mt-5 inline-flex">
              Upload Report
            </Link>
          </div>
        ) : (
          <p className="text-slate-400 text-sm">
            You have {allReports.length} report{allReports.length !== 1 ? "s" : ""} uploaded.
          </p>
        )}
      </div>
    </div>
  );
}
