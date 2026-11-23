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
import {
  EmergencyFundAnalysis,
  FinancialSummary,
  Portfolio,
  PortfolioValuation,
  Transaction,
} from "@/types";

export default function OverviewPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [summary, setSummary] = useState<FinancialSummary | null>(null);
  const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([]);
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [valuation, setValuation] = useState<PortfolioValuation | null>(null);
  const [allocationData, setAllocationData] = useState<any[]>([]);
  const [emergencyFund, setEmergencyFund] = useState<EmergencyFundAnalysis | null>(null);
  const [newsRelevance, setNewsRelevance] = useState<any[]>([]);
  const [liquidityWarning, setLiquidityWarning] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
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
          if (allocRes.status === "fulfilled" && allocRes.value.allocations) {
            setAllocationData(
              allocRes.value.allocations.map((a) => ({
                name: a.asset_class,
                asset_class: a.asset_class,
                value: parseFloat(a.actual_weight) * 100,
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

      // 4. Portfolio News
      try {
        const relRes = await newsApi.getPortfolioRelevance({ min_confidence: 0.65 });
        setNewsRelevance(relRes.matches || []);
      } catch {}
    } catch (err: any) {
      setError(err?.message || "Failed to load dashboard overview.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return <LoadingState message="Aggregating verified financial metrics..." />;
  }

  return (
    <div className="space-y-8">
      {/* Page Title & Context */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl lg:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
            Financial Overview
          </h1>
          <p className="text-base text-slate-500 dark:text-slate-400 mt-1.5 font-medium">
            Unified executive snapshot: cash flow, net worth, risk runway, and market themes.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/assistant">
            <Button variant="primary" size="md" className="gap-2 shadow-md shadow-indigo-600/20">
              <Sparkles className="w-4 h-4" />
              <span>Ask Financial AI</span>
            </Button>
          </Link>
        </div>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {liquidityWarning && (
        <div className="p-4 rounded-2xl bg-amber-50/80 border border-amber-200/90 text-amber-900 flex items-start gap-3 shadow-xs">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="text-sm">
            <strong className="font-bold block">Cash-Flow Liquidity Alert:</strong>
            <p className="mt-0.5">{liquidityWarning}</p>
          </div>
        </div>
      )}

      {/* Top 4 Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Portfolio Value"
          value={valuation ? formatCurrency(valuation.total_value, valuation.currency) : "—"}
          subtitle={
            valuation
              ? `Unrealized: ${formatCurrency(valuation.unrealized_gain_loss, valuation.currency, { showPlusSign: true })} (${formatPercentage(valuation.unrealized_gain_loss_percentage, { showPlusSign: true })})`
              : "No active portfolios valued"
          }
          icon={<Briefcase className="w-6 h-6" />}
          variant="brand"
        />

        <MetricCard
          title="Monthly Cash Inflow"
          value={summary ? formatCurrency(summary.total_income, "INR") : "—"}
          subtitle={
            summary
              ? `Net Savings: ${formatCurrency(summary.net_savings, "INR")} (${formatPercentage(summary.savings_rate_percentage)})`
              : "No monthly inflows recorded"
          }
          icon={<TrendingUp className="w-6 h-6" />}
          variant="success"
        />

        <MetricCard
          title="Monthly Outflow"
          value={summary ? formatCurrency(summary.total_expenses, "INR") : "—"}
          subtitle={summary ? `Transactions: ${summary.transaction_count} items` : "No transaction ledger entries"}
          icon={<TrendingDown className="w-6 h-6" />}
          variant="danger"
        />

        <MetricCard
          title="Emergency Fund Runway"
          value={
            emergencyFund?.months_of_coverage
              ? `${parseFloat(emergencyFund.months_of_coverage).toFixed(1)} mo`
              : emergencyFund?.current_coverage_months
              ? `${parseFloat(emergencyFund.current_coverage_months).toFixed(1)} mo`
              : "—"
          }
          subtitle={
            emergencyFund?.months_of_coverage
              ? `Target: 6.0 mo (${parseFloat(emergencyFund.months_of_coverage) >= 6 ? "SECURED" : "INSUFFICIENT"})`
              : emergencyFund?.balance_status === "unknown"
              ? "Emergency balance not set"
              : emergencyFund?.status
              ? `Status: ${String(emergencyFund.status).toUpperCase()}`
              : "Baseline profile unconfigured"
          }
          icon={<ShieldCheck className="w-6 h-6" />}
          variant={
            parseFloat(emergencyFund?.months_of_coverage || emergencyFund?.current_coverage_months || "0") >= 6
              ? "success"
              : "warning"
          }
        />
      </div>

      {/* Mid Section: Allocation Donut & Relevant News */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Asset Allocation Card */}
        <Card className="lg:col-span-1 flex flex-col">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Asset Allocation</CardTitle>
              <Link href="/portfolio" className="text-sm text-indigo-600 hover:text-indigo-800 font-bold hover:underline">
                View Details
              </Link>
            </div>
            <CardDescription>Primary portfolio asset distribution</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col justify-center">
            <AllocationDonutChart data={allocationData} height={280} />
          </CardContent>
        </Card>

        {/* Portfolio Relevant News */}
        <Card className="lg:col-span-2 flex flex-col">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Market Intelligence & FinBERT Insights</CardTitle>
                <CardDescription>Recent articles contextually matched to your portfolio holdings</CardDescription>
              </div>
              <Link href="/news" className="text-sm text-indigo-600 hover:text-indigo-800 font-bold hover:underline flex items-center gap-1.5">
                <span>All Headlines</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </CardHeader>
          <CardContent className="flex-1">
            {newsRelevance.length === 0 ? (
              <div className="py-12 text-center text-sm text-slate-400 font-medium">
                No recent news articles matched to your holdings. Ingest feeds on the Market News page.
              </div>
            ) : (
              <div className="space-y-3.5">
                {newsRelevance.slice(0, 3).map((item, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-2xl border border-slate-100 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/50 hover:bg-slate-100/70 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                  >
                    <div className="space-y-1.5 flex-1 min-w-0">
                      <div className="flex items-center gap-2.5 flex-wrap">
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
                        <span className="text-xs font-bold text-indigo-700 dark:text-indigo-400 bg-indigo-50 px-2.5 py-0.5 rounded-md">
                          {item.matched_entity}
                        </span>
                        {item.source_name && (
                          <span className="text-xs text-slate-500 font-medium">
                            {item.source_name}
                          </span>
                        )}
                      </div>
                      <a
                        href={item.canonical_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm font-bold text-slate-900 dark:text-slate-100 hover:text-indigo-600 dark:hover:text-indigo-400 line-clamp-1 block"
                      >
                        {item.article_title}
                      </a>
                    </div>
                    {item.published_at && (
                      <span className="text-xs text-slate-400 font-medium shrink-0">
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

      {/* Bottom Section: Recent Transactions Table */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <CardTitle>Recent Transactions</CardTitle>
              <CardDescription>Latest financial inflows and outflows verified by ledger</CardDescription>
            </div>
            <Link href="/transactions">
              <Button variant="outline" size="sm" className="gap-2 text-sm font-semibold">
                <Receipt className="w-4 h-4" />
                <span>Manage Transactions</span>
              </Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {recentTransactions.length === 0 ? (
            <div className="py-12 text-center text-sm text-slate-400 font-medium">
              No transactions recorded. Import CSV or add a transaction to track cash flow.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-slate-50/80 dark:bg-slate-800/60 text-slate-500 uppercase tracking-wider text-xs font-bold border-y border-slate-100">
                  <tr>
                    <th className="py-3.5 px-6">Date</th>
                    <th className="py-3.5 px-6">Description</th>
                    <th className="py-3.5 px-6">Category</th>
                    <th className="py-3.5 px-6 text-right">Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {recentTransactions.map((tx) => (
                    <tr key={tx.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="py-4 px-6 text-slate-500 font-medium">{formatDate(tx.date)}</td>
                      <td className="py-4 px-6 font-semibold text-slate-900 dark:text-slate-100">
                        {tx.description}
                      </td>
                      <td className="py-4 px-6">
                        <Badge variant="default">{tx.category}</Badge>
                      </td>
                      <td
                        className={`py-4 px-6 text-right font-bold text-base ${
                          tx.transaction_type === "income"
                            ? "text-emerald-600 dark:text-emerald-400"
                            : "text-slate-900 dark:text-slate-100"
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
