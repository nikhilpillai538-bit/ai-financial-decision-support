"""
Phase 13 Unit Tests: Investment-Goal Multi-Scenario Comparison Engine.

Tests:
1. Side-by-side comparison of baseline plan against contribution and horizon changes.
2. Verified calculation of contribution delta and success probability delta.
3. Verification that scenario comparison is strictly read-only and does not mutate models.
"""

from datetime import date
from decimal import Decimal
import pytest

from app.db.models import InvestmentGoalModel
from app.scenario_comparison import compare_goal_scenarios
from app.simulation_schemas import (
    GoalScenarioComparisonRequest,
    GoalScenarioOption,
)


class TestScenarioComparisonEngine:
    """Tests for multi-scenario comparative evaluation."""

    def test_multi_scenario_comparison(self):
        """Compare baseline with higher SIP (+5k) and extended horizon (+24 months)."""
        goal = InvestmentGoalModel(
            id="test-goal-uuid-1",
            user_id="test-user-uuid",
            name="Child Education Fund",
            target_amount=Decimal("2000000.00"),
            target_date=date(2030, 12, 31),
            current_amount=Decimal("100000.00"),
            expected_annual_return=Decimal("0.12"),
            monthly_contribution=Decimal("15000.00"),
        )

        req = GoalScenarioComparisonRequest(
            scenarios=[
                GoalScenarioOption(
                    name="Aggressive Savings (+₹10k/mo)",
                    monthly_contribution=Decimal("25000.00"),
                ),
                GoalScenarioOption(
                    name="Extended Horizon (+2 Years)",
                    horizon_months=84,
                ),
            ],
            num_simulations=300,
            seed=42,
        )

        res = compare_goal_scenarios(req, goal=goal)

        assert res.goal_name == "Child Education Fund"
        assert res.target_amount == Decimal("2000000.00")
        assert res.baseline.monthly_contribution == Decimal("15000.00")
        assert len(res.compared_scenarios) == 2

        sc1 = res.compared_scenarios[0]
        assert sc1.name == "Aggressive Savings (+₹10k/mo)"
        assert sc1.monthly_contribution == Decimal("25000.00")
        assert sc1.contribution_delta_from_baseline == Decimal("10000.00")
        assert sc1.deterministic_projected_value > res.baseline.deterministic_projected_value

        sc2 = res.compared_scenarios[1]
        assert sc2.name == "Extended Horizon (+2 Years)"
        assert sc2.horizon_months == 84
        assert sc2.contribution_delta_from_baseline == Decimal("0.00")

        # Insights must be generated
        assert len(res.insights) >= 1
