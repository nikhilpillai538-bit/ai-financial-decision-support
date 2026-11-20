import { apiClient } from "./client";
import { MarketDataSummary, OptimizationResult } from "@/types";

export interface OptimizePortfolioPayload {
  objective: "max_sharpe" | "min_volatility" | "target_return";
  target_return?: string;
  risk_free_rate?: string;
  min_weight?: string;
  max_weight?: string;
}

export interface YahooFetchHistoricalPayload {
  symbols: string[];
  period?: string;
  portfolio_id?: string | null;
}

export interface YahooFetchHistoricalResponse {
  symbols_requested: string[];
  symbols_successful: string[];
  symbols_failed: string[];
  imported_rows: number;
  skipped_rows: number;
  period: string;
  date_range_start?: string | null;
  date_range_end?: string | null;
  message: string;
}

export interface MarketPreset {
  id: string;
  name: string;
  description: string;
  symbols: string[];
}

export interface MarketQuoteItem {
  symbol: string;
  last_price: number;
  currency: string;
  previous_close?: number | null;
  change?: number | null;
  change_percent?: number | null;
  fetched_at: string;
}

export interface MarketQuotesResponse {
  quotes: Record<string, MarketQuoteItem>;
  count: number;
}

export interface PortfolioMarketSyncHoldingItem {
  holding_id: string;
  symbol: string;
  asset_name: string;
  old_price?: number | null;
  new_price: number;
  currency: string;
}

export interface PortfolioMarketSyncResponse {
  portfolio_id: string;
  synced_count: number;
  failed_count: number;
  updated_holdings: PortfolioMarketSyncHoldingItem[];
  message: string;
}

export const optimizationApi = {
  async optimizePortfolio(
    portfolioId: string,
    payload: OptimizePortfolioPayload
  ): Promise<OptimizationResult> {
    return apiClient<OptimizationResult>(`/portfolios/${portfolioId}/optimize`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async getOptimizationHistory(portfolioId: string): Promise<OptimizationResult[]> {
    return apiClient<OptimizationResult[]>(`/portfolios/${portfolioId}/optimization-history`);
  },

  async getMarketDataSummary(): Promise<MarketDataSummary> {
    return apiClient<MarketDataSummary>("/market-data/summary");
  },

  async getMarketPresets(): Promise<MarketPreset[]> {
    return apiClient<MarketPreset[]>("/market-data/presets");
  },

  async fetchYahooHistorical(
    payload: YahooFetchHistoricalPayload
  ): Promise<YahooFetchHistoricalResponse> {
    return apiClient<YahooFetchHistoricalResponse>("/market-data/yfinance/fetch-historical", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async getQuotes(symbols: string[]): Promise<MarketQuotesResponse> {
    return apiClient<MarketQuotesResponse>("/market-data/quotes", {
      method: "POST",
      body: JSON.stringify({ symbols }),
    });
  },

  async syncPortfolioMarketPrices(
    portfolioId: string
  ): Promise<PortfolioMarketSyncResponse> {
    return apiClient<PortfolioMarketSyncResponse>(
      `/portfolios/${portfolioId}/sync-market-prices`,
      {
        method: "POST",
      }
    );
  },

  async uploadMarketDataCSV(file: File): Promise<any> {
    const formData = new FormData();
    formData.append("file", file);

    return apiClient("/market-data/historical-prices/import-csv", {
      method: "POST",
      body: formData,
    });
  },

  async importInlineMarketData(csvContent: string): Promise<any> {
    return apiClient("/market-data/import-inline", {
      method: "POST",
      body: JSON.stringify({ csv_content: csvContent }),
    });
  },
};
