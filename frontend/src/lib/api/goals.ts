import { apiClient } from "./client";
import {
  ForwardSIPResult,
  GlidePathMilestone,
  GoalProjection,
  InvestmentGoal,
  PortfolioDrift,
  ReverseSIPResult,
} from "@/types";

export interface CreateGoalPayload {
  name: string;
  target_amount: string;
  target_date: string;
  current_amount?: string;
  planned_monthly_contribution?: string;
  portfolio_id?: string | null;
}

export const goalsApi = {
  async listGoals(): Promise<InvestmentGoal[]> {
    return apiClient<InvestmentGoal[]>("/investment-goals");
  },

  async createGoal(payload: CreateGoalPayload): Promise<InvestmentGoal> {
    return apiClient<InvestmentGoal>("/investment-goals", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async deleteGoal(id: string): Promise<void> {
    await apiClient(`/investment-goals/${id}`, {
      method: "DELETE",
    });
  },

  async getGoalProjection(goalId: string): Promise<GoalProjection> {
    return apiClient<GoalProjection>(`/investment-goals/${goalId}/projection`);
  },

  async calculateForwardSIP(payload: {
    monthly_investment: string;
    annual_rate: string;
    tenure_months: number;
    step_up_percentage?: string;
  }): Promise<ForwardSIPResult> {
    return apiClient<ForwardSIPResult>("/calculators/sip/forward", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async calculateReverseSIP(payload: {
    target_amount: string;
    annual_rate: string;
    tenure_months: number;
  }): Promise<ReverseSIPResult> {
    return apiClient<ReverseSIPResult>("/calculators/sip/reverse", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async getPortfolioDrift(portfolioId: string, thresholdPercent: number = 5.0): Promise<PortfolioDrift> {
    return apiClient<PortfolioDrift>(`/portfolios/${portfolioId}/drift`, {
      params: { threshold_percent: thresholdPercent },
    });
  },

  async generateGlidePath(yearsToHorizon: number, riskProfile: string = "moderate"): Promise<{
    milestones: GlidePathMilestone[];
  }> {
    return apiClient("/glide-paths/generate", {
      params: {
        years_to_horizon: yearsToHorizon,
        risk_profile: riskProfile,
      },
    });
  },
};
