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
  Cpu,
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
    <div className="space-y-8 max-w-5xl animate-fadeIn">
      {/* Page Header */}
      <div className="border-b border-[#202D45] pb-6">
        <div className="flex items-center gap-2.5">
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            Account Settings & System Diagnostics
          </h1>
          <Badge variant="cyan" className="font-mono text-[10px] uppercase tracking-wider">
            Configuration
          </Badge>
        </div>
        <p className="text-sm text-slate-400 mt-1.5 font-normal">
          Manage your authenticated identity, financial baseline parameters, and backend cluster telemetry.
        </p>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}
      {profileSuccess && (
        <div className="p-3 bg-emerald-950/40 border border-emerald-500/30 text-xs text-emerald-300 rounded-xl flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{profileSuccess}</span>
        </div>
      )}

      {/* User Account Details */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base text-white flex items-center gap-2">
            <User className="w-4 h-4 text-cyan-400" />
            Authenticated Identity
          </CardTitle>
          <CardDescription className="text-xs text-slate-400">
            Account credentials and cryptographic tenant boundary.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-xs">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-3.5 bg-[#0A0F1D] rounded-xl border border-[#202D45]">
              <span className="text-slate-400 block mb-0.5 text-[11px] font-medium uppercase tracking-wider">Email Address</span>
              <span className="font-mono font-bold text-white text-sm">
                {user?.email || "—"}
              </span>
            </div>
            <div className="p-3.5 bg-[#0A0F1D] rounded-xl border border-[#202D45]">
              <span className="text-slate-400 block mb-0.5 text-[11px] font-medium uppercase tracking-wider">Account Status</span>
              <div className="flex items-center gap-2 mt-0.5">
                <Badge variant={user?.is_active ? "success" : "danger"}>
                  {user?.is_active ? "Active" : "Inactive"}
                </Badge>
                <span className="text-slate-400 font-mono text-[11px]">
                  Registered {user?.created_at ? formatDate(user.created_at) : "—"}
                </span>
              </div>
            </div>
          </div>

          <div className="p-3.5 bg-cyan-950/30 rounded-xl border border-cyan-500/20 flex items-start gap-3">
            <Shield className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0" />
            <div className="text-cyan-200">
              <span className="font-semibold block mb-0.5">Cryptographic Tenant Data Boundary</span>
              All personal financial transactions, portfolios, holdings, and AI decision threads are isolated under your tenant identifier (<code className="text-cyan-300 font-mono text-[11px]">{user?.id || "anonymous"}</code>).
            </div>
          </div>
        </CardContent>
        <CardFooter className="bg-[#0A0F1D] border-t border-[#202D45] justify-between">
          <span className="text-[11px] text-slate-400 font-mono">
            Session active via cryptographic token in secure browser storage
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={logout}
            className="text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 border-rose-500/30"
          >
            <LogOut className="w-4 h-4 mr-1.5" />
            Sign Out
          </Button>
        </CardFooter>
      </Card>

      {/* Financial Profile Baseline */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base text-white flex items-center gap-2">
            <Activity className="w-4 h-4 text-teal-400" />
            Financial Baseline Profile
          </CardTitle>
          <CardDescription className="text-xs text-slate-400">
            Override or configure default parameters used for emergency fund reserve runway and cash-flow projections.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSaveProfile} className="space-y-4 text-xs">
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
              <Button type="submit" variant="primary" size="sm" isLoading={isSavingProfile}>
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
          <CardTitle className="text-base text-white flex items-center gap-2">
            <Server className="w-4 h-4 text-cyan-400" />
            Backend API Connectivity & Health
          </CardTitle>
          <CardDescription className="text-xs text-slate-400">
            Verify network connectivity and response latency to the FastAPI financial computation engine.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 bg-[#0A0F1D] rounded-xl border border-[#202D45]">
            <div>
              <span className="text-slate-400 block mb-0.5 text-[11px] uppercase font-semibold">Target API Host:</span>
              <code className="text-cyan-300 font-mono text-xs">
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
            <div className="p-3.5 bg-[#0A0F1D] border border-[#202D45] rounded-xl space-y-2 font-mono">
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-sans text-xs">Health Endpoint:</span>
                <span className="text-slate-200 text-xs">{pingResult.url}/health</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-sans text-xs">Response Status:</span>
                <Badge variant={pingResult.status.includes("200") ? "success" : "danger"}>
                  {pingResult.status}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-sans text-xs">Roundtrip Latency:</span>
                <span className="text-cyan-300 text-xs font-bold">{pingResult.latencyMs} ms</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <RegulatoryDisclaimer />
    </div>
  );
}
