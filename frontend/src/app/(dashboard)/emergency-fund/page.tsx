"use client";

import React, { useEffect, useState } from "react";
import {
  ShieldCheck,
  AlertCircle,
  CheckCircle2,
  Edit2,
  DollarSign,
  TrendingUp,
} from "lucide-react";
import { MetricCard } from "@/components/shared/MetricCard";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Badge } from "@/components/ui/Badge";
import { LoadingState, ErrorBanner, RegulatoryDisclaimer } from "@/components/shared/States";
import { formatCurrency } from "@/lib/formatters";
import { analysisApi } from "@/lib/api/analysis";
import { EmergencyFundAnalysis } from "@/types";

export default function EmergencyFundPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<EmergencyFundAnalysis | null>(null);

  // Edit Profile Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [savingsInput, setSavingsInput] = useState("");
  const [expensesInput, setExpensesInput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await analysisApi.getEmergencyFundAnalysis();
      setAnalysis(data);
      if (data) {
        setSavingsInput(data.available_liquid_savings || "");
        setExpensesInput(data.monthly_essential_expenses || "");
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load emergency fund analysis.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalysis();
  }, []);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await analysisApi.updateFinancialProfile({
        available_liquid_savings: savingsInput,
        monthly_essential_expenses: expensesInput,
      });
      setIsModalOpen(false);
      await fetchAnalysis();
    } catch (err: any) {
      alert(`Error updating profile: ${err?.detail || err?.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return <LoadingState message="Analyzing emergency liquidity reserves..." />;
  }

  const coverageMonths = parseFloat(analysis?.months_of_coverage || analysis?.current_coverage_months || "0");
  const isTargetAchieved = coverageMonths >= 6;

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-[#1A263D]">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            Emergency Fund Analysis
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 font-medium">
            Evaluate liquidity reserves against 3-month and 6-month essential living costs.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsModalOpen(true)}
          className="gap-1.5 border-[#202D45] text-slate-300 hover:text-white"
        >
          <Edit2 className="w-3.5 h-3.5 text-cyan-400" />
          <span>Update Savings & Expenses</span>
        </Button>
      </div>

      {error && <ErrorBanner message={error} onRetry={fetchAnalysis} />}

      {/* Top Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Current Liquid Savings"
          value={formatCurrency(analysis?.emergency_fund_balance || analysis?.available_liquid_savings, "INR")}
          subtitle="Available for emergency liquidity"
          icon={<DollarSign className="w-5 h-5 text-cyan-400" />}
          variant="brand"
        />

        <MetricCard
          title="Monthly Essential Expenses"
          value={formatCurrency(analysis?.average_monthly_essential_expenses || analysis?.monthly_essential_expenses, "INR")}
          subtitle="Rent, groceries, utilities & healthcare"
          icon={<TrendingUp className="w-5 h-5 text-slate-300" />}
          variant="default"
        />

        <MetricCard
          title="Current Coverage"
          value={
            analysis?.months_of_coverage
              ? `${parseFloat(analysis.months_of_coverage).toFixed(1)} Months`
              : analysis?.current_coverage_months
              ? `${analysis.current_coverage_months} Months`
              : "—"
          }
          subtitle={`Status: ${String(analysis?.status || analysis?.balance_status || "unknown").toUpperCase()}`}
          icon={<ShieldCheck className="w-5 h-5 text-emerald-400" />}
          variant={coverageMonths >= 6 ? "success" : coverageMonths >= 3 ? "default" : "danger"}
        />

        <MetricCard
          title="6-Month Target Shortfall"
          value={
            parseFloat(analysis?.shortfall_six_month || analysis?.shortfall_6_months || "0") <= 0 && analysis?.balance_status === "known"
              ? "Fully Funded"
              : formatCurrency(analysis?.shortfall_six_month || analysis?.shortfall_6_months, "INR")
          }
          subtitle={`Target: ${formatCurrency(analysis?.six_month_target || analysis?.recommended_target_6_months, "INR")}`}
          icon={isTargetAchieved ? <CheckCircle2 className="w-5 h-5 text-emerald-400" /> : <AlertCircle className="w-5 h-5 text-amber-400" />}
          variant={isTargetAchieved ? "success" : "warning"}
        />
      </div>

      {/* Coverage Progress Bar Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Reserve Runway vs Recommended Targets</CardTitle>
            <Badge variant={isTargetAchieved ? "success" : coverageMonths >= 3 ? "warning" : "danger"}>
              {coverageMonths >= 6 ? "6+ Months Secured" : coverageMonths >= 3 ? "Minimal 3-Mo Secured" : "Underfunded"}
            </Badge>
          </div>
          <CardDescription>
            Target 1: 3 months minimal buffer ({formatCurrency(analysis?.recommended_target_3_months, "INR")}) | Target 2: 6 months comfortable buffer ({formatCurrency(analysis?.recommended_target_6_months, "INR")})
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-2">
            <div className="flex justify-between text-xs font-mono font-bold text-slate-300">
              <span>Runway: {coverageMonths.toFixed(1)} months</span>
              <span className="text-cyan-400">Target Goal: 6.0 months</span>
            </div>
            <div className="h-4 w-full bg-[#0D1422] border border-[#1E2B42] rounded-full overflow-hidden flex p-0.5">
              <div
                style={{ width: `${Math.min(100, (coverageMonths / 6) * 100)}%` }}
                className={`h-full transition-all rounded-full ${
                  coverageMonths >= 6
                    ? "bg-gradient-to-r from-emerald-500 to-teal-400"
                    : coverageMonths >= 3
                    ? "bg-gradient-to-r from-amber-500 to-amber-400"
                    : "bg-gradient-to-r from-rose-500 to-rose-400"
                }`}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div className="p-4 rounded-xl border border-[#202D45] bg-[#0E1524] space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                3-Month Target (Minimal Buffer)
              </span>
              <p className="text-xl font-bold font-mono text-white">
                {formatCurrency(analysis?.recommended_target_3_months, "INR")}
              </p>
              <p className="text-xs font-medium text-slate-400 font-mono">
                Shortfall:{" "}
                {parseFloat(analysis?.shortfall_3_months || "0") <= 0
                  ? "₹0.00 (Target Met)"
                  : formatCurrency(analysis?.shortfall_3_months, "INR")}
              </p>
            </div>

            <div className="p-4 rounded-xl border border-[#202D45] bg-[#0E1524] space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                6-Month Target (Comfortable Buffer)
              </span>
              <p className="text-xl font-bold font-mono text-white">
                {formatCurrency(analysis?.recommended_target_6_months, "INR")}
              </p>
              <p className="text-xs font-medium text-slate-400 font-mono">
                Shortfall:{" "}
                {parseFloat(analysis?.shortfall_6_months || "0") <= 0
                  ? "₹0.00 (Target Met)"
                  : formatCurrency(analysis?.shortfall_6_months, "INR")}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recommendations Card */}
      {analysis?.recommendations && analysis.recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Strategic Liquidity Recommendations</CardTitle>
            <CardDescription>Automated rules-based guidance on buffer adequacy</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2.5 text-xs sm:text-sm text-slate-300">
              {analysis.recommendations.map((rec, idx) => (
                <li key={idx} className="flex items-start gap-2.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shrink-0 mt-2" />
                  <span className="leading-relaxed">{rec}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Edit Profile Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Update Emergency Profile Inputs"
        description="Update your liquid cash reserves and monthly essential costs"
      >
        <form onSubmit={handleUpdateProfile} className="space-y-4">
          <Input
            label="Available Liquid Savings (INR)"
            type="number"
            step="100"
            min="0"
            placeholder="e.g. 200000"
            value={savingsInput}
            onChange={(e) => setSavingsInput(e.target.value)}
            required
          />

          <Input
            label="Monthly Essential Expenses (INR)"
            type="number"
            step="100"
            min="0"
            placeholder="e.g. 45000"
            value={expensesInput}
            onChange={(e) => setExpensesInput(e.target.value)}
            required
          />

          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={isSubmitting}>
              Save Changes
            </Button>
          </div>
        </form>
      </Modal>

      <RegulatoryDisclaimer />
    </div>
  );
}
