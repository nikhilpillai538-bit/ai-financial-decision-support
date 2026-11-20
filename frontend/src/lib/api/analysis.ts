import { apiClient } from "./client";
import { CashFlowForecast, EmergencyFundAnalysis } from "@/types";

export const analysisApi = {
  async getEmergencyFundAnalysis(): Promise<EmergencyFundAnalysis> {
    return apiClient<EmergencyFundAnalysis>("/financial-analysis/emergency-fund");
  },

  async getCashFlowForecast(forecastDays: number = 30): Promise<CashFlowForecast> {
    return apiClient<CashFlowForecast>("/financial-analysis/cash-flow-forecast", {
      params: { forecast_days: forecastDays },
    });
  },

  async updateFinancialProfile(payload: {
    monthly_essential_expenses?: string;
    available_liquid_savings?: string;
  }): Promise<any> {
    return apiClient("/financial-profile", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },
};
