import { apiClient } from "./client";
import {
  NewsArticle,
  NewsArticleListResponse,
  PortfolioNewsInsights,
  PortfolioNewsRelevanceResponse,
  SentimentSummary,
} from "@/types";

export const newsApi = {
  async listArticles(params: {
    sentiment_label?: string;
    search?: string;
    limit?: number;
    offset?: number;
  } = {}): Promise<NewsArticleListResponse> {
    return apiClient<NewsArticleListResponse>("/news", {
      params: params as any,
    });
  },

  async getArticle(articleId: string): Promise<NewsArticle> {
    return apiClient<NewsArticle>(`/news/${articleId}`);
  },

  async refreshFeeds(force: boolean = false): Promise<any> {
    return apiClient("/news/refresh", {
      method: "POST",
      body: JSON.stringify({ force }),
    });
  },

  async getSentimentSummary(timeWindow: string = "24h"): Promise<SentimentSummary> {
    return apiClient<SentimentSummary>("/news/sentiment/summary", {
      params: { time_window: timeWindow },
    });
  },

  async getPortfolioRelevance(params: {
    portfolio_id?: string;
    min_confidence?: number;
  } = {}): Promise<PortfolioNewsRelevanceResponse> {
    return apiClient<PortfolioNewsRelevanceResponse>("/news/portfolio-relevance", {
      params: params as any,
    });
  },

  async getPortfolioInsights(portfolioId?: string): Promise<PortfolioNewsInsights> {
    return apiClient<PortfolioNewsInsights>("/news/portfolio-insights", {
      method: "POST",
      params: portfolioId ? { portfolio_id: portfolioId } : undefined,
    });
  },
};
