import { redirect } from "next/navigation";
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { ReportUploader } from "@/components/ReportUploader";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Reports — Clinexa",
  description: "Upload and manage your medical reports. View extracted lab parameters.",
};

export default async function ReportsPage() {
  let session = null;
  let reports: any[] = [];

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
        const { data: repData } = await supabase
          .from("reports")
          .select("id, file_name, report_type, status, uploaded_at")
          .order("uploaded_at", { ascending: false });
        reports = repData ?? [];
      }
    }
  } catch (err) {
    session = null;
  }

  if (!session) redirect("/login");

  return (
    <div className="px-8 py-8 max-w-5xl mx-auto animate-fade-in">
      <div className="mb-8">
        <h1 className="section-title">Medical Reports</h1>
        <p className="section-subtitle">Upload PDFs or images of your medical reports for AI analysis.</p>
      </div>

      <ReportUploader />

      <div className="mt-8 glass-card overflow-hidden">
        <div className="px-6 py-4 border-b border-surface-border">
          <h2 className="font-semibold text-slate-200">Your Reports</h2>
        </div>
        {!reports || reports.length === 0 ? (
          <div className="text-center py-16 text-slate-500">
            <p className="font-medium mb-1">No reports uploaded yet.</p>
            <p className="text-sm">Use the uploader above to add your first report.</p>
          </div>
        ) : (
          <div className="divide-y divide-surface-border">
            {reports.map((report) => (
              <div key={report.id} className="px-6 py-4 flex items-center justify-between hover:bg-surface-elevated transition-colors">
                <div>
                  <p className="font-medium text-slate-200 text-sm">{report.file_name}</p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {report.report_type ?? "Unknown type"} · {new Date(report.uploaded_at).toLocaleDateString()}
                  </p>
                </div>
                <span className={
                  report.status === "ready" ? "badge-normal" :
                  report.status === "processing" ? "badge-processing" : "badge-high"
                }>
                  {report.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
