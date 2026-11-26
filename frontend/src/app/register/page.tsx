"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth/AuthContext";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { ErrorBanner, RegulatoryDisclaimer } from "@/components/shared/States";
import { Sparkles, ArrowRight, ShieldCheck, UserPlus } from "lucide-react";

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
              INITIALIZE WORKSPACE
            </h1>
            <p className="text-xs sm:text-sm font-medium text-slate-400 mt-1">
              Multi-Tenant Isolated Financial Ledger & Risk Analytics
            </p>
          </div>
        </div>

        {/* Card */}
        <div className="bg-[#101726]/90 backdrop-blur-xl border border-[#202E47] rounded-3xl p-6 sm:p-8 shadow-2xl space-y-6 relative before:content-[''] before:absolute before:top-0 before:left-0 before:right-0 before:h-[2px] before:bg-gradient-to-r before:from-cyan-400 before:via-teal-400 before:to-emerald-400">
          <div className="border-b border-[#1C273C] pb-4">
            <h2 className="text-lg sm:text-xl font-bold text-white flex items-center gap-2">
              <UserPlus className="w-4 h-4 text-cyan-400" />
              <span>Create Account Profile</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Configure your dedicated portfolio tenant workspace
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

          <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-5">
            <Input
              label="Email Address"
              type="email"
              placeholder="user@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={submitting}
              autoComplete="email"
              helperText="Cryptographically bound to your financial positions."
            />

            <Input
              label="Password (min 8 characters)"
              type="password"
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={submitting}
              autoComplete="new-password"
            />

            <Input
              label="Confirm Password"
              type="password"
              placeholder="••••••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              disabled={submitting}
              autoComplete="new-password"
            />

            <div className="flex items-center gap-2 p-2.5 bg-[#0D1422] border border-[#1F2C45] rounded-xl text-[11px] text-slate-400">
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>Zero-knowledge hashing & strict tenant boundary isolation.</span>
            </div>

            <Button
              type="submit"
              variant="primary"
              className="w-full py-3 text-sm font-extrabold shadow-lg shadow-cyan-950/40 rounded-xl group"
              isLoading={submitting || isLoading}
            >
              <span>Initialize Workspace</span>
              <ArrowRight className="w-4 h-4 ml-2 transition-transform group-hover:translate-x-1" />
            </Button>
          </form>

          <div className="pt-2 text-center text-xs text-slate-400 border-t border-[#1C273C]">
            Already have an account?{" "}
            <Link
              href="/login"
              className="font-bold text-cyan-400 hover:text-cyan-300 hover:underline inline-flex items-center ml-1"
            >
              Sign In Instead
            </Link>
          </div>
        </div>

        <RegulatoryDisclaimer />
      </div>
    </div>
  );
}
