"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  TrendingUp,
  TrendingDown,
  ShieldCheck,
  Briefcase,
  AlertTriangle,
  ArrowRight,
  Receipt,
  Sparkles,
  Sliders,
  Activity,
  Target,
  Plus,
  ArrowUpRight,
  ChevronRight,
  RefreshCw,
  Zap,
} from "lucide-react";
import { MetricCard } from "@/components/shared/MetricCard";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { AllocationDonutChart } from "@/components/charts/AllocationDonutChart";
import { LoadingState, ErrorBanner, RegulatoryDisclaimer } from "@/components/shared/States";
import { formatCurrency, formatDate, formatPercentage } from "@/lib/formatters";
import { transactionsApi } from "@/lib/api/transactions";
import { portfolioApi } from "@/lib/api/portfolio";
import { analysisApi } from "@/lib/api/analysis";
import { newsApi } from "@/lib/api/news";
import { goalsApi } from "@/lib/api/goals";
import {
  EmergencyFundAnalysis,
  FinancialSummary,
  Portfolio,
  PortfolioValuation,
  Transaction,
  InvestmentGoal,
} from "@/types";

export default function OverviewPage() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [summary, setSummary] = useState<FinancialSummary | null>(null);
  const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([]);
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [valuation, setValuation] = useState<PortfolioValuation | null>(null);
  const [allocationData, setAllocationData] = useState<any[]>([]);
  const [emergencyFund, setEmergencyFund] = useState<EmergencyFundAnalysis | null>(null);
  const [newsRelevance, setNewsRelevance] = useState<any[]>([]);
  const [goals, setGoals] = useState<InvestmentGoal[]>([]);
  const [liquidityWarning, setLiquidityWarning] = useState<string | null>(null);

  const fetchData = async (isManualRefresh = false) => {
    if (isManualRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      // 1. Transactions & Financial Summary
      const [sumRes, txListRes] = await Promise.allSettled([
        transactionsApi.getFinancialSummary(),
        transactionsApi.listTransactions({ limit: 5 }),
      ]);

      if (sumRes.status === "fulfilled") setSummary(sumRes.value);
      if (txListRes.status === "fulfilled") {
        const val = txListRes.value;
        const items = Array.isArray(val) ? val : (val?.items || []);
        setRecentTransactions(items.slice(0, 5));
      }

      // 2. Portfolios & Valuation
      try {
        const portList = await portfolioApi.listPortfolios();
        setPortfolios(portList || []);
        if (portList && portList.length > 0) {
          const primaryPort = portList[0];
          const [valRes, allocRes] = await Promise.allSettled([
            portfolioApi.getPortfolioValuation(primaryPort.id),
            portfolioApi.getPortfolioAllocation(primaryPort.id),
          ]);
          if (valRes.status === "fulfilled") setValuation(valRes.value);
          if (allocRes.status === "fulfilled" && allocRes.value.allocations && allocRes.value.allocations.length > 0) {
            setAllocationData(
              allocRes.value.allocations.map((a) => ({
                name: a.asset_class,
                asset_class: a.asset_class,
                value: parseFloat(a.actual_weight) * 100,
              }))
            );
          } else if (valRes.status === "fulfilled" && (valRes.value as any)?.asset_class_breakdown) {
            setAllocationData(
              (valRes.value as any).asset_class_breakdown.map((b: any) => ({
                name: b.asset_class,
                asset_class: b.asset_class,
                value: parseFloat(b.allocation_percentage) || 0,
              }))
            );
          }
        }
      } catch {}

      // 3. Emergency Fund & Cash Flow Warning
      try {
        const [efRes, cfRes] = await Promise.allSettled([
          analysisApi.getEmergencyFundAnalysis(),
          analysisApi.getCashFlowForecast(30),
        ]);
        if (efRes.status === "fulfilled") setEmergencyFund(efRes.value);
        if (cfRes.status === "fulfilled") setLiquidityWarning(cfRes.value.liquidity_warning || null);
      } catch {}

      // 4. Portfolio News Relevance
      try {
        const relRes = await newsApi.getPortfolioRelevance({ min_confidence: 0.65 });
        setNewsRelevance(relRes.matches || []);
      } catch {}

      // 5. Active Goals
      try {
        const goalsList = await goalsApi.listGoals();
        setGoals(Array.isArray(goalsList) ? goalsList.slice(0, 3) : []);
      } catch {}
    } catch (err: any) {
      setError(err?.message || "Failed to load dashboard overview.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return <LoadingState message="Aggregating fintech telemetry & multi-asset valuation..." />;
  }

  const totalPortfolioValueNum = valuation ? parseFloat(valuation.total_value) || 0 : 0;
  const monthlyInflowNum = summary ? parseFloat(summary.total_income) || 0 : 0;
  const monthlyOutflowNum = summary ? parseFloat(summary.total_expenses) || 0 : 0;
  const netSavingsNum = summary ? parseFloat(summary.net_savings) || 0 : 0;

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in">
      {/* Executive Command Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#1A263D]">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
              Executive Overview
            </h1>
            <Badge variant="info" className="hidden sm:inline-flex">
              Real-time Ingest
            </Badge>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 font-medium">
            Command Center: unified portfolio valuation, liquidity velocity, and risk parameters.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchData(true)}
            disabled={refreshing}
            className="text-xs gap-1.5 border-[#202D45] text-slate-300 hover:text-white"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-cyan-400" : ""}`} />
            <span>Refresh</span>
          </Button>

          <Link href="/transactions">
            <Button variant="secondary" size="sm" className="text-xs gap-1.5">
              <Plus className="w-3.5 h-3.5 text-cyan-400" />
              <span>Record Txn</span>
            </Button>
          </Link>

          <Link href="/assistant">
            <Button variant="primary" size="sm" className="text-xs gap-1.5 shadow-md shadow-cyan-950/40">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Ask AI Copilot</span>
            </Button>
          </Link>
        </div>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {liquidityWarning && (
        <div className="p-4 rounded-2xl bg-amber-950/30 border border-amber-800/70 text-amber-200 flex items-start gap-3 shadow-sm animate-fade-in">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-xs sm:text-sm">
            <strong className="font-bold text-amber-300 block">Cash-Flow Liquidity Warning:</strong>
            <p className="mt-0.5 leading-relaxed text-amber-200/90">{liquidityWarning}</p>
          </div>
        </div>
      )}

      {/* Hero Financial Command Bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-gradient-to-br from-[#121A2B] via-[#101726] to-[#0D1422] p-5 sm:p-6 rounded-3xl border border-[#22324E] shadow-xl relative overflow-hidden">
        <div className="space-y-1.5 md:border-r border-[#1C273C] md:pr-6">
          <span className="text-[10px] font-bold tracking-wider uppercase text-cyan-400 flex items-center gap-1.5">
            <Briefcase className="w-3.5 h-3.5" />
            <span>Active Portfolio Valuation</span>
          </span>
          <div className="text-2xl sm:text-3xl font-black tracking-tight text-white font-mono">
            {valuation ? formatCurrency(valuation.total_value, valuation.currency) : "₹0.00"}
          </div>
          <div className="flex items-center gap-2 pt-0.5 text-xs text-slate-400">
            {valuation && (
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-0.5 ${
                  parseFloat(valuation.unrealized_gain_loss || "0") >= 0
                    ? "bg-emerald-950/70 text-emerald-400 border border-emerald-800/80"
                    : "bg-rose-950/70 text-rose-400 border border-rose-800/80"
                }`}
              >
                {formatCurrency(valuation.unrealized_gain_loss, valuation.currency, { showPlusSign: true })}
                {" ("}
                {formatPercentage(valuation.unrealized_gain_loss_percentage, { showPlusSign: true })}
                {")"}
              </span>
            )}
            <span className="text-[11px] truncate">
              {portfolios.length > 0 ? portfolios[0].name : "Primary Portfolio"}
            </span>
          </div>
        </div>

        <div className="space-y-1.5 md:border-r border-[#1C273C] md:px-6">
          <span className="text-[10px] font-bold tracking-wider uppercase text-teal-400 flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>Net Monthly Velocity</span>
          </span>
          <div className={`text-2xl sm:text-3xl font-black tracking-tight font-mono ${
            netSavingsNum >= 0 ? "text-emerald-400" : "text-rose-400"
          }`}>
            {summary ? formatCurrency(summary.net_savings, "INR", { showPlusSign: true }) : "₹0.00"}
          </div>
          <div className="flex items-center gap-2 pt-0.5 text-xs text-slate-400">
            <span className="text-[10px] font-bold bg-[#172235] text-cyan-300 border border-[#273855] px-2 py-0.5 rounded-full">
              Savings Rate: {summary ? formatPercentage(summary.savings_rate_percentage) : "0%"}
            </span>
            <span className="text-[11px] text-slate-400">Inflow minus outflows</span>
          </div>
        </div>

        <div className="space-y-1.5 md:pl-6">
          <span className="text-[10px] font-bold tracking-wider uppercase text-emerald-400 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Emergency Coverage Runway</span>
          </span>
          <div className="text-2xl sm:text-3xl font-black tracking-tight text-white font-mono">
            {emergencyFund?.months_of_coverage
              ? `${parseFloat(emergencyFund.months_of_coverage).toFixed(1)} mo`
              : emergencyFund?.current_coverage_months
              ? `${parseFloat(emergencyFund.current_coverage_months).toFixed(1)} mo`
              : "0.0 mo"}
          </div>
          <div className="flex items-center gap-2 pt-0.5 text-xs">
            <Badge
              variant={
                parseFloat(emergencyFund?.months_of_coverage || emergencyFund?.current_coverage_months || "0") >= 6
                  ? "success"
                  : "warning"
              }
            >
              {parseFloat(emergencyFund?.months_of_coverage || emergencyFund?.current_coverage_months || "0") >= 6
                ? "SECURED (6.0+ MO)"
                : "RESERVE ATTENTION"}
            </Badge>
            <Link href="/emergency-fund" className="text-[11px] text-cyan-400 hover:underline">
              Analyze Reserve →
            </Link>
          </div>
        </div>
      </div>

      {/* Top 4 Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
        <MetricCard
          title="Total Portfolio Value"
          value={valuation ? formatCurrency(valuation.total_value, valuation.currency) : "—"}
          subtitle={
            valuation
              ? `Unrealized: ${formatCurrency(valuation.unrealized_gain_loss, valuation.currency, { showPlusSign: true })}`
              : "No active positions valued"
          }
          icon={<Briefcase className="w-5 h-5 text-cyan-400" />}
          variant="brand"
        />

        <MetricCard
          title="Monthly Cash Inflow"
          value={summary ? formatCurrency(summary.total_income, "INR") : "—"}
          subtitle={
            summary
              ? `Net Savings: ${formatCurrency(summary.net_savings, "INR")}`
              : "No monthly inflows recorded"
          }
          icon={<TrendingUp className="w-5 h-5 text-emerald-400" />}
          variant="success"
        />

        <MetricCard
          title="Monthly Outflow"
          value={summary ? formatCurrency(summary.total_expenses, "INR") : "—"}
          subtitle={summary ? `Transactions: ${summary.transaction_count} records` : "No transaction ledger entries"}
          icon={<TrendingDown className="w-5 h-5 text-rose-400" />}
          variant="danger"
        />

        <MetricCard
          title="Emergency Runway"
          value={
            emergencyFund?.months_of_coverage
              ? `${parseFloat(emergencyFund.months_of_coverage).toFixed(1)} mo`
              : emergencyFund?.current_coverage_months
              ? `${parseFloat(emergencyFund.current_coverage_months).toFixed(1)} mo`
              : "—"
          }
          subtitle={
            emergencyFund?.months_of_coverage
              ? `Target: 6.0 mo (${parseFloat(emergencyFund.months_of_coverage) >= 6 ? "SECURED" : "ATTENTION"})`
              : "Baseline profile unconfigured"
          }
          icon={<ShieldCheck className="w-5 h-5 text-amber-400" />}
          variant={
            parseFloat(emergencyFund?.months_of_coverage || emergencyFund?.current_coverage_months || "0") >= 6
              ? "success"
              : "warning"
          }
        />
      </div>

      {/* Quick Launchpad & Quantitative Command Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Link href="/portfolio" className="p-3.5 rounded-2xl bg-[#111827] border border-[#202D45] hover:border-cyan-500/50 hover:bg-[#152033] transition-all group flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-cyan-950/60 text-cyan-400 border border-cyan-800/60">
              <Briefcase className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-white group-hover:text-cyan-300">Positions</div>
              <div className="text-[10px] text-slate-400">Holdings & Prices</div>
            </div>
          </div>
          <ArrowUpRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-cyan-400 transition-transform group-hover:translate-x-0.5" />
        </Link>

        <Link href="/optimization" className="p-3.5 rounded-2xl bg-[#111827] border border-[#202D45] hover:border-cyan-500/50 hover:bg-[#152033] transition-all group flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-teal-950/60 text-teal-400 border border-teal-800/60">
              <Sliders className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-white group-hover:text-teal-300">MPT Optimizer</div>
              <div className="text-[10px] text-slate-400">Sharpe & Min Variance</div>
            </div>
          </div>
          <ArrowUpRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-teal-400 transition-transform group-hover:translate-x-0.5" />
        </Link>

        <Link href="/simulations" className="p-3.5 rounded-2xl bg-[#111827] border border-[#202D45] hover:border-cyan-500/50 hover:bg-[#152033] transition-all group flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-purple-950/60 text-purple-400 border border-purple-800/60">
              <Activity className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-white group-hover:text-purple-300">Stress & MC</div>
              <div className="text-[10px] text-slate-400">Monte Carlo Sim</div>
            </div>
          </div>
          <ArrowUpRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-purple-400 transition-transform group-hover:translate-x-0.5" />
        </Link>

        <Link href="/assistant" className="p-3.5 rounded-2xl bg-[#111827] border border-[#202D45] hover:border-cyan-500/50 hover:bg-[#152033] transition-all group flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-cyan-500 to-teal-500 text-slate-950 font-bold">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-white group-hover:text-cyan-300">AI Copilot</div>
              <div className="text-[10px] text-slate-400">Grounded Reasoning</div>
            </div>
          </div>
          <ArrowUpRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-cyan-400 transition-transform group-hover:translate-x-0.5" />
        </Link>
      </div>

      {/* Mid Section: Allocation Donut & FinBERT Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Asset Allocation Card */}
        <Card className="lg:col-span-1 flex flex-col">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Asset Allocation</CardTitle>
              <Link href="/portfolio" className="text-xs text-cyan-400 hover:text-cyan-300 font-bold hover:underline inline-flex items-center gap-1">
                <span>View Details</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
            <CardDescription>Primary portfolio weight distribution by asset class</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col justify-center">
            <AllocationDonutChart data={allocationData} height={280} />
          </CardContent>
        </Card>

        {/* Portfolio Relevant News & FinBERT Insights */}
        <Card className="lg:col-span-2 flex flex-col">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Market Intelligence & FinBERT Sentiment</CardTitle>
                <CardDescription>Live RSS feeds scored with Transformer sentiment matched to your holdings</CardDescription>
              </div>
              <Link href="/news" className="text-xs text-cyan-400 hover:text-cyan-300 font-bold hover:underline flex items-center gap-1">
                <span>All Headlines</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </CardHeader>
          <CardContent className="flex-1">
            {newsRelevance.length === 0 ? (
              <div className="py-12 text-center text-xs text-slate-400 font-medium">
                No recent news articles matched to your holdings. Ingest feeds on the Market News page.
              </div>
            ) : (
              <div className="space-y-3">
                {newsRelevance.slice(0, 3).map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 sm:p-4 rounded-xl border border-[#1E2B42] bg-[#0E1523]/70 hover:bg-[#141E30] transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 group"
                  >
                    <div className="space-y-1.5 flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge
                          variant={
                            item.sentiment_label === "positive"
                              ? "success"
                              : item.sentiment_label === "negative"
                              ? "danger"
                              : "default"
                          }
                        >
                          {item.sentiment_label ? item.sentiment_label.toUpperCase() : "NEUTRAL"}
                        </Badge>
                        <span className="text-[11px] font-bold text-cyan-300 bg-cyan-950/70 border border-cyan-800/80 px-2 py-0.5 rounded-md">
                          {item.matched_entity}
                        </span>
                        {item.source_name && (
                          <span className="text-[11px] text-slate-400 font-medium">
                            {item.source_name}
                          </span>
                        )}
                      </div>
                      <a
                        href={item.canonical_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs sm:text-sm font-bold text-white group-hover:text-cyan-300 line-clamp-1 block transition-colors"
                      >
                        {item.article_title}
                      </a>
                    </div>
                    {item.published_at && (
                      <span className="text-[11px] text-slate-400 font-mono shrink-0">
                        {formatDate(item.published_at)}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Active Financial Goals Preview Strip (if any goals exist) */}
      {goals.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Financial Goals & Milestone Progress</CardTitle>
                <CardDescription>Target horizons, active accumulations, and planned contributions</CardDescription>
              </div>
              <Link href="/goals" className="text-xs text-cyan-400 hover:text-cyan-300 font-bold hover:underline flex items-center gap-1">
                <span>All Goals</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </CardHeader>
          <CardContent className="p-4 sm:p-6">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {goals.map((g) => {
                const targetAmt = parseFloat(g.target_amount) || 1;
                const currentAmt = parseFloat(g.current_amount || "0") || 0;
                const progressPct = Math.min(100, Math.round((currentAmt / targetAmt) * 100));

                return (
                  <div key={g.id} className="p-4 rounded-xl border border-[#202D45] bg-[#0E1524] space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white truncate max-w-[150px]">{g.name}</span>
                      <span className="text-[11px] font-mono text-cyan-400 font-bold">{progressPct}%</span>
                    </div>
                    <div className="w-full bg-[#182336] h-2 rounded-full overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-cyan-400 to-teal-400 h-full rounded-full transition-all"
                        style={{ width: `${progressPct}%` }}
                      />
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
                      <span>{formatCurrency(currentAmt, "INR")}</span>
                      <span>Target: {formatCurrency(targetAmt, "INR")}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Bottom Section: Recent Verified Transactions Table */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <CardTitle>Recent Ledger Transactions</CardTitle>
              <CardDescription>Latest financial inflows and outflows verified by the double-entry store</CardDescription>
            </div>
            <Link href="/transactions">
              <Button variant="outline" size="sm" className="text-xs font-semibold gap-1.5 border-[#202D45] text-slate-300 hover:text-white">
                <Receipt className="w-3.5 h-3.5 text-cyan-400" />
                <span>Open Transaction Ledger</span>
              </Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {recentTransactions.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-400 font-medium">
              No transactions recorded in the ledger. Import a CSV statement or add entries to track cash flow.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs sm:text-sm text-left">
                <thead className="bg-[#0C121F] text-slate-400 uppercase tracking-wider text-[11px] font-bold border-y border-[#1C273C]">
                  <tr>
                    <th className="py-3 px-5 sm:px-6">Date</th>
                    <th className="py-3 px-5 sm:px-6">Description</th>
                    <th className="py-3 px-5 sm:px-6">Category</th>
                    <th className="py-3 px-5 sm:px-6 text-right">Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1C273C]">
                  {recentTransactions.map((tx) => (
                    <tr key={tx.id} className="hover:bg-[#141C2C]/50 transition-colors">
                      <td className="py-3.5 px-5 sm:px-6 text-slate-400 font-mono text-xs">{formatDate(tx.date)}</td>
                      <td className="py-3.5 px-5 sm:px-6 font-semibold text-white">
                        {tx.description}
                      </td>
                      <td className="py-3.5 px-5 sm:px-6">
                        <Badge variant="default">{tx.category}</Badge>
                      </td>
                      <td
                        className={`py-3.5 px-5 sm:px-6 text-right font-bold text-xs sm:text-sm font-mono ${
                          tx.transaction_type === "income"
                            ? "text-emerald-400"
                            : "text-slate-100"
                        }`}
                      >
                        {tx.transaction_type === "income" ? "+" : "-"}
                        {formatCurrency(tx.amount, "INR")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <RegulatoryDisclaimer />
    </div>
  );
}
