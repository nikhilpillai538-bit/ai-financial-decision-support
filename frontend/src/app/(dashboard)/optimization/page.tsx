"use client";

import React, { useEffect, useState, useMemo } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import {
  LoadingState,
  EmptyState,
  ErrorBanner,
  RegulatoryDisclaimer,
} from "@/components/shared/States";
import { MetricCard } from "@/components/shared/MetricCard";
import { DriftComparisonBarChart } from "@/components/charts/DriftComparisonBarChart";
import { portfolioApi } from "@/lib/api/portfolio";
import {
  optimizationApi,
  OptimizePortfolioPayload,
  MarketPreset,
} from "@/lib/api/optimization";
import { goalsApi } from "@/lib/api/goals";
import {
  Portfolio,
  OptimizationResult,
  PortfolioDrift,
  MarketDataSummary,
} from "@/types";
import { formatCurrency, formatPercentage, formatDate } from "@/lib/formatters";
import {
  TrendingUp,
  Percent,
  Play,
  History,
  Upload,
  RefreshCw,
  Sliders,
  Scale,
  ArrowRight,
  Zap,
  Sparkles,
  CheckCircle2,
} from "lucide-react";

export default function OptimizationPage() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<string>("");
  const [marketData, setMarketData] = useState<MarketDataSummary | null>(null);

  // Optimization Form State
  const [objective, setObjective] = useState<"max_sharpe" | "min_volatility" | "target_return">("max_sharpe");
  const [targetReturn, setTargetReturn] = useState("0.12");
  const [riskFreeRate, setRiskFreeRate] = useState("0.06");
  const [minWeight, setMinWeight] = useState("0.00");
  const [maxWeight, setMaxWeight] = useState("1.00");

  // Output States
  const [optimizationResult, setOptimizationResult] = useState<OptimizationResult | null>(null);
  const [history, setHistory] = useState<OptimizationResult[]>([]);
  const [drift, setDrift] = useState<PortfolioDrift | null>(null);

  // UI States
  const [isLoadingPortfolios, setIsLoadingPortfolios] = useState(true);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [isLoadingDrift, setIsLoadingDrift] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  // Yahoo Finance Auto-Fetch States
  const [modalTab, setModalTab] = useState<"yfinance" | "csv">("yfinance");
  const [yfinanceSymbols, setYfinanceSymbols] = useState("RELIANCE.NS, TCS.NS, HDFCBANK.NS, INFY.NS, ICICIBANK.NS");
  const [yfinancePeriod, setYfinancePeriod] = useState("1y");
  const [isFetchingYahoo, setIsFetchingYahoo] = useState(false);
  const [yahooFetchSuccess, setYahooFetchSuccess] = useState<string | null>(null);
  const [presets, setPresets] = useState<MarketPreset[]>([]);

  // Load initial data
  useEffect(() => {
    loadInitialData();
  }, []);

  // When portfolio changes, load history & drift
  useEffect(() => {
    if (selectedPortfolioId) {
      loadPortfolioDetails(selectedPortfolioId);
    } else {
      setOptimizationResult(null);
      setHistory([]);
      setDrift(null);
    }
  }, [selectedPortfolioId]);

  async function loadInitialData() {
    setIsLoadingPortfolios(true);
    setError(null);
    try {
      const [ports, md, presetList] = await Promise.all([
        portfolioApi.listPortfolios().catch(() => []),
        optimizationApi.getMarketDataSummary().catch(() => null),
        optimizationApi.getMarketPresets().catch(() => []),
      ]);
      const validPorts = Array.isArray(ports) ? ports : [];
      setPortfolios(validPorts);
      setMarketData(md);
      if (Array.isArray(presetList) && presetList.length > 0) {
        setPresets(presetList);
      }
      if (validPorts.length > 0) {
        setSelectedPortfolioId(validPorts[0].id);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load portfolios or market data");
    } finally {
      setIsLoadingPortfolios(false);
    }
  }

  async function loadPortfolioDetails(portfolioId: string) {
    if (!portfolioId) return;
    setIsLoadingDrift(true);
    try {
      const [hist, driftData] = await Promise.all([
        optimizationApi.getOptimizationHistory(portfolioId).catch(() => []),
        goalsApi.getPortfolioDrift(portfolioId, 5.0).catch(() => null),
      ]);
      const validHist = Array.isArray(hist) ? hist : [];
      setHistory(validHist);
      setDrift(driftData);
      if (validHist.length > 0) {
        setOptimizationResult(validHist[0]);
      } else {
        setOptimizationResult(null);
      }
    } catch (err: any) {
      console.error("Error loading portfolio details:", err);
    } finally {
      setIsLoadingDrift(false);
    }
  }

  async function handleRunOptimization(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedPortfolioId) return;

    setIsOptimizing(true);
    setError(null);

    const payload: OptimizePortfolioPayload = {
      objective,
      risk_free_rate: riskFreeRate,
      min_weight: minWeight,
      max_weight: maxWeight,
    };
    if (objective === "target_return") {
      payload.target_return = targetReturn;
    }

    try {
      const res = await optimizationApi.optimizePortfolio(selectedPortfolioId, payload);
      setOptimizationResult(res);
      // Reload history and drift
      const hist = await optimizationApi.getOptimizationHistory(selectedPortfolioId).catch(() => []);
      setHistory(Array.isArray(hist) ? hist : []);
      const updatedDrift = await goalsApi.getPortfolioDrift(selectedPortfolioId, 5.0).catch(() => null);
      setDrift(updatedDrift);
    } catch (err: any) {
      setError(err?.message || "Optimization solver encountered an error. Check if assets have historical price data.");
    } finally {
      setIsOptimizing(false);
    }
  }

  async function handleUploadMarketData(e: React.FormEvent) {
    e.preventDefault();
    if (!uploadFile) return;

    setIsUploading(true);
    setError(null);
    setUploadSuccess(null);
    try {
      const res = await optimizationApi.uploadMarketDataCSV(uploadFile);
      setUploadSuccess(`Uploaded market data successfully. Ingested ${res?.rows_inserted || res?.imported || "records"}.`);
      setUploadFile(null);
      const updatedMd = await optimizationApi.getMarketDataSummary().catch(() => null);
      setMarketData(updatedMd);
      setTimeout(() => setShowUploadModal(false), 1500);
    } catch (err: any) {
      setError(err?.message || "Failed to upload market data CSV");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleFetchYahooMarketData(e: React.FormEvent) {
    e.preventDefault();
    const symbolsList = yfinanceSymbols
      .split(/[\s,]+/)
      .map((s) => s.trim().toUpperCase())
      .filter(Boolean);

    if (symbolsList.length === 0) {
      setError("Please enter at least one valid stock or ETF symbol.");
      return;
    }

    setIsFetchingYahoo(true);
    setError(null);
    setYahooFetchSuccess(null);

    try {
      const res = await optimizationApi.fetchYahooHistorical({
        symbols: symbolsList,
        period: yfinancePeriod,
        portfolio_id: selectedPortfolioId || undefined,
      });

      let msg = `Successfully fetched ${res.symbols_successful.length} symbol(s) (${res.imported_rows} price points imported, ${res.skipped_rows} existing observations).`;
      if (res.symbols_failed && res.symbols_failed.length > 0) {
        msg += ` Warning: ${res.symbols_failed.join(", ")} could not be retrieved.`;
      }
      setYahooFetchSuccess(msg);

      const updatedMd = await optimizationApi.getMarketDataSummary().catch(() => null);
      setMarketData(updatedMd);
    } catch (err: any) {
      setError(err?.message || "Failed to fetch market data from Yahoo Finance.");
    } finally {
      setIsFetchingYahoo(false);
    }
  }

  // Robust derivations to prevent any undefined crashes across backend schema variations
  const resolvedWeights: Record<string, number> = useMemo(() => {
    if (!optimizationResult) return {};
    const res: Record<string, number> = {};
    if (optimizationResult.weights && typeof optimizationResult.weights === "object") {
      Object.entries(optimizationResult.weights).forEach(([sym, w]) => {
        res[sym] = parseFloat(String(w)) || 0;
      });
    } else if (Array.isArray((optimizationResult as any).allocations)) {
      (optimizationResult as any).allocations.forEach((al: any) => {
        if (al.symbol) {
          res[al.symbol] = parseFloat(String(al.optimal_weight ?? al.weight ?? 0)) || 0;
        }
      });
    }
    return res;
  }, [optimizationResult]);

  const resolvedTrades = useMemo(() => {
    if (!optimizationResult) return [];
    if (optimizationResult.rebalancing_trades && optimizationResult.rebalancing_trades.length > 0) {
      return optimizationResult.rebalancing_trades;
    }
    if (Array.isArray((optimizationResult as any).allocations)) {
      return (optimizationResult as any).allocations
        .filter((al: any) => al.action && String(al.action).toUpperCase() !== "HOLD" && String(al.action).toLowerCase() !== "none")
        .map((al: any) => ({
          asset_symbol: al.symbol,
          action: String(al.action).toLowerCase() as "buy" | "sell" | "hold",
          units: String(al.target_shares || al.units || "—"),
          estimated_amount: String(al.trade_amount || al.estimated_amount || "0"),
        }));
    }
    return [];
  }, [optimizationResult]);

  const resolvedDriftItems = useMemo(() => {
    const rawList = drift?.drift_items || (drift as any)?.asset_classes || [];
    if (!Array.isArray(rawList)) return [];

    return rawList.map((it: any) => {
      const rawCurr = it.current_weight_percentage ?? it.current_weight ?? 0;
      const numCurr = typeof rawCurr === "number" ? rawCurr : parseFloat(rawCurr) || 0;
      const currPct = Math.abs(numCurr) <= 1 && numCurr !== 0 ? numCurr * 100 : numCurr;

      const rawTgt = it.target_weight_percentage ?? it.target_weight ?? 0;
      const numTgt = typeof rawTgt === "number" ? rawTgt : parseFloat(rawTgt) || 0;
      const tgtPct = Math.abs(numTgt) <= 1 && numTgt !== 0 ? numTgt * 100 : numTgt;

      const rawDrift = it.absolute_drift_percentage_points ?? it.drift ?? 0;
      const numDrift = typeof rawDrift === "number" ? rawDrift : parseFloat(rawDrift) || 0;
      const driftPct = Math.abs(numDrift) <= 1 && numDrift !== 0 ? numDrift * 100 : numDrift;

      let action = "HOLD";
      if (it.action) {
        action = String(it.action).toUpperCase();
      } else if (it.status) {
        if (it.status === "underweight") action = "BUY";
        else if (it.status === "overweight") action = "SELL";
        else action = "HOLD";
      }

      return {
        asset_class: it.asset_class || "Asset",
        current_weight: currPct,
        target_weight: tgtPct,
        drift: driftPct,
        action,
        status: it.status || "on_target",
        exceeds_threshold: Boolean(it.exceeds_threshold ?? (driftPct > 5)),
      };
    });
  }, [drift]);

  const isDriftBreached = Boolean(
    drift?.threshold_breached ??
    (drift as any)?.portfolio_exceeds_threshold ??
    resolvedDriftItems.some((it) => it.exceeds_threshold)
  );

  if (isLoadingPortfolios) {
    return <LoadingState message="Loading portfolio optimization engine..." />;
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl lg:text-4xl font-extrabold tracking-tight text-slate-900">
            Portfolio Optimization & MPT Engine
          </h1>
          <p className="text-base text-slate-500 mt-1.5 font-medium">
            Deterministic Modern Portfolio Theory solver, risk-adjusted returns, and drift analysis.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="primary"
            size="md"
            onClick={() => {
              setModalTab("yfinance");
              setShowUploadModal(true);
            }}
            className="gap-2 shadow-md shadow-indigo-600/20"
          >
            <Zap className="w-4 h-4 text-amber-300" />
            <span>Fetch Market Data</span>
          </Button>
          <Button
            variant="outline"
            size="md"
            onClick={() => selectedPortfolioId && loadPortfolioDetails(selectedPortfolioId)}
            disabled={!selectedPortfolioId}
          >
            <RefreshCw className="w-4 h-4 mr-1.5" />
            Refresh
          </Button>
        </div>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {/* Market Data Status Strip */}
      <Card className="bg-slate-50/80 border-dashed border-slate-300">
        <div className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 text-sm font-medium">
          <div className="flex items-center gap-3">
            <span className="font-semibold text-slate-700">Market Data Store:</span>
            {marketData ? (
              <span className="text-slate-600">
                <span className="font-medium text-slate-900">{marketData.symbols_count || 0}</span> symbols indexed (
                <span className="font-medium text-slate-900">{marketData.data_points_count || 0}</span> price observations)
                {marketData.date_range_start && (
                  <span className="text-slate-500 ml-1">
                    from {formatDate(marketData.date_range_start)} to {formatDate(marketData.date_range_end)}
                  </span>
                )}
              </span>
            ) : (
              <span className="text-amber-700 font-medium">
                No historical prices loaded. Upload price series to calculate covariance matrices.
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 text-slate-500">
            <span>Covariance Model: <strong className="text-slate-800">Ledoit-Wolf / Sample</strong></span>
            <span>•</span>
            <span>Risk-Free Benchmark: <strong className="text-slate-800">RBI 91D T-Bill ({(parseFloat(riskFreeRate || "0.06") * 100).toFixed(1)}%)</strong></span>
          </div>
        </div>
      </Card>

      {/* Portfolio Selector & Optimization Config */}
      {portfolios.length === 0 ? (
        <EmptyState
          title="No Portfolios Available"
          description="Create a portfolio and add asset holdings before running Modern Portfolio Theory optimization."
          actionLabel="Go to Portfolios"
          onAction={() => (window.location.href = "/portfolio")}
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Controls Column */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-indigo-600" />
                  Optimization Parameters
                </CardTitle>
                <CardDescription>
                  Configure mathematical objective and allocation bounds.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleRunOptimization} className="space-y-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 mb-1">
                      Target Portfolio
                    </label>
                    <select
                      value={selectedPortfolioId}
                      onChange={(e) => setSelectedPortfolioId(e.target.value)}
                      className="w-full text-sm rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      {portfolios.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name} ({p.base_currency || "INR"})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-700 mb-1">
                      Objective Function
                    </label>
                    <select
                      value={objective}
                      onChange={(e) => setObjective(e.target.value as any)}
                      className="w-full text-sm rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="max_sharpe">Maximize Sharpe Ratio (Tangency)</option>
                      <option value="min_volatility">Minimize Volatility (Global Minimum Variance)</option>
                      <option value="target_return">Target Expected Return</option>
                    </select>
                  </div>

                  {objective === "target_return" && (
                    <Input
                      label="Target Annual Return (e.g. 0.14 for 14%)"
                      type="number"
                      step="0.01"
                      min="0.01"
                      max="1.00"
                      value={targetReturn}
                      onChange={(e) => setTargetReturn(e.target.value)}
                      required
                    />
                  )}

                  <div className="grid grid-cols-2 gap-3">
                    <Input
                      label="Risk-Free Rate"
                      type="number"
                      step="0.005"
                      min="0.00"
                      max="0.20"
                      value={riskFreeRate}
                      onChange={(e) => setRiskFreeRate(e.target.value)}
                    />
                    <Input
                      label="Min Asset Weight"
                      type="number"
                      step="0.05"
                      min="0.00"
                      max="1.00"
                      value={minWeight}
                      onChange={(e) => setMinWeight(e.target.value)}
                    />
                  </div>

                  <Input
                    label="Max Asset Weight (Concentration Cap)"
                    type="number"
                    step="0.05"
                    min="0.10"
                    max="1.00"
                    value={maxWeight}
                    onChange={(e) => setMaxWeight(e.target.value)}
                  />

                  <Button
                    type="submit"
                    className="w-full"
                    isLoading={isOptimizing}
                    disabled={!selectedPortfolioId}
                  >
                    <Play className="w-4 h-4 mr-2" />
                    Solve Efficient Frontier
                  </Button>
                </form>
              </CardContent>
            </Card>

            {/* Optimization Run History */}
            <Card>
              <CardHeader className="py-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <History className="w-4 h-4 text-slate-500" />
                  Past Optimizations
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {history.length === 0 ? (
                  <div className="p-4 text-xs text-slate-500 text-center">
                    No previous optimization records for this portfolio.
                  </div>
                ) : (
                  <div className="divide-y divide-slate-100 max-h-64 overflow-y-auto">
                    {history.map((h: any, i: number) => {
                      const strat = String(h.strategy || h.objective || "Optimal Run").replace(/_/g, " ");
                      const expVol = h.expected_volatility ?? h.volatility;
                      const statusVal = h.solver_status || "optimal";
                      return (
                        <button
                          key={h.id || i}
                          type="button"
                          onClick={() => setOptimizationResult(h)}
                          className={`w-full text-left p-3 text-xs hover:bg-slate-50 flex items-center justify-between transition-colors ${
                            optimizationResult === h ? "bg-indigo-50/50 font-medium" : ""
                          }`}
                        >
                          <div>
                            <div className="font-semibold text-slate-800 capitalize">
                              {strat}
                            </div>
                            <div className="text-slate-500 mt-0.5">
                              Exp. Return: {formatPercentage(h.expected_return)} • Vol: {formatPercentage(expVol)}
                            </div>
                          </div>
                          <Badge
                            variant={statusVal === "optimal" ? "success" : "warning"}
                          >
                            {statusVal}
                          </Badge>
                        </button>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Results Column */}
          <div className="lg:col-span-2 space-y-6">
            {optimizationResult ? (
              <>
                {/* Key Metrics */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <MetricCard
                    title="Expected Annual Return"
                    value={formatPercentage(optimizationResult.expected_return)}
                    icon={<TrendingUp className="w-4 h-4 text-emerald-600" />}
                    subtitle={`Annualized (${String(optimizationResult.strategy || optimizationResult.objective || "Optimal").replace(/_/g, " ")})`}
                  />
                  <MetricCard
                    title="Annualized Volatility"
                    value={formatPercentage(optimizationResult.expected_volatility ?? optimizationResult.volatility)}
                    icon={<Percent className="w-4 h-4 text-amber-600" />}
                    subtitle="Standard deviation of returns"
                  />
                  <MetricCard
                    title="Sharpe Ratio"
                    value={
                      optimizationResult.sharpe_ratio !== undefined && optimizationResult.sharpe_ratio !== null
                        ? parseFloat(String(optimizationResult.sharpe_ratio)).toFixed(2)
                        : "—"
                    }
                    icon={<Scale className="w-4 h-4 text-blue-600" />}
                    subtitle={`Above Rf: ${(parseFloat(riskFreeRate || "0.06") * 100).toFixed(1)}%`}
                  />
                </div>

                {/* Optimal Weights Table */}
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-base">Optimal Asset Allocation Weights</CardTitle>
                        <CardDescription>
                          Mathematically solved asset weights satisfying all objective constraints.
                        </CardDescription>
                      </div>
                      <Badge variant={(optimizationResult.solver_status || "optimal") === "optimal" ? "success" : "info"}>
                        Status: {optimizationResult.solver_status || "Optimal"}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="p-0">
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs text-left">
                        <thead className="bg-slate-50 text-slate-500 border-y border-slate-200">
                          <tr>
                            <th className="px-4 py-2 font-medium">Asset Symbol</th>
                            <th className="px-4 py-2 font-medium text-right">Optimal Weight</th>
                            <th className="px-4 py-2 font-medium text-right">Visual Share</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {Object.keys(resolvedWeights).length === 0 ? (
                            <tr>
                              <td colSpan={3} className="px-4 py-4 text-center text-slate-400">
                                No asset weight breakdown available for this optimization.
                              </td>
                            </tr>
                          ) : (
                            Object.entries(resolvedWeights).map(([symbol, weight]) => {
                              const pct = weight * (Math.abs(weight) <= 1 && weight !== 0 ? 100 : 1);
                              return (
                                <tr key={symbol} className="hover:bg-slate-50/50">
                                  <td className="px-4 py-2.5 font-medium text-slate-900">
                                    {symbol}
                                  </td>
                                  <td className="px-4 py-2.5 text-right font-semibold text-slate-800">
                                    {pct.toFixed(2)}%
                                  </td>
                                  <td className="px-4 py-2.5 text-right w-48">
                                    <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                                      <div
                                        className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                                        style={{ width: `${Math.max(0, Math.min(pct, 100))}%` }}
                                      />
                                    </div>
                                  </td>
                                </tr>
                              );
                            })
                          )}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>

                {/* Rebalancing Trades */}
                {resolvedTrades.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Suggested Rebalancing Trades</CardTitle>
                      <CardDescription>
                        Deterministic adjustment trades required to bring current holdings into alignment.
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="overflow-x-auto">
                        <table className="w-full text-xs text-left">
                          <thead className="bg-slate-50 text-slate-500 border-y border-slate-200">
                            <tr>
                              <th className="px-4 py-2 font-medium">Asset</th>
                              <th className="px-4 py-2 font-medium">Action</th>
                              <th className="px-4 py-2 font-medium text-right">Units</th>
                              <th className="px-4 py-2 font-medium text-right">Est. Value</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                            {resolvedTrades.map((tr: any, idx: number) => {
                              const act = String(tr.action || "HOLD").toUpperCase();
                              return (
                                <tr key={idx} className="hover:bg-slate-50/50">
                                  <td className="px-4 py-2.5 font-medium text-slate-900">
                                    {tr.asset_symbol || tr.symbol}
                                  </td>
                                  <td className="px-4 py-2.5">
                                    <Badge
                                      variant={
                                        act === "BUY"
                                          ? "success"
                                          : act === "SELL"
                                          ? "danger"
                                          : "outline"
                                      }
                                    >
                                      {act}
                                    </Badge>
                                  </td>
                                  <td className="px-4 py-2.5 text-right font-medium text-slate-700">
                                    {tr.units}
                                  </td>
                                  <td className="px-4 py-2.5 text-right font-semibold text-slate-900">
                                    {formatCurrency(tr.estimated_amount)}
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Assumptions Card */}
                {optimizationResult.assumptions && optimizationResult.assumptions.length > 0 && (
                  <Card className="bg-slate-50">
                    <CardHeader className="py-3">
                      <CardTitle className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                        Solver Methodology & Assumptions
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="text-xs text-slate-600 space-y-1">
                      {optimizationResult.assumptions.map((ass, i) => (
                        <div key={i} className="flex items-start gap-2">
                          <ArrowRight className="w-3.5 h-3.5 text-slate-400 mt-0.5 shrink-0" />
                          <span>{ass}</span>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                )}
              </>
            ) : (
              <Card className="p-8 text-center border-dashed">
                <Sliders className="w-10 h-10 text-slate-400 mx-auto mb-3" />
                <h3 className="text-sm font-semibold text-slate-800 mb-1">
                  Ready to Optimize
                </h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto mb-4">
                  Select an objective in the left panel and click &ldquo;Solve Efficient Frontier&rdquo; to calculate the mathematical risk-return frontier.
                </p>
              </Card>
            )}

            {/* Drift Analysis Section */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base flex items-center gap-2">
                      <Scale className="w-4 h-4 text-indigo-600" />
                      Asset Allocation Drift Analysis
                    </CardTitle>
                    <CardDescription>
                      Comparison of current portfolio weights vs target baseline.
                    </CardDescription>
                  </div>
                  {drift && (
                    <Badge variant={isDriftBreached ? "danger" : "success"}>
                      {isDriftBreached ? "Drift Breach Detected" : "Within 5% Tolerance"}
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {isLoadingDrift ? (
                  <LoadingState message="Checking allocation drift against targets..." />
                ) : resolvedDriftItems.length > 0 ? (
                  <>
                    <DriftComparisonBarChart items={resolvedDriftItems as any} height={240} />
                    <div className="overflow-x-auto border-t border-slate-100 pt-3">
                      <table className="w-full text-xs text-left">
                        <thead className="text-slate-500">
                          <tr>
                            <th className="py-1">Asset Class</th>
                            <th className="py-1 text-right">Current</th>
                            <th className="py-1 text-right">Target</th>
                            <th className="py-1 text-right">Variance</th>
                            <th className="py-1 text-right">Action</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {resolvedDriftItems.map((it: any, idx: number) => (
                            <tr key={idx}>
                              <td className="py-2 font-medium text-slate-800 capitalize">
                                {it.asset_class}
                              </td>
                              <td className="py-2 text-right">
                                {formatPercentage(it.current_weight)}
                              </td>
                              <td className="py-2 text-right">
                                {formatPercentage(it.target_weight)}
                              </td>
                              <td
                                className={`py-2 text-right font-medium ${
                                  it.drift > 5 ? "text-rose-600" : "text-slate-600"
                                }`}
                              >
                                {formatPercentage(it.drift)}
                              </td>
                              <td className="py-2 text-right">
                                <Badge
                                  variant={
                                    it.action === "BUY"
                                      ? "success"
                                      : it.action === "SELL"
                                      ? "danger"
                                      : "outline"
                                  }
                                >
                                  {it.action}
                                </Badge>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-6 text-xs text-slate-500">
                    No target allocation set or holdings found for this portfolio. Set targets in Goals or Portfolios to evaluate drift.
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Market Data Modal */}
      <Modal
        isOpen={showUploadModal}
        onClose={() => {
          setShowUploadModal(false);
          setYahooFetchSuccess(null);
          setUploadSuccess(null);
        }}
        title="Historical Market Price Ingestion"
      >
        <div className="space-y-4">
          {/* Tab Selector */}
          <div className="flex border-b border-slate-200 dark:border-slate-800 pb-1">
            <button
              type="button"
              onClick={() => setModalTab("yfinance")}
              className={`pb-2.5 px-4 text-sm font-bold transition-all border-b-2 flex items-center gap-2 ${
                modalTab === "yfinance"
                  ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                  : "border-transparent text-slate-500 hover:text-slate-700"
              }`}
            >
              <Zap className="w-4 h-4 text-amber-500" />
              <span>Auto-Fetch (Yahoo Finance)</span>
            </button>
            <button
              type="button"
              onClick={() => setModalTab("csv")}
              className={`pb-2.5 px-4 text-sm font-bold transition-all border-b-2 flex items-center gap-2 ${
                modalTab === "csv"
                  ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                  : "border-transparent text-slate-500 hover:text-slate-700"
              }`}
            >
              <Upload className="w-4 h-4 text-slate-500" />
              <span>Upload CSV File</span>
            </button>
          </div>

          {modalTab === "yfinance" ? (
            <form onSubmit={handleFetchYahooMarketData} className="space-y-4">
              <div className="p-3 bg-indigo-50/70 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900/40 rounded-xl text-xs text-indigo-950 dark:text-indigo-200 flex items-start gap-2.5">
                <Sparkles className="w-4 h-4 text-indigo-600 dark:text-indigo-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold">Instant Market Ingestion:</span> Enter Indian stock tickers (e.g.,{" "}
                  <code className="bg-indigo-100/70 dark:bg-indigo-900/50 px-1 py-0.5 rounded font-mono font-bold">RELIANCE.NS</code>,{" "}
                  <code className="bg-indigo-100/70 dark:bg-indigo-900/50 px-1 py-0.5 rounded font-mono font-bold">TCS.NS</code>) or US stocks (
                  <code className="bg-indigo-100/70 dark:bg-indigo-900/50 px-1 py-0.5 rounded font-mono font-bold">AAPL</code>,{" "}
                  <code className="bg-indigo-100/70 dark:bg-indigo-900/50 px-1 py-0.5 rounded font-mono font-bold">NVDA</code>). Daily prices are downloaded and aligned for MPT optimization.
                </div>
              </div>

              {/* Presets */}
              {presets.length > 0 && (
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Quick Preset Groups:
                  </label>
                  <div className="flex flex-wrap gap-1.5">
                    {presets.map((p) => (
                      <button
                        key={p.id}
                        type="button"
                        onClick={() => setYfinanceSymbols(p.symbols.join(", "))}
                        className="px-2.5 py-1 text-xs font-medium rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-indigo-50 hover:text-indigo-600 transition-colors border border-slate-200/80 dark:border-slate-700"
                      >
                        {p.name}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Symbols Input */}
              <div className="space-y-1">
                <Input
                  label="Ticker Symbols (comma-separated)"
                  value={yfinanceSymbols}
                  onChange={(e) => setYfinanceSymbols(e.target.value)}
                  placeholder="e.g. RELIANCE.NS, TCS.NS, HDFCBANK.NS, AAPL"
                />
                <p className="text-[11px] text-slate-500">
                  Tip: Append <span className="font-mono font-bold">.NS</span> for NSE India stocks (e.g. INFOSYS is INFY.NS).
                </p>
              </div>

              {/* Period Select */}
              <div className="space-y-1">
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                  Historical Lookback Period
                </label>
                <select
                  value={yfinancePeriod}
                  onChange={(e) => setYfinancePeriod(e.target.value)}
                  className="w-full px-3 py-2 text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="1mo">1 Month</option>
                  <option value="3mo">3 Months</option>
                  <option value="6mo">6 Months</option>
                  <option value="1y">1 Year (Recommended for MPT)</option>
                  <option value="2y">2 Years</option>
                  <option value="5y">5 Years</option>
                </select>
              </div>

              {yahooFetchSuccess && (
                <div className="p-3 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-200 rounded-lg flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>{yahooFetchSuccess}</span>
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowUploadModal(false)}
                >
                  Close
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  variant="primary"
                  isLoading={isFetchingYahoo}
                  className="gap-1.5"
                >
                  <Zap className="w-3.5 h-3.5" />
                  <span>Fetch Market Data</span>
                </Button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleUploadMarketData} className="space-y-4">
              <p className="text-xs text-slate-600 dark:text-slate-400">
                Upload a CSV containing historical closing prices. Expected format:{" "}
                <code className="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded font-mono">
                  date,symbol,adjusted_close
                </code>
                .
              </p>

              <input
                type="file"
                accept=".csv"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                className="w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
              />

              {uploadSuccess && (
                <div className="p-3 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-200 rounded-lg flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>{uploadSuccess}</span>
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowUploadModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  isLoading={isUploading}
                  disabled={!uploadFile}
                >
                  Upload CSV
                </Button>
              </div>
            </form>
          )}
        </div>
      </Modal>

      <RegulatoryDisclaimer />
    </div>
  );
}
