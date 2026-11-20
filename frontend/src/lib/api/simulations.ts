import { apiClient } from "./client";

export interface StressPreset {
  id: string;
  name: string;
  description: string;
  asset_class_shocks: Record<string, number>;
}

export interface HoldingShockResult {
  symbol: string;
  asset_name: string;
  asset_class: string;
  baseline_value: string;
  shock_percentage: string;
  stressed_value: string;
  absolute_change: string;
  contribution_to_loss_pct: string;
}

export interface AssetClassShockResult {
  asset_class: string;
  baseline_value: string;
  baseline_weight_pct: string;
  shock_percentage: string;
  stressed_value: string;
  stressed_weight_pct: string;
  absolute_change: string;
  contribution_to_loss_pct: string;
}

export interface StressTestResponse {
  scenario_name: string;
  description: string;
  baseline_portfolio_value: string;
  stressed_portfolio_value: string;
  absolute_change: string;
  percentage_change: string;
  holdings_breakdown: HoldingShockResult[];
  asset_class_breakdown: AssetClassShockResult[];
  warnings: string[];
  assumptions: string[];
  disclaimers: string[];
}

export interface StressTestRequest {
  portfolio_id?: string;
  scenario?: string;
  custom_shocks?: Array<{
    asset_class?: string;
    symbol?: string;
    shock_percentage: number;
  }>;
  custom_holdings?: Array<{
    symbol: string;
    asset_class: string;
    current_value: number;
  }>;
  name?: string;
}

export interface BacktestEquityPoint {
  date: string;
  portfolio_value: string;
  portfolio_return_pct: string;
  benchmark_value?: string;
  benchmark_return_pct?: string;
  drawdown_pct: string;
}

export interface RebalanceEventItem {
  date: string;
  portfolio_value_pre: string;
  turnover_value: string;
  transaction_cost: string;
  pre_weights: Record<string, string>;
  post_weights: Record<string, string>;
}

export interface BacktestBenchmarkSummary {
  symbol: string;
  final_value: string;
  cumulative_return_pct: string;
  annualized_return_cagr_pct: string;
  annualized_volatility_pct: string;
  sharpe_ratio: string;
  max_drawdown_pct: string;
}

export interface BacktestResponse {
  symbols: string[];
  start_date: string;
  end_date: string;
  trading_days: number;
  initial_value: string;
  final_value: string;
  cumulative_return_pct: string;
  annualized_return_cagr_pct: string;
  annualized_volatility_pct: string;
  sharpe_ratio: string;
  max_drawdown_pct: string;
  calmar_ratio: string;
  total_transaction_costs: string;
  rebalance_count: number;
  benchmark_summary?: BacktestBenchmarkSummary;
  equity_curve: BacktestEquityPoint[];
  rebalance_events: RebalanceEventItem[];
  warnings: string[];
  assumptions: string[];
  disclaimers: string[];
}

export interface BacktestRequest {
  portfolio_id?: string;
  symbols?: string[];
  weights?: Record<string, number>;
  initial_value?: number;
  start_date?: string;
  end_date?: string;
  rebalance_frequency?: string;
  fee_bps?: number;
  benchmark_symbol?: string;
  risk_free_rate_pct?: number;
}

export interface MonteCarloPercentilePoint {
  month: number;
  year: number;
  p5: string;
  p25: string;
  p50: string;
  p75: string;
  p95: string;
  sample_paths: string[];
}

export interface TerminalWealthStats {
  mean: string;
  median: string;
  std_dev: string;
  p5: string;
  p25: string;
  p75: string;
  p95: string;
  min: string;
  max: string;
}

export interface MonteCarloResponse {
  initial_value: string;
  monthly_contribution: string;
  horizon_months: number;
  num_simulations: number;
  annual_return_assumed_pct: string;
  annual_volatility_assumed_pct: string;
  target_amount?: string;
  goal_success_probability_pct?: string;
  terminal_wealth: TerminalWealthStats;
  percentile_trajectory: MonteCarloPercentilePoint[];
  warnings: string[];
  assumptions: string[];
  disclaimers: string[];
}

export interface MonteCarloRequest {
  portfolio_id?: string;
  initial_value?: number;
  monthly_contribution?: number;
  horizon_months?: number;
  num_simulations?: number;
  expected_annual_return_pct?: number;
  annual_volatility_pct?: number;
  target_amount?: number;
  seed?: number;
}

export interface ScenarioComparisonItem {
  name: string;
  monthly_contribution: string;
  horizon_months: number;
  target_date: string;
  expected_annual_return_pct: string;
  deterministic_projected_value: string;
  deterministic_gap: string;
  deterministic_required_sip: string;
  mc_median_projected_value: string;
  mc_p5_downside_value: string;
  mc_p95_upside_value: string;
  mc_goal_success_probability_pct: string;
  contribution_delta_from_baseline: string;
  success_probability_delta_pct: string;
}

export interface GoalScenarioComparisonResponse {
  goal_id?: string;
  goal_name: string;
  target_amount: string;
  baseline: ScenarioComparisonItem;
  compared_scenarios: ScenarioComparisonItem[];
  insights: string[];
  assumptions: string[];
  disclaimers: string[];
}

export interface GoalScenarioOption {
  name: string;
  monthly_contribution?: number;
  horizon_months?: number;
  target_date?: string;
  expected_annual_return_pct?: number;
  initial_amount?: number;
}

export interface GoalScenarioComparisonRequest {
  goal_id?: string;
  baseline_target_amount?: number;
  baseline_current_amount?: number;
  baseline_monthly_contribution?: number;
  baseline_target_date?: string;
  baseline_annual_return_pct?: number;
  scenarios: GoalScenarioOption[];
  num_simulations?: number;
  seed?: number;
}

// ---------------------------------------------------------------------------
// API Methods
// ---------------------------------------------------------------------------

export async function fetchStressPresets(): Promise<{ presets: StressPreset[] }> {
  return apiClient<{ presets: StressPreset[] }>("/portfolio/stress-test-presets");
}

export async function runStressTest(payload: StressTestRequest): Promise<StressTestResponse> {
  const path = payload.portfolio_id
    ? `/portfolios/${payload.portfolio_id}/stress-test`
    : "/portfolio/stress-tests";
  return apiClient<StressTestResponse>(path, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function runBacktest(payload: BacktestRequest): Promise<BacktestResponse> {
  const path = payload.portfolio_id
    ? `/portfolios/${payload.portfolio_id}/backtest`
    : "/portfolio/backtests";
  return apiClient<BacktestResponse>(path, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function runMonteCarlo(payload: MonteCarloRequest): Promise<MonteCarloResponse> {
  const path = payload.portfolio_id
    ? `/portfolios/${payload.portfolio_id}/monte-carlo`
    : "/portfolio/monte-carlo";
  return apiClient<MonteCarloResponse>(path, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function runGoalScenarioComparison(
  payload: GoalScenarioComparisonRequest
): Promise<GoalScenarioComparisonResponse> {
  const path = payload.goal_id
    ? `/goals/${payload.goal_id}/scenario-comparison`
    : "/goals/scenario-comparison";
  return apiClient<GoalScenarioComparisonResponse>(path, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
