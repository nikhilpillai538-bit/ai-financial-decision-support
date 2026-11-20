"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth/AuthContext";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { ErrorBanner, RegulatoryDisclaimer } from "@/components/shared/States";
import { Sparkles, ArrowRight, ShieldCheck } from "lucide-react";

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
    <div className="min-h-screen flex flex-col justify-center items-center p-6 bg-gradient-to-b from-indigo-50/70 via-slate-50 to-slate-100 selection:bg-indigo-500 selection:text-white">
      <div className="w-full max-w-lg space-y-8">
        {/* Logo and Brand */}
        <div className="text-center space-y-3">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-600 text-white mx-auto flex items-center justify-center shadow-xl shadow-indigo-500/25 ring-4 ring-white">
            <Sparkles className="w-7 h-7" />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">
              Create Your Account
            </h1>
            <p className="text-sm font-medium text-slate-500 mt-1">
              Isolated, Multi-Tenant Personal Financial Intelligence
            </p>
          </div>
        </div>

        {/* Card */}
        <div className="bg-white/95 backdrop-blur-xl border border-slate-200/90 rounded-3xl p-8 sm:p-10 shadow-elevated space-y-6">
          <div className="border-b border-slate-100 pb-5">
            <h2 className="text-xl font-bold text-slate-900">Get Started Free</h2>
            <p className="text-sm text-slate-500 mt-1">
              Set up your secure, user-isolated financial portfolio workspace
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

          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              label="Email Address"
              type="email"
              placeholder="user@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={submitting}
              autoComplete="email"
              helperText="Your email will be cryptographically bound to your financial profile."
            />

            <Input
              label="Password (min 8 chars)"
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

            <div className="flex items-center gap-2 p-3 bg-indigo-50/70 border border-indigo-100 rounded-xl text-xs text-indigo-900">
              <ShieldCheck className="w-4 h-4 text-indigo-600 shrink-0" />
              <span>Passwords are protected with Argon2id cryptographic hashing.</span>
            </div>

            <Button
              type="submit"
              variant="primary"
              className="w-full py-3.5 text-base font-bold shadow-lg shadow-indigo-600/25 rounded-xl group"
              isLoading={submitting || isLoading}
            >
              <span>Create Account</span>
              <ArrowRight className="w-4 h-4 ml-2 transition-transform group-hover:translate-x-1" />
            </Button>
          </form>

          <div className="pt-2 text-center text-sm text-slate-600 border-t border-slate-100">
            Already have an account?{" "}
            <Link
              href="/login"
              className="font-bold text-indigo-600 hover:text-indigo-700 hover:underline inline-flex items-center"
            >
              Sign In Instead
            </Link>
          </div>
        </div>

        {/* Regulatory disclaimer */}
        <RegulatoryDisclaimer />
      </div>
    </div>
  );
}
