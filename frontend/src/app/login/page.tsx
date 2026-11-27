"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth/AuthContext";
import { ErrorBanner } from "@/components/shared/States";
import {
  ArrowRight,
  ShieldCheck,
  Lock,
  PieChart,
  TrendingUp,
  Activity,
  Layers,
  Sparkles,
  CheckCircle2,
  Cpu,
  BarChart2,
  ExternalLink,
  ChevronRight,
  Database,
} from "lucide-react";

export default function LoginPage() {
  const { login, error, clearError, isLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;

    setSubmitting(true);
    clearError();
    try {
      await login(email, password);
    } catch {
      // Error handled by AuthContext
    } finally {
      setSubmitting(false);
    }
  };

  const fillDemoAccount = () => {
    setEmail("nikhilpillai538@gmail.com");
    setPassword("password123");
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
              V11.0 Engine
            </span>
          </div>

          {/* Navigation Links & Action */}
          <nav className="flex items-center gap-3 sm:gap-6">
            <div className="hidden md:flex items-center gap-6 text-xs sm:text-sm font-semibold text-slate-600">
              <a href="#architecture" className="hover:text-slate-950 transition-colors">
                Architecture
              </a>
              <a href="#algorithms" className="hover:text-slate-950 transition-colors">
                Solvers
              </a>
              <a href="#security" className="hover:text-slate-950 transition-colors">
                Security
              </a>
            </div>

            <Link
              href="/register"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-slate-950 text-white text-xs sm:text-sm font-bold hover:bg-black transition-all shadow-sm hover:shadow-md active:scale-95"
            >
              <span>Get started</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </nav>
        </div>
      </header>

      {/* 2. Main Hero Section (Editorial Typography + Authentication Card) */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-10 sm:py-16 lg:py-20">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-start">
          {/* Left Column: Giant Bold Editorial Title & Micro-Cards */}
          <div className="lg:col-span-7 space-y-8 sm:space-y-10">
            {/* Status pill */}
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200/80 text-emerald-800 text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Deterministic Portfolio Analytics & Decision Support</span>
            </div>

            {/* Giant Stacked Words (Exactly matching Significa editorial style) */}
            <div className="space-y-1">
              <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-[5.25rem] font-black tracking-tight text-slate-950 leading-[0.98]">
                Analyze.
              </h1>
              <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-[5.25rem] font-black tracking-tight text-slate-950 leading-[0.98]">
                Allocate.
              </h1>
              <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-[5.25rem] font-black tracking-tight text-slate-950 leading-[0.98]">
                Optimize.
              </h1>
              <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-[5.25rem] font-black tracking-tight text-slate-950 leading-[0.98]">
                Protect.
              </h1>
              <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-[5.25rem] font-black tracking-tight text-slate-300 leading-[0.98]">
                Scale.
              </h1>
            </div>

            <p className="text-base sm:text-lg text-slate-600 max-w-xl font-normal leading-relaxed">
              Personal financial portfolio management and decision intelligence. Powered by
              Markowitz Modern Portfolio Theory, FinBERT sentiment scoring, and stochastic risk
              modeling.
            </p>

            {/* Micro-Cards Row (Matching the 4 horizontal preview capsules in Significa image) */}
            <div className="pt-2">
              <p className="text-[11px] font-bold text-slate-400 tracking-wider uppercase mb-3">
                Core Mathematical & AI Engines
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {/* Capsule 1: MPT */}
                <div className="p-3 bg-white border border-slate-200/80 rounded-2xl shadow-xs hover:border-slate-400 transition-all group">
                  <div className="w-7 h-7 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center mb-2">
                    <PieChart className="w-3.5 h-3.5" />
                  </div>
                  <h4 className="text-xs font-bold text-slate-900 group-hover:text-rose-600 transition-colors">
                    MPT Solver
                  </h4>
                  <p className="text-[10px] text-slate-500 mt-0.5 truncate">
                    Tangency Sharpe
                  </p>
                </div>

                {/* Capsule 2: FinBERT */}
                <div className="p-3 bg-white border border-slate-200/80 rounded-2xl shadow-xs hover:border-slate-400 transition-all group">
                  <div className="w-7 h-7 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center mb-2">
                    <TrendingUp className="w-3.5 h-3.5" />
                  </div>
                  <h4 className="text-xs font-bold text-slate-900 group-hover:text-teal-600 transition-colors">
                    FinBERT NLP
                  </h4>
                  <p className="text-[10px] text-slate-500 mt-0.5 truncate">
                    Market Polarity
                  </p>
                </div>

                {/* Capsule 3: Monte Carlo */}
                <div className="p-3 bg-white border border-slate-200/80 rounded-2xl shadow-xs hover:border-slate-400 transition-all group">
                  <div className="w-7 h-7 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center mb-2">
                    <Activity className="w-3.5 h-3.5" />
                  </div>
                  <h4 className="text-xs font-bold text-slate-900 group-hover:text-amber-600 transition-colors">
                    Monte Carlo
                  </h4>
                  <p className="text-[10px] text-slate-500 mt-0.5 truncate">
                    1k+ GBM Paths
                  </p>
                </div>

                {/* Capsule 4: Multi-Tenant Ledger */}
                <div className="p-3 bg-white border border-slate-200/80 rounded-2xl shadow-xs hover:border-slate-400 transition-all group">
                  <div className="w-7 h-7 rounded-lg bg-slate-100 text-slate-800 flex items-center justify-center mb-2">
                    <ShieldCheck className="w-3.5 h-3.5" />
                  </div>
                  <h4 className="text-xs font-bold text-slate-900 group-hover:text-slate-950 transition-colors">
                    Argon2id
                  </h4>
                  <p className="text-[10px] text-slate-500 mt-0.5 truncate">
                    Tenant Isolation
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Pristine Significa-Styled Login Card */}
          <div className="lg:col-span-5 w-full">
            <div className="bg-white border border-slate-200/90 rounded-[2rem] p-7 sm:p-10 shadow-[0_20px_50px_rgba(0,0,0,0.06)] relative overflow-hidden">
              {/* Subtle top accent line */}
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-slate-950 via-slate-800 to-slate-400" />

              <div className="mb-6 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-extrabold tracking-widest text-slate-400 uppercase">
                    Secure Authentication
                  </span>
                  <button
                    type="button"
                    onClick={fillDemoAccount}
                    className="text-[11px] font-bold text-teal-700 hover:text-teal-900 bg-teal-50 hover:bg-teal-100/80 px-2.5 py-1 rounded-full transition-colors flex items-center gap-1"
                    title="Click to automatically fill credentials"
                  >
                    <Sparkles className="w-3 h-3 text-teal-600" />
                    <span>Fill Demo</span>
                  </button>
                </div>
                <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-950">
                  Welcome back.
                </h2>
                <p className="text-xs sm:text-sm text-slate-500">
                  Sign in to access your isolated financial ledger & decision models.
                </p>
              </div>

              {error && <ErrorBanner message={error} onDismiss={clearError} />}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label
                    htmlFor="login-email"
                    className="block text-[11px] font-bold text-slate-700 tracking-wider uppercase mb-1.5"
                  >
                    Email Address
                  </label>
                  <input
                    id="login-email"
                    type="email"
                    required
                    disabled={submitting}
                    autoComplete="email"
                    placeholder="e.g. nikhilpillai538@gmail.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-3 text-sm bg-white border border-slate-300 rounded-xl text-slate-900 placeholder:text-slate-400 font-medium focus:outline-none focus:border-slate-950 focus:ring-2 focus:ring-slate-950/10 transition-all"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label
                      htmlFor="login-password"
                      className="block text-[11px] font-bold text-slate-700 tracking-wider uppercase"
                    >
                      Password
                    </label>
                  </div>
                  <input
                    id="login-password"
                    type="password"
                    required
                    disabled={submitting}
                    autoComplete="current-password"
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-3 text-sm bg-white border border-slate-300 rounded-xl text-slate-900 placeholder:text-slate-400 font-medium focus:outline-none focus:border-slate-950 focus:ring-2 focus:ring-slate-950/10 transition-all font-mono"
                  />
                </div>

                <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl text-[11px] text-slate-600 flex items-start gap-2.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span className="leading-snug">
                    Multi-tenant data isolation active. Session tokens are HMAC signed with Argon2id cryptographic hashes.
                  </span>
                </div>

                <button
                  type="submit"
                  disabled={submitting || isLoading}
                  className="w-full py-3.5 px-6 rounded-full bg-slate-950 hover:bg-black text-white text-sm font-bold transition-all shadow-md hover:shadow-xl active:scale-[0.99] flex items-center justify-center gap-2 group disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span>{submitting ? "Signing In..." : "Sign in to Command Center"}</span>
                  <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                </button>
              </form>

              <div className="mt-6 pt-5 text-center text-xs text-slate-500 border-t border-slate-100 flex items-center justify-center gap-1">
                <span>Don&apos;t have an account yet?</span>
                <Link
                  href="/register"
                  className="font-bold text-slate-950 hover:underline inline-flex items-center"
                >
                  Create one now →
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* 3. Bottom Showcase Section (Directly inspired by the 4 colored award/product cards in the Significa screenshot) */}
        <div id="architecture" className="mt-16 sm:mt-24 pt-12 border-t border-slate-200/80">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-8 gap-4">
            <div>
              <span className="text-[11px] font-extrabold tracking-widest text-slate-400 uppercase">
                Platform Architecture
              </span>
              <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-950 tracking-tight mt-1">
                Grounded in Institutional Methods.
              </h3>
            </div>
            <p className="text-xs sm:text-sm text-slate-500 max-w-md">
              Every metric on your dashboard is calculated deterministically by proven financial formulas, not hallucinated by generative models.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Card 1: Red/Coral Theme (like iF Design in Significa) */}
            <div className="bg-[#FFF5F5] border border-rose-200/80 rounded-3xl p-6 flex flex-col justify-between hover:-translate-y-1 transition-transform duration-200 shadow-xs">
              <div>
                <div className="inline-flex items-center px-2.5 py-1 rounded-md text-[10px] font-black uppercase tracking-wider bg-rose-600 text-white mb-4">
                  MPT ENGINE 2026
                </div>
                <h4 className="text-lg font-bold text-slate-950 leading-tight">
                  Modern Portfolio Theory
                </h4>
                <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                  Solves tangency portfolio weights maximizing Sharpe ratio along the Markowitz efficient frontier.
                </p>
              </div>

              {/* Simulated UI Mockup */}
              <div className="mt-6 bg-white rounded-2xl p-4 border border-rose-100 shadow-xs space-y-2 font-mono text-[11px]">
                <div className="flex justify-between items-center text-slate-500 pb-1 border-b border-slate-100">
                  <span className="font-sans">Sharpe Tangency</span>
                  <strong className="text-rose-600 font-bold">1.84x</strong>
                </div>
                <div className="flex justify-between items-center text-slate-700">
                  <span className="font-sans">Expected Return</span>
                  <span className="font-bold text-slate-900">14.8% p.a.</span>
                </div>
                <div className="flex justify-between items-center text-slate-700">
                  <span className="font-sans">Annual Volatility</span>
                  <span className="font-bold text-slate-900">9.2%</span>
                </div>
              </div>
            </div>

            {/* Card 2: Emerald/Teal Theme (like reddot winner in Significa) */}
            <div className="bg-[#F0FDF4] border border-emerald-200/80 rounded-3xl p-6 flex flex-col justify-between hover:-translate-y-1 transition-transform duration-200 shadow-xs">
              <div>
                <div className="inline-flex items-center px-2.5 py-1 rounded-md text-[10px] font-black uppercase tracking-wider bg-emerald-700 text-white mb-4">
                  FINBERT NLP
                </div>
                <h4 className="text-lg font-bold text-slate-950 leading-tight">
                  Market Sentiment Stream
                </h4>
                <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                  Analyzes live financial news headlines with domain-adapted transformers for objective sentiment polarity.
                </p>
              </div>

              {/* Simulated UI Mockup */}
              <div className="mt-6 bg-white rounded-2xl p-4 border border-emerald-100 shadow-xs space-y-2 text-[11px]">
                <div className="flex justify-between items-center pb-1 border-b border-slate-100">
                  <span className="text-slate-500">Net Market Sentiment</span>
                  <span className="font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded text-[10px] uppercase">
                    Bullish (+0.42)
                  </span>
                </div>
                <div className="space-y-1 pt-1">
                  <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                    <span>Positive 74%</span>
                    <span>Neutral 18%</span>
                    <span>Negative 8%</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden flex">
                    <div className="bg-emerald-500 w-[74%]" />
                    <div className="bg-slate-300 w-[18%]" />
                    <div className="bg-rose-500 w-[8%]" />
                  </div>
                </div>
              </div>
            </div>

            {/* Card 3: Terracotta/Orange Theme (like German Design in Significa) */}
            <div className="bg-[#FFFBEB] border border-amber-200/80 rounded-3xl p-6 flex flex-col justify-between hover:-translate-y-1 transition-transform duration-200 shadow-xs">
              <div>
                <div className="inline-flex items-center px-2.5 py-1 rounded-md text-[10px] font-black uppercase tracking-wider bg-amber-600 text-white mb-4">
                  STOCHASTIC LAB
                </div>
                <h4 className="text-lg font-bold text-slate-950 leading-tight">
                  Monte Carlo Projections
                </h4>
                <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                  Generates thousands of Geometric Brownian Motion paths to determine wealth percentiles and goal probabilities.
                </p>
              </div>

              {/* Simulated UI Mockup */}
              <div className="mt-6 bg-white rounded-2xl p-4 border border-amber-100 shadow-xs space-y-2 font-mono text-[11px]">
                <div className="flex justify-between items-center text-slate-500 pb-1 border-b border-slate-100">
                  <span className="font-sans">Simulated Paths</span>
                  <strong className="text-amber-700 font-bold">1,000 Trajectories</strong>
                </div>
                <div className="flex justify-between items-center text-slate-700">
                  <span className="font-sans">P50 Median</span>
                  <span className="font-bold text-slate-900">₹48.2 Lakhs</span>
                </div>
                <div className="flex justify-between items-center text-slate-700">
                  <span className="font-sans">P95 Optimistic</span>
                  <span className="font-bold text-emerald-600">₹76.5 Lakhs</span>
                </div>
              </div>
            </div>

            {/* Card 4: Slate/Warm Gray Theme (like European Design in Significa) */}
            <div className="bg-[#F8FAFC] border border-slate-200/90 rounded-3xl p-6 flex flex-col justify-between hover:-translate-y-1 transition-transform duration-200 shadow-xs">
              <div>
                <div className="inline-flex items-center px-2.5 py-1 rounded-md text-[10px] font-black uppercase tracking-wider bg-slate-950 text-white mb-4">
                  ZERO KNOWLEDGE
                </div>
                <h4 className="text-lg font-bold text-slate-950 leading-tight">
                  Multi-Tenant Ledger
                </h4>
                <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                  Cryptographically isolated workspaces. Each user session and ledger entry is guarded by rigorous tenant boundaries.
                </p>
              </div>

              {/* Simulated UI Mockup */}
              <div className="mt-6 bg-white rounded-2xl p-4 border border-slate-200 shadow-xs space-y-2 text-[11px]">
                <div className="flex justify-between items-center pb-1 border-b border-slate-100">
                  <span className="text-slate-500">Tenant Status</span>
                  <span className="font-bold text-slate-900 flex items-center gap-1 font-mono text-[10px]">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                    Isolated
                  </span>
                </div>
                <div className="flex justify-between items-center text-slate-700 font-mono">
                  <span>Hash Algorithm</span>
                  <span className="font-bold text-slate-900">Argon2id</span>
                </div>
                <div className="flex justify-between items-center text-slate-700 font-mono">
                  <span>HMAC Signature</span>
                  <span className="font-bold text-slate-900">SHA-256</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* 4. Minimalist Studio Footer */}
      <footer className="w-full border-t border-slate-200/80 bg-white py-8 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-slate-950" />
            <span className="font-semibold text-slate-900">Significa.fin</span>
            <span>— AI-Powered Financial Portfolio Management and Decision Support System.</span>
          </div>
          <div className="text-[11px] text-slate-400">
            For educational decision support only. All calculations verified deterministically.
          </div>
        </div>
      </footer>
    </div>
  );
}
