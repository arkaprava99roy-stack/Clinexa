"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase";
import { Activity, Mail, Lock, User, Eye, EyeOff, AlertCircle, CheckCircle2 } from "lucide-react";

type Mode = "login" | "signup" | "forgot";

export default function LoginPage() {
  const router = useRouter();
  const supabase = createClient();

  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const clearMessages = () => { setError(null); setSuccess(null); };

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    clearMessages();
    setLoading(true);
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    setLoading(false);
    if (error) {
      setError(error.message);
    } else {
      router.push("/dashboard");
      router.refresh();
    }
  }

  async function handleSignUp(e: React.FormEvent) {
    e.preventDefault();
    clearMessages();
    setLoading(true);
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { full_name: fullName } },
    });
    setLoading(false);
    if (error) {
      setError(error.message);
    } else {
      setSuccess("Check your email to confirm your account, then sign in.");
      setMode("login");
    }
  }

  async function handleForgot(e: React.FormEvent) {
    e.preventDefault();
    clearMessages();
    setLoading(true);
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    });
    setLoading(false);
    if (error) {
      setError(error.message);
    } else {
      setSuccess("Password reset link sent! Check your email.");
    }
  }

  const onSubmit = mode === "login" ? handleLogin : mode === "signup" ? handleSignUp : handleForgot;

  return (
    <main className="min-h-screen flex items-center justify-center bg-hero-gradient relative overflow-hidden px-4">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-glow-brand pointer-events-none" />
      <div className="absolute top-[-10rem] right-[-10rem] w-[40rem] h-[40rem] rounded-full bg-brand-600/5 blur-3xl pointer-events-none" />
      <div className="absolute bottom-[-10rem] left-[-10rem] w-[40rem] h-[40rem] rounded-full bg-brand-800/5 blur-3xl pointer-events-none" />

      {/* Grid pattern */}
      <div
        className="absolute inset-0 opacity-[0.02] pointer-events-none"
        style={{
          backgroundImage: "linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />

      <div className="relative w-full max-w-md animate-slide-up">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-brand-600/20 border border-brand-500/30 mb-4 shadow-glow">
            <Activity className="w-8 h-8 text-brand-400" />
          </div>
          <h1 className="text-3xl font-bold text-slate-100 glow-text">Clinexa</h1>
          <p className="text-slate-400 mt-1 text-sm">AI Healthcare Intelligence Platform</p>
        </div>

        {/* Card */}
        <div className="glass-card p-8">
          {/* Tab switcher */}
          <div className="flex gap-1 p-1 bg-surface rounded-xl mb-6">
            <button
              id="tab-login"
              onClick={() => { setMode("login"); clearMessages(); }}
              className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                mode === "login"
                  ? "bg-brand-600 text-white shadow-glow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Sign In
            </button>
            <button
              id="tab-signup"
              onClick={() => { setMode("signup"); clearMessages(); }}
              className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                mode === "signup"
                  ? "bg-brand-600 text-white shadow-glow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Sign Up
            </button>
          </div>

          {/* Mode title */}
          <h2 className="text-xl font-semibold text-slate-100 mb-6">
            {mode === "login" ? "Welcome back" : mode === "signup" ? "Create your account" : "Reset password"}
          </h2>

          {/* Feedback messages */}
          {error && (
            <div className="flex items-start gap-3 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm mb-5 animate-fade-in">
              <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
          {success && (
            <div className="flex items-start gap-3 px-4 py-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm mb-5 animate-fade-in">
              <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>{success}</span>
            </div>
          )}

          <form onSubmit={onSubmit} className="space-y-5">
            {/* Full name (signup only) */}
            {mode === "signup" && (
              <div className="animate-fade-in">
                <label htmlFor="full-name" className="label">Full Name</label>
                <div className="relative">
                  <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                  <input
                    id="full-name"
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Dr. Jane Smith"
                    className="input-field pl-10"
                  />
                </div>
              </div>
            )}

            {/* Email */}
            <div>
              <label htmlFor="email" className="label">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  autoComplete="email"
                  className="input-field pl-10"
                />
              </div>
            </div>

            {/* Password */}
            {mode !== "forgot" && (
              <div>
                <label htmlFor="password" className="label">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    required
                    minLength={8}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={mode === "signup" ? "Min. 8 characters" : "••••••••"}
                    autoComplete={mode === "login" ? "current-password" : "new-password"}
                    className="input-field pl-10 pr-11"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    id="toggle-password"
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            )}

            {/* Forgot link */}
            {mode === "login" && (
              <div className="text-right -mt-2">
                <button
                  type="button"
                  id="forgot-password-link"
                  onClick={() => { setMode("forgot"); clearMessages(); }}
                  className="text-sm text-brand-400 hover:text-brand-300 transition-colors"
                >
                  Forgot password?
                </button>
              </div>
            )}

            {/* Submit */}
            <button
              id="auth-submit"
              type="submit"
              disabled={loading}
              className="btn-primary w-full mt-2 disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:bg-brand-600"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  {mode === "login" ? "Signing in…" : mode === "signup" ? "Creating account…" : "Sending link…"}
                </span>
              ) : (
                mode === "login" ? "Sign In" : mode === "signup" ? "Create Account" : "Send Reset Link"
              )}
            </button>
          </form>

          {/* Back link for forgot */}
          {mode === "forgot" && (
            <button
              id="back-to-login"
              onClick={() => { setMode("login"); clearMessages(); }}
              className="mt-4 text-sm text-slate-400 hover:text-slate-200 transition-colors w-full text-center"
            >
              ← Back to Sign In
            </button>
          )}
        </div>

        {/* Privacy notice */}
        <p className="text-center text-slate-600 text-xs mt-6">
          Your health data is encrypted and protected under our privacy policy.
          <br />
          Clinexa does not share your data with third parties.
        </p>
      </div>
    </main>
  );
}
