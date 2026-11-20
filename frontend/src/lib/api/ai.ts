import { apiClient } from "./client";
import { AIChatResponse, AIThreadDetail, AIThreadSummary, FinancialHealthReport } from "@/types";

export const aiApi = {
  async sendMessage(payload: {
    message: string;
    thread_id?: string;
    portfolio_id?: string;
  }): Promise<AIChatResponse> {
    return apiClient<AIChatResponse>("/ai/chat", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async listThreads(): Promise<AIThreadSummary[]> {
    return apiClient<AIThreadSummary[]>("/ai/threads");
  },

  async getThread(threadId: string): Promise<AIThreadDetail> {
    return apiClient<AIThreadDetail>(`/ai/threads/${threadId}`);
  },

  async generateHealthReport(portfolioId?: string): Promise<FinancialHealthReport> {
    return apiClient<FinancialHealthReport>("/ai/health-report", {
      method: "POST",
      body: JSON.stringify({ portfolio_id: portfolioId || null }),
    });
  },

  async evaluateScenario(scenarioType: string, params: Record<string, any>): Promise<any> {
    return apiClient("/ai/scenario", {
      method: "POST",
      body: JSON.stringify({ scenario_type: scenarioType, params }),
    });
  },
};
