"use client";

import React, { useEffect, useState } from "react";
import {
  Target,
  Plus,
  Calculator,
  Compass,
  ArrowRight,
  TrendingUp,
  Trash2,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { SIPGrowthChart } from "@/components/charts/SIPGrowthChart";
import { LoadingState, EmptyState, ErrorBanner, RegulatoryDisclaimer } from "@/components/shared/States";
import { formatCurrency, formatDate, formatPercentage } from "@/lib/formatters";
import { goalsApi } from "@/lib/api/goals";
import { ForwardSIPResult, GlidePathMilestone, InvestmentGoal, ReverseSIPResult } from "@/types";

export default function GoalsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [goals, setGoals] = useState<InvestmentGoal[]>([]);

  // Create Goal Modal
  const [isGoalModalOpen, setIsGoalModalOpen] = useState(false);
  const [goalName, setGoalName] = useState("");
  const [goalTargetAmount, setGoalTargetAmount] = useState("");
  const [goalTargetDate, setGoalTargetDate] = useState("");
  const [goalCurrentAmount, setGoalCurrentAmount] = useState("0");
  const [goalPlannedSip, setGoalPlannedSip] = useState("0");
  const [isSubmittingGoal, setIsSubmittingGoal] = useState(false);

  // Forward SIP Calculator State
  const [fSipMonthly, setFSipMonthly] = useState("10000");
  const [fSipRate, setFSipRate] = useState("12");
  const [fSipTenureYears, setFSipTenureYears] = useState("5");
  const [fSipStepUp, setFSipStepUp] = useState("0");
  const [fSipResult, setFSipResult] = useState<ForwardSIPResult | null>(null);
  const [fSipLoading, setFSipLoading] = useState(false);

  // Reverse SIP Calculator State
  const [rSipTarget, setRSipTarget] = useState("1000000");
  const [rSipRate, setRSipRate] = useState("12");
  const [rSipTenureYears, setRSipTenureYears] = useState("5");
  const [rSipResult, setRSipResult] = useState<ReverseSIPResult | null>(null);
  const [rSipLoading, setRSipLoading] = useState(false);

  // Glide Path State
  const [glideYears, setGlideYears] = useState("15");
  const [glideMilestones, setGlideMilestones] = useState<GlidePathMilestone[]>([]);
  const [glideLoading, setGlideLoading] = useState(false);

  const fetchGoals = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await goalsApi.listGoals();
      setGoals(data || []);
    } catch (err: any) {
      setError(err?.message || "Failed to load investment goals.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGoals();
  }, []);

  const handleCreateGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!goalName || !goalTargetAmount || !goalTargetDate) return;

    setIsSubmittingGoal(true);
    try {
      await goalsApi.createGoal({
        name: goalName,
        target_amount: goalTargetAmount,
        target_date: goalTargetDate,
        current_amount: goalCurrentAmount || "0",
        planned_monthly_contribution: goalPlannedSip || "0",
      });
      setIsGoalModalOpen(false);
      setGoalName("");
      setGoalTargetAmount("");
      setGoalTargetDate("");
      await fetchGoals();
    } catch (err: any) {
      alert(`Error creating goal: ${err?.detail || err?.message}`);
    } finally {
      setIsSubmittingGoal(false);
    }
  };

  const handleDeleteGoal = async (id: string) => {
    if (!confirm("Are you sure you want to delete this investment goal?")) return;
    try {
      await goalsApi.deleteGoal(id);
      await fetchGoals();
    } catch (err: any) {
      alert(`Error deleting goal: ${err?.detail || err?.message}`);
    }
  };

  const handleCalculateForwardSIP = async (e: React.FormEvent) => {
    e.preventDefault();
    setFSipLoading(true);
    try {
      const res = await goalsApi.calculateForwardSIP({
        monthly_investment: fSipMonthly,
        annual_rate: fSipRate,
        tenure_months: parseInt(fSipTenureYears) * 12,
        step_up_percentage: fSipStepUp || "0",
      });
      setFSipResult(res);
    } catch (err: any) {
      alert(`Error: ${err?.detail || err?.message}`);
    } finally {
      setFSipLoading(false);
    }
  };

  const handleCalculateReverseSIP = async (e: React.FormEvent) => {
    e.preventDefault();
    setRSipLoading(true);
    try {
      const res = await goalsApi.calculateReverseSIP({
        target_amount: rSipTarget,
        annual_rate: rSipRate,
        tenure_months: parseInt(rSipTenureYears) * 12,
      });
      setRSipResult(res);
    } catch (err: any) {
      alert(`Error: ${err?.detail || err?.message}`);
    } finally {
      setRSipLoading(false);
    }
  };

  const handleGenerateGlidePath = async () => {
    setGlideLoading(true);
    try {
      const res = await goalsApi.generateGlidePath(parseInt(glideYears), "moderate");
      setGlideMilestones(res.milestones || []);
    } catch (err: any) {
      alert(`Error generating glide path: ${err?.detail || err?.message}`);
    } finally {
      setGlideLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl lg:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
            Investment Goals & SIP Calculators
          </h1>
          <p className="text-base text-slate-500 dark:text-slate-400 mt-1.5 font-medium">
            Track milestones, calculate forward and reverse SIP requirements, and plan glide paths
          </p>
        </div>
        <Button
          variant="primary"
          size="md"
          onClick={() => setIsGoalModalOpen(true)}
          className="gap-2 shadow-md shadow-indigo-600/20"
        >
          <Plus className="w-4 h-4" />
          <span>New Investment Goal</span>
        </Button>
      </div>

      {error && <ErrorBanner message={error} onRetry={fetchGoals} />}

      {/* Goals List Section */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
          <Target className="w-5 h-5 text-indigo-600" />
          <span>Active Investment Goals</span>
        </h2>

        {loading ? (
          <LoadingState message="Fetching active investment goals..." />
        ) : goals.length === 0 ? (
          <EmptyState
            title="No investment goals yet"
            description="Create your first goal (e.g. Retirement, Child Education, Down Payment) to track monthly SIP requirements."
            icon={<Target className="w-8 h-8" />}
            action={
              <Button variant="primary" size="sm" onClick={() => setIsGoalModalOpen(true)}>
                Create Goal
              </Button>
            }
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {goals.map((g) => {
              const current = parseFloat(g.current_amount || "0");
              const target = parseFloat(g.target_amount || "1");
              const progressPct = Math.min(100, Math.round((current / target) * 100));

              return (
                <Card key={g.id} className="flex flex-col justify-between">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <CardTitle className="text-sm font-bold truncate max-w-[180px]">
                        {g.name}
                      </CardTitle>
                      <button
                        onClick={() => handleDeleteGoal(g.id)}
                        className="text-slate-400 hover:text-rose-600 p-1 transition-colors"
                        title="Delete Goal"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                    <CardDescription>Target Date: {formatDate(g.target_date)}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3 text-xs">
                    <div className="space-y-1">
                      <div className="flex justify-between text-slate-500">
                        <span>Progress: {progressPct}%</span>
                        <span className="font-semibold text-slate-900 dark:text-slate-100">
                          {formatCurrency(g.current_amount, "INR")} / {formatCurrency(g.target_amount, "INR")}
                        </span>
                      </div>
                      <div className="h-2 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                        <div
                          style={{ width: `${progressPct}%` }}
                          className="h-full bg-indigo-600 rounded-full transition-all"
                        />
                      </div>
                    </div>

                    <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex justify-between items-center text-[11px] text-slate-500">
                      <span>Planned Monthly SIP:</span>
                      <span className="font-semibold text-indigo-600">
                        {formatCurrency(g.planned_monthly_contribution, "INR")}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* SIP Calculators Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
        {/* Forward SIP Calculator */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Calculator className="w-4 h-4 text-indigo-600" />
              <CardTitle className="text-base">Forward SIP Calculator</CardTitle>
            </div>
            <CardDescription>
              Calculate future wealth gain from regular monthly investments
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <form onSubmit={handleCalculateForwardSIP} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <Input
                  label="Monthly SIP (INR)"
                  type="number"
                  step="500"
                  min="500"
                  value={fSipMonthly}
                  onChange={(e) => setFSipMonthly(e.target.value)}
                  required
                />
                <Input
                  label="Expected Return (% p.a.)"
                  type="number"
                  step="0.5"
                  min="1"
                  max="30"
                  value={fSipRate}
                  onChange={(e) => setFSipRate(e.target.value)}
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <Input
                  label="Tenure (Years)"
                  type="number"
                  step="1"
                  min="1"
                  max="40"
                  value={fSipTenureYears}
                  onChange={(e) => setFSipTenureYears(e.target.value)}
                  required
                />
                <Input
                  label="Annual Step-Up (%)"
                  type="number"
                  step="1"
                  min="0"
                  max="25"
                  value={fSipStepUp}
                  onChange={(e) => setFSipStepUp(e.target.value)}
                />
              </div>

              <Button type="submit" variant="primary" size="sm" className="w-full" isLoading={fSipLoading}>
                Calculate Future Wealth
              </Button>
            </form>

            {fSipResult && (
              <div className="pt-3 border-t border-slate-100 dark:border-slate-800 space-y-3">
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="p-2 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                    <span className="text-[10px] text-slate-500 uppercase block">Total Invested</span>
                    <strong className="text-xs font-bold text-slate-900 dark:text-slate-100">
                      {formatCurrency(fSipResult.total_invested, "INR")}
                    </strong>
                  </div>
                  <div className="p-2 bg-emerald-50 dark:bg-emerald-950/40 rounded-lg">
                    <span className="text-[10px] text-emerald-600 uppercase block">Wealth Gain</span>
                    <strong className="text-xs font-bold text-emerald-700 dark:text-emerald-400">
                      {formatCurrency(fSipResult.estimated_returns, "INR")}
                    </strong>
                  </div>
                  <div className="p-2 bg-indigo-50 dark:bg-indigo-950/40 rounded-lg">
                    <span className="text-[10px] text-indigo-600 uppercase block">Total Future Value</span>
                    <strong className="text-xs font-bold text-indigo-700 dark:text-indigo-400">
                      {formatCurrency(fSipResult.future_value, "INR")}
                    </strong>
                  </div>
                </div>

                <SIPGrowthChart schedule={fSipResult.schedule} height={200} currency="INR" />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Reverse SIP Calculator */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-indigo-600" />
              <CardTitle className="text-base">Reverse SIP Calculator</CardTitle>
            </div>
            <CardDescription>
              Determine the exact monthly investment required to reach a specific financial target
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <form onSubmit={handleCalculateReverseSIP} className="space-y-3">
              <Input
                label="Target Amount (INR)"
                type="number"
                step="10000"
                min="10000"
                value={rSipTarget}
                onChange={(e) => setRSipTarget(e.target.value)}
                required
              />

              <div className="grid grid-cols-2 gap-3">
                <Input
                  label="Expected Return (% p.a.)"
                  type="number"
                  step="0.5"
                  min="1"
                  max="30"
                  value={rSipRate}
                  onChange={(e) => setRSipRate(e.target.value)}
                  required
                />
                <Input
                  label="Tenure (Years)"
                  type="number"
                  step="1"
                  min="1"
                  max="40"
                  value={rSipTenureYears}
                  onChange={(e) => setRSipTenureYears(e.target.value)}
                  required
                />
              </div>

              <Button type="submit" variant="secondary" size="sm" className="w-full" isLoading={rSipLoading}>
                Calculate Required Monthly Contribution
              </Button>
            </form>

            {rSipResult && (
              <div className="p-4 rounded-xl bg-indigo-50/70 border border-indigo-100 dark:bg-indigo-950/40 dark:border-indigo-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-indigo-900 dark:text-indigo-300">
                    Required Monthly Contribution:
                  </span>
                  <span className="text-lg font-bold text-indigo-700 dark:text-indigo-300">
                    {formatCurrency(rSipResult.required_monthly_investment, "INR")}/mo
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs text-indigo-800 dark:text-indigo-400 pt-1 border-t border-indigo-100 dark:border-indigo-800">
                  <span>Total Capital Outlay:</span>
                  <span className="font-semibold">{formatCurrency(rSipResult.total_invested, "INR")}</span>
                </div>
                <div className="flex items-center justify-between text-xs text-indigo-800 dark:text-indigo-400">
                  <span>Compounded Interest Generated:</span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                    {formatCurrency(rSipResult.estimated_returns, "INR")}
                  </span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Glide Path Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Compass className="w-4 h-4 text-indigo-600" />
              <CardTitle className="text-base">Risk-Aware Investment Glide Path</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <select
                value={glideYears}
                onChange={(e) => setGlideYears(e.target.value)}
                className="px-2.5 py-1 text-xs bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-200"
              >
                <option value="5">5 Years Horizon</option>
                <option value="10">10 Years Horizon</option>
                <option value="15">15 Years Horizon</option>
                <option value="20">20 Years Horizon</option>
              </select>
              <Button variant="outline" size="sm" onClick={handleGenerateGlidePath} isLoading={glideLoading}>
                Generate Milestones
              </Button>
            </div>
          </div>
          <CardDescription>
            Systematic derisking schedule that progressively shifts asset allocation from equities toward debt and cash
          </CardDescription>
        </CardHeader>
        <CardContent>
          {glideMilestones.length === 0 ? (
            <div className="py-6 text-center text-xs text-slate-400">
              Select an investment horizon and click &quot;Generate Milestones&quot; to preview asset allocation transitions.
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
              {glideMilestones.map((m, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 space-y-2"
                >
                  <div className="flex justify-between items-center text-xs font-bold text-slate-900 dark:text-slate-100">
                    <span>{m.years_to_horizon} Yrs Remaining</span>
                    <Badge variant="outline">Stage {idx + 1}</Badge>
                  </div>
                  <div className="space-y-1 text-xs">
                    <div className="flex justify-between text-indigo-600 font-semibold">
                      <span>Equity:</span>
                      <span>{formatPercentage(parseFloat(m.equity_weight) * 100)}</span>
                    </div>
                    <div className="flex justify-between text-sky-600 font-semibold">
                      <span>Debt:</span>
                      <span>{formatPercentage(parseFloat(m.debt_weight) * 100)}</span>
                    </div>
                    <div className="flex justify-between text-emerald-600 font-semibold">
                      <span>Cash:</span>
                      <span>{formatPercentage(parseFloat(m.cash_weight) * 100)}</span>
                    </div>
                  </div>
                  <p className="text-[10px] text-slate-400 leading-tight pt-1">{m.description}</p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Goal Modal */}
      <Modal
        isOpen={isGoalModalOpen}
        onClose={() => setIsGoalModalOpen(false)}
        title="Create Investment Goal"
        description="Configure target amount, horizon, and monthly contribution"
      >
        <form onSubmit={handleCreateGoal} className="space-y-4">
          <Input
            label="Goal Name"
            placeholder="e.g. Retirement Corpus, Down Payment"
            value={goalName}
            onChange={(e) => setGoalName(e.target.value)}
            required
          />

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Target Amount (INR)"
              type="number"
              step="1000"
              min="1000"
              placeholder="e.g. 5000000"
              value={goalTargetAmount}
              onChange={(e) => setGoalTargetAmount(e.target.value)}
              required
            />
            <Input
              label="Target Deadline"
              type="date"
              value={goalTargetDate}
              onChange={(e) => setGoalTargetDate(e.target.value)}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Initial Capital Invested (INR)"
              type="number"
              step="100"
              min="0"
              value={goalCurrentAmount}
              onChange={(e) => setGoalCurrentAmount(e.target.value)}
            />
            <Input
              label="Planned Monthly SIP (INR)"
              type="number"
              step="100"
              min="0"
              value={goalPlannedSip}
              onChange={(e) => setGoalPlannedSip(e.target.value)}
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsGoalModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={isSubmittingGoal}>
              Save Goal
            </Button>
          </div>
        </form>
      </Modal>

      <RegulatoryDisclaimer text="Hypothetical SIP simulations and glide paths are for educational planning only. Compounding calculations assume consistent annual return rates which are not guaranteed in market investments." />
    </div>
  );
}
