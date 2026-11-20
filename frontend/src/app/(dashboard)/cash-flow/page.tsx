"use client";

import React, { useEffect, useState } from "react";
import {
  TrendingUp,
  AlertTriangle,
  Calendar,
  ArrowDownRight,
  ArrowUpRight,
  Info,
} from "lucide-react";
import { MetricCard } from "@/components/shared/MetricCard";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { CashFlowForecastChart } from "@/components/charts/CashFlowForecastChart";
import { LoadingState, ErrorBanner, WarningBanner, RegulatoryDisclaimer } from "@/components/shared/States";
import { formatCurrency, formatDate } from "@/lib/formatters";
import { analysisApi } from "@/lib/api/analysis";
import { CashFlowForecast } from "@/types";

export default function CashFlowPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [forecast, setForecast] = useState<CashFlowForecast | null>(null);

  const fetchForecast = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await analysisApi.getCashFlowForecast(30);
      setForecast(data);
    } catch (err: any) {
      setError(err?.message || "Failed to load 30-day cash flow forecast.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchForecast();
  }, []);

  if (loading) {
    return <LoadingState message="Generating deterministic cash flow forecast..." />;
  }

  const startingBalance = parseFloat(forecast?.opening_balance || forecast?.starting_balance || "0");
  const endingBalance = parseFloat(forecast?.projected_closing_balance || forecast?.projected_ending_balance || "0");
  const minBalance = parseFloat(forecast?.projected_minimum_balance || "0");
  const netFlow = endingBalance - startingBalance;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl lg:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
          30-Day Cash Flow Forecast
        </h1>
        <p className="text-base text-slate-500 dark:text-slate-400 mt-1.5 font-medium">
          Deterministic projection of liquidity, estimated daily inflows, and recurring outflows
        </p>
      </div>

      {error && <ErrorBanner message={error} onRetry={fetchForecast} />}

      {/* Liquidity Alert if present */}
      {forecast?.liquidity_warning && (
        <WarningBanner message={`Forecast Alert: ${forecast.liquidity_warning}`} />
      )}

      {/* Top 4 Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Starting Balance"
          value={formatCurrency(forecast?.opening_balance || forecast?.starting_balance, "INR")}
          subtitle="Baseline liquid cash balance"
          icon={<Calendar className="w-5 h-5" />}
          variant="default"
        />

        <MetricCard
          title="Projected Ending Balance"
          value={formatCurrency(forecast?.projected_closing_balance || forecast?.projected_ending_balance, "INR")}
          subtitle={`Net change: ${formatCurrency(netFlow, "INR", { showPlusSign: true })}`}
          icon={netFlow >= 0 ? <ArrowUpRight className="w-5 h-5" /> : <ArrowDownRight className="w-5 h-5" />}
          variant={netFlow >= 0 ? "success" : "danger"}
        />

        <MetricCard
          title="Projected Minimum"
          value={formatCurrency(forecast?.projected_minimum_balance || "0", "INR")}
          subtitle={`Lowest date: ${forecast?.lowest_projected_date ? formatDate(forecast.lowest_projected_date) : "—"}`}
          icon={<AlertTriangle className="w-5 h-5" />}
          variant={minBalance < 0 ? "danger" : "default"}
        />

        <MetricCard
          title="Forecast Horizon"
          value={`${forecast?.forecast_days || 30} Days`}
          subtitle="Daily projection granularity"
          icon={<TrendingUp className="w-5 h-5" />}
          variant="brand"
        />
      </div>

      {/* Main Chart Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-bold">Projected Liquid Balance Over Next 30 Days</CardTitle>
          <CardDescription className="text-sm">
            Estimated balance trajectory based on historical cash flow frequency
          </CardDescription>
        </CardHeader>
        <CardContent>
          <CashFlowForecastChart
            data={forecast?.daily_forecasts || forecast?.daily_projections || []}
            height={360}
            currency="INR"
          />
        </CardContent>
      </Card>

      {/* Forecast Assumptions Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2.5">
            <Info className="w-5 h-5 text-indigo-600" />
            <CardTitle className="text-base font-bold">Model Assumptions & Notes</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-400 list-disc list-inside font-medium">
            {forecast?.assumptions && forecast.assumptions.length > 0 ? (
              forecast.assumptions.map((asm, idx) => <li key={idx}>{asm}</li>)
            ) : (
              <>
                <li>Projections are computed deterministically from categorized transaction histories.</li>
                <li>Recurring monthly income and bill cycles are modeled based on recorded transaction dates.</li>
                <li>Unscheduled discretionary expenses are not predicted and may alter actual ending balances.</li>
              </>
            )}
          </ul>
        </CardContent>
      </Card>

      <RegulatoryDisclaimer text="Projections are analytical estimates based on past transaction timing, not guaranteed balances. Actual cash flow depends on future timing of deposits and withdrawals." />
    </div>
  );
}
