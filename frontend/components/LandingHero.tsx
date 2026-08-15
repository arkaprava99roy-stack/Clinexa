import React from "react";
import {
  FileText,
  MessageSquare,
  Activity,
  Shield,
  Cpu,
  ArrowLeft,
  ChevronDown,
} from "lucide-react";
import { HeroHelixCanvas } from "./HeroHelixCanvas";

interface LandingHeroProps {
  onLaunchDashboard: () => void;
}

export const LandingHero: React.FC<LandingHeroProps> = ({
  onLaunchDashboard,
}) => {
  return (
    <div className="relative min-h-screen w-full bg-gradient-to-b from-[#05070f] via-[#0b0f1f] to-[#05070f] text-slate-100 overflow-hidden flex flex-col justify-between select-none">
      {/* 3D Helix Background Canvas */}
      <HeroHelixCanvas />

      {/* Ambient background glow blobs */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-cyan-500/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-1/3 left-1/3 w-[500px] h-[500px] bg-rose-500/10 rounded-full blur-[140px] pointer-events-none" />

      {/* Top Bar */}
      <header className="relative z-20 px-6 py-5 flex items-center justify-between max-w-7xl mx-auto w-full">
        {/* Left branding */}
        <div className="flex items-center gap-3">
          <button
            onClick={onLaunchDashboard}
            className="w-10 h-10 rounded-full glass-card flex items-center justify-center text-slate-300 hover:text-white hover:border-cyan-500/40 transition-all group"
            title="Toggle Dashboard"
          >
            <ArrowLeft className="w-5 h-5 group-hover:-translate-x-0.5 transition-transform" />
          </button>
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600 p-0.5 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <div className="w-full h-full bg-[#0b0f1f] rounded-[10px] flex items-center justify-center">
                <Activity className="w-5 h-5 text-cyan-400" />
              </div>
            </div>
            <span className="text-xl font-extrabold tracking-tighter text-white">
              Clinexa
            </span>
          </div>
        </div>

        {/* Center/Right Actions */}
        <div className="flex items-center gap-6">
          <div className="hidden md:flex items-center gap-4 text-xs font-mono text-slate-400 tracking-wider">
            <span>HEALTH INTELLIGENCE PLATFORM</span>
            <span className="text-slate-600">•</span>
            <span>© 2026</span>
          </div>
          <button
            onClick={onLaunchDashboard}
            className="px-5 py-2.5 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 text-black font-semibold text-sm shadow-lg shadow-cyan-500/25 hover:shadow-cyan-500/40 hover:scale-[1.02] active:scale-[0.98] transition-all"
          >
            Launch Platform
          </button>
        </div>
      </header>

      {/* Hero Center Content */}
      <main className="relative z-10 max-w-5xl mx-auto px-6 py-12 text-center flex-1 flex flex-col justify-center items-center">
        {/* Telemetry Corner Chips Container */}
        <div className="w-full relative min-h-[320px] md:min-h-[380px] flex flex-col items-center justify-center">
          {/* Top-Left Chip */}
          <button
            onClick={onLaunchDashboard}
            className="absolute top-0 left-0 md:left-4 glass-card px-4 py-2 rounded-full flex items-center gap-2 text-xs font-mono text-slate-300 hover:border-cyan-500/40 hover:text-cyan-400 transition-all pointer-events-auto shadow-lg"
          >
            <FileText className="w-3.5 h-3.5 text-cyan-400" />
            <span>AI Report Analysis</span>
          </button>

          {/* Top-Right Chip */}
          <button
            onClick={onLaunchDashboard}
            className="absolute top-0 right-0 md:right-4 glass-card px-4 py-2 rounded-full flex items-center gap-2 text-xs font-mono text-slate-300 hover:border-cyan-500/40 hover:text-cyan-400 transition-all pointer-events-auto shadow-lg"
          >
            <MessageSquare className="w-3.5 h-3.5 text-cyan-400" />
            <span>RAG Health Chat</span>
          </button>

          {/* Bottom-Left Chip */}
          <button
            onClick={onLaunchDashboard}
            className="absolute bottom-0 left-0 md:left-4 glass-card px-4 py-2 rounded-full flex items-center gap-2 text-xs font-mono text-slate-300 hover:border-cyan-500/40 hover:text-cyan-400 transition-all pointer-events-auto shadow-lg"
          >
            <Activity className="w-3.5 h-3.5 text-rose-400" />
            <span>Trend Intelligence</span>
          </button>

          {/* Bottom-Right Chip */}
          <button
            onClick={onLaunchDashboard}
            className="absolute bottom-0 right-0 md:right-4 glass-card px-4 py-2 rounded-full flex items-center gap-2 text-xs font-mono text-slate-300 hover:border-cyan-500/40 hover:text-cyan-400 transition-all pointer-events-auto shadow-lg"
          >
            <Shield className="w-3.5 h-3.5 text-emerald-400" />
            <span>Multi-Agent Safety</span>
          </button>

          {/* Headline */}
          <h1 className="text-5xl sm:text-7xl lg:text-8xl font-extrabold tracking-tighter leading-[1.05] max-w-4xl">
            <span className="text-white/95">Understanding </span>
            <span className="bg-gradient-to-r from-cyan-400 via-sky-300 to-indigo-400 bg-clip-text text-transparent">
              Your Health
            </span>
            <br />
            <span className="text-white/95">Instantly</span>
          </h1>

          {/* Subhead */}
          <p className="mt-6 max-w-2xl text-slate-300 text-base md:text-lg font-normal leading-relaxed">
            Multi-agent AI platform that transforms complex lab reports and
            medical documents into crystal-clear insights with deterministic
            rule checks and verified citations.
          </p>

          {/* CTA Buttons */}
          <div className="mt-8 flex flex-wrap items-center justify-center gap-4 pointer-events-auto">
            <button
              onClick={onLaunchDashboard}
              className="px-8 py-4 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 text-black font-bold text-base flex items-center gap-3 shadow-xl shadow-cyan-500/30 hover:shadow-cyan-500/50 hover:scale-[1.02] active:scale-[0.98] transition-all"
            >
              <Cpu className="w-5 h-5 text-black" />
              <span>Launch Clinexa Dashboard</span>
            </button>
            <a
              href="#features"
              className="px-8 py-4 rounded-full glass-card font-semibold text-base text-slate-200 hover:text-white hover:border-white/20 transition-all"
            >
              Explore Capabilities
            </a>
          </div>

          {/* Bottom Center Pill */}
          <div className="hidden md:flex items-center gap-2 mt-8 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs font-mono text-slate-400 pointer-events-none">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Grounded, Cited Answers</span>
          </div>
        </div>
      </main>

      {/* Footer Line */}
      <footer className="relative z-20 px-6 py-6 text-center text-xs font-mono text-slate-500 tracking-wider border-t border-white/5">
        <span>Scroll to explore core intelligence modules</span>
      </footer>
    </div>
  );
};
