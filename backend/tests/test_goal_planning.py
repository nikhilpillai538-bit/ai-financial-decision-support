"""
Unit tests for Phase 8 Goal-Based Investment Planning.

Tests:
- Goal progress percentage and remaining amount calculations
- Horizon calculation in months
- Projections with no initial investment
- Projections with existing investment
- Integration with linked portfolio valuation (priced holdings)
- Unpriced holdings warning detection
- Positive and zero return assumptions
- Shortfall, surplus, and status assessment (ahead, on_track, behind, expired)
- Required monthly contribution (Reverse SIP) to bridge goal shortfall
- Expired or overdue goal deadlines
- Standalone goal planning without a database goal
"""

from datetime import date, timedelta
from decimal import Decimal
import pytest

from app.db.models import AssetModel, InvestmentGoalModel, PortfolioHoldingModel, PortfolioModel
from app.goal_planning import (
    _compute_remaining_months,
    calculate_goal_projection,
    calculate_standalone_goal_plan,
)
from app.goal_schemas import GoalProjectionRequest, StandaloneGoalPlanRequest


class TestHorizonCalculation:
    """Tests for remaining months calculation."""

    def test_past_date_returns_zero(self):
        today = date(2025, 6, 1)
        past = date(2025, 1, 1)
        assert _compute_remaining_months(past, today) == 0

    def test_today_returns_zero(self):
        today = date(2025, 6, 1)
        assert _compute_remaining_months(today, today) == 0

    def test_one_year_returns_12_months(self):
        today = date(2025, 1, 1)
        future = date(2026, 1, 1)
        assert _compute_remaining_months(future, today) == 12

    def test_half_year_returns_6_months(self):
        today = date(2025, 1, 1)
        future = date(2025, 7, 1)
        assert _compute_remaining_months(future, today) == 6


