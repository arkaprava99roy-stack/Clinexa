export interface HealthParameter {
  name: string;
  value: number;
  unit: string;
  refMin: number;
  refMax: number;
  status: "NORMAL" | "HIGH" | "LOW" | "UNKNOWN";
}

export interface ReportItem {
  id: string;
  filename: string;
  uploadedAt: string;
  reportType: string;
  status: "ready" | "processing" | "failed";
  parameters: HealthParameter[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: { reportName: string; page: number }[];
  riskLevel?: "low" | "medium" | "high";
}

export interface TrendItem {
  parameter: string;
  unit: string;
  direction: "increasing" | "decreasing" | "stable";
  dataPoints: { date: string; value: number; status: string }[];
}

export const INITIAL_REPORTS: ReportItem[] = [
  {
    id: "rep-001",
    filename: "Comprehensive_Metabolic_Panel_Jan2026.pdf",
    uploadedAt: "2026-01-15",
    reportType: "blood_test",
    status: "ready",
    parameters: [
      { name: "Hemoglobin", value: 14.2, unit: "g/dL", refMin: 13.5, refMax: 17.5, status: "NORMAL" },
      { name: "WBC", value: 11.5, unit: "x10^3/uL", refMin: 4.5, refMax: 11.0, status: "HIGH" },
      { name: "Glucose", value: 65.0, unit: "mg/dL", refMin: 70.0, refMax: 99.0, status: "LOW" },
      { name: "TSH", value: 2.1, unit: "mIU/L", refMin: 0.4, refMax: 4.0, status: "NORMAL" },
      { name: "Platelets", value: 225, unit: "x10^3/uL", refMin: 150, refMax: 400, status: "NORMAL" },
    ],
  },
  {
    id: "rep-002",
    filename: "Lipid_Profile_Dec2025.pdf",
    uploadedAt: "2025-12-10",
    reportType: "blood_test",
    status: "ready",
    parameters: [
      { name: "Total Cholesterol", value: 215.0, unit: "mg/dL", refMin: 125.0, refMax: 200.0, status: "HIGH" },
      { name: "HDL Cholesterol", value: 55.0, unit: "mg/dL", refMin: 40.0, refMax: 60.0, status: "NORMAL" },
      { name: "LDL Cholesterol", value: 135.0, unit: "mg/dL", refMin: 50.0, refMax: 100.0, status: "HIGH" },
      { name: "Triglycerides", value: 140.0, unit: "mg/dL", refMin: 30.0, refMax: 150.0, status: "NORMAL" },
    ],
  },
];

export const INITIAL_TRENDS: Record<string, TrendItem> = {
  Hemoglobin: {
    parameter: "Hemoglobin",
    unit: "g/dL",
    direction: "stable",
    dataPoints: [
      { date: "2025-06-01", value: 14.0, status: "NORMAL" },
      { date: "2025-09-15", value: 14.1, status: "NORMAL" },
      { date: "2025-12-10", value: 14.3, status: "NORMAL" },
      { date: "2026-01-15", value: 14.2, status: "NORMAL" },
    ],
  },
  Cholesterol: {
    parameter: "Total Cholesterol",
    unit: "mg/dL",
    direction: "increasing",
    dataPoints: [
      { date: "2025-06-01", value: 185.0, status: "NORMAL" },
      { date: "2025-09-15", value: 195.0, status: "NORMAL" },
      { date: "2025-12-10", value: 215.0, status: "HIGH" },
    ],
  },
  Glucose: {
    parameter: "Glucose",
    unit: "mg/dL",
    direction: "decreasing",
    dataPoints: [
      { date: "2025-06-01", value: 92.0, status: "NORMAL" },
      { date: "2025-09-15", value: 85.0, status: "NORMAL" },
      { date: "2026-01-15", value: 65.0, status: "LOW" },
    ],
  },
  TSH: {
    parameter: "TSH",
    unit: "mIU/L",
    direction: "stable",
    dataPoints: [
      { date: "2025-06-01", value: 2.0, status: "NORMAL" },
      { date: "2025-09-15", value: 2.2, status: "NORMAL" },
      { date: "2026-01-15", value: 2.1, status: "NORMAL" },
    ],
  },
};

export const INITIAL_MESSAGES: ChatMessage[] = [
  {
    id: "msg-1",
    role: "assistant",
    content: "Hello John! I'm Clinexa, your AI health assistant. I can explain your lab parameters, review historical trends, and answer questions grounded directly in your uploaded reports.",
  },
];
