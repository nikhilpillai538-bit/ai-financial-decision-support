"use client";

import React, { useEffect, useState } from "react";
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
import {
  LoadingState,
  EmptyState,
  ErrorBanner,
  RegulatoryDisclaimer,
} from "@/components/shared/States";
import { MetricCard } from "@/components/shared/MetricCard";
import { SentimentDistributionChart } from "@/components/charts/SentimentDistributionChart";
import { newsApi } from "@/lib/api/news";
import { portfolioApi } from "@/lib/api/portfolio";
import {
  NewsArticle,
  SentimentSummary,
  PortfolioNewsInsights,
  PortfolioNewsRelevanceResponse,
  Portfolio,
} from "@/types";
import { formatDate } from "@/lib/formatters";
import {
  Newspaper,
  TrendingUp,
  RefreshCw,
  ExternalLink,
  Search,
  Filter,
  Layers,
  Sparkles,
  BarChart2,
  AlertTriangle,
} from "lucide-react";

export default function NewsIntelligencePage() {
  const [timeWindow, setTimeWindow] = useState<"24h" | "7d" | "30d">("24h");
  const [summary, setSummary] = useState<SentimentSummary | null>(null);
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<string>("");
  const [insights, setInsights] = useState<PortfolioNewsInsights | null>(null);
  const [relevance, setRelevance] = useState<PortfolioNewsRelevanceResponse | null>(null);

  // Articles Feed State
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [totalArticles, setTotalArticles] = useState(0);
  const [sentimentFilter, setSentimentFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [page, setPage] = useState(0);
  const pageSize = 15;

  // UI States
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isLoadingInsights, setIsLoadingInsights] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshMessage, setRefreshMessage] = useState<string | null>(null);

  // Initial load
  useEffect(() => {
    loadBaseData();
  }, [timeWindow]);

  // Load articles when filter/search/page change
  useEffect(() => {
    loadArticles();
  }, [sentimentFilter, page]);

  // Load insights when portfolio changes
  useEffect(() => {
    loadPortfolioNews(selectedPortfolioId);
  }, [selectedPortfolioId]);

  async function loadBaseData() {
    setIsLoading(true);
    setError(null);
    try {
      const [sum, ports] = await Promise.all([
        newsApi.getSentimentSummary(timeWindow).catch(() => null),
        portfolioApi.listPortfolios().catch(() => []),
      ]);
      setSummary(sum);
      setPortfolios(ports);
      if (ports.length > 0 && !selectedPortfolioId) {
        setSelectedPortfolioId(ports[0].id);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load sentiment summary");
    } finally {
      setIsLoading(false);
    }
  }

  async function loadPortfolioNews(portfolioId?: string) {
    setIsLoadingInsights(true);
    try {
      const [ins, rel] = await Promise.all([
        newsApi.getPortfolioInsights(portfolioId || undefined).catch(() => null),
        newsApi.getPortfolioRelevance({ portfolio_id: portfolioId || undefined }).catch(() => null),
      ]);
      setInsights(ins);
      setRelevance(rel);
    } catch (err: any) {
      console.error("Error loading portfolio news insights:", err);
    } finally {
      setIsLoadingInsights(false);
    }
  }

  async function loadArticles() {
    try {
      const res = await newsApi.listArticles({
        sentiment_label: sentimentFilter === "all" ? undefined : sentimentFilter,
        search: searchQuery ? searchQuery : undefined,
        limit: pageSize,
        offset: page * pageSize,
      });
      setArticles(res.articles || []);
      setTotalArticles(res.total_count || 0);
    } catch (err: any) {
      console.error("Error loading articles feed:", err);
    }
  }

  async function handleRefreshFeeds() {
    setIsRefreshing(true);
    setError(null);
    setRefreshMessage(null);
    try {
      const res = await newsApi.refreshFeeds(true);
      setRefreshMessage(`Feeds refreshed. Processed ${res?.fetched_count || res?.articles_added || "new"} items.`);
      await loadBaseData();
      await loadArticles();
      if (selectedPortfolioId) {
        await loadPortfolioNews(selectedPortfolioId);
      }
    } catch (err: any) {
      setError(err?.message || "Feed ingestion failed or rate limited");
    } finally {
      setIsRefreshing(false);
    }
  }

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    setPage(0);
    loadArticles();
  }

  if (isLoading) {
    return <LoadingState message="Aggregating market intelligence & FinBERT sentiment..." />;
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl lg:text-4xl font-extrabold tracking-tight text-slate-900">
            Market Intelligence & FinBERT Sentiment
          </h1>
          <p className="text-base text-slate-500 mt-1.5 font-medium">
            Natural language financial news processing, sentiment distributions, and portfolio theme mapping.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Time window toggles */}
          <div className="flex items-center bg-slate-100 dark:bg-slate-800 p-1.5 rounded-xl text-sm font-bold">
            {(["24h", "7d", "30d"] as const).map((tw) => (
              <button
                key={tw}
                onClick={() => setTimeWindow(tw)}
                className={`px-4 py-1.5 rounded-lg transition-all ${
                  timeWindow === tw
                    ? "bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-sm font-bold"
                    : "text-slate-500 hover:text-slate-900 dark:text-slate-400"
                }`}
              >
                {tw.toUpperCase()}
              </button>
            ))}
          </div>

          <Button
            variant="outline"
            size="md"
            onClick={handleRefreshFeeds}
            isLoading={isRefreshing}
          >
            <RefreshCw className="w-4 h-4 mr-1.5" />
            Refresh Feeds
          </Button>
        </div>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}
      {refreshMessage && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 rounded-lg flex items-center justify-between">
          <span>{refreshMessage}</span>
          <button onClick={() => setRefreshMessage(null)} className="text-emerald-700 font-bold ml-2">×</button>
        </div>
      )}

      {/* Top Sentiment Metrics */}
      {summary && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title="Articles Processed"
              value={summary.total_articles.toString()}
              icon={<Newspaper className="w-4 h-4 text-primary-600" />}
              subtitle={`Window: ${summary.time_window}`}
            />
            <MetricCard
              title="Positive / Bullish"
              value={`${summary.positive_count} (${(summary.positive_percentage * 100).toFixed(1)}%)`}
              icon={<TrendingUp className="w-4 h-4 text-emerald-600" />}
              subtitle="FinBERT positive classification"
            />
            <MetricCard
              title="Negative / Bearish"
              value={`${summary.negative_count} (${(summary.negative_percentage * 100).toFixed(1)}%)`}
              icon={<AlertTriangle className="w-4 h-4 text-rose-600" />}
              subtitle="FinBERT negative classification"
            />
            <MetricCard
              title="Net Market Sentiment"
              value={summary.overall_sentiment_label.toUpperCase()}
              icon={<BarChart2 className="w-4 h-4 text-blue-600" />}
              subtitle={`Score: ${summary.average_sentiment_score > 0 ? "+" : ""}${summary.average_sentiment_score.toFixed(3)}`}
            />
          </div>

          {/* Sentiment Distribution Bar Card */}
          <Card>
            <CardHeader className="py-3">
              <CardTitle className="text-sm font-semibold text-slate-800">
                Market Sentiment Distribution ({summary.time_window.toUpperCase()})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <SentimentDistributionChart
                positive={summary.positive_percentage * 100}
                negative={summary.negative_percentage * 100}
                neutral={summary.neutral_percentage * 100}
                total={summary.total_articles}
                overallLabel={summary.overall_sentiment_label}
              />
              {summary.warnings && summary.warnings.length > 0 && (
                <div className="mt-3 text-xs text-amber-700 bg-amber-50 p-2 rounded border border-amber-200">
                  {summary.warnings.join(" ")}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* Two Columns: Portfolio News Insights & Sector Sentiment */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Portfolio-Specific Insights */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-amber-500" />
                    Portfolio News Themes & Impact
                  </CardTitle>
                  <CardDescription>
                    Contextual mapping of news stories to your asset holdings.
                  </CardDescription>
                </div>
                {portfolios.length > 0 && (
                  <select
                    value={selectedPortfolioId}
                    onChange={(e) => setSelectedPortfolioId(e.target.value)}
                    className="text-xs rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-slate-800 focus:outline-none focus:ring-1 focus:ring-primary-500"
                  >
                    <option value="">All Portfolios / Aggregate</option>
                    {portfolios.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {isLoadingInsights ? (
                <LoadingState message="Correlating news feeds to portfolio holdings..." />
              ) : insights ? (
                <>
                  {/* Executive Summary */}
                  {insights.executive_summary && (
                    <div className="bg-primary-50/60 border border-primary-100 rounded-lg p-3 text-xs text-slate-700 leading-relaxed">
                      <strong className="text-primary-900 block mb-1">Portfolio Synthesis:</strong>
                      {insights.executive_summary}
                    </div>
                  )}

                  {/* Themes List */}
                  {insights.themes && insights.themes.length > 0 ? (
                    <div className="space-y-3">
                      {insights.themes.map((theme, idx) => (
                        <div
                          key={idx}
                          className="border border-slate-200 rounded-lg p-3 space-y-2 bg-white"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <h4 className="text-xs font-semibold text-slate-900">
                              {theme.theme_title}
                            </h4>
                            <Badge
                              variant={
                                theme.sentiment === "positive" || theme.sentiment === "bullish"
                                  ? "success"
                                  : theme.sentiment === "negative" || theme.sentiment === "bearish"
                                  ? "danger"
                                  : "outline"
                              }
                            >
                              {theme.sentiment.toUpperCase()}
                            </Badge>
                          </div>
                          <p className="text-xs text-slate-600">
                            {theme.relevance_to_portfolio}
                          </p>

                          {/* Referenced articles */}
                          {theme.articles && theme.articles.length > 0 && (
                            <div className="pt-2 border-t border-slate-100 space-y-1">
                              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block">
                                Supporting Headlines:
                              </span>
                              {theme.articles.map((art, aIdx) => (
                                <a
                                  key={aIdx}
                                  href={art.canonical_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-xs text-primary-600 hover:text-primary-800 hover:underline flex items-center gap-1 truncate"
                                >
                                  <ExternalLink className="w-3 h-3 shrink-0" />
                                  <span className="truncate">{art.title}</span>
                                  {art.source_name && (
                                    <span className="text-slate-400 text-[10px] shrink-0">
                                      ({art.source_name})
                                    </span>
                                  )}
                                </a>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-6 text-xs text-slate-500">
                      No direct news theme clusters detected for this portfolio in the current window.
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-6 text-xs text-slate-500">
                  Select a portfolio to see news insights.
                </div>
              )}
            </CardContent>
          </Card>

          {/* Matched Entities Strip */}
          {relevance && relevance.matches && relevance.matches.length > 0 && (
            <Card>
              <CardHeader className="py-3">
                <CardTitle className="text-xs font-semibold text-slate-700 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-slate-500" />
                  Portfolio Asset Mentions ({relevance.matches.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto max-h-56 overflow-y-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-50 text-slate-500 border-y border-slate-200">
                      <tr>
                        <th className="px-3 py-2 font-medium">Asset / Ticker</th>
                        <th className="px-3 py-2 font-medium">Article</th>
                        <th className="px-3 py-2 font-medium">Sentiment</th>
                        <th className="px-3 py-2 font-medium text-right">Confidence</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {relevance.matches.map((m, idx) => (
                        <tr key={idx} className="hover:bg-slate-50/50">
                          <td className="px-3 py-2 font-semibold text-slate-900">
                            {m.matched_entity}
                            <span className="text-[10px] text-slate-400 block font-normal capitalize">
                              {m.entity_type}
                            </span>
                          </td>
                          <td className="px-3 py-2 max-w-xs truncate">
                            <a
                              href={m.canonical_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-primary-600 hover:underline flex items-center gap-1 truncate"
                            >
                              <span className="truncate">{m.article_title}</span>
                              <ExternalLink className="w-3 h-3 shrink-0 text-slate-400" />
                            </a>
                            <span className="text-[10px] text-slate-400">{m.source_name}</span>
                          </td>
                          <td className="px-3 py-2">
                            <Badge
                              variant={
                                m.sentiment_label === "positive"
                                  ? "success"
                                  : m.sentiment_label === "negative"
                                  ? "danger"
                                  : "outline"
                              }
                            >
                              {m.sentiment_label || "neutral"}
                            </Badge>
                          </td>
                          <td className="px-3 py-2 text-right font-medium text-slate-600">
                            {(m.match_confidence * 100).toFixed(0)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right 1 Col: Sector Breakdown */}
        <div className="space-y-6">
          <Card>
            <CardHeader className="py-3">
              <CardTitle className="text-sm font-semibold text-slate-800">
                Sector Sentiment Breakdown
              </CardTitle>
              <CardDescription className="text-xs">
                FinBERT aggregation by economic sector.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              {summary && summary.sector_breakdown && summary.sector_breakdown.length > 0 ? (
                <div className="divide-y divide-slate-100">
                  {summary.sector_breakdown.map((sec, idx) => (
                    <div key={idx} className="p-3 text-xs space-y-1.5 hover:bg-slate-50/50">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-800 capitalize">
                          {sec.sector}
                        </span>
                        <Badge
                          variant={
                            sec.net_sentiment_score > 0.1
                              ? "success"
                              : sec.net_sentiment_score < -0.1
                              ? "danger"
                              : "outline"
                          }
                        >
                          {sec.net_sentiment_score > 0 ? "+" : ""}
                          {sec.net_sentiment_score.toFixed(2)}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between text-[11px] text-slate-500">
                        <span>{sec.article_count} articles</span>
                        <span>
                          <strong className="text-emerald-600">{(sec.positive_percentage * 100).toFixed(0)}% +</strong> /{" "}
                          <strong className="text-rose-600">{(sec.negative_percentage * 100).toFixed(0)}% -</strong>
                        </span>
                      </div>
                      {/* Mini bar */}
                      <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden flex">
                        <div
                          className="bg-emerald-500 h-full"
                          style={{ width: `${sec.positive_percentage * 100}%` }}
                        />
                        <div
                          className="bg-slate-300 h-full"
                          style={{ width: `${sec.neutral_percentage * 100}%` }}
                        />
                        <div
                          className="bg-rose-500 h-full"
                          style={{ width: `${sec.negative_percentage * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 text-center text-xs text-slate-400">
                  No sector classifications available in this time window.
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Raw Ingested Articles Feed */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <Newspaper className="w-4 h-4 text-slate-600" />
                Financial Headlines & Ingested Stories ({totalArticles})
              </CardTitle>
              <CardDescription>
                Verified news feed articles scored by the FinBERT sentiment model.
              </CardDescription>
            </div>

            {/* Filter buttons */}
            <div className="flex items-center gap-2 flex-wrap">
              <form onSubmit={handleSearchSubmit} className="relative">
                <Input
                  type="text"
                  placeholder="Search articles..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-44 sm:w-56 text-xs pr-8"
                />
                <button
                  type="submit"
                  className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600"
                >
                  <Search className="w-3.5 h-3.5" />
                </button>
              </form>

              <div className="flex items-center bg-slate-100 p-0.5 rounded-lg text-xs">
                {(["all", "positive", "negative", "neutral"] as const).map((label) => (
                  <button
                    key={label}
                    onClick={() => {
                      setSentimentFilter(label);
                      setPage(0);
                    }}
                    className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                      sentimentFilter === label
                        ? "bg-white text-slate-900 shadow-sm font-semibold"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    {label.charAt(0).toUpperCase() + label.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {articles.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500">
              No news articles found matching the current criteria. Click &ldquo;Refresh Feeds&rdquo; to fetch the latest headlines.
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {articles.map((art) => (
                <div
                  key={art.id}
                  className="p-4 hover:bg-slate-50/60 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                >
                  <div className="space-y-1 max-w-3xl">
                    <div className="flex items-center gap-2 flex-wrap">
                      {art.source_name && (
                        <span className="font-semibold text-slate-700 bg-slate-100 px-2 py-0.5 rounded text-[11px]">
                          {art.source_name}
                        </span>
                      )}
                      {art.published_at && (
                        <span className="text-slate-400 text-[11px]">
                          {formatDate(art.published_at)}
                        </span>
                      )}
                    </div>
                    <a
                      href={art.canonical_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium text-slate-900 hover:text-primary-600 hover:underline block text-sm"
                    >
                      {art.title}
                    </a>
                    {art.summary && (
                      <p className="text-slate-500 line-clamp-2 text-xs">
                        {art.summary}
                      </p>
                    )}
                  </div>

                  <div className="shrink-0 flex sm:flex-col items-center sm:items-end gap-2">
                    <Badge
                      variant={
                        art.sentiment_label === "positive"
                          ? "success"
                          : art.sentiment_label === "negative"
                          ? "danger"
                          : "outline"
                      }
                    >
                      {art.sentiment_label ? art.sentiment_label.toUpperCase() : "UNSCORED"}
                    </Badge>
                    {art.sentiment_score && (
                      <span className="text-[11px] text-slate-400">
                        Conf: {(parseFloat(art.sentiment_score) * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalArticles > pageSize && (
            <div className="p-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
              <span>
                Showing {page * pageSize + 1}–{Math.min((page + 1) * pageSize, totalArticles)} of {totalArticles}
              </span>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 0}
                  onClick={() => setPage(page - 1)}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={(page + 1) * pageSize >= totalArticles}
                  onClick={() => setPage(page + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <RegulatoryDisclaimer />
    </div>
  );
}
