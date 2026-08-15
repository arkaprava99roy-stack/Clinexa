"use client";

import { useCallback, useState } from "react";
import { Upload, FileText, X, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { useAuth } from "@/components/AuthProvider";
import { apiClient } from "@/services/api";
import { clsx } from "clsx";

type UploadState = "idle" | "uploading" | "success" | "error";

export function ReportUploader() {
  const { session } = useAuth();
  const [state, setState] = useState<UploadState>("idle");
  const [dragOver, setDragOver] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const upload = useCallback(async (file: File) => {
    if (!session) return;
    setFileName(file.name);
    setState("uploading");
    setProgress(0);
    setErrorMsg(null);

    // Simulate progress for UX
    const progressInterval = setInterval(() => {
      setProgress((p) => Math.min(p + 12, 85));
    }, 300);

    try {
      await apiClient.uploadReport(file, session.access_token);
      clearInterval(progressInterval);
      setProgress(100);
      setState("success");
    } catch (err: any) {
      clearInterval(progressInterval);
      setState("error");
      setErrorMsg(err?.message ?? "Upload failed. Please try again.");
    }
  }, [session]);

  const onDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) upload(file);
  }, [upload]);

  const onFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) upload(file);
    e.target.value = "";
  }, [upload]);

  const reset = () => {
    setState("idle");
    setFileName(null);
    setErrorMsg(null);
    setProgress(0);
  };

  return (
    <div
      id="report-uploader"
      onDrop={onDrop}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      className={clsx(
        "glass-card p-8 text-center transition-all duration-300 border-2 border-dashed",
        dragOver && state === "idle" ? "border-brand-500 bg-brand-500/5 scale-[1.01]" : "border-surface-border",
        state === "success" ? "border-emerald-500/40" : "",
        state === "error" ? "border-red-500/40" : "",
      )}
    >
      {state === "idle" && (
        <label htmlFor="file-input" className="cursor-pointer block">
          <div className={clsx(
            "w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center transition-all duration-200",
            dragOver ? "bg-brand-600/30 shadow-glow scale-110" : "bg-surface-elevated border border-surface-border"
          )}>
            <Upload className={clsx("w-7 h-7 transition-colors", dragOver ? "text-brand-400" : "text-slate-500")} />
          </div>
          <p className="font-semibold text-slate-200 mb-1">
            {dragOver ? "Drop it here!" : "Upload a Medical Report"}
          </p>
          <p className="text-sm text-slate-400 mb-4">
            Drag & drop or click to browse · PDF, JPG, PNG up to 15 MB
          </p>
          <span className="btn-primary cursor-pointer">Choose File</span>
          <input
            id="file-input"
            type="file"
            accept=".pdf,.jpg,.jpeg,.png,.tiff"
            onChange={onFileInput}
            className="hidden"
          />
        </label>
      )}

      {state === "uploading" && (
        <div>
          <div className="w-16 h-16 rounded-2xl mx-auto mb-4 bg-brand-600/20 border border-brand-500/30 flex items-center justify-center">
            <FileText className="w-7 h-7 text-brand-400" />
          </div>
          <p className="font-medium text-slate-200 mb-1">Uploading {fileName}</p>
          <p className="text-sm text-slate-400 mb-4">Sending to AI pipeline…</p>
          <div className="w-full max-w-xs mx-auto bg-surface-elevated rounded-full h-2 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-brand-600 to-brand-400 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-xs text-slate-500 mt-2">{progress}%</p>
        </div>
      )}

      {state === "success" && (
        <div>
          <div className="w-16 h-16 rounded-2xl mx-auto mb-4 bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center">
            <CheckCircle2 className="w-7 h-7 text-emerald-400" />
          </div>
          <p className="font-semibold text-slate-200 mb-1">Report uploaded!</p>
          <p className="text-sm text-slate-400 mb-4">
            <span className="font-medium text-slate-300">{fileName}</span> is being processed. Results will appear shortly.
          </p>
          <button id="uploader-reset" onClick={reset} className="btn-secondary text-sm px-4 py-2">
            Upload Another
          </button>
        </div>
      )}

      {state === "error" && (
        <div>
          <div className="w-16 h-16 rounded-2xl mx-auto mb-4 bg-red-500/20 border border-red-500/30 flex items-center justify-center">
            <AlertCircle className="w-7 h-7 text-red-400" />
          </div>
          <p className="font-semibold text-slate-200 mb-1">Upload failed</p>
          <p className="text-sm text-red-400 mb-4">{errorMsg}</p>
          <button id="uploader-retry" onClick={reset} className="btn-secondary text-sm px-4 py-2">
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}
