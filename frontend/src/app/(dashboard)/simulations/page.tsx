"use client";

import React, { useEffect, useState } from "react";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  CheckCircle2,
  ChevronRight,
  Clock,
  Coins,
  History,
  Info,
  Layers,
  LineChart as LineChartIcon,
  RefreshCw,
  Sliders,
  Sparkles,
  TrendingDown,
  TrendingUp,
  Cpu,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { MetricCard } from "@/components/shared/MetricCard";
import { EmptyState, ErrorBanner, LoadingState } from "@/components/shared/States";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { goalsApi } from "@/lib/api/goals";
import { portfolioApi } from "@/lib/api/portfolio";
import {
  BacktestResponse,
  fetchStressPresets,
  GoalScenarioComparisonResponse,
  MonteCarloResponse,
  runBacktest,
  runGoalScenarioComparison,
  runMonteCarlo,
  runStressTest,
  StressPreset,
  StressTestResponse,
} from "@/lib/api/simulations";
import { formatCurrency, formatPercentage } from "@/lib/formatters";
import { InvestmentGoal, Portfolio } from "@/types";

type ActiveTab = "stress" | "backtest" | "monte_carlo" | "scenarios";

export default function SimulationsPage() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("stress");
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [goals, setGoals] = useState<InvestmentGoal[]>([]);
  const [presets, setPresets] = useState<StressPreset[]>([]);
  const [initLoading, setInitLoading] = useState(true);

  // Tab 1: Stress Test State
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<string>("");
  const [selectedScenario, setSelectedScenario] = useState<string>("equity_market_crash");
  const [stressLoading, setStressLoading] = useState(false);
  const [stressError, setStressError] = useState<string | null>(null);
  const [stressResult, setStressResult] = useState<StressTestResponse | null>(null);

  // Tab 2: Backtest State
  const [btPortfolioId, setBtPortfolioId] = useState<string>("");
  const [btInitialVal, setBtInitialVal] = useState<string>("100000");
  const [btRebalFreq, setBtRebalFreq] = useState<string>("monthly");
  const [btFeeBps, setBtFeeBps] = useState<string>("10");
  const [btBenchmark, setBtBenchmark] = useState<string>("");
  const [btLoading, setBtLoading] = useState(false);
  const [btError, setBtError] = useState<string | null>(null);
  const [btResult, setBtResult] = useState<BacktestResponse | null>(null);

  // Tab 3: Monte Carlo State
  const [mcInitialVal, setMcInitialVal] = useState<string>("100000");
  const [mcMonthlySip, setMcMonthlySip] = useState<string>("10000");
  const [mcHorizonYears, setMcHorizonYears] = useState<string>("10");
  const [mcExpectedRet, setMcExpectedRet] = useState<string>("12");
  const [mcVolatility, setMcVolatility] = useState<string>("15");
  const [mcTargetAmt, setMcTargetAmt] = useState<string>("3000000");
  const [mcSimCount, setMcSimCount] = useState<string>("1000");
  const [mcLoading, setMcLoading] = useState(false);
  const [mcError, setMcError] = useState<string | null>(null);
  const [mcResult, setMcResult] = useState<MonteCarloResponse | null>(null);

  // Tab 4: Goal Scenario Comparison State
  const [selectedGoalId, setSelectedGoalId] = useState<string>("");
  const [scLoading, setScLoading] = useState(false);
  const [scError, setScError] = useState<string | null>(null);
  const [scResult, setScResult] = useState<GoalScenarioComparisonResponse | null>(null);

  // Load portfolios, goals, and presets on mount
  useEffect(() => {
    async function loadInitial() {
      try {
        const [portData, goalData, presetData] = await Promise.all([
          portfolioApi.listPortfolios().catch(() => []),
          goalsApi.listGoals().catch(() => []),
          fetchStressPresets().catch(() => ({ presets: [] })),
        ]);
        setPortfolios(portData);
        setGoals(goalData);
        setPresets(presetData.presets);

        if (portData.length > 0) {
          setSelectedPortfolioId(portData[0].id);
          setBtPortfolioId(portData[0].id);
        }
        if (goalData.length > 0) {
          setSelectedGoalId(goalData[0].id);
        }
      } catch (err: any) {
        console.error("Initialization error:", err);
      } finally {
        setInitLoading(false);
      }
    }
    loadInitial();
  }, []);

  const handleRunStressTest = async () => {
    setStressLoading(true);
    setStressError(null);
    try {
      const res = await runStressTest({
        portfolio_id: selectedPortfolioId || undefined,
        scenario: selectedScenario,
        custom_holdings: !selectedPortfolioId
          ? [
              { symbol: "EQUITY_BASKET", asset_class: "equity", current_value: 60000 },
              { symbol: "BOND_BASKET", asset_class: "fixed_income", current_value: 40000 },
            ]
          : undefined,
      });
      setStressResult(res);
    } catch (err: any) {
      setStressError(err?.detail || err?.message || "Stress test failed.");
    } finally {
      setStressLoading(false);
    }
  };

  const handleRunBacktest = async () => {
    setBtLoading(true);
    setBtError(null);
    try {
      const res = await runBacktest({
        portfolio_id: btPortfolioId || undefined,
        initial_value: parseFloat(btInitialVal) || 100000,
        rebalance_frequency: btRebalFreq,
        fee_bps: parseFloat(btFeeBps) || 10,
        benchmark_symbol: btBenchmark.trim() || undefined,
      });
      setBtResult(res);
    } catch (err: any) {
      setBtError(err?.detail || err?.message || "Backtest failed.");
    } finally {
      setBtLoading(false);
    }
  };

  const handleRunMonteCarlo = async () => {
    setMcLoading(true);
    setMcError(null);
    try {
      const horizonMonths = Math.round((parseFloat(mcHorizonYears) || 10) * 12);
      const res = await runMonteCarlo({
        initial_value: parseFloat(mcInitialVal) || 100000,
        monthly_contribution: parseFloat(mcMonthlySip) || 0,
        horizon_months: horizonMonths,
        expected_annual_return_pct: parseFloat(mcExpectedRet) || 12,
        annual_volatility_pct: parseFloat(mcVolatility) || 15,
        target_amount: parseFloat(mcTargetAmt) || undefined,
        num_simulations: parseInt(mcSimCount, 10) || 1000,
        seed: 42,
      });
      setMcResult(res);
    } catch (err: any) {
      setMcError(err?.detail || err?.message || "Simulation failed.");
    } finally {
      setMcLoading(false);
    }
  };

  const handleRunGoalComparison = async () => {
    setScLoading(true);
    setScError(null);
    try {
      const chosenGoal = goals.find((g) => g.id === selectedGoalId);
      const baseMonthly = chosenGoal?.planned_monthly_contribution
        ? parseFloat(chosenGoal.planned_monthly_contribution)
        : 10000;

      const res = await runGoalScenarioComparison({
        goal_id: selectedGoalId || undefined,
        baseline_target_amount: !selectedGoalId ? 2500000 : undefined,
        baseline_current_amount: !selectedGoalId ? 100000 : undefined,
        baseline_monthly_contribution: !selectedGoalId ? 10000 : undefined,
        baseline_annual_return_pct: !selectedGoalId ? 12 : undefined,
        scenarios: [
          {
            name: "Conservative (+₹3,000/mo)",
            monthly_contribution: baseMonthly + 3000,
          },
          {
            name: "Aggressive (+₹7,500/mo)",
            monthly_contribution: baseMonthly + 7500,
          },
          {
            name: "Extended Horizon (+2 Years)",
            horizon_months: 84,
          },
        ],
        num_simulations: 1000,
        seed: 42,
      });
      setScResult(res);
    } catch (err: any) {
      setScError(err?.detail || err?.message || "Scenario comparison failed.");
    } finally {
      setScLoading(false);
    }
  };

  if (initLoading) {
    return <LoadingState message="Loading simulation analytics workspace..." />;
  }

  return (
    <div className="space-y-8 animate-fadeIn pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#202D45] pb-6">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
              Stress Testing & Quantitative Simulations
            </h1>
            <Badge variant="cyan" className="font-mono text-[10px] uppercase tracking-wider">
              Simulation Lab
            </Badge>
          </div>
          <p className="text-sm text-slate-400 mt-1.5 font-normal">
            Crisis shock modeling, look-ahead free historical backtesting, Geometric Brownian Motion Monte Carlo projections, and what-if scenarios.
          </p>
        </div>
      </div>

      {/* Workspace Tabs Navigation */}
      <div className="flex flex-wrap gap-2 p-1.5 rounded-xl bg-[#0E1524] border border-[#202D45]">
        <button
          onClick={() => setActiveTab("stress")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold text-xs transition-all duration-200 ${
            activeTab === "stress"
              ? "bg-[#162032] text-cyan-300 border border-cyan-500/30 shadow-glow-cyan"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          Macro Stress Testing
        </button>

        <button
          onClick={() => setActiveTab("backtest")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold text-xs transition-all duration-200 ${
            activeTab === "backtest"
              ? "bg-[#162032] text-cyan-300 border border-cyan-500/30 shadow-glow-cyan"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <History className="w-3.5 h-3.5" />
          Historical Backtesting
        </button>

        <button
          onClick={() => setActiveTab("monte_carlo")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold text-xs transition-all duration-200 ${
            activeTab === "monte_carlo"
              ? "bg-[#162032] text-cyan-300 border border-cyan-500/30 shadow-glow-cyan"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <Sparkles className="w-3.5 h-3.5" />
          Monte Carlo Simulator
        </button>

        <button
          onClick={() => setActiveTab("scenarios")}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold text-xs transition-all duration-200 ${
            activeTab === "scenarios"
              ? "bg-[#162032] text-cyan-300 border border-cyan-500/30 shadow-glow-cyan"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          Goal Scenario Comparison
        </button>
      </div>

      {/* ==================================================================== */}
      {/* TAB 1: MACRO STRESS TESTING                                           */}
      {/* ==================================================================== */}
      {activeTab === "stress" && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base text-white flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-400" />
                Configure Macro Stress Scenario
              </CardTitle>
              <CardDescription className="text-xs text-slate-400">
                Simulate instantaneous shocks across asset classes without relying on historical correlations.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
                    Target Portfolio
                  </label>
                  <select
                    value={selectedPortfolioId}
                    onChange={(e) => setSelectedPortfolioId(e.target.value)}
                    className="w-full h-10 px-3 rounded-lg border border-[#202D45] bg-[#0E1524] text-white font-medium focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  >
                    {portfolios.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.base_currency})
                      </option>
                    ))}
                    {portfolios.length === 0 && (
                      <option value="">Sample 60/40 Baseline Basket</option>
                    )}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
                    Macro Shock Preset
                  </label>
                  <select
                    value={selectedScenario}
                    onChange={(e) => setSelectedScenario(e.target.value)}
                    className="w-full h-10 px-3 rounded-lg border border-[#202D45] bg-[#0E1524] text-white font-medium focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  >
                    {presets.map((pr) => (
                      <option key={pr.id} value={pr.id}>
                        {pr.name}
                      </option>
                    ))}
                    {presets.length === 0 && (
                      <>
                        <option value="equity_market_crash">Equity Market Crash (-25%)</option>
                        <option value="bond_market_decline">Rate Hike & Bond Slump (-12%)</option>
                        <option value="stagflation_shock">Stagflation Crisis (-20% eq, +25% comm)</option>
                        <option value="tech_sector_rout">Tech Multiple Compression (-35%)</option>
                        <option value="covid_liquidity_shock">Acute Liquidity Freeze (-30%)</option>
                      </>
                    )}
                  </select>
                </div>

                <div className="flex items-end">
                  <Button
                    onClick={handleRunStressTest}
                    disabled={stressLoading}
                    variant="primary"
                    className="w-full h-10"
                  >
                    {stressLoading ? (
                      <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                    ) : (
                      <Activity className="w-4 h-4 mr-2" />
                    )}
                    Execute Stress Test
                  </Button>
                </div>
              </div>

              {stressError && (
                <div className="mt-4 p-3 rounded-xl bg-rose-950/40 border border-rose-500/30 flex items-center gap-2.5 text-rose-300 text-xs">
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
                  <span>{stressError}</span>
                </div>
              )}
            </CardContent>
          </Card>

          {stressResult && (
            <div className="space-y-6 animate-fadeIn">
              {/* Metric Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <MetricCard
                  title="Baseline Value"
                  value={formatCurrency(stressResult.baseline_portfolio_value)}
                  subtitle="Pre-shock portfolio valuation"
                  icon={<Coins className="w-4 h-4" />}
                  variant="default"
                />
                <MetricCard
                  title="Post-Shock Value"
                  value={formatCurrency(stressResult.stressed_portfolio_value)}
                  subtitle="Estimated value after crisis"
                  icon={<TrendingDown className="w-4 h-4" />}
                  variant={parseFloat(stressResult.absolute_change) < 0 ? "danger" : "success"}
                />
                <MetricCard
                  title="Estimated Net Loss"
                  value={formatCurrency(stressResult.absolute_change)}
                  subtitle="Absolute dollar variance"
                  icon={<ArrowDownRight className="w-4 h-4" />}
                  variant={parseFloat(stressResult.absolute_change) < 0 ? "danger" : "success"}
                />
                <MetricCard
                  title="Portfolio Contraction"
                  value={formatPercentage(stressResult.percentage_change)}
                  subtitle="Total percentage drawdown"
                  icon={<Activity className="w-4 h-4" />}
                  variant={parseFloat(stressResult.percentage_change) < 0 ? "danger" : "success"}
                />
              </div>

              {/* Asset Class Loss Contribution Chart & Table */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base text-white flex items-center gap-2">
                      <BarChart3 className="w-4 h-4 text-cyan-400" />
                      Loss Contribution by Asset Class
                    </CardTitle>
                    <CardDescription className="text-xs text-slate-400">
                      Share of total portfolio loss generated by each asset category
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={stressResult.asset_class_breakdown.map((c) => ({
                            name: c.asset_class.toUpperCase(),
                            lossContribution: parseFloat(c.contribution_to_loss_pct),
                            shock: parseFloat(c.shock_percentage),
                          }))}
                          margin={{ top: 10, right: 10, left: -20, bottom: 20 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#202D45" />
                          <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#94a3b8" }} />
                          <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} unit="%" />
                          <Tooltip
                            formatter={(val: any) => [`${val}%`, "Contribution to Total Loss"]}
                            contentStyle={{ backgroundColor: "#0E1524", borderColor: "#202D45", borderRadius: 8, color: "#fff", fontSize: 12 }}
                          />
                          <Bar dataKey="lossContribution" fill="#06B6D4" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base text-white flex items-center gap-2">
                      <Layers className="w-4 h-4 text-cyan-400" />
                      Asset Class Shift Breakdown
                    </CardTitle>
                    <CardDescription className="text-xs text-slate-400">
                      Weight migration resulting from uneven asset class contractions
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="p-0">
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs text-left">
                        <thead className="bg-[#0A0F1D] text-slate-400 border-b border-[#202D45] uppercase tracking-wider font-semibold">
                          <tr>
                            <th className="px-4 py-2.5">Asset Class</th>
                            <th className="px-4 py-2.5 text-right">Shock %</th>
                            <th className="px-4 py-2.5 text-right">Base Wt</th>
                            <th className="px-4 py-2.5 text-right">Stressed Wt</th>
                            <th className="px-4 py-2.5 text-right">Variance</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#202D45] font-mono">
                          {stressResult.asset_class_breakdown.map((ac, idx) => (
                            <tr key={idx} className="hover:bg-[#162032]/30">
                              <td className="px-4 py-2.5 font-bold capitalize text-white font-sans">
                                {ac.asset_class.replace("_", " ")}
                              </td>
                              <td className="px-4 py-2.5 text-right text-rose-400 font-bold">
                                {ac.shock_percentage}%
                              </td>
                              <td className="px-4 py-2.5 text-right text-slate-300">{ac.baseline_weight_pct}%</td>
                              <td className="px-4 py-2.5 text-right font-bold text-cyan-300">
                                {ac.stressed_weight_pct}%
                              </td>
                              <td className="px-4 py-2.5 text-right text-slate-400">
                                {formatCurrency(ac.absolute_change)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Holdings Breakdown Table */}
              <Card className="overflow-hidden">
                <CardHeader>
                  <CardTitle className="text-base text-white">Granular Holdings Stress Impact</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs text-left">
                      <thead className="bg-[#0A0F1D] text-slate-400 border-b border-[#202D45] uppercase tracking-wider font-semibold">
                        <tr>
                          <th className="px-4 py-2.5">Symbol / Name</th>
                          <th className="px-4 py-2.5">Asset Class</th>
                          <th className="px-4 py-2.5 text-right">Base Value</th>
                          <th className="px-4 py-2.5 text-right">Shock %</th>
                          <th className="px-4 py-2.5 text-right">Stressed Value</th>
                          <th className="px-4 py-2.5 text-right">Impact</th>
                          <th className="px-4 py-2.5 text-right">Loss Share</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#202D45] font-mono">
                        {stressResult.holdings_breakdown.map((h, idx) => (
                          <tr key={idx} className="hover:bg-[#162032]/30">
                            <td className="px-4 py-2.5 font-bold text-white font-sans">
                              {h.symbol}
                              <span className="block text-[10px] text-slate-400 font-normal">{h.asset_name}</span>
                            </td>
                            <td className="px-4 py-2.5 capitalize text-slate-300 font-sans">{h.asset_class.replace("_", " ")}</td>
                            <td className="px-4 py-2.5 text-right text-slate-300">{formatCurrency(h.baseline_value)}</td>
                            <td className="px-4 py-2.5 text-right text-rose-400 font-bold">
                              {h.shock_percentage}%
                            </td>
                            <td className="px-4 py-2.5 text-right font-bold text-white">
                              {formatCurrency(h.stressed_value)}
                            </td>
                            <td className="px-4 py-2.5 text-right text-rose-400">
                              {formatCurrency(h.absolute_change)}
                            </td>
                            <td className="px-4 py-2.5 text-right text-slate-300">
                              {h.contribution_to_loss_pct}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>

              {/* Warnings and Disclaimers */}
              {stressResult.warnings.length > 0 && (
                <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-500/30 space-y-1">
                  <div className="flex items-center gap-2 font-bold text-xs text-amber-300">
                    <AlertTriangle className="w-4 h-4" />
                    Data Quality Warnings
                  </div>
                  {stressResult.warnings.map((w, i) => (
                    <p key={i} className="text-xs text-amber-400">
                      • {w}
                    </p>
                  ))}
                </div>
              )}

              <div className="p-4 rounded-xl bg-[#0A0F1D] border border-[#202D45] text-xs text-slate-400 space-y-1">
                <p className="font-bold text-slate-300">Model Assumptions & Disclaimers:</p>
                <p>• {stressResult.assumptions.join(" • ")}</p>
                <p className="italic">Notice: {stressResult.disclaimers.join(" ")}</p>
              </div>
            </div>
          )}

          {!stressResult && !stressLoading && (
            <EmptyState
              title="No Stress Test Executed Yet"
              description="Choose a portfolio and scenario preset above and click 'Execute Stress Test' to analyze crisis resilience."
              action={
                <Button variant="primary" size="sm" onClick={handleRunStressTest}>
                  Run Default Stress Test
                </Button>
              }
            />
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 2: HISTORICAL BACKTESTING                                         */}
      {/* ==================================================================== */}
      {activeTab === "backtest" && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base text-white flex items-center gap-2">
                <History className="w-4 h-4 text-cyan-400" />
                Configure Historical Backtest
              </CardTitle>
              <CardDescription className="text-xs text-slate-400">
                Replay historical asset allocations without look-ahead bias, applying periodic rebalancing and turnover fees.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
                    Portfolio
                  </label>
                  <select
                    value={btPortfolioId}
                    onChange={(e) => setBtPortfolioId(e.target.value)}
                    className="w-full h-10 px-3 rounded-lg border border-[#202D45] bg-[#0E1524] text-white font-medium focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  >
                    {portfolios.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                    {portfolios.length === 0 && <option value="">No Portfolios Available</option>}
                  </select>
                </div>

                <div>
                  <Input
                    label="Starting Capital (₹)"
                    type="number"
                    value={btInitialVal}
                    onChange={(e) => setBtInitialVal(e.target.value)}
                    placeholder="100000"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
                    Rebalance Schedule
                  </label>
                  <select
                    value={btRebalFreq}
                    onChange={(e) => setBtRebalFreq(e.target.value)}
                    className="w-full h-10 px-3 rounded-lg border border-[#202D45] bg-[#0E1524] text-white font-medium focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  >
                    <option value="monthly">Monthly Rebalancing</option>
                    <option value="quarterly">Quarterly Rebalancing</option>
                    <option value="annual">Annual Rebalancing</option>
                    <option value="drift_5pct">Drift Threshold (&gt; 5%)</option>
                    <option value="none">Buy &amp; Hold (No Rebalancing)</option>
                  </select>
                </div>

                <div>
                  <Input
                    label="Turnover Fee (bps)"
                    type="number"
                    value={btFeeBps}
                    onChange={(e) => setBtFeeBps(e.target.value)}
                    placeholder="10"
                  />
                </div>
              </div>

              <div className="mt-4 flex justify-end">
                <Button
                  onClick={handleRunBacktest}
                  disabled={btLoading || portfolios.length === 0}
                  variant="primary"
                  size="md"
                >
                  {btLoading ? (
                    <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                  ) : (
                    <History className="w-4 h-4 mr-2" />
                  )}
                  Run Historical Backtest
                </Button>
              </div>

              {btError && (
                <div className="mt-4 p-3 rounded-xl bg-rose-950/40 border border-rose-500/30 flex items-center gap-2.5 text-rose-300 text-xs">
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
                  <span>{btError}</span>
                </div>
              )}
            </CardContent>
          </Card>

          {btResult && (
            <div className="space-y-6 animate-fadeIn">
              {/* Backtest Metric Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
                <MetricCard
                  title="Cumulative Return"
                  value={formatPercentage(btResult.cumulative_return_pct)}
                  subtitle={`From ${btResult.start_date} to ${btResult.end_date}`}
                  variant={parseFloat(btResult.cumulative_return_pct) >= 0 ? "success" : "danger"}
                />
                <MetricCard
                  title="CAGR"
                  value={formatPercentage(btResult.annualized_return_cagr_pct)}
                  subtitle="Compound annual growth"
                  variant="cyan"
                />
                <MetricCard
                  title="Annualized Volatility"
                  value={formatPercentage(btResult.annualized_volatility_pct)}
                  subtitle="Trading standard deviation"
                  variant="warning"
                />
                <MetricCard
                  title="Max Drawdown"
                  value={formatPercentage(btResult.max_drawdown_pct)}
                  subtitle="Peak-to-trough contraction"
                  variant="danger"
                />
                <MetricCard
                  title="Sharpe Ratio"
                  value={btResult.sharpe_ratio}
                  subtitle={`Calmar: ${btResult.calmar_ratio}`}
                  variant="success"
                />
              </div>

              {/* Equity Curve Chart */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base text-white flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <LineChartIcon className="w-4 h-4 text-cyan-400" />
                      Backtest Equity Curve
                    </span>
                    <Badge variant="cyan" className="font-mono text-xs">
                      {btResult.trading_days} Trading Days
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={btResult.equity_curve} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
                        <defs>
                          <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.35} />
                            <stop offset="95%" stopColor="#06B6D4" stopOpacity={0.0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#202D45" />
                        <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#94a3b8" }} />
                        <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} domain={["auto", "auto"]} />
                        <Tooltip
                          formatter={(val: any, name: any) => [
                            name === "portfolio_value" ? formatCurrency(val) : `${val}%`,
                            name === "portfolio_value" ? "Portfolio Value" : "Drawdown",
                          ]}
                          contentStyle={{ backgroundColor: "#0E1524", borderColor: "#202D45", borderRadius: 8, color: "#fff", fontSize: 12 }}
                        />
                        <Area
                          type="monotone"
                          dataKey="portfolio_value"
                          stroke="#06B6D4"
                          strokeWidth={2.5}
                          fillOpacity={1}
                          fill="url(#equityGrad)"
                          name="portfolio_value"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Rebalance Events Table */}
              {btResult.rebalance_events.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base text-white flex items-center justify-between">
                      <span>Rebalancing Events Log</span>
                      <Badge variant="cyan" className="font-mono text-xs">
                        {btResult.rebalance_count} Executions • {formatCurrency(btResult.total_transaction_costs)} Total Fees
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    <div className="overflow-x-auto max-h-60">
                      <table className="w-full text-xs text-left">
                        <thead className="bg-[#0A0F1D] text-slate-400 border-b border-[#202D45] uppercase tracking-wider font-semibold">
                          <tr>
                            <th className="px-4 py-2.5">Date</th>
                            <th className="px-4 py-2.5 text-right">Pre-Rebalance Value</th>
                            <th className="px-4 py-2.5 text-right">Turnover</th>
                            <th className="px-4 py-2.5 text-right">Fees Incurred</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#202D45] font-mono">
                          {btResult.rebalance_events.map((ev, i) => (
                            <tr key={i} className="hover:bg-[#162032]/30">
                              <td className="px-4 py-2.5 text-slate-300">{ev.date}</td>
                              <td className="px-4 py-2.5 text-right text-slate-300">{formatCurrency(ev.portfolio_value_pre)}</td>
                              <td className="px-4 py-2.5 text-right text-slate-300">{formatCurrency(ev.turnover_value)}</td>
                              <td className="px-4 py-2.5 text-right text-rose-400 font-bold">
                                {formatCurrency(ev.transaction_cost)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {!btResult && !btLoading && (
            <EmptyState
              title="No Backtest Run Yet"
              description="Configure portfolio backtest parameters above and click 'Run Historical Backtest' to view historical performance."
              action={
                <Button variant="primary" size="sm" onClick={handleRunBacktest}>
                  Run Backtest
                </Button>
              }
            />
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 3: MONTE CARLO WEALTH SIMULATION                                  */}
      {/* ==================================================================== */}
      {activeTab === "monte_carlo" && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-cyan-400" />
                Configure Monte Carlo Stochastic Projection
              </CardTitle>
              <CardDescription className="text-xs text-slate-400">
                Generate thousands of Geometric Brownian Motion paths to estimate terminal wealth distributions and goal probabilities.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                <div>
                  <Input
                    label="Initial Capital (₹)"
                    type="number"
                    value={mcInitialVal}
                    onChange={(e) => setMcInitialVal(e.target.value)}
                    placeholder="100000"
                  />
                </div>

                <div>
                  <Input
                    label="Monthly SIP (₹)"
                    type="number"
                    value={mcMonthlySip}
                    onChange={(e) => setMcMonthlySip(e.target.value)}
                    placeholder="10000"
                  />
                </div>

                <div>
                  <Input
                    label="Horizon (Years)"
                    type="number"
                    value={mcHorizonYears}
                    onChange={(e) => setMcHorizonYears(e.target.value)}
                    placeholder="10"
                    min="1"
                    max="30"
                  />
                </div>

                <div>
                  <Input
                    label="Target Goal Amount (₹)"
                    type="number"
                    value={mcTargetAmt}
                    onChange={(e) => setMcTargetAmt(e.target.value)}
                    placeholder="3000000"
                  />
                </div>

                <div>
                  <Input
                    label="Expected Return (% p.a.)"
                    type="number"
                    value={mcExpectedRet}
                    onChange={(e) => setMcExpectedRet(e.target.value)}
                    placeholder="12"
                  />
                </div>

                <div>
                  <Input
                    label="Annual Volatility (%)"
                    type="number"
                    value={mcVolatility}
                    onChange={(e) => setMcVolatility(e.target.value)}
                    placeholder="15"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
                    Simulation Count
                  </label>
                  <select
                    value={mcSimCount}
                    onChange={(e) => setMcSimCount(e.target.value)}
                    className="w-full h-10 px-3 rounded-lg border border-[#202D45] bg-[#0E1524] text-white font-medium focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  >
                    <option value="500">500 Trajectories (Fast)</option>
                    <option value="1000">1,000 Trajectories (Recommended)</option>
                    <option value="2000">2,000 Trajectories (High Precision)</option>
                  </select>
                </div>

                <div className="flex items-end">
                  <Button
                    onClick={handleRunMonteCarlo}
                    disabled={mcLoading}
                    variant="primary"
                    className="w-full h-10"
                  >
                    {mcLoading ? (
                      <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                    ) : (
                      <Sparkles className="w-4 h-4 mr-2" />
                    )}
                    Run Stochastic Simulation
                  </Button>
                </div>
              </div>

              {mcError && (
                <div className="mt-4 p-3 rounded-xl bg-rose-950/40 border border-rose-500/30 flex items-center gap-2.5 text-rose-300 text-xs">
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
                  <span>{mcError}</span>
                </div>
              )}
            </CardContent>
          </Card>

          {mcResult && (
            <div className="space-y-6 animate-fadeIn">
              {/* Monte Carlo Summary Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <MetricCard
                  title="Median Projected Wealth"
                  value={formatCurrency(mcResult.terminal_wealth.median)}
                  subtitle={`50th percentile at Year ${mcHorizonYears}`}
                  icon={<Coins className="w-4 h-4" />}
                  variant="cyan"
                />
                <MetricCard
                  title="Conservative Floor (P5)"
                  value={formatCurrency(mcResult.terminal_wealth.p5)}
                  subtitle="95% probability of exceeding"
                  icon={<TrendingDown className="w-4 h-4" />}
                  variant="warning"
                />
                <MetricCard
                  title="Optimistic Ceiling (P95)"
                  value={formatCurrency(mcResult.terminal_wealth.p95)}
                  subtitle="Top 5th percentile outcome"
                  icon={<TrendingUp className="w-4 h-4" />}
                  variant="success"
                />
                {Boolean(mcResult.goal_success_probability_pct) && (
                  <MetricCard
                    title="Goal Success Probability"
                    value={formatPercentage(mcResult.goal_success_probability_pct)}
                    subtitle={`Target: ${formatCurrency(mcResult.target_amount)}`}
                    icon={<CheckCircle2 className="w-4 h-4" />}
                    variant={
                      parseFloat(mcResult.goal_success_probability_pct || "0") >= 75
                        ? "success"
                        : parseFloat(mcResult.goal_success_probability_pct || "0") >= 50
                        ? "warning"
                        : "danger"
                    }
                  />
                )}
              </div>

              {/* Percentile Trajectory Fan Chart */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base text-white flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <LineChartIcon className="w-4 h-4 text-cyan-400" />
                      Wealth Percentile Fan Chart (P5 • P25 • P50 • P75 • P95)
                    </span>
                    <Badge variant="cyan" className="text-xs font-mono">
                      {mcResult.num_simulations} Simulated Paths
                    </Badge>
                  </CardTitle>
                  <CardDescription className="text-xs text-slate-400">
                    Probability cones over time. The solid cyan line indicates median projected wealth.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={mcResult.percentile_trajectory} margin={{ top: 10, right: 10, left: 20, bottom: 20 }}>
                        <defs>
                          <linearGradient id="p95p5Grad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.25} />
                            <stop offset="95%" stopColor="#06B6D4" stopOpacity={0.02} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#202D45" />
                        <XAxis dataKey="year" tick={{ fontSize: 10, fill: "#94a3b8" }} label={{ value: "Horizon (Years)", position: "insideBottom", offset: -10, fontSize: 11, fill: "#64748b" }} />
                        <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} tickFormatter={(v) => `₹${(v / 100000).toFixed(0)}L`} />
                        <Tooltip
                          formatter={(val: any, name: any) => [formatCurrency(val), name.toUpperCase()]}
                          contentStyle={{ backgroundColor: "#0E1524", borderColor: "#202D45", borderRadius: 8, color: "#fff", fontSize: 12 }}
                        />
                        <Area type="monotone" dataKey="p95" stroke="#38BDF8" strokeWidth={1} fill="url(#p95p5Grad)" name="p95" />
                        <Area type="monotone" dataKey="p75" stroke="#22D3EE" strokeWidth={1.5} fill="#06B6D4" fillOpacity={0.15} name="p75" />
                        <Area type="monotone" dataKey="p50" stroke="#06B6D4" strokeWidth={3} fill="#06B6D4" fillOpacity={0.1} name="p50 (Median)" />
                        <Area type="monotone" dataKey="p25" stroke="#14B8A6" strokeWidth={1.5} fill="#14B8A6" fillOpacity={0.1} name="p25" />
                        <Area type="monotone" dataKey="p5" stroke="#F43F5E" strokeWidth={1.5} fill="none" name="p5 (Floor)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Terminal Distribution Stats Grid */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base text-white">Terminal Wealth Distribution Statistics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3 text-center">
                    <div className="p-3 rounded-xl bg-[#0A0F1D] border border-[#202D45]">
                      <p className="text-[10px] font-bold text-slate-400 uppercase">Mean</p>
                      <p className="text-xs font-mono font-bold mt-1 text-white">
                        {formatCurrency(mcResult.terminal_wealth.mean)}
                      </p>
                    </div>
                    <div className="p-3 rounded-xl bg-[#0A0F1D] border border-cyan-500/30">
                      <p className="text-[10px] font-bold text-cyan-400 uppercase">Median</p>
                      <p className="text-xs font-mono font-bold mt-1 text-cyan-300">
                        {formatCurrency(mcResult.terminal_wealth.median)}
                      </p>
                    </div>
                    <div className="p-3 rounded-xl bg-[#0A0F1D] border border-[#202D45]">
                      <p className="text-[10px] font-bold text-slate-400 uppercase">Std Deviation</p>
                      <p className="text-xs font-mono font-bold mt-1 text-slate-300">
                        {formatCurrency(mcResult.terminal_wealth.std_dev)}
                      </p>
                    </div>
                    <div className="p-3 rounded-xl bg-[#0A0F1D] border border-rose-500/30">
                      <p className="text-[10px] font-bold text-rose-400 uppercase">P5 Floor</p>
                      <p className="text-xs font-mono font-bold mt-1 text-rose-400">
                        {formatCurrency(mcResult.terminal_wealth.p5)}
                      </p>
                    </div>
                    <div className="p-3 rounded-xl bg-[#0A0F1D] border border-emerald-500/30">
                      <p className="text-[10px] font-bold text-emerald-400 uppercase">P95 Ceiling</p>
                      <p className="text-xs font-mono font-bold mt-1 text-emerald-400">
                        {formatCurrency(mcResult.terminal_wealth.p95)}
                      </p>
                    </div>
                    <div className="p-3 rounded-xl bg-[#0A0F1D] border border-[#202D45]">
                      <p className="text-[10px] font-bold text-slate-400 uppercase">Sim Min</p>
                      <p className="text-xs font-mono font-bold mt-1 text-slate-400">
                        {formatCurrency(mcResult.terminal_wealth.min)}
                      </p>
                    </div>
                    <div className="p-3 rounded-xl bg-[#0A0F1D] border border-[#202D45]">
                      <p className="text-[10px] font-bold text-slate-400 uppercase">Sim Max</p>
                      <p className="text-xs font-mono font-bold mt-1 text-slate-300">
                        {formatCurrency(mcResult.terminal_wealth.max)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {!mcResult && !mcLoading && (
            <EmptyState
              title="No Monte Carlo Simulation Run Yet"
              description="Adjust capital, monthly SIP, and horizon parameters above and click 'Run Stochastic Simulation' to preview probabilistic wealth distributions."
              action={
                <Button variant="primary" size="sm" onClick={handleRunMonteCarlo}>
                  Run 10-Year Simulation
                </Button>
              }
            />
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 4: GOAL MULTI-SCENARIO COMPARISON                                */}
      {/* ==================================================================== */}
      {activeTab === "scenarios" && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-cyan-400" />
                Select Goal for Scenario Trade-Off Analysis
              </CardTitle>
              <CardDescription className="text-xs text-slate-400">
                Compare higher contributions, extended deadlines, and return variations against your baseline goal without altering persisted records.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col sm:flex-row gap-4 items-end text-xs">
                <div className="flex-1">
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
                    Select Persisted Investment Goal
                  </label>
                  <select
                    value={selectedGoalId}
                    onChange={(e) => setSelectedGoalId(e.target.value)}
                    className="w-full h-10 px-3 rounded-lg border border-[#202D45] bg-[#0E1524] text-white font-medium focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  >
                    {goals.map((g) => (
                      <option key={g.id} value={g.id}>
                        {g.name} (Target: {formatCurrency(g.target_amount)})
                      </option>
                    ))}
                    {goals.length === 0 && <option value="">Sample Goal: ₹25 Lakhs Corpus</option>}
                  </select>
                </div>

                <Button
                  onClick={handleRunGoalComparison}
                  disabled={scLoading}
                  variant="primary"
                  className="h-10 px-6 font-semibold text-xs"
                >
                  {scLoading ? (
                    <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                  ) : (
                    <Layers className="w-4 h-4 mr-2" />
                  )}
                  Compare What-If Scenarios
                </Button>
              </div>

              {scError && (
                <div className="mt-4 p-3 rounded-xl bg-rose-950/40 border border-rose-500/30 flex items-center gap-2.5 text-rose-300 text-xs">
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
                  <span>{scError}</span>
                </div>
              )}
            </CardContent>
          </Card>

          {scResult && (
            <div className="space-y-6 animate-fadeIn">
              {/* Recommendation Callout Banner */}
              {scResult.insights.length > 0 && (
                <div className="p-4 rounded-xl bg-cyan-950/30 border border-cyan-500/30 space-y-2">
                  <div className="flex items-center gap-2 font-bold text-xs text-cyan-200">
                    <Sparkles className="w-4 h-4 text-cyan-400" />
                    Analytical Insights &amp; Recommendation
                  </div>
                  {scResult.insights.map((ins, i) => (
                    <p key={i} className="text-xs text-cyan-300/90">
                      • {ins}
                    </p>
                  ))}
                </div>
              )}

              {/* Side-by-Side Comparison Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {/* Baseline Card */}
                <Card className="border-2 border-[#202D45] bg-[#0A0F1D]">
                  <CardHeader className="pb-3">
                    <Badge variant="outline" className="w-fit text-[10px] font-bold">
                      BASELINE
                    </Badge>
                    <CardTitle className="text-base font-bold text-white mt-1">{scResult.baseline.name}</CardTitle>
                    <CardDescription className="text-xs text-slate-400 font-mono">
                      {scResult.baseline.horizon_months}m • {formatPercentage(scResult.baseline.expected_annual_return_pct)} p.a.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3 pt-0 text-xs">
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-semibold">Monthly SIP</span>
                      <span className="text-base font-mono font-bold text-white">
                        {formatCurrency(scResult.baseline.monthly_contribution)}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-semibold">Deterministic FV</span>
                      <span className="text-xs font-mono font-semibold text-slate-300">
                        {formatCurrency(scResult.baseline.deterministic_projected_value)}
                      </span>
                    </div>
                    <div className="pt-2 border-t border-[#202D45]">
                      <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-semibold">Goal Success Odds</span>
                      <span className="text-lg font-mono font-extrabold text-cyan-400">
                        {formatPercentage(scResult.baseline.mc_goal_success_probability_pct)}
                      </span>
                    </div>
                  </CardContent>
                </Card>

                {/* Scenario Variants */}
                {scResult.compared_scenarios.map((sc, idx) => (
                  <Card
                    key={idx}
                    className="border border-cyan-500/30 hover:border-cyan-400 transition-colors"
                  >
                    <CardHeader className="pb-3">
                      <Badge variant="cyan" className="w-fit text-[10px] font-bold">
                        VARIANT {idx + 1}
                      </Badge>
                      <CardTitle className="text-base font-bold text-white mt-1">
                        {sc.name}
                      </CardTitle>
                      <CardDescription className="text-xs text-slate-400 font-mono">
                        {sc.horizon_months}m • {formatPercentage(sc.expected_annual_return_pct)} p.a.
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3 pt-0 text-xs">
                      <div>
                        <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-semibold">Monthly SIP</span>
                        <div className="flex items-center gap-1.5">
                          <span className="text-base font-mono font-bold text-white">
                            {formatCurrency(sc.monthly_contribution)}
                          </span>
                          {parseFloat(sc.contribution_delta_from_baseline) !== 0 && (
                            <span className="text-[10px] font-mono font-bold text-cyan-400">
                              ({formatCurrency(sc.contribution_delta_from_baseline, "INR", { showPlusSign: true })})
                            </span>
                          )}
                        </div>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-semibold">Deterministic FV</span>
                        <span className="text-xs font-mono font-semibold text-slate-300">
                          {formatCurrency(sc.deterministic_projected_value)}
                        </span>
                      </div>
                      <div className="pt-2 border-t border-[#202D45]">
                        <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-semibold">Goal Success Odds</span>
                        <div className="flex items-center gap-1.5">
                          <span className="text-lg font-mono font-extrabold text-emerald-400">
                            {formatPercentage(sc.mc_goal_success_probability_pct)}
                          </span>
                          {parseFloat(sc.success_probability_delta_pct) > 0 && (
                            <span className="text-xs font-mono font-bold text-emerald-400">
                              (+{sc.success_probability_delta_pct}%)
                            </span>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Detailed Comparison Table */}
              <Card className="overflow-hidden">
                <CardHeader>
                  <CardTitle className="text-base text-white">Comprehensive Scenario Matrix</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs text-left">
                      <thead className="bg-[#0A0F1D] text-slate-400 border-b border-[#202D45] uppercase tracking-wider font-semibold">
                        <tr>
                          <th className="px-4 py-2.5">Scenario</th>
                          <th className="px-4 py-2.5 text-right">Monthly SIP</th>
                          <th className="px-4 py-2.5 text-right">Horizon</th>
                          <th className="px-4 py-2.5 text-right">Deterministic FV</th>
                          <th className="px-4 py-2.5 text-right">MC Median FV</th>
                          <th className="px-4 py-2.5 text-right">P5 (Downside)</th>
                          <th className="px-4 py-2.5 text-right">P95 (Upside)</th>
                          <th className="px-4 py-2.5 text-right">Success Odds</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#202D45] font-mono">
                        <tr className="bg-[#0A0F1D]/50 font-bold">
                          <td className="px-4 py-2.5 text-cyan-400 font-sans">{scResult.baseline.name} (Base)</td>
                          <td className="px-4 py-2.5 text-right">{formatCurrency(scResult.baseline.monthly_contribution)}</td>
                          <td className="px-4 py-2.5 text-right">{scResult.baseline.horizon_months}m</td>
                          <td className="px-4 py-2.5 text-right">{formatCurrency(scResult.baseline.deterministic_projected_value)}</td>
                          <td className="px-4 py-2.5 text-right">{formatCurrency(scResult.baseline.mc_median_projected_value)}</td>
                          <td className="px-4 py-2.5 text-right text-rose-400">{formatCurrency(scResult.baseline.mc_p5_downside_value)}</td>
                          <td className="px-4 py-2.5 text-right text-emerald-400">{formatCurrency(scResult.baseline.mc_p95_upside_value)}</td>
                          <td className="px-4 py-2.5 text-right text-cyan-400">{formatPercentage(scResult.baseline.mc_goal_success_probability_pct)}</td>
                        </tr>
                        {scResult.compared_scenarios.map((sc, i) => (
                          <tr key={i} className="hover:bg-[#162032]/30">
                            <td className="px-4 py-2.5 font-bold text-white font-sans">{sc.name}</td>
                            <td className="px-4 py-2.5 text-right font-bold text-cyan-300">{formatCurrency(sc.monthly_contribution)}</td>
                            <td className="px-4 py-2.5 text-right">{sc.horizon_months}m</td>
                            <td className="px-4 py-2.5 text-right">{formatCurrency(sc.deterministic_projected_value)}</td>
                            <td className="px-4 py-2.5 text-right">{formatCurrency(sc.mc_median_projected_value)}</td>
                            <td className="px-4 py-2.5 text-right text-rose-400">{formatCurrency(sc.mc_p5_downside_value)}</td>
                            <td className="px-4 py-2.5 text-right text-emerald-400">{formatCurrency(sc.mc_p95_upside_value)}</td>
                            <td className="px-4 py-2.5 text-right font-bold text-emerald-400">{formatPercentage(sc.mc_goal_success_probability_pct)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {!scResult && !scLoading && (
            <EmptyState
              title="No Goal Scenarios Compared Yet"
              description="Choose a goal and click 'Compare What-If Scenarios' to analyze trade-offs between higher contributions and extended time horizons."
              action={
                <Button variant="primary" size="sm" onClick={handleRunGoalComparison}>
                  Compare Sample Goal Scenarios
                </Button>
              }
            />
          )}
        </div>
      )}
    </div>
  );
}
