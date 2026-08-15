// ============================================================
// Clinexa — TypeScript type definitions for all API shapes
// ============================================================

export interface UploadResponse {
  report_id: string;
  status: "processing";
}

export interface ReportSummary {
  id: string;
  file_name: string;
  report_type: string | null;
  status: "processing" | "ready" | "failed";
  uploaded_at: string;
}

export interface HealthParameter {
  parameter: string;
  value: number | null;
  unit: string | null;
  ref_min: number | null;
  ref_max: number | null;
  status: "NORMAL" | "HIGH" | "LOW" | "UNKNOWN" | null;
  page_number: number | null;
}

export interface ReportDetail {
  id: string;
  file_name: string;
  status: "processing" | "ready" | "failed";
  parameters: HealthParameter[];
}

export interface Citation {
  report_id: string;
  report_name: string;
  page: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  risk_level?: "low" | "medium" | "high";
  created_at: string;
}

export interface ChatSession {
  session_id: string;
}

export interface DataPoint {
  date: string;
  value: number;
  unit?: string;
  status: "NORMAL" | "HIGH" | "LOW" | "UNKNOWN";
}

export interface TrendData {
  parameter: string;
  unit: string | null;
  direction: "increasing" | "decreasing" | "stable" | null;
  data_points: DataPoint[];
}

export interface Profile {
  id: string;
  full_name: string | null;
  preferred_language: string;
  created_at: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
  };
}
