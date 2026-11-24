import { apiClient } from "./client";
import {
  Asset,
  AssetAllocationAnalysis,
  Holding,
  Portfolio,
  PortfolioValuation,
} from "@/types";

export const portfolioApi = {
  async listPortfolios(): Promise<Portfolio[]> {
    const raw = await apiClient<any>("/portfolios");
    return Array.isArray(raw) ? raw : (raw?.items || []);
  },

  async createPortfolio(payload: {
    name: string;
    description?: string;
    base_currency?: string;
  }): Promise<Portfolio> {
    return apiClient<Portfolio>("/portfolios", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async getPortfolio(id: string): Promise<any> {
    const raw = await apiClient<any>(`/portfolios/${id}`);
    if (!raw?.holdings || raw.holdings.length === 0) {
      try {
        const holdingsRaw = await apiClient<any>(`/portfolios/${id}/holdings`);
        if (Array.isArray(holdingsRaw)) {
          raw.holdings = holdingsRaw;
        }
      } catch {}
    }
    return raw;
  },

  async deletePortfolio(id: string): Promise<void> {
    await apiClient(`/portfolios/${id}`, {
      method: "DELETE",
    });
  },

  async getPortfolioValuation(id: string): Promise<PortfolioValuation> {
    const raw = await apiClient<any>(`/portfolios/${id}/valuation`);
    return {
      portfolio_id: raw?.portfolio_id ?? id,
      total_value: String(raw?.total_value ?? raw?.priced_holdings_value ?? "0.00"),
      cost_basis: String(raw?.cost_basis ?? raw?.cost_basis_all ?? raw?.cost_basis_priced ?? "0.00"),
      unrealized_gain_loss: String(raw?.unrealized_gain_loss ?? "0.00"),
      unrealized_gain_loss_percentage: String(raw?.unrealized_gain_loss_percentage ?? "0.00"),
      valued_at: raw?.valued_at ?? raw?.valuation_as_of ?? new Date().toISOString(),
      unpriced_holdings_count: Number(raw?.unpriced_holdings_count ?? 0),
      currency: raw?.currency ?? raw?.base_currency ?? "INR",
    };
  },

  async getPortfolioAllocation(id: string): Promise<AssetAllocationAnalysis> {
    let raw: any;
    try {
      raw = await apiClient<any>(`/portfolios/${id}/allocation-analysis`);
    } catch {
      raw = await apiClient<any>(`/portfolios/${id}/allocation`);
    }

    let allocations: any[] = [];
    if (Array.isArray(raw?.allocations) && raw.allocations.length > 0) {
      allocations = raw.allocations;
    } else if (Array.isArray(raw?.comparisons) && raw.comparisons.length > 0) {
      allocations = raw.comparisons.map((c: any) => ({
        asset_class: c.asset_class,
        actual_weight: c.current_percentage != null ? (Number(c.current_percentage) / 100).toString() : "0",
        target_weight: c.target_percentage != null ? (Number(c.target_percentage) / 100).toString() : "0",
        variance: c.difference_percentage_points != null ? (Number(c.difference_percentage_points) / 100).toString() : "0",
        status: c.status === "on_target" ? "balanced" : c.status || "balanced",
      }));
    }

    return {
      portfolio_id: raw?.portfolio_id ?? id,
      total_value: String(raw?.total_value ?? raw?.priced_holdings_value ?? "0.00"),
      allocations,
      has_target: Boolean(raw?.has_target_allocation ?? raw?.has_target ?? false),
      max_drift: String(raw?.max_drift ?? "0.00"),
    };
  },

  async listHoldings(portfolioId: string): Promise<Holding[]> {
    try {
      const raw = await apiClient<any>(`/portfolios/${portfolioId}/holdings`);
      if (Array.isArray(raw)) return raw;
      if (Array.isArray(raw?.items)) return raw.items;
      if (Array.isArray(raw?.holdings)) return raw.holdings;
    } catch (e) {
      console.warn("Direct /holdings endpoint failed, checking /portfolios/{id}", e);
    }

    try {
      const portRaw = await apiClient<any>(`/portfolios/${portfolioId}`);
      if (Array.isArray(portRaw?.holdings)) return portRaw.holdings;
    } catch {}

    return [];
  },

  async addHolding(
    portfolioId: string,
    payload: {
      asset_id: string;
      quantity: string;
      average_purchase_price: string;
      current_price?: string | null;
    }
  ): Promise<Holding> {
    return apiClient<Holding>(`/portfolios/${portfolioId}/holdings`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async deleteHolding(portfolioId: string, holdingId: string): Promise<void> {
    await apiClient(`/portfolios/${portfolioId}/holdings/${holdingId}`, {
      method: "DELETE",
    });
  },

  async listAssets(): Promise<Asset[]> {
    const raw = await apiClient<any>("/assets");
    return Array.isArray(raw) ? raw : (raw?.items || []);
  },

  async createAsset(payload: {
    symbol?: string;
    name: string;
    asset_class: string;
    currency?: string;
    instrument_type?: string;
  }): Promise<Asset> {
    return apiClient<Asset>("/assets", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};
