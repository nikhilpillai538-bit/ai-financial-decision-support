"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth/AuthContext";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { ErrorBanner, RegulatoryDisclaimer } from "@/components/shared/States";
import { Sparkles, Shield, ArrowRight } from "lucide-react";

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
    <div className="min-h-screen flex flex-col justify-center items-center p-6 bg-gradient-to-b from-indigo-50/70 via-slate-50 to-slate-100 selection:bg-indigo-500 selection:text-white">
      <div className="w-full max-w-lg space-y-8">
        {/* Logo and Brand */}
        <div className="text-center space-y-3">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-600 text-white mx-auto flex items-center justify-center shadow-xl shadow-indigo-500/25 ring-4 ring-white">
            <Sparkles className="w-7 h-7" />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">
              Sign In to Financial AI
            </h1>
            <p className="text-sm font-medium text-slate-500 mt-1">
              AI-Powered Portfolio Management & Decision Support System
            </p>
          </div>
        </div>

        {/* Card */}
        <div className="bg-white/95 backdrop-blur-xl border border-slate-200/90 rounded-3xl p-8 sm:p-10 shadow-elevated space-y-6">
          <div className="border-b border-slate-100 pb-5">
            <h2 className="text-xl font-bold text-slate-900">Welcome Back</h2>
            <p className="text-sm text-slate-500 mt-1">
              Enter your account credentials to access your financial dashboard
            </p>
          </div>

          {error && <ErrorBanner message={error} onDismiss={clearError} />}

          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              label="Email Address"
              type="email"
              placeholder="nikhilpillai538@gmail.com"
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

            <Button
              type="submit"
              variant="primary"
              className="w-full py-3.5 text-base font-bold shadow-lg shadow-indigo-600/25 rounded-xl group"
              isLoading={submitting || isLoading}
            >
              <span>Sign In to Dashboard</span>
              <ArrowRight className="w-4 h-4 ml-2 transition-transform group-hover:translate-x-1" />
            </Button>
          </form>

          <div className="pt-2 text-center text-sm text-slate-600 border-t border-slate-100">
            Don&apos;t have an account yet?{" "}
            <Link
              href="/register"
              className="font-bold text-indigo-600 hover:text-indigo-700 hover:underline inline-flex items-center"
            >
              Create Account
            </Link>
          </div>
        </div>

        {/* Regulatory disclaimer */}
        <RegulatoryDisclaimer />
      </div>
    </div>
  );
}
