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
    return apiClient<Portfolio[]>("/portfolios");
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
    return apiClient(`/portfolios/${id}`);
  },

  async deletePortfolio(id: string): Promise<void> {
    await apiClient(`/portfolios/${id}`, {
      method: "DELETE",
    });
  },

  async getPortfolioValuation(id: string): Promise<PortfolioValuation> {
    return apiClient<PortfolioValuation>(`/portfolios/${id}/valuation`);
  },

  async getPortfolioAllocation(id: string): Promise<AssetAllocationAnalysis> {
    return apiClient<AssetAllocationAnalysis>(`/portfolios/${id}/allocation`);
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
    return apiClient<Asset[]>("/assets");
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
