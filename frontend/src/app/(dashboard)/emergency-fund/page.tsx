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

  const coverageMonths = parseFloat(analysis?.current_coverage_months || "0");
  const isTargetAchieved = coverageMonths >= 6;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl lg:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
            Emergency Fund Analysis
          </h1>
          <p className="text-base text-slate-500 dark:text-slate-400 mt-1.5 font-medium">
            Evaluate liquidity reserves against 3-month and 6-month essential living costs
          </p>
        </div>
        <Button
          variant="outline"
          size="md"
          onClick={() => setIsModalOpen(true)}
          className="gap-2 shadow-xs"
        >
          <Edit2 className="w-4 h-4" />
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
          icon={<DollarSign className="w-5 h-5" />}
          variant="brand"
        />

        <MetricCard
          title="Monthly Essential Expenses"
          value={formatCurrency(analysis?.average_monthly_essential_expenses || analysis?.monthly_essential_expenses, "INR")}
          subtitle="Rent, groceries, utilities & healthcare"
          icon={<TrendingUp className="w-5 h-5" />}
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
          icon={<ShieldCheck className="w-5 h-5" />}
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
          icon={isTargetAchieved ? <CheckCircle2 className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
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
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between text-xs font-semibold">
              <span>Runway: {analysis?.current_coverage_months || "0"} months</span>
              <span>Goal: 6.0 months</span>
            </div>
            <div className="h-4 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden flex">
              <div
                style={{ width: `${Math.min(100, (coverageMonths / 6) * 100)}%` }}
                className={`h-full transition-all rounded-full ${
                  coverageMonths >= 6
                    ? "bg-emerald-500"
                    : coverageMonths >= 3
                    ? "bg-amber-500"
                    : "bg-rose-500"
                }`}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div className="p-3.5 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 space-y-1">
              <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                3-Month Target (Minimal Buffer)
              </span>
              <p className="text-lg font-bold text-slate-900 dark:text-slate-100">
                {formatCurrency(analysis?.recommended_target_3_months, "INR")}
              </p>
              <p className="text-xs text-slate-500">
                Shortfall:{" "}
                {parseFloat(analysis?.shortfall_3_months || "0") <= 0
                  ? "₹0.00 (Target Met)"
                  : formatCurrency(analysis?.shortfall_3_months, "INR")}
              </p>
            </div>

            <div className="p-3.5 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 space-y-1">
              <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                6-Month Target (Comfortable Buffer)
              </span>
              <p className="text-lg font-bold text-slate-900 dark:text-slate-100">
                {formatCurrency(analysis?.recommended_target_6_months, "INR")}
              </p>
              <p className="text-xs text-slate-500">
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
            <CardTitle className="text-sm">Strategic Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-400">
              {analysis.recommendations.map((rec, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 shrink-0 mt-1.5" />
                  <span>{rec}</span>
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
