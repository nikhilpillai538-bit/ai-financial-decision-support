/**
 * Full TypeScript interfaces for the AI Financial Decision Support System.
 * Matches backend FastAPI Pydantic request and response schemas (Phases 1–10).
 */

// ---------------------------------------------------------------------------
// 1. Authentication Types (Phase 5)
// ---------------------------------------------------------------------------

export interface User {
  id: string;
  email: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// ---------------------------------------------------------------------------
// 2. Transaction & Cash Flow Types (Phases 1 & 2)
// ---------------------------------------------------------------------------

export type TransactionType = "income" | "expense";

export interface Transaction {
  id: string;
  date: string;
  amount: string;
  transaction_type: TransactionType;
  category: string;
  description: string;
  created_at?: string;
}

export interface TransactionListResponse {
  items: Transaction[];
  total_count: number;
  limit: number;
  offset: number;
}

export interface FinancialSummary {
  total_income: string;
  total_expenses: string;
  net_savings: string;
  savings_rate_percentage: string;
  category_breakdown: Record<string, string>;
  transaction_count: number;
}

export interface CSVImportResult {
  total_rows: number;
  imported_count: number;
  duplicate_count: number;
  skipped_count: number;
  errors: string[];
}

// ---------------------------------------------------------------------------
// 3. Emergency Fund & Forecasting Types (Phase 3)
// ---------------------------------------------------------------------------

export interface EmergencyFundAnalysis {
  currency?: string;
  average_monthly_essential_expenses?: string;
  three_month_target?: string;
  six_month_target?: string;
  emergency_fund_balance?: string | null;
  balance_status?: string;
  shortfall_three_month?: string | null;
  shortfall_six_month?: string | null;
  months_of_coverage?: string | null;
  warnings?: string[];
  assumptions?: string[];
  // Backward compatibility aliases
  monthly_essential_expenses?: string;
  available_liquid_savings?: string;
  current_coverage_months?: string;
  recommended_target_3_months?: string;
  recommended_target_6_months?: string;
  shortfall_3_months?: string;
  shortfall_6_months?: string;
  status?: "insufficient" | "minimal" | "comfortable" | "surplus" | string;
  recommendations?: string[];
}

export interface DailyProjection {
  date: string;
  projected_balance?: string;
  closing_balance?: string;
  inflow?: string;
  projected_income?: string;
  outflow?: string;
  projected_expenses?: string;
  net_flow?: string;
  net_daily_flow?: string;
}

export interface CashFlowForecast {
  opening_balance?: string;
  projected_closing_balance?: string;
  total_projected_income?: string;
  total_projected_expenses?: string;
  net_projected_cash_flow?: string;
  daily_forecasts?: DailyProjection[];
  // Backward compatibility aliases
  forecast_days?: number;
  starting_balance?: string;
  projected_minimum_balance?: string;
  lowest_projected_date?: string;
  liquidity_warning?: string | null;
  projected_ending_balance?: string;
  daily_projections?: DailyProjection[];
  assumptions?: string[];
  warnings?: string[];
}

// ---------------------------------------------------------------------------
// 4. Portfolio & Assets Types (Phase 6)
// ---------------------------------------------------------------------------

export interface Asset {
  id: string;
  symbol: string | null;
  name: string;
  asset_class: "equity" | "debt" | "mutual_fund" | "etf" | "cash" | "commodities_gold" | "other";
  currency: string;
  instrument_type: string | null;
}

export interface Holding {
  id: string;
  portfolio_id: string;
  asset_id: string;
  asset?: Asset;
  quantity: string;
  average_purchase_price: string;
  current_price: string | null;
  current_value?: string | null;
}

export interface Portfolio {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  base_currency: string;
  created_at?: string;
  updated_at?: string;
}

export interface PortfolioValuation {
  portfolio_id: string;
  total_value: string;
  cost_basis: string;
  unrealized_gain_loss: string;
  unrealized_gain_loss_percentage: string;
  valued_at: string;
  unpriced_holdings_count: number;
  currency: string;
}

export interface AssetAllocationVariance {
  asset_class: string;
  actual_weight: string;
  target_weight: string;
  variance: string;
  status: "underweight" | "balanced" | "overweight";
}

export interface AssetAllocationAnalysis {
  portfolio_id: string;
  total_value: string;
  allocations: AssetAllocationVariance[];
  has_target: boolean;
  max_drift: string;
}

// ---------------------------------------------------------------------------
// 5. MPT Optimization & Risk Analytics (Phase 7)
// ---------------------------------------------------------------------------

export interface OptimizationResult {
  portfolio_id: string;
  objective?: "max_sharpe" | "min_volatility" | "target_return" | string;
  strategy?: string;
  expected_return: string | number;
  volatility?: string | number;
  expected_volatility?: string | number;
  sharpe_ratio: string | number;
  weights?: Record<string, string | number>;
  allocations?: Array<{
    asset_id?: string;
    symbol: string;
    name?: string;
    asset_class?: string;
    current_weight?: string | number;
    optimal_weight?: string | number;
    weight_delta?: string | number;
    current_value?: string | number;
    target_value?: string | number;
    action?: string;
    trade_amount?: string | number;
    target_shares?: string | number;
  }>;
  frontier?: Array<{ expected_return: string; volatility: string; sharpe_ratio: string }>;
  rebalancing_trades?: Array<{
    asset_symbol: string;
    action: "buy" | "sell" | "hold" | string;
    units: string;
    estimated_amount: string;
  }>;
  solver_status?: string;
  assumptions?: string[];
  warnings?: string[];
  methodology?: string;
}

export interface MarketDataSummary {
  symbols_count: number;
  data_points_count: number;
  date_range_start: string | null;
  date_range_end: string | null;
  available_symbols: string[];
}

// ---------------------------------------------------------------------------
// 6. Goals, SIP & Drift Types (Phase 8)
// ---------------------------------------------------------------------------

export interface InvestmentGoal {
  id: string;
  portfolio_id?: string | null;
  name: string;
  target_amount: string;
  target_date: string;
  current_amount: string;
  planned_monthly_contribution: string;
  created_at?: string;
}

export interface ForwardSIPResult {
  monthly_investment: string;
  annual_rate_percentage: string;
  tenure_months: number;
  step_up_percentage?: string | null;
  total_invested: string;
  future_value: string;
  estimated_returns: string;
  schedule?: Array<{
    month: number;
    investment: string;
    interest: string;
    balance: string;
  }>;
}

export interface ReverseSIPResult {
  target_amount: string;
  annual_rate_percentage: string;
  tenure_months: number;
  required_monthly_investment: string;
  total_invested: string;
  estimated_returns: string;
}

export interface GoalProjection {
  goal_id: string;
  projected_future_value: string;
  shortfall_or_surplus: string;
  required_monthly_sip: string;
  status_assessment: "on_track" | "minor_shortfall" | "critical_shortfall" | "ahead";
  remaining_months: number;
}

export interface PortfolioDriftItem {
  asset_class: string;
  current_weight?: string | number;
  target_weight?: string | number;
  current_weight_percentage?: string | number;
  target_weight_percentage?: string | number;
  drift?: string | number;
  absolute_drift_percentage_points?: string | number;
  relative_drift_percentage?: string | number;
  status?: string;
  action?: "buy" | "sell" | "rebalance" | "none" | string;
  recommended_trade_amount?: string;
  exceeds_threshold?: boolean;
}

export interface PortfolioDrift {
  portfolio_id: string;
  portfolio_name?: string;
  base_currency?: string;
  total_portfolio_value?: string | number;
  max_drift?: string;
  max_drift_percentage_points?: string | number;
  threshold_breached?: boolean;
  portfolio_exceeds_threshold?: boolean;
  drift_items?: PortfolioDriftItem[];
  asset_classes?: PortfolioDriftItem[];
  suggested_trades?: Array<{
    asset_class: string;
    action: "buy" | "sell" | string;
    trade_amount: string;
  }>;
}

export interface GlidePathMilestone {
  years_to_horizon: number;
  equity_weight: string;
  debt_weight: string;
  cash_weight: string;
  description: string;
}

// ---------------------------------------------------------------------------
// 7. News & Sentiment Types (Phase 10)
// ---------------------------------------------------------------------------

export interface NewsArticle {
  id: string;
  source_id: string;
  source_name: string | null;
  title: string;
  canonical_url: string;
  summary: string | null;
  published_at: string | null;
  fetched_at: string;
  sentiment_label: "positive" | "negative" | "neutral" | null;
  sentiment_score: string | null;
  sentiment_probabilities: Record<string, number> | null;
  sentiment_model: string | null;
  sentiment_analyzed_at: string | null;
}

export interface NewsArticleListResponse {
  articles: NewsArticle[];
  total_count: number;
  limit: number;
  offset: number;
}

export interface SectorSentimentItem {
  sector: string;
  article_count: number;
  positive_percentage: number;
  negative_percentage: number;
  neutral_percentage: number;
  net_sentiment_score: number;
}

export interface SentimentSummary {
  time_window: string;
  window_start: string;
  window_end: string;
  total_articles: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  positive_percentage: number;
  negative_percentage: number;
  neutral_percentage: number;
  average_sentiment_score: number;
  overall_sentiment_label: "bullish" | "bearish" | "neutral";
  sources_covered: string[];
  sector_breakdown: SectorSentimentItem[];
  warnings: string[];
}

export interface PortfolioNewsRelevanceItem {
  article_id: string;
  article_title: string;
  canonical_url: string;
  source_name: string;
  published_at: string | null;
  sentiment_label: string | null;
  sentiment_score: string | null;
  matched_entity: string;
  entity_type: "ticker" | "company" | "sector" | "macro";
  match_method: string;
  match_confidence: number;
  ambiguity_warning: string | null;
}

export interface PortfolioNewsRelevanceResponse {
  user_id: string;
  portfolio_id: string | null;
  matches_count: number;
  matches: PortfolioNewsRelevanceItem[];
}

export interface PortfolioNewsTheme {
  theme_title: string;
  sentiment: string;
  relevance_to_portfolio: string;
  articles: Array<{
    article_id: string;
    title: string;
    canonical_url: string;
    source_name: string;
    published_at: string | null;
    sentiment_label: string | null;
    sentiment_score: string | null;
  }>;
}

export interface PortfolioNewsInsights {
  user_id: string;
  generated_at: string;
  portfolio_name: string | null;
  executive_summary: string;
  themes: PortfolioNewsTheme[];
  relevance_matches_count: number;
  coverage_notes: string[];
  disclaimers: string[];
}

// ---------------------------------------------------------------------------
// 8. AI Financial Assistant Types (Phase 9)
// ---------------------------------------------------------------------------

export interface AIChatResponse {
  message: string;
  thread_id: string;
  domains_retrieved: string[];
  verified_metrics: Record<string, any>;
  suggested_followups: string[];
  warnings: string[];
}

export interface AIThreadSummary {
  thread_id: string;
  title: string;
  message_count: number;
  created_at: string;
  last_message_at: string;
}

export interface AIMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  domains_retrieved?: string[];
  verified_metrics?: Record<string, any>;
  suggested_followups?: string[];
  warnings?: string[];
}

export interface AIThreadDetail {
  thread_id: string;
  messages: AIMessage[];
}

export interface FinancialHealthReport {
  user_id: string;
  generated_at: string;
  executive_summary: string;
  health_score?: number;
  domain_insights: Record<string, string>;
  warnings: string[];
  disclaimers: string[];
}