class TestGoalProjectionEngine:
    """Tests for calculate_goal_projection."""

    def _make_goal(self, **kwargs) -> InvestmentGoalModel:
        defaults = {
            "id": "goal-test-1",
            "user_id": "user-test-1",
            "name": "Higher Education Fund",
            "target_amount": Decimal("1000000.00"),  # 10 Lakhs
            "target_date": date(2028, 1, 1),
            "priority": "high",
            "status": "in_progress",
            "current_amount": Decimal("200000.00"),
            "expected_annual_return": Decimal("0.1200"),  # 12%
            "monthly_contribution": Decimal("15000.00"),
        }
        defaults.update(kwargs)
        return InvestmentGoalModel(**defaults)

    def test_goal_with_existing_investment_and_positive_return(self):
        goal = self._make_goal()
        as_of = date(2025, 1, 1)  # 36 months horizon
        req = GoalProjectionRequest(as_of_date=as_of, rate_convention="nominal")

        res = calculate_goal_projection(goal, req)

        assert res.goal_id == "goal-test-1"
        assert res.target_amount == Decimal("1000000.00")
        assert res.current_amount == Decimal("200000.00")
        assert res.progress_percentage == Decimal("20.00")
        assert res.remaining_amount == Decimal("800000.00")
        assert res.remaining_months == 36
        assert res.projected_future_value > Decimal("900000.00")
        assert res.required_monthly_contribution > Decimal("0.00")
        assert len(res.schedule) == 3  # 3 annual checkpoints

    def test_goal_with_zero_initial_investment(self):
        goal = self._make_goal(current_amount=Decimal("0.00"), monthly_contribution=Decimal("25000.00"))
        as_of = date(2025, 1, 1)
        req = GoalProjectionRequest(as_of_date=as_of, rate_convention="nominal")

        res = calculate_goal_projection(goal, req)

        assert res.current_amount == Decimal("0.00")
        assert res.progress_percentage == Decimal("0.00")
        assert res.remaining_amount == Decimal("1000000.00")
        assert res.projected_future_value > Decimal("0.00")

    def test_goal_with_zero_return_assumption(self):
        goal = self._make_goal(
            current_amount=Decimal("100000.00"),
            monthly_contribution=Decimal("10000.00"),
            expected_annual_return=Decimal("0.0000"),
        )
        as_of = date(2025, 1, 1)
        req = GoalProjectionRequest(
            as_of_date=as_of,
            expected_annual_return=Decimal("0.0000"),
            rate_convention="nominal",
        )

        res = calculate_goal_projection(goal, req)

        # 36 months * 10,000 + 100,000 = 460,000
        assert res.projected_future_value == Decimal("460000.00")
        assert res.shortfall_or_surplus == Decimal("-540000.00")
        assert res.is_on_track is False
        assert res.status_assessment == "behind"
        # Required SIP to reach 1,000,000 from 100,000 over 36 mos = 900,000 / 36 = 25,000
        assert res.required_monthly_contribution == Decimal("25000.00")

    def test_status_assessment_ahead_on_track_and_behind(self):
        # 1. Behind: planned 5,000 vs required ~16,000
        goal_behind = self._make_goal(monthly_contribution=Decimal("5000.00"))
        res_behind = calculate_goal_projection(goal_behind, GoalProjectionRequest(as_of_date=date(2025, 1, 1)))
        assert res_behind.status_assessment == "behind"
        assert res_behind.is_on_track is False
        assert res_behind.contribution_difference < Decimal("0.00")

        # 2. Ahead: planned 40,000 produces > 5% surplus
        goal_ahead = self._make_goal(monthly_contribution=Decimal("40000.00"))
        res_ahead = calculate_goal_projection(goal_ahead, GoalProjectionRequest(as_of_date=date(2025, 1, 1)))
        assert res_ahead.status_assessment == "ahead"
        assert res_ahead.is_on_track is True
        assert res_ahead.shortfall_or_surplus > Decimal("50000.00")

    def test_expired_goal_deadline(self):
        goal = self._make_goal(target_date=date(2024, 1, 1))
        as_of = date(2025, 1, 1)  # Target is in the past
        res = calculate_goal_projection(goal, GoalProjectionRequest(as_of_date=as_of))

        assert res.remaining_months == 0
        assert res.status_assessment == "expired"
        assert any("passed" in w for w in res.warnings)
        assert res.projected_future_value == res.current_amount

    def test_goal_integration_with_linked_portfolio(self):
        """Priced holdings in linked portfolio are automatically used as current investment."""
        asset = AssetModel(
            id="a-1",
            name="Nifty 50 ETF",
            symbol="NIFTYBEES",
            asset_class="equity",
            currency="INR",
        )
        holding1 = PortfolioHoldingModel(
            id="h-1",
            portfolio_id="port-1",
            asset_id="a-1",
            quantity=Decimal("1000.0000"),
            average_purchase_price=Decimal("200.00"),
            current_price=Decimal("250.00"),  # Value: 250,000
            asset=asset,
        )
        portfolio = PortfolioModel(
            id="port-1",
            user_id="user-test-1",
            name="Wealth Portfolio",
            base_currency="INR",
            holdings=[holding1],
        )

        goal = self._make_goal(
            portfolio_id="port-1",
            current_amount=None,  # Not hardcoded; must pull from portfolio
            target_amount=Decimal("500000.00"),
        )
        as_of = date(2025, 1, 1)
        res = calculate_goal_projection(goal, GoalProjectionRequest(as_of_date=as_of), portfolio=portfolio)

        assert res.current_amount == Decimal("250000.00")
        assert res.progress_percentage == Decimal("50.00")
        assert res.remaining_amount == Decimal("250000.00")

    def test_linked_portfolio_unpriced_holdings_warning(self):
        asset = AssetModel(id="a-1", name="Unpriced Real Estate", asset_class="real_estate", currency="INR")
        holding = PortfolioHoldingModel(
            id="h-1",
            portfolio_id="port-1",
            asset_id="a-1",
            quantity=Decimal("1.0000"),
            average_purchase_price=Decimal("500000.00"),
            current_price=None,  # Unpriced
            asset=asset,
        )
        portfolio = PortfolioModel(
            id="port-1",
            user_id="user-test-1",
            name="Unpriced Portfolio",
            base_currency="INR",
            holdings=[holding],
        )
        goal = self._make_goal(portfolio_id="port-1", current_amount=None)

        res = calculate_goal_projection(goal, GoalProjectionRequest(as_of_date=date(2025, 1, 1)), portfolio=portfolio)
        assert res.current_amount == Decimal("0.00")
        assert any("unpriced holding(s)" in w for w in res.warnings)


class TestStandaloneGoalPlan:
    """Tests for calculate_standalone_goal_plan."""

    def test_standalone_plan_execution(self):
        req = StandaloneGoalPlanRequest(
            goal_name="Home Down Payment",
            target_amount=Decimal("1500000.00"),
            target_date=date(2029, 1, 1),
            current_amount=Decimal("300000.00"),
            expected_annual_return=Decimal("0.1000"),
            planned_monthly_contribution=Decimal("20000.00"),
            as_of_date=date(2025, 1, 1),
        )
        res = calculate_standalone_goal_plan(req)

        assert res.goal_name == "Home Down Payment"
        assert res.target_amount == Decimal("1500000.00")
        assert res.current_amount == Decimal("300000.00")
        assert res.progress_percentage == Decimal("20.00")
        assert res.remaining_months == 48
        assert res.projected_future_value > Decimal("1600000.00")
        assert res.status_assessment in ["on_track", "ahead"]
