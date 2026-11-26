"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth/AuthContext";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { ErrorBanner, RegulatoryDisclaimer } from "@/components/shared/States";
import { Sparkles, ArrowRight, ShieldCheck, Lock } from "lucide-react";

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

  return (
    <div className="min-h-screen flex flex-col justify-center items-center p-4 sm:p-6 bg-[#080C14] text-slate-100 relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[500px] h-[300px] bg-cyan-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-10 right-1/4 w-[350px] h-[250px] bg-teal-500/10 rounded-full blur-[100px] pointer-events-none" />

      <div className="w-full max-w-md space-y-6 sm:space-y-8 relative z-10 animate-fade-in">
        {/* Logo and Brand */}
        <div className="text-center space-y-2.5">
          <div className="w-13 h-13 sm:w-14 sm:h-14 rounded-2xl bg-gradient-to-tr from-cyan-400 via-teal-400 to-emerald-400 text-slate-950 mx-auto flex items-center justify-center shadow-lg shadow-cyan-500/25 ring-2 ring-white/20">
            <Sparkles className="w-7 h-7" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
              FINANCIAL<span className="text-cyan-400">AI</span> COMMAND
            </h1>
            <p className="text-xs sm:text-sm font-medium text-slate-400 mt-1">
              Deterministic Portfolio Analytics & Decision Support
            </p>
          </div>
        </div>

        {/* Card */}
        <div className="bg-[#101726]/90 backdrop-blur-xl border border-[#202E47] rounded-3xl p-6 sm:p-8 shadow-2xl space-y-6 relative before:content-[''] before:absolute before:top-0 before:left-0 before:right-0 before:h-[2px] before:bg-gradient-to-r before:from-cyan-400 before:via-teal-400 before:to-emerald-400">
          <div className="border-b border-[#1C273C] pb-4">
            <h2 className="text-lg sm:text-xl font-bold text-white flex items-center gap-2">
              <Lock className="w-4 h-4 text-cyan-400" />
              <span>Authenticate Session</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Enter your credentials to access your isolated financial ledger
            </p>
          </div>

          {error && <ErrorBanner message={error} onDismiss={clearError} />}

          <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-5">
            <Input
              label="Email Address"
              type="email"
              placeholder="e.g. nikhilpillai538@gmail.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={submitting}
              autoComplete="email"
            />

            <Input
              label="Password"
              type="password"
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={submitting}
              autoComplete="current-password"
            />

            <div className="flex items-center gap-2 p-2.5 bg-[#0D1422] border border-[#1F2C45] rounded-xl text-[11px] text-slate-400">
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>Multi-tenant data isolation active. Session tokens HMAC verified.</span>
            </div>

            <Button
              type="submit"
              variant="primary"
              className="w-full py-3 text-sm font-extrabold shadow-lg shadow-cyan-950/40 rounded-xl group"
              isLoading={submitting || isLoading}
            >
              <span>Access Command Center</span>
              <ArrowRight className="w-4 h-4 ml-2 transition-transform group-hover:translate-x-1" />
            </Button>
          </form>

          <div className="pt-2 text-center text-xs text-slate-400 border-t border-[#1C273C]">
            Don&apos;t have an account yet?{" "}
            <Link
              href="/register"
              className="font-bold text-cyan-400 hover:text-cyan-300 hover:underline inline-flex items-center ml-1"
            >
              Create Account
            </Link>
          </div>
        </div>

        <RegulatoryDisclaimer />
      </div>
    </div>
  );
}
