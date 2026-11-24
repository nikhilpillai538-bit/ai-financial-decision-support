"use client";

import React, { useEffect, useState } from "react";
import {
  Briefcase,
  Plus,
  Trash2,
  AlertTriangle,
  TrendingUp,
  DollarSign,
  PieChart,
  Zap,
  Sparkles,
  RefreshCw,
} from "lucide-react";
import { MetricCard } from "@/components/shared/MetricCard";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { AllocationDonutChart } from "@/components/charts/AllocationDonutChart";
import { LoadingState, EmptyState, ErrorBanner, RegulatoryDisclaimer } from "@/components/shared/States";
import { formatCurrency, formatDate, formatPercentage } from "@/lib/formatters";
import { portfolioApi } from "@/lib/api/portfolio";
import { optimizationApi } from "@/lib/api/optimization";
import {
  Asset,
  AssetAllocationAnalysis,
  Holding,
  Portfolio,
  PortfolioValuation,
} from "@/types";

export default function PortfolioPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<string | null>(null);
  const [valuation, setValuation] = useState<PortfolioValuation | null>(null);
  const [allocation, setAllocation] = useState<AssetAllocationAnalysis | null>(null);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);

  // Modals state
  const [isAddHoldingOpen, setIsAddHoldingOpen] = useState(false);
  const [isCreateAssetOpen, setIsCreateAssetOpen] = useState(false);
  const [isCreatePortOpen, setIsCreatePortOpen] = useState(false);

  // Add Holding Form
  const [holdingAssetId, setHoldingAssetId] = useState("");
  const [holdingQty, setHoldingQty] = useState("");
  const [holdingBuyPrice, setHoldingBuyPrice] = useState("");
  const [holdingCurrPrice, setHoldingCurrPrice] = useState("");
  const [isSavingHolding, setIsSavingHolding] = useState(false);

  // Create Asset Form
  const [assetSymbol, setAssetSymbol] = useState("");
  const [assetName, setAssetName] = useState("");
  const [assetClass, setAssetClass] = useState("equity");
  const [assetCurrency, setAssetCurrency] = useState("INR");
  const [assetType, setAssetType] = useState("Technology");
  const [isSavingAsset, setIsSavingAsset] = useState(false);

  // Create Portfolio Form
  const [portName, setPortName] = useState("");
  const [portDesc, setPortDesc] = useState("");
  const [portCurrency, setPortCurrency] = useState("INR");
  const [isSavingPort, setIsSavingPort] = useState(false);

  // Live Price Sync states
  const [isSyncingPrices, setIsSyncingPrices] = useState(false);
  const [syncNotification, setSyncNotification] = useState<string | null>(null);
  const [isLookingUpQuote, setIsLookingUpQuote] = useState(false);

  const handleSyncLivePrices = async () => {
    if (!selectedPortfolioId) return;
    setIsSyncingPrices(true);
    setSyncNotification(null);
    try {
      const res = await optimizationApi.syncPortfolioMarketPrices(selectedPortfolioId);
      setSyncNotification(res.message);
      await loadPortfolioDetails(selectedPortfolioId);
    } catch (err: any) {
      alert(`Error syncing live prices: ${err?.detail || err?.message}`);
    } finally {
      setIsSyncingPrices(false);
    }
  };

  const handleLookupQuote = async (symbolToLookup: string) => {
    if (!symbolToLookup || !symbolToLookup.trim()) return;
    setIsLookingUpQuote(true);
    try {
      const res = await optimizationApi.getQuotes([symbolToLookup.trim().toUpperCase()]);
      const q = res.quotes[symbolToLookup.trim().toUpperCase()];
      if (q && q.last_price) {
        setHoldingCurrPrice(q.last_price.toString());
        if (!holdingBuyPrice) {
          setHoldingBuyPrice(q.last_price.toString());
        }
      } else {
        alert(`Quote for symbol "${symbolToLookup}" could not be retrieved from Yahoo Finance.`);
      }
    } catch (err: any) {
      alert(`Could not fetch live quote: ${err?.message}`);
    } finally {
      setIsLookingUpQuote(false);
    }
  };

  const fetchInitialData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ports, availableAssets] = await Promise.all([
        portfolioApi.listPortfolios(),
        portfolioApi.listAssets(),
      ]);
      setPortfolios(ports || []);
      setAssets(availableAssets || []);

      if (ports && ports.length > 0) {
        const portId = selectedPortfolioId || ports[0].id;
        setSelectedPortfolioId(portId);
        await loadPortfolioDetails(portId);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load portfolios.");
    } finally {
      setLoading(false);
    }
  };

  const loadPortfolioDetails = async (portId: string) => {
    try {
      const [holdingsRes, portDetail, valRes, allocRes] = await Promise.allSettled([
        portfolioApi.listHoldings(portId),
        portfolioApi.getPortfolio(portId),
        portfolioApi.getPortfolioValuation(portId),
        portfolioApi.getPortfolioAllocation(portId),
      ]);

      let loadedHoldings: Holding[] = [];
      if (holdingsRes.status === "fulfilled" && Array.isArray(holdingsRes.value) && holdingsRes.value.length > 0) {
        loadedHoldings = holdingsRes.value;
      } else if (portDetail.status === "fulfilled" && Array.isArray(portDetail.value?.holdings) && portDetail.value.holdings.length > 0) {
        loadedHoldings = portDetail.value.holdings;
      } else if (holdingsRes.status === "fulfilled" && Array.isArray(holdingsRes.value)) {
        loadedHoldings = holdingsRes.value;
      }
      setHoldings(loadedHoldings);

      if (valRes.status === "fulfilled") {
        setValuation(valRes.value);
      }
      if (allocRes.status === "fulfilled") {
        setAllocation(allocRes.value);
      }
    } catch (err: any) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchInitialData();
  }, []);

  const handleSelectPortfolio = async (id: string) => {
    setSelectedPortfolioId(id);
    await loadPortfolioDetails(id);
  };

  const handleCreatePortfolio = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!portName) return;

    setIsSavingPort(true);
    try {
      const created = await portfolioApi.createPortfolio({
        name: portName,
        description: portDesc,
        base_currency: portCurrency,
      });
      setIsCreatePortOpen(false);
      setPortName("");
      setPortDesc("");
      await fetchInitialData();
      setSelectedPortfolioId(created.id);
    } catch (err: any) {
      alert(`Error creating portfolio: ${err?.detail || err?.message}`);
    } finally {
      setIsSavingPort(false);
    }
  };

  const handleCreateAsset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assetName) return;

    setIsSavingAsset(true);
    try {
      const created = await portfolioApi.createAsset({
        symbol: assetSymbol || undefined,
        name: assetName,
        asset_class: assetClass,
        currency: assetCurrency,
        instrument_type: assetType || undefined,
      });
      setIsCreateAssetOpen(false);
      setAssetSymbol("");
      setAssetName("");
      const refreshedAssets = await portfolioApi.listAssets();
      setAssets(refreshedAssets || []);
      setHoldingAssetId(created.id);
      setIsAddHoldingOpen(true);
    } catch (err: any) {
      alert(`Error creating asset: ${err?.detail || err?.message}`);
    } finally {
      setIsSavingAsset(false);
    }
  };

  const handleAddHolding = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPortfolioId || !holdingAssetId || !holdingQty || !holdingBuyPrice) return;

    setIsSavingHolding(true);
    try {
      await portfolioApi.addHolding(selectedPortfolioId, {
        asset_id: holdingAssetId,
        quantity: holdingQty,
        average_purchase_price: holdingBuyPrice,
        current_price: holdingCurrPrice?.trim() ? holdingCurrPrice.trim() : null,
      });
      setIsAddHoldingOpen(false);
      setHoldingQty("");
      setHoldingBuyPrice("");
      setHoldingCurrPrice("");
      await loadPortfolioDetails(selectedPortfolioId);
    } catch (err: any) {
      alert(`Error adding holding: ${err?.detail || err?.message}`);
    } finally {
      setIsSavingHolding(false);
    }
  };

  const handleDeleteHolding = async (holdingId: string) => {
    if (!selectedPortfolioId) return;
    if (!confirm("Are you sure you want to remove this position from your portfolio?")) return;

    try {
      await portfolioApi.deleteHolding(selectedPortfolioId, holdingId);
      await loadPortfolioDetails(selectedPortfolioId);
    } catch (err: any) {
      alert(`Error removing position: ${err?.detail || err?.message}`);
    }
  };

  if (loading) {
    return <LoadingState message="Retrieving portfolio holdings & real-time valuation..." />;
  }

  const allocationChartData =
    allocation?.allocations && allocation.allocations.length > 0
      ? allocation.allocations.map((a) => ({
          name: a.asset_class,
          asset_class: a.asset_class,
          value: parseFloat(a.actual_weight) * 100,
        }))
      : (valuation as any)?.asset_class_breakdown?.map((b: any) => ({
          name: b.asset_class,
          asset_class: b.asset_class,
          value: parseFloat(b.allocation_percentage) || 0,
        })) || [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl lg:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
            Portfolio Management & Assets
          </h1>
          <p className="text-base text-slate-500 dark:text-slate-400 mt-1.5 font-medium">
            Holdings, asset allocation analysis, and deterministic valuation
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="md"
            disabled={!selectedPortfolioId || isSyncingPrices}
            onClick={handleSyncLivePrices}
            isLoading={isSyncingPrices}
            className="gap-2 shadow-xs text-indigo-600 dark:text-indigo-400 border-indigo-200 dark:border-indigo-800 hover:bg-indigo-50"
          >
            <Zap className="w-4 h-4 text-amber-500" />
            <span>Sync Live Prices</span>
          </Button>
          <Button
            variant="outline"
            size="md"
            onClick={() => setIsCreatePortOpen(true)}
            className="gap-2 shadow-xs"
          >
            <Briefcase className="w-4 h-4" />
            <span>New Portfolio</span>
          </Button>
          <Button
            variant="primary"
            size="md"
            disabled={!selectedPortfolioId}
            onClick={() => setIsAddHoldingOpen(true)}
            className="gap-2 shadow-md shadow-indigo-600/20"
          >
            <Plus className="w-4 h-4" />
            <span>Add Position</span>
          </Button>
        </div>
      </div>

      {error && <ErrorBanner message={error} onRetry={fetchInitialData} />}

      {syncNotification && (
        <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50 text-emerald-900 text-sm flex items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-2.5 font-medium">
            <Zap className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{syncNotification}</span>
          </div>
          <button
            onClick={() => setSyncNotification(null)}
            className="text-xs font-bold text-emerald-700 hover:text-emerald-900 px-2 py-1 rounded-md bg-emerald-100/50"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Portfolio Selector Tabs */}
      {portfolios.length > 1 && (
        <div className="flex items-center gap-2.5 overflow-x-auto pb-1">
          {portfolios.map((p) => (
            <button
              key={p.id}
              onClick={() => handleSelectPortfolio(p.id)}
              className={`px-5 py-2.5 rounded-xl text-sm font-bold transition-all shrink-0 ${
                selectedPortfolioId === p.id
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                  : "bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-800 hover:bg-slate-50"
              }`}
            >
              {p.name} ({p.base_currency})
            </button>
          ))}
        </div>
      )}

      {/* Unpriced Holdings Alert */}
      {valuation && valuation.unpriced_holdings_count > 0 && (
        <div className="p-4 rounded-xl border border-amber-200 bg-amber-50 text-amber-900 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-2.5">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
            <span className="font-medium">
              {valuation.unpriced_holdings_count} position(s) have unrecorded market prices. Total valuation reflects only positions with known current prices.
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleSyncLivePrices}
            isLoading={isSyncingPrices}
            className="bg-white text-amber-900 border-amber-300 hover:bg-amber-100 gap-1.5 shrink-0 self-start sm:self-auto"
          >
            <Zap className="w-3.5 h-3.5 text-amber-600" />
            <span>Fetch from Yahoo Finance</span>
          </Button>
        </div>
      )}

      {/* Valuation Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Portfolio Value"
          value={formatCurrency(valuation?.total_value, valuation?.currency || "INR")}
          subtitle={`Valued as of ${formatDate(valuation?.valued_at)}`}
          icon={<DollarSign className="w-5 h-5" />}
          variant="brand"
        />

        <MetricCard
          title="Cost Basis (Invested)"
          value={formatCurrency(valuation?.cost_basis, valuation?.currency || "INR")}
          subtitle="Total acquisition cost across holdings"
          icon={<Briefcase className="w-5 h-5" />}
          variant="default"
        />

        <MetricCard
          title="Unrealized Gain / Loss"
          value={formatCurrency(valuation?.unrealized_gain_loss, valuation?.currency || "INR", {
            showPlusSign: true,
          })}
          subtitle={
            valuation?.unrealized_gain_loss_percentage
              ? `Return: ${formatPercentage(valuation.unrealized_gain_loss_percentage, { showPlusSign: true })}`
              : "—"
          }
          icon={<TrendingUp className="w-5 h-5" />}
          variant={parseFloat(valuation?.unrealized_gain_loss || "0") >= 0 ? "success" : "danger"}
        />

        <MetricCard
          title="Max Allocation Drift"
          value={allocation?.max_drift ? formatPercentage(parseFloat(allocation.max_drift) * 100) : "0.00%"}
          subtitle={allocation?.has_target ? "Measured against target asset weights" : "No target allocation configured"}
          icon={<PieChart className="w-5 h-5" />}
          variant="default"
        />
      </div>

      {/* Mid Section: Allocation Donut & Allocation Variance Table */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1 flex flex-col">
          <CardHeader>
            <CardTitle>Asset Class Distribution</CardTitle>
            <CardDescription>Weights across equity, debt, cash, and commodities</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col justify-center">
            <AllocationDonutChart data={allocationChartData} height={240} />
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Allocation Targets & Variances</CardTitle>
            <CardDescription>Comparison between actual weights and target policy</CardDescription>
          </CardHeader>
          <CardContent>
            {(!allocation?.allocations || allocation.allocations.length === 0) ? (
              <div className="py-8 text-center text-xs text-slate-400">
                No asset allocation data available for this portfolio. Add holdings to compute weights.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 uppercase font-semibold">
                    <tr>
                      <th className="py-2.5 px-3">Asset Class</th>
                      <th className="py-2.5 px-3 text-right">Actual Weight</th>
                      <th className="py-2.5 px-3 text-right">Target Weight</th>
                      <th className="py-2.5 px-3 text-right">Variance</th>
                      <th className="py-2.5 px-3 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {allocation.allocations.map((a, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/50">
                        <td className="py-2.5 px-3 font-medium capitalize text-slate-900 dark:text-slate-100">
                          {a.asset_class.replace("_", " ")}
                        </td>
                        <td className="py-2.5 px-3 text-right font-semibold">
                          {formatPercentage(parseFloat(a.actual_weight) * 100)}
                        </td>
                        <td className="py-2.5 px-3 text-right text-slate-500">
                          {formatPercentage(parseFloat(a.target_weight) * 100)}
                        </td>
                        <td className="py-2.5 px-3 text-right font-semibold text-slate-700">
                          {formatPercentage(parseFloat(a.variance) * 100, { showPlusSign: true })}
                        </td>
                        <td className="py-2.5 px-3 text-center">
                          <Badge
                            variant={
                              a.status === "balanced"
                                ? "success"
                                : a.status === "overweight"
                                ? "warning"
                                : "info"
                            }
                          >
                            {a.status}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Holdings Table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Portfolio Positions & Holdings</CardTitle>
            <CardDescription>{holdings.length} total active asset instruments</CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsAddHoldingOpen(true)}
            className="text-xs gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Position</span>
          </Button>
        </CardHeader>
        <CardContent className="p-0">
          {holdings.length === 0 ? (
            <EmptyState
              title="No holdings in portfolio"
              description="Add stocks, ETFs, mutual funds, or bonds to compute portfolio valuation and allocation."
              icon={<Briefcase className="w-8 h-8" />}
              action={
                <Button variant="primary" size="sm" onClick={() => setIsAddHoldingOpen(true)}>
                  Add Position
                </Button>
              }
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 uppercase tracking-wider font-semibold border-y border-slate-100 dark:border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Instrument</th>
                    <th className="py-3 px-4">Asset Class</th>
                    <th className="py-3 px-4 text-right">Quantity</th>
                    <th className="py-3 px-4 text-right">Avg Purchase Price</th>
                    <th className="py-3 px-4 text-right">Current Price</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {holdings.map((h) => {
                    const asset = h.asset || assets.find((a) => a.id === h.asset_id);
                    const symbol = asset?.symbol || (h as any).asset_symbol;
                    const name = asset?.name || (h as any).asset_name || symbol || "Asset";
                    const assetClass = asset?.asset_class || (h as any).asset_class || "—";
                    const curr = asset?.currency || (h as any).currency || "INR";
                    return (
                      <tr key={h.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                        <td className="py-3 px-4">
                          <div className="font-semibold text-slate-900 dark:text-slate-100">
                            {symbol || name}
                          </div>
                          <div className="text-[10px] text-slate-400 truncate max-w-xs">
                            {name}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <Badge variant="outline">{assetClass}</Badge>
                        </td>
                        <td className="py-3 px-4 text-right font-medium">{h.quantity}</td>
                        <td className="py-3 px-4 text-right text-slate-600">
                          {formatCurrency(h.average_purchase_price, curr)}
                        </td>
                        <td className="py-3 px-4 text-right font-semibold">
                          {h.current_price
                            ? formatCurrency(h.current_price, curr)
                            : <span className="text-amber-500 font-normal">Unpriced</span>}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => handleDeleteHolding(h.id)}
                            className="text-slate-400 hover:text-rose-600 p-1 transition-colors"
                            title="Remove position"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add Holding Modal */}
      <Modal
        isOpen={isAddHoldingOpen}
        onClose={() => setIsAddHoldingOpen(false)}
        title="Add Position to Portfolio"
        description="Select an asset instrument, input quantity and cost basis"
      >
        <form onSubmit={handleAddHolding} className="space-y-4">
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Asset Instrument
              </label>
              <button
                type="button"
                onClick={() => {
                  setIsAddHoldingOpen(false);
                  setIsCreateAssetOpen(true);
                }}
                className="text-[11px] text-indigo-600 font-medium hover:underline"
              >
                + Create Custom Instrument
              </button>
            </div>
            <select
              value={holdingAssetId}
              onChange={(e) => setHoldingAssetId(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100"
              required
            >
              <option value="">Select an asset...</option>
              {assets.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.symbol ? `${a.symbol} — ` : ""}{a.name} ({a.asset_class})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <Input
              label="Quantity (Shares/Units)"
              type="number"
              step="0.0001"
              min="0.0001"
              placeholder="e.g. 50"
              value={holdingQty}
              onChange={(e) => setHoldingQty(e.target.value)}
              required
            />
            <Input
              label="Purchase Price"
              type="number"
              step="0.01"
              min="0.01"
              placeholder="e.g. 1500.00"
              value={holdingBuyPrice}
              onChange={(e) => setHoldingBuyPrice(e.target.value)}
              required
            />
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Current Market Price
                </label>
                {holdingAssetId && assets.find((a) => a.id === holdingAssetId)?.symbol && (
                  <button
                    type="button"
                    onClick={() => {
                      const sym = assets.find((a) => a.id === holdingAssetId)?.symbol;
                      if (sym) handleLookupQuote(sym);
                    }}
                    disabled={isLookingUpQuote}
                    className="text-[11px] font-bold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
                  >
                    <Zap className="w-3 h-3 text-amber-500" />
                    <span>{isLookingUpQuote ? "Fetching..." : "Live Price"}</span>
                  </button>
                )}
              </div>
              <Input
                type="number"
                step="0.01"
                min="0"
                placeholder="Optional"
                value={holdingCurrPrice}
                onChange={(e) => setHoldingCurrPrice(e.target.value)}
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsAddHoldingOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={isSavingHolding}>
              Save Position
            </Button>
          </div>
        </form>
      </Modal>

      {/* Create Custom Asset Instrument Modal */}
      <Modal
        isOpen={isCreateAssetOpen}
        onClose={() => setIsCreateAssetOpen(false)}
        title="Create Asset Instrument"
        description="Register a stock, mutual fund, ETF, or fixed income instrument"
      >
        <form onSubmit={handleCreateAsset} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Input
                label="Symbol / Ticker"
                placeholder="e.g. RELIANCE.NS, TCS.NS, AAPL"
                value={assetSymbol}
                onChange={(e) => setAssetSymbol(e.target.value)}
              />
              <span className="text-[10px] text-slate-500 mt-0.5 block">
                Use .NS for NSE India, .BO for BSE, or US ticker
              </span>
            </div>
            <Input
              label="Instrument Name"
              placeholder="e.g. Reliance Industries, Apple Inc"
              value={assetName}
              onChange={(e) => setAssetName(e.target.value)}
              required
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Asset Class
              </label>
              <select
                value={assetClass}
                onChange={(e) => setAssetClass(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100"
              >
                <option value="equity">Equity</option>
                <option value="debt">Debt / Fixed Income</option>
                <option value="mutual_fund">Mutual Fund</option>
                <option value="etf">ETF</option>
                <option value="cash">Cash / Liquid</option>
                <option value="commodities_gold">Gold / Commodities</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Currency
              </label>
              <select
                value={assetCurrency}
                onChange={(e) => setAssetCurrency(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100"
              >
                <option value="INR">INR (₹)</option>
                <option value="USD">USD ($)</option>
                <option value="EUR">EUR (€)</option>
              </select>
            </div>

            <Input
              label="Sector / Category"
              placeholder="e.g. Technology"
              value={assetType}
              onChange={(e) => setAssetType(e.target.value)}
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsCreateAssetOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={isSavingAsset}>
              Create Instrument
            </Button>
          </div>
        </form>
      </Modal>

      {/* Create Portfolio Modal */}
      <Modal
        isOpen={isCreatePortOpen}
        onClose={() => setIsCreatePortOpen(false)}
        title="Create Portfolio"
        description="Add a new segregated investment portfolio"
      >
        <form onSubmit={handleCreatePortfolio} className="space-y-4">
          <Input
            label="Portfolio Name"
            placeholder="e.g. Core Wealth, Growth Strategy"
            value={portName}
            onChange={(e) => setPortName(e.target.value)}
            required
          />

          <Input
            label="Description"
            placeholder="e.g. Long-term retirement portfolio"
            value={portDesc}
            onChange={(e) => setPortDesc(e.target.value)}
          />

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
              Base Currency
            </label>
            <select
              value={portCurrency}
              onChange={(e) => setPortCurrency(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100"
            >
              <option value="INR">INR (₹)</option>
              <option value="USD">USD ($)</option>
              <option value="EUR">EUR (€)</option>
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setIsCreatePortOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" isLoading={isSavingPort}>
              Create Portfolio
            </Button>
          </div>
        </form>
      </Modal>

      <RegulatoryDisclaimer />
    </div>
  );
}
