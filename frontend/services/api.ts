// ============================================================
// Clinexa — API Client
// Wraps fetch with JWT auth and standardized error handling.
// ============================================================

import type {
  UploadResponse, ReportSummary, ReportDetail,
  ChatSession, ChatMessage, TrendData, ApiError,
} from "@/types/health";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

class APIError extends Error {
  constructor(
    public code: string,
    message: string,
    public status: number
  ) {
    super(message);
    this.name = "APIError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit & { token?: string } = {}
): Promise<T> {
  const { token, ...fetchOptions } = options;

  const headers: Record<string, string> = {
    ...(fetchOptions.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(fetchOptions.headers as Record<string, string> ?? {}),
  };

  const response = await fetch(`${API_BASE}${path}`, {
    ...fetchOptions,
    headers,
  });

  if (!response.ok) {
    let errorBody: ApiError | null = null;
    try {
      errorBody = await response.json();
    } catch {}
    throw new APIError(
      errorBody?.error?.code ?? "unknown_error",
      errorBody?.error?.message ?? `HTTP ${response.status}`,
      response.status
    );
  }

  if (response.status === 204) return undefined as T;
  return response.json();
}

export const apiClient = {
  // ── Reports ────────────────────────────────────────────────────
  async uploadReport(file: File, token: string): Promise<UploadResponse> {
    const form = new FormData();
    form.append("file", file);
    return request<UploadResponse>("/api/reports/upload", {
      method: "POST",
      body: form,
      token,
    });
  },

  async listReports(token: string): Promise<ReportSummary[]> {
    return request<ReportSummary[]>("/api/reports", { token });
  },

  async getReport(reportId: string, token: string): Promise<ReportDetail> {
    return request<ReportDetail>(`/api/reports/${reportId}`, { token });
  },

  async deleteReport(reportId: string, token: string): Promise<void> {
    return request<void>(`/api/reports/${reportId}`, { method: "DELETE", token });
  },

  // ── Chat ───────────────────────────────────────────────────────
  async createChatSession(token: string): Promise<ChatSession> {
    return request<ChatSession>("/api/chat/sessions", { method: "POST", token });
  },

  async sendMessage(sessionId: string, content: string, token: string): Promise<ChatMessage> {
    return request<ChatMessage>(`/api/chat/sessions/${sessionId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content }),
      token,
    });
  },

  async getMessages(sessionId: string, token: string): Promise<ChatMessage[]> {
    return request<ChatMessage[]>(`/api/chat/sessions/${sessionId}/messages`, { token });
  },

  // ── Trends ─────────────────────────────────────────────────────
  async getTrend(parameter: string, period: string, token: string): Promise<TrendData> {
    return request<TrendData>(
      `/api/trends?parameter=${encodeURIComponent(parameter)}&period=${period}`,
      { token }
    );
  },

  async getTrendParameters(token: string): Promise<string[]> {
    return request<string[]>("/api/trends/parameters", { token });
  },
};
