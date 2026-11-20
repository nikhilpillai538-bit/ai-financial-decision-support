"use client";

import React, { useState } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import {
  ErrorBanner,
  RegulatoryDisclaimer,
} from "@/components/shared/States";
import { useAuth } from "@/lib/auth/AuthContext";
import { analysisApi } from "@/lib/api/analysis";
import { formatDate } from "@/lib/formatters";
import {
  User,
  Shield,
  Activity,
  LogOut,
  Server,
  Save,
  CheckCircle2,
  Lock,
} from "lucide-react";

export default function SettingsPage() {
  const { user, logout } = useAuth();

  // Profile Form State
  const [monthlyExpenses, setMonthlyExpenses] = useState("");
  const [liquidSavings, setLiquidSavings] = useState("");
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [profileSuccess, setProfileSuccess] = useState<string | null>(null);

  // Diagnostics State
  const [isPinging, setIsPinging] = useState(false);
  const [pingResult, setPingResult] = useState<{
    status: string;
    latencyMs: number;
    url: string;
  } | null>(null);

  const [error, setError] = useState<string | null>(null);

  async function handleSaveProfile(e: React.FormEvent) {
    e.preventDefault();
    setIsSavingProfile(true);
    setError(null);
    setProfileSuccess(null);
    try {
      await analysisApi.updateFinancialProfile({
        monthly_essential_expenses: monthlyExpenses || undefined,
        available_liquid_savings: liquidSavings || undefined,
      });
      setProfileSuccess("Financial baseline profile updated successfully.");
      setTimeout(() => setProfileSuccess(null), 3000);
    } catch (err: any) {
      setError(err?.message || "Failed to update financial profile.");
    } finally {
      setIsSavingProfile(false);
    }
  }

  async function handleDiagnosticPing() {
    setIsPinging(true);
    const start = performance.now();
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
    try {
      const res = await fetch(`${apiUrl}/health`);
      const latency = Math.round(performance.now() - start);
      if (res.ok) {
        setPingResult({
          status: `200 OK (${res.statusText || "Healthy"})`,
          latencyMs: latency,
          url: apiUrl,
        });
      } else {
        setPingResult({
          status: `${res.status} ${res.statusText}`,
          latencyMs: latency,
          url: apiUrl,
        });
      }
    } catch (err: any) {
      setPingResult({
        status: `Connection Failed: ${err?.message || "Unreachable"}`,
        latencyMs: Math.round(performance.now() - start),
        url: apiUrl,
      });
    } finally {
      setIsPinging(false);
    }
  }

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl lg:text-4xl font-extrabold tracking-tight text-slate-900">
          Account Settings & System Diagnostics
        </h1>
        <p className="text-base text-slate-500 mt-1.5 font-medium">
          Manage your authenticated identity, financial baseline parameters, and backend connectivity.
        </p>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}
      {profileSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 rounded-lg flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{profileSuccess}</span>
        </div>
      )}

      {/* User Account Details */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <User className="w-4 h-4 text-primary-600" />
            Authenticated Identity
          </CardTitle>
          <CardDescription>
            Account credentials and multi-tenant data boundary.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-xs">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
              <span className="text-slate-400 block mb-0.5">Email Address</span>
              <span className="font-semibold text-slate-800 text-sm">
                {user?.email || "—"}
              </span>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
              <span className="text-slate-400 block mb-0.5">Account Status</span>
              <div className="flex items-center gap-2 mt-0.5">
                <Badge variant={user?.is_active ? "success" : "danger"}>
                  {user?.is_active ? "Active" : "Inactive"}
                </Badge>
                <span className="text-slate-500 text-[11px]">
                  Created {user?.created_at ? formatDate(user.created_at) : "—"}
                </span>
              </div>
            </div>
          </div>

          <div className="p-3 bg-blue-50/70 rounded-lg border border-blue-100 flex items-start gap-2.5">
            <Shield className="w-4 h-4 text-blue-600 mt-0.5 shrink-0" />
            <div className="text-blue-900">
              <span className="font-semibold block mb-0.5">Strict User Data Isolation</span>
              All financial transactions, portfolios, holdings, and AI chat sessions are isolated by your unique cryptographic user ID (<code className="text-blue-800 text-[11px]">{user?.id || "anonymous"}</code>).
            </div>
          </div>
        </CardContent>
        <CardFooter className="bg-slate-50/50 border-t border-slate-100 justify-between">
          <span className="text-[11px] text-slate-400">
            Session stored in secure browser memory / sessionStorage
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={logout}
            className="text-rose-600 hover:text-rose-700 hover:bg-rose-50"
          >
            <LogOut className="w-4 h-4 mr-1.5" />
            Sign Out
          </Button>
        </CardFooter>
      </Card>

      {/* Financial Profile Baseline */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-600" />
            Financial Baseline Profile
          </CardTitle>
          <CardDescription>
            Override or set defaults used for emergency fund targets and cash-flow projections.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSaveProfile} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Baseline Monthly Essential Expenses (₹)"
                type="number"
                placeholder="e.g. 45000"
                value={monthlyExpenses}
                onChange={(e) => setMonthlyExpenses(e.target.value)}
                helperText="Used if fewer than 3 months of transaction history exist."
              />
              <Input
                label="Available Liquid Savings Balance (₹)"
                type="number"
                placeholder="e.g. 250000"
                value={liquidSavings}
                onChange={(e) => setLiquidSavings(e.target.value)}
                helperText="Current liquid savings earmarked for emergency reserve."
              />
            </div>
            <div className="flex justify-end">
              <Button type="submit" size="sm" isLoading={isSavingProfile}>
                <Save className="w-4 h-4 mr-1.5" />
                Update Baseline
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Backend Diagnostics */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Server className="w-4 h-4 text-slate-600" />
            Backend API Connectivity & Health
          </CardTitle>
          <CardDescription>
            Verify network connectivity and response latency to the FastAPI financial engine.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
            <div>
              <span className="text-slate-400 block mb-0.5">Target API Host:</span>
              <code className="text-slate-800 font-mono text-xs">
                {process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}
              </code>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleDiagnosticPing}
              isLoading={isPinging}
            >
              Test Connectivity
            </Button>
          </div>

          {pingResult && (
            <div className="p-3 bg-white border border-slate-200 rounded-lg space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-700">Health Endpoint:</span>
                <span className="font-mono text-slate-800">{pingResult.url}/health</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-700">Response Status:</span>
                <Badge variant={pingResult.status.includes("200") ? "success" : "danger"}>
                  {pingResult.status}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-700">Roundtrip Latency:</span>
                <span className="font-mono text-slate-800">{pingResult.latencyMs} ms</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <RegulatoryDisclaimer />
    </div>
  );
}
