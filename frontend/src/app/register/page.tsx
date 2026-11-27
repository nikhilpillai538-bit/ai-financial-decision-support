"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth/AuthContext";
import { ErrorBanner } from "@/components/shared/States";
import {
  ArrowRight,
  ShieldCheck,
  Lock,
  UserPlus,
  PieChart,
  TrendingUp,
  Activity,
  Layers,
  Sparkles,
  CheckCircle2,
  Cpu,
  KeyRound,
  ShieldAlert,
} from "lucide-react";

export default function RegisterPage() {
  const { register, error, clearError, isLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    if (!email || !password) return;

    if (password.length < 8) {
      setValidationError("Password must be at least 8 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      setValidationError("Passwords do not match.");
      return;
    }

    setSubmitting(true);
    clearError();
    try {
      await register(email, password);
    } catch {
      // Error handled by AuthContext
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FBFBFA] text-slate-900 font-sans selection:bg-slate-900 selection:text-white flex flex-col justify-between">
      {/* 1. Significa-style Minimal Top Navigation */}
      <header className="w-full border-b border-slate-200/70 bg-white/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-18 sm:h-20 flex items-center justify-between">
          {/* Brand Wordmark */}
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2.5 group">
              <span className="w-3.5 h-3.5 rounded-full bg-slate-950 group-hover:scale-125 transition-transform duration-200" />
              <span className="text-xl sm:text-2xl font-black tracking-tight text-slate-950 font-sans">
                Significa<span className="text-slate-400 font-normal">.fin</span>
              </span>
            </Link>
            <span className="hidden md:inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-widest bg-slate-100 text-slate-600 border border-slate-200">
              Workspace Setup
            </span>
          </div>

          {/* Navigation Links & Action */}
          <nav className="flex items-center gap-3 sm:gap-6">
            <div className="hidden md:flex items-center gap-6 text-xs sm:text-sm font-semibold text-slate-600">
              <Link href="/login" className="hover:text-slate-950 transition-colors">
                Sign In
              </Link>
              <a href="#security" className="hover:text-slate-950 transition-colors">
                Security Guarantee
              </a>
            </div>

            <Link
              href="/login"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-slate-950 text-white text-xs sm:text-sm font-bold hover:bg-black transition-all shadow-sm hover:shadow-md active:scale-95"
            >
              <span>Existing Member</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </nav>
        </div>
      </header>

      {/* 2. Main Hero Section */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-10 sm:py-16 lg:py-20">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-start">
          {/* Left Column: Editorial Typography */}
          <div className="lg:col-span-7 space-y-8 sm:space-y-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-50 border border-cyan-200/80 text-cyan-800 text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse" />
              <span>Dedicated Multi-Tenant Workspace Provisioning</span>
            </div>

            {/* Giant Stacked Words */}
            <div className="space-y-1">
              <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-[5.25rem] font-black tracking-tight text-slate-950 leading-[0.98]">
                Initialize.
              </h1>
              <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-[5.25rem] font-black tracking-tight text-slate-950 leading-[0.98]">
                Configure.
              </h1>
              <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-[5.25rem] font-black tracking-tight text-slate-950 leading-[0.98]">
                Protect.
              </h1>
              <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-[5.25rem] font-black tracking-tight text-slate-300 leading-[0.98]">
                Deploy.
              </h1>
            </div>

            <p className="text-base sm:text-lg text-slate-600 max-w-xl font-normal leading-relaxed">
              Create your cryptographically isolated personal portfolio ledger. Access deterministic
              solvers, live market sentiment feeds, and stress testing simulations under complete privacy.
            </p>

            {/* Micro-Features */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-slate-200/80">
              <div className="space-y-1">
                <div className="flex items-center gap-2 font-bold text-slate-950 text-sm">
                  <KeyRound className="w-4 h-4 text-slate-700" />
                  <span>Argon2id Hash</span>
                </div>
                <p className="text-xs text-slate-500 leading-snug">
                  State-of-the-art memory-hard key derivation protecting your credentials.
                </p>
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-2 font-bold text-slate-950 text-sm">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  <span>Tenant Boundary</span>
                </div>
                <p className="text-xs text-slate-500 leading-snug">
                  Strict user-level row isolation across portfolios, transactions, and AI threads.
                </p>
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-2 font-bold text-slate-950 text-sm">
                  <Activity className="w-4 h-4 text-cyan-600" />
                  <span>Zero Hallucination</span>
                </div>
                <p className="text-xs text-slate-500 leading-snug">
                  All metrics computed via verified deterministic math and real market series.
                </p>
              </div>
            </div>
          </div>

          {/* Right Column: Register Card */}
          <div className="lg:col-span-5 w-full">
            <div className="bg-white border border-slate-200/90 rounded-[2rem] p-7 sm:p-10 shadow-[0_20px_50px_rgba(0,0,0,0.06)] relative overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-slate-950 via-slate-800 to-slate-400" />

              <div className="mb-6 space-y-1.5">
                <span className="text-[10px] font-extrabold tracking-widest text-slate-400 uppercase">
                  New Ledger Provisioning
                </span>
                <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-950">
                  Create Workspace
                </h2>
                <p className="text-xs sm:text-sm text-slate-500">
                  Set up your email and password to initialize your ledger.
                </p>
              </div>

              {(error || validationError) && (
                <ErrorBanner
                  message={validationError || error || ""}
                  onDismiss={() => {
                    setValidationError(null);
                    clearError();
                  }}
                />
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label
                    htmlFor="register-email"
                    className="block text-[11px] font-bold text-slate-700 tracking-wider uppercase mb-1.5"
                  >
                    Email Address
                  </label>
                  <input
                    id="register-email"
                    type="email"
                    required
                    disabled={submitting}
                    autoComplete="email"
                    placeholder="user@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-3 text-sm bg-white border border-slate-300 rounded-xl text-slate-900 placeholder:text-slate-400 font-medium focus:outline-none focus:border-slate-950 focus:ring-2 focus:ring-slate-950/10 transition-all"
                  />
                </div>

                <div>
                  <label
                    htmlFor="register-password"
                    className="block text-[11px] font-bold text-slate-700 tracking-wider uppercase mb-1.5"
                  >
                    Password (Min 8 Characters)
                  </label>
                  <input
                    id="register-password"
                    type="password"
                    required
                    disabled={submitting}
                    autoComplete="new-password"
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-3 text-sm bg-white border border-slate-300 rounded-xl text-slate-900 placeholder:text-slate-400 font-medium focus:outline-none focus:border-slate-950 focus:ring-2 focus:ring-slate-950/10 transition-all font-mono"
                  />
                </div>

                <div>
                  <label
                    htmlFor="register-confirm-password"
                    className="block text-[11px] font-bold text-slate-700 tracking-wider uppercase mb-1.5"
                  >
                    Confirm Password
                  </label>
                  <input
                    id="register-confirm-password"
                    type="password"
                    required
                    disabled={submitting}
                    autoComplete="new-password"
                    placeholder="••••••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full px-4 py-3 text-sm bg-white border border-slate-300 rounded-xl text-slate-900 placeholder:text-slate-400 font-medium focus:outline-none focus:border-slate-950 focus:ring-2 focus:ring-slate-950/10 transition-all font-mono"
                  />
                </div>

                <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl text-[11px] text-slate-600 flex items-start gap-2.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span className="leading-snug">
                    Zero-knowledge cryptographic boundary. Your transactions and portfolio details are never accessible across tenants.
                  </span>
                </div>

                <button
                  type="submit"
                  disabled={submitting || isLoading}
                  className="w-full py-3.5 px-6 rounded-full bg-slate-950 hover:bg-black text-white text-sm font-bold transition-all shadow-md hover:shadow-xl active:scale-[0.99] flex items-center justify-center gap-2 group disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span>{submitting ? "Initializing..." : "Initialize Workspace"}</span>
                  <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                </button>
              </form>

              <div className="mt-6 pt-5 text-center text-xs text-slate-500 border-t border-slate-100 flex items-center justify-center gap-1">
                <span>Already have an account?</span>
                <Link
                  href="/login"
                  className="font-bold text-slate-950 hover:underline inline-flex items-center"
                >
                  Sign in here →
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* 3. Minimalist Studio Footer */}
      <footer className="w-full border-t border-slate-200/80 bg-white py-8 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-slate-950" />
            <span className="font-semibold text-slate-900">Significa.fin</span>
            <span>— Personal Financial Decision Support & Modern Portfolio Analytics.</span>
          </div>
          <div className="text-[11px] text-slate-400">
            For educational decision support only. All calculations verified deterministically.
          </div>
        </div>
      </footer>
    </div>
  );
}
