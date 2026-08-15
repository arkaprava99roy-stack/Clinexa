"use client";

import React, { useState } from "react";
import {
  Activity,
  FileText,
  MessageSquare,
  TrendingUp,
  Settings,
  Menu,
  X,
  Upload,
  Send,
  Plus,
  ShieldAlert,
  FileCheck,
  Trash2,
  Cpu,
  BarChart2,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import {
  INITIAL_REPORTS,
  INITIAL_TRENDS,
  INITIAL_MESSAGES,
  ReportItem,
  ChatMessage,
} from "@/lib/mockData";

interface ClinexaAppProps {
  onReturnToHero: () => void;
}

export const ClinexaApp: React.FC<ClinexaAppProps> = ({ onReturnToHero }) => {
  const [activeTab, setActiveTab] = useState<
    "dashboard" | "reports" | "chat" | "trends" | "settings"
  >("dashboard");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // App State
  const [reports, setReports] = useState<ReportItem[]>(INITIAL_REPORTS);
  const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_MESSAGES);
  const [chatInput, setChatInput] = useState("");
  const [uploading, setUploading] = useState(false);
  const [selectedTrend, setSelectedTrend] = useState("Hemoglobin");
  const [highRiskBanner, setHighRiskBanner] = useState<string | null>(null);

  // Stats Calculations
  const allParams = reports.flatMap((r) => r.parameters);
  const normalParams = allParams.filter((p) => p.status === "NORMAL").length;
  const reviewParams = allParams.filter(
    (p) => p.status === "HIGH" || p.status === "LOW"
  ).length;

  // Handlers
  const handleSimulatedUpload = () => {
    setUploading(true);
    setTimeout(() => {
      const newRep: ReportItem = {
        id: `rep-${Date.now()}`,
        filename: "Complete_Blood_Count_Feb2026.pdf",
        uploadedAt: new Date().toISOString().split("T")[0],
        reportType: "blood_test",
        status: "ready",
        parameters: [
          { name: "Hemoglobin", value: 14.5, unit: "g/dL", refMin: 13.5, refMax: 17.5, status: "NORMAL" },
          { name: "RBC", value: 4.8, unit: "x10^6/uL", refMin: 4.3, refMax: 5.9, status: "NORMAL" },
          { name: "WBC", value: 7.2, unit: "x10^3/uL", refMin: 4.5, refMax: 11.0, status: "NORMAL" },
        ],
      };
      setReports((prev) => [newRep, ...prev]);
      setUploading(false);
    }, 1500);
  };

  const handleSendMessage = (textToSend?: string) => {
    const query = textToSend || chatInput;
    if (!query.trim()) return;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: query,
    };
    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setChatInput("");

    const qLower = query.toLowerCase();

    setTimeout(() => {
      if (
        qLower.includes("dose") ||
        qLower.includes("medication") ||
        qLower.includes("prescription") ||
        qLower.includes("cure") ||
        qLower.includes("emergency") ||
        qLower.includes("chest pain")
      ) {
        setHighRiskBanner("High-risk medical query intercepted by Safety Agent");
        const safetyMsg: ChatMessage = {
          id: `msg-${Date.now() + 1}`,
          role: "assistant",
          riskLevel: "high",
          content:
            "⚠️ **MEDICAL SAFETY NOTICE** ⚠️\n\nI cannot prescribe medications, suggest dosages, or diagnose acute conditions. Please consult a licensed medical professional or contact emergency services immediately if you are experiencing severe symptoms.",
        };
        setMessages((prev) => [...prev, safetyMsg]);
      } else if (qLower.includes("hemoglobin") || qLower.includes("iron") || qLower.includes("anemia")) {
        const hgbMsg: ChatMessage = {
          id: `msg-${Date.now() + 1}`,
          role: "assistant",
          citations: [{ reportName: "Comprehensive_Metabolic_Panel_Jan2026.pdf", page: 2 }],
          content:
            "Your **Hemoglobin** level from your Jan 15, 2026 report is **14.2 g/dL**, which falls within the normal reference range (13.5 – 17.5 g/dL). Normal hemoglobin levels indicate healthy oxygen-carrying capacity in red blood cells.",
        };
        setMessages((prev) => [...prev, hgbMsg]);
      } else if (qLower.includes("cholesterol") || qLower.includes("lipid")) {
        const cholMsg: ChatMessage = {
          id: `msg-${Date.now() + 1}`,
          role: "assistant",
          citations: [{ reportName: "Lipid_Profile_Dec2025.pdf", page: 1 }],
          content:
            "Your **Total Cholesterol** is **215 mg/dL** (Reference: 125 – 200 mg/dL), classified as **HIGH** by the deterministic rule engine. LDL Cholesterol is also slightly elevated at **135 mg/dL**.",
        };
        setMessages((prev) => [...prev, cholMsg]);
      } else {
        const genMsg: ChatMessage = {
          id: `msg-${Date.now() + 1}`,
          role: "assistant",
          citations: [{ reportName: "Comprehensive_Metabolic_Panel_Jan2026.pdf", page: 1 }],
          content:
            `Based on your 2 uploaded reports, your overall health score is **88/100**. You have **${normalParams} normal parameters** and **${reviewParams} parameters needing review**.`,
        };
        setMessages((prev) => [...prev, genMsg]);
      }
    }, 600);
  };

  return (
    <div className="min-h-screen bg-[#05070f] text-slate-100 flex flex-col">
      {/* Sticky Glass Navigation Bar */}
      <header className="sticky top-0 z-40 bg-[#0b0f1f]/80 backdrop-blur-xl border-b border-white/10 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={onReturnToHero}
            className="flex items-center gap-2.5 group focus:outline-none"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600 p-0.5 flex items-center justify-center shadow-md shadow-cyan-500/20">
              <div className="w-full h-full bg-[#0b0f1f] rounded-[6px] flex items-center justify-center">
                <Activity className="w-4 h-4 text-cyan-400" />
              </div>
            </div>
            <span className="text-lg font-extrabold tracking-tighter text-white group-hover:text-cyan-400 transition-colors">
              Clinexa
            </span>
          </button>
          <span className="hidden sm:inline-block text-xs font-mono px-2.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
            PROTOTYPE v1.0
          </span>
        </div>

        {/* Desktop Tabs */}
        <nav className="hidden md:flex items-center gap-1.5 p-1 rounded-full bg-white/5 border border-white/10">
          {[
            { id: "dashboard", label: "Dashboard", icon: Activity },
            { id: "reports", label: "Reports", icon: FileText },
            { id: "chat", label: "Chat", icon: MessageSquare },
            { id: "trends", label: "Trends", icon: TrendingUp },
            { id: "settings", label: "Settings", icon: Settings },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium transition-all ${
                  isActive
                    ? "bg-gradient-to-r from-cyan-500 to-blue-600 text-black font-semibold shadow-md shadow-cyan-500/20"
                    : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Mobile Hamburger Toggle */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden p-2 rounded-lg glass-card text-slate-300"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </header>

      {/* Mobile Slide-out Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-[#0b0f1f] border-b border-white/10 px-6 py-4 space-y-2 animate-fade-in">
          {[
            { id: "dashboard", label: "Dashboard", icon: Activity },
            { id: "reports", label: "Reports", icon: FileText },
            { id: "chat", label: "Chat", icon: MessageSquare },
            { id: "trends", label: "Trends", icon: TrendingUp },
            { id: "settings", label: "Settings", icon: Settings },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id as any);
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium ${
                activeTab === tab.id
                  ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                  : "text-slate-400 hover:bg-white/5"
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6">
        {/* TAB 1: DASHBOARD */}
        {activeTab === "dashboard" && (
          <div className="space-y-8 animate-fade-in">
            {/* Welcome Banner */}
            <div className="relative glass-card p-8 overflow-hidden rounded-3xl">
              <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
              <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative z-10">
                <div>
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-mono mb-3">
                    <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                    <span>RAG Verified Active</span>
                  </div>
                  <h1 className="text-3xl font-extrabold tracking-tight text-white">
                    Welcome back, John Doe 👋
                  </h1>
                  <p className="text-slate-400 mt-2 max-w-xl text-sm leading-relaxed">
                    System monitoring **{reports.length} uploaded reports** and **{allParams.length} parameters**. Rule Engine verified zero status anomalies.
                  </p>
                </div>

                <div className="flex items-center gap-4 bg-white/5 border border-white/10 rounded-2xl p-4">
                  <div className="text-center px-3 border-r border-white/10">
                    <span className="block text-2xl font-extrabold text-cyan-400">88</span>
                    <span className="text-[10px] font-mono uppercase text-slate-400">Health Score</span>
                  </div>
                  <div className="text-center px-3 border-r border-white/10">
                    <span className="block text-2xl font-extrabold text-emerald-400">{normalParams}</span>
                    <span className="text-[10px] font-mono uppercase text-slate-400">Normal</span>
                  </div>
                  <div className="text-center px-3">
                    <span className="block text-2xl font-extrabold text-amber-400">{reviewParams}</span>
                    <span className="text-[10px] font-mono uppercase text-slate-400">Review</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Stat Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
              <div className="glass-card p-6 rounded-2xl">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-mono uppercase text-slate-400">Total Reports</span>
                  <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400">
                    <FileText className="w-5 h-5" />
                  </div>
                </div>
                <div className="text-3xl font-extrabold text-white">{reports.length}</div>
                <p className="text-xs text-slate-400 mt-2">Parsed via PDFPlumber + OCR</p>
              </div>

              <div className="glass-card p-6 rounded-2xl">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-mono uppercase text-slate-400">Normal Parameters</span>
                  <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
                    <CheckCircle2 className="w-5 h-5" />
                  </div>
                </div>
                <div className="text-3xl font-extrabold text-emerald-400">{normalParams}</div>
                <p className="text-xs text-slate-400 mt-2">Deterministic rule verified</p>
              </div>

              <div className="glass-card p-6 rounded-2xl">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-mono uppercase text-slate-400">Review Needed</span>
                  <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400">
                    <AlertTriangle className="w-5 h-5" />
                  </div>
                </div>
                <div className="text-3xl font-extrabold text-amber-400">{reviewParams}</div>
                <p className="text-xs text-slate-400 mt-2">Requires clinical evaluation</p>
              </div>

              <div className="glass-card p-6 rounded-2xl">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-mono uppercase text-slate-400">Safety Guardrails</span>
                  <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400">
                    <ShieldAlert className="w-5 h-5" />
                  </div>
                </div>
                <div className="text-3xl font-extrabold text-purple-400">100%</div>
                <p className="text-xs text-slate-400 mt-2">Safety Agent online</p>
              </div>
            </div>

            {/* Two Column Section */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Reports List (2 cols) */}
              <div className="lg:col-span-2 glass-card p-6 rounded-3xl">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-lg font-bold text-white">Recent Lab Reports</h2>
                  <button
                    onClick={() => setActiveTab("reports")}
                    className="text-xs text-cyan-400 hover:text-cyan-300 font-mono"
                  >
                    View All →
                  </button>
                </div>
                <div className="space-y-4">
                  {reports.map((r) => (
                    <div
                      key={r.id}
                      className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/5 hover:border-white/10 transition-all"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-400">
                          <FileText className="w-5 h-5" />
                        </div>
                        <div>
                          <h4 className="text-sm font-semibold text-white">{r.filename}</h4>
                          <p className="text-xs text-slate-400 mt-0.5">
                            Uploaded {r.uploadedAt} • {r.parameters.length} parameters extracted
                          </p>
                        </div>
                      </div>
                      <span className="px-3 py-1 rounded-full text-xs font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {r.status.toUpperCase()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* RAG Assistant Card (1 col) */}
              <div className="glass-card p-6 rounded-3xl flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2.5 mb-4">
                    <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400">
                      <Cpu className="w-5 h-5" />
                    </div>
                    <h3 className="font-bold text-white">Ask RAG Assistant</h3>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed mb-6">
                    Quickly query your lab results with zero hallucination. Verified citations backed by RRF vector search.
                  </p>
                  <div className="space-y-2 mb-6">
                    <button
                      onClick={() => {
                        setActiveTab("chat");
                        handleSendMessage("Why is my Hemoglobin low?");
                      }}
                      className="w-full text-left p-3 rounded-xl bg-white/5 hover:bg-white/10 text-xs text-slate-300 transition-all border border-white/5"
                    >
                      "Why is my Hemoglobin low?"
                    </button>
                    <button
                      onClick={() => {
                        setActiveTab("chat");
                        handleSendMessage("Summarize my lipid profile");
                      }}
                      className="w-full text-left p-3 rounded-xl bg-white/5 hover:bg-white/10 text-xs text-slate-300 transition-all border border-white/5"
                    >
                      "Summarize my lipid profile"
                    </button>
                  </div>
                </div>
                <button
                  onClick={() => setActiveTab("chat")}
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-black font-bold text-xs uppercase tracking-wider shadow-lg shadow-cyan-500/20"
                >
                  Open Full RAG Chat
                </button>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: REPORTS */}
        {activeTab === "reports" && (
          <div className="space-y-8 animate-fade-in">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <h1 className="text-2xl font-extrabold text-white">Medical Reports & Parameters</h1>
                <p className="text-slate-400 text-sm mt-1">
                  PDF OCR Ingestion & Deterministic Rule-Engine Parameter Verification
                </p>
              </div>
              <button
                onClick={handleSimulatedUpload}
                disabled={uploading}
                className="px-6 py-3 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 text-black font-bold text-xs uppercase tracking-wider flex items-center gap-2 shadow-lg shadow-cyan-500/20"
              >
                <Upload className="w-4 h-4" />
                <span>{uploading ? "Parsing OCR..." : "Simulate Upload"}</span>
              </button>
            </div>

            <div className="space-y-6">
              {reports.map((rep) => (
                <div key={rep.id} className="glass-card p-6 rounded-3xl">
                  <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/10">
                    <div className="flex items-center gap-3">
                      <FileText className="w-6 h-6 text-cyan-400" />
                      <div>
                        <h3 className="font-bold text-white text-base">{rep.filename}</h3>
                        <p className="text-xs text-slate-400">Uploaded on {rep.uploadedAt}</p>
                      </div>
                    </div>
                    <span className="px-3 py-1 rounded-full text-xs font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      READY
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {rep.parameters.map((p, idx) => (
                      <div
                        key={idx}
                        className="p-4 rounded-2xl bg-white/5 border border-white/5 flex flex-col justify-between"
                      >
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-semibold text-slate-300">{p.name}</span>
                            <span
                              className={`px-2 py-0.5 rounded-full text-[10px] font-mono uppercase font-bold ${
                                p.status === "NORMAL"
                                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                                  : p.status === "HIGH"
                                  ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                                  : "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                              }`}
                            >
                              {p.status}
                            </span>
                          </div>
                          <div className="text-xl font-extrabold text-white">
                            {p.value} <span className="text-xs font-normal text-slate-400">{p.unit}</span>
                          </div>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-3 font-mono">
                          Ref: {p.refMin} - {p.refMax} {p.unit}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 3: CHAT */}
        {activeTab === "chat" && (
          <div className="h-[calc(100vh-140px)] grid grid-cols-1 lg:grid-cols-4 gap-6 animate-fade-in">
            {/* Sidebar */}
            <div className="hidden lg:flex flex-col glass-card p-5 rounded-3xl">
              <button
                onClick={() => setMessages(INITIAL_MESSAGES)}
                className="w-full py-3 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 text-xs font-bold text-slate-200 flex items-center justify-center gap-2 mb-6"
              >
                <Plus className="w-4 h-4" />
                <span>New Chat</span>
              </button>

              <div className="flex-1 space-y-2">
                <div className="p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-xs font-semibold text-cyan-400">
                  Current Session: Metabolic Review
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-white/5 border border-white/5 text-[11px] text-slate-400 space-y-2">
                <div className="flex items-center gap-1.5 font-mono text-cyan-400 font-bold">
                  <ShieldAlert className="w-3.5 h-3.5" />
                  <span>Zero Hallucination Guarantee</span>
                </div>
                <p className="leading-relaxed">
                  Answers are anchored directly to document chunks via pgvector hybrid retrieval.
                </p>
              </div>
            </div>

            {/* Main Chat Panel */}
            <div className="lg:col-span-3 glass-card rounded-3xl flex flex-col overflow-hidden">
              {/* Header */}
              <div className="p-4 px-6 border-b border-white/10 flex items-center justify-between bg-white/5">
                <div>
                  <h3 className="font-extrabold text-white text-sm">Clinexa RAG Health Assistant</h3>
                  <p className="text-[11px] text-slate-400">Powered by Llama 3 & pgvector hybrid retrieval</p>
                </div>
                <span className="px-3 py-1 rounded-full text-[10px] font-mono bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  SECURE RAG
                </span>
              </div>

              {/* High Risk Banner */}
              {highRiskBanner && (
                <div className="bg-rose-500/20 border-b border-rose-500/30 px-6 py-3 flex items-center justify-between text-xs text-rose-300">
                  <div className="flex items-center gap-2">
                    <ShieldAlert className="w-4 h-4 text-rose-400" />
                    <span>{highRiskBanner}</span>
                  </div>
                  <button onClick={() => setHighRiskBanner(null)} className="text-slate-400 hover:text-white">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}

              {/* Messages Area */}
              <div className="flex-1 p-6 overflow-y-auto space-y-6">
                {messages.map((m) => (
                  <div
                    key={m.id}
                    className={`flex flex-col ${m.role === "user" ? "items-end" : "items-start"}`}
                  >
                    <div
                      className={`max-w-2xl p-4 rounded-2xl text-sm leading-relaxed ${
                        m.role === "user"
                          ? "bg-gradient-to-r from-cyan-500 to-blue-600 text-black font-medium"
                          : m.riskLevel === "high"
                          ? "bg-rose-500/10 border border-rose-500/30 text-rose-200"
                          : "bg-white/5 border border-white/10 text-slate-200"
                      }`}
                    >
                      {m.content}
                    </div>

                    {/* Citation Chips */}
                    {m.citations && m.citations.length > 0 && (
                      <div className="mt-2 flex items-center gap-2">
                        {m.citations.map((c, i) => (
                          <div
                            key={i}
                            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-[10px] font-mono text-cyan-400"
                          >
                            <FileCheck className="w-3 h-3" />
                            <span>{c.reportName} (p. {c.page})</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Input Bar */}
              <div className="p-4 border-t border-white/10 bg-white/5 flex items-center gap-3">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
                  placeholder="Ask a question about your reports..."
                  className="flex-1 bg-white/5 border border-white/10 rounded-full px-5 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                />
                <button
                  onClick={() => handleSendMessage()}
                  className="p-3 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 text-black hover:scale-105 transition-all shadow-md shadow-cyan-500/20"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: TRENDS */}
        {activeTab === "trends" && (
          <div className="space-y-8 animate-fade-in">
            <div>
              <h1 className="text-2xl font-extrabold text-white">Health Parameter Trends</h1>
              <p className="text-slate-400 text-sm mt-1">Linear Regression Slope Trajectory Analysis</p>
            </div>

            {/* Parameter Selector Pills */}
            <div className="flex items-center gap-3 overflow-x-auto pb-2">
              {Object.keys(INITIAL_TRENDS).map((paramKey) => (
                <button
                  key={paramKey}
                  onClick={() => setSelectedTrend(paramKey)}
                  className={`px-5 py-2.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all ${
                    selectedTrend === paramKey
                      ? "bg-gradient-to-r from-cyan-500 to-blue-600 text-black shadow-md shadow-cyan-500/20"
                      : "glass-card text-slate-400 hover:text-white"
                  }`}
                >
                  {paramKey}
                </button>
              ))}
            </div>

            {/* Selected Parameter Trend Detail */}
            {INITIAL_TRENDS[selectedTrend] && (
              <div className="glass-card p-8 rounded-3xl space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xl font-bold text-white">
                      {INITIAL_TRENDS[selectedTrend].parameter}
                    </h3>
                    <p className="text-xs text-slate-400 font-mono mt-0.5">
                      Unit: {INITIAL_TRENDS[selectedTrend].unit}
                    </p>
                  </div>
                  <span
                    className={`px-4 py-1.5 rounded-full text-xs font-mono font-bold uppercase ${
                      INITIAL_TRENDS[selectedTrend].direction === "increasing"
                        ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                        : "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                    }`}
                  >
                    Direction: {INITIAL_TRENDS[selectedTrend].direction}
                  </span>
                </div>

                {/* Data Points Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                  {INITIAL_TRENDS[selectedTrend].dataPoints.map((dp, i) => (
                    <div key={i} className="p-4 rounded-2xl bg-white/5 border border-white/5">
                      <span className="text-[10px] font-mono text-slate-500 block mb-1">{dp.date}</span>
                      <div className="text-lg font-extrabold text-white">{dp.value}</div>
                      <span className="text-[10px] font-mono text-emerald-400 mt-2 block">{dp.status}</span>
                    </div>
                  ))}
                </div>

                {/* Trend Agent Summary Note */}
                <div className="p-4 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-xs text-cyan-300 space-y-1">
                  <div className="font-bold font-mono text-cyan-400 flex items-center gap-1.5">
                    <Activity className="w-4 h-4" />
                    <span>Trend Agent Trajectory Summary</span>
                  </div>
                  <p className="leading-relaxed">
                    Values for {INITIAL_TRENDS[selectedTrend].parameter} show a **{INITIAL_TRENDS[selectedTrend].direction}** slope across monitored dates. All points are logged in the `health_trends` historical dataset.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 5: SETTINGS */}
        {activeTab === "settings" && (
          <div className="max-w-4xl space-y-8 animate-fade-in">
            <div>
              <h1 className="text-2xl font-extrabold text-white">User Profile & Preferences</h1>
              <p className="text-slate-400 text-sm mt-1">Manage Account Settings & Observability Metrics</p>
            </div>

            {/* Profile Settings */}
            <div className="glass-card p-6 rounded-3xl space-y-6">
              <h3 className="font-bold text-white text-base">Account Information</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-mono text-slate-400 block mb-2">FULL NAME</label>
                  <input
                    type="text"
                    defaultValue="John Doe"
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50"
                  />
                </div>
                <div>
                  <label className="text-xs font-mono text-slate-400 block mb-2">PREFERRED LANGUAGE</label>
                  <select className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50">
                    <option value="en">English (US)</option>
                    <option value="es">Español</option>
                    <option value="fr">Français</option>
                  </select>
                </div>
              </div>

              <div className="pt-4 border-t border-white/10 flex justify-between items-center">
                <span className="text-xs text-rose-400 font-mono">DANGER ZONE</span>
                <button className="px-4 py-2 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 hover:bg-rose-500/20 text-xs font-bold flex items-center gap-2">
                  <Trash2 className="w-4 h-4" />
                  <span>Delete All Health Data</span>
                </button>
              </div>
            </div>

            {/* Admin Observability */}
            <div className="glass-card p-6 rounded-3xl space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-white text-base">Observability & Token Cost Metrics</h3>
                <span className="px-3 py-1 rounded-full text-[10px] font-mono bg-purple-500/10 text-purple-400 border border-purple-500/20">
                  ADMIN EVAL
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                  <span className="text-xs font-mono text-slate-400 block mb-1">Retrieval Recall@K</span>
                  <div className="text-2xl font-extrabold text-cyan-400">96.8%</div>
                  <span className="text-[10px] text-slate-500 mt-1 block">RRF Rerank Performance</span>
                </div>
                <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                  <span className="text-xs font-mono text-slate-400 block mb-1">Answer Faithfulness</span>
                  <div className="text-2xl font-extrabold text-emerald-400">99.2%</div>
                  <span className="text-[10px] text-slate-500 mt-1 block">Zero Hallucination Score</span>
                </div>
                <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                  <span className="text-xs font-mono text-slate-400 block mb-1">Est. Groq Token Spend</span>
                  <div className="text-2xl font-extrabold text-amber-400">$0.042</div>
                  <span className="text-[10px] text-slate-500 mt-1 block">Current Session Usage</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="py-6 px-8 border-t border-white/10 text-center text-xs font-mono text-slate-500">
        Clinexa AI Healthcare Intelligence Platform © 2026 • Secure RAG & Deterministic Rule Verification
      </footer>
    </div>
  );
};
