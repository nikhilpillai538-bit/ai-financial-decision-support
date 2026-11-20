"""
Unit tests for Phase 9 Deterministic Hypothetical Scenario Evaluator.
"""

from decimal import Decimal
import pytest

from app.ai.scenario_evaluator import ScenarioEvaluationResult, ScenarioEvaluator


class TestScenarioEvaluator:
    def test_evaluate_sip_increase_success(self):
        res = ScenarioEvaluator.evaluate_sip_increase(
            initial_investment=Decimal("0.00"),
            current_monthly_contribution=Decimal("10000.00"),
            additional_monthly_contribution=Decimal("5000.00"),
            annual_return_percentage=Decimal("12.00"),
            duration_months=36,
            rate_convention="effective",
        )
        assert isinstance(res, ScenarioEvaluationResult)
        assert res.scenario_type == "sip_increase"
        assert res.baseline["monthly_contribution"] == "10000.00"
        assert res.hypothetical["monthly_contribution"] == "15000.00"

        base_fv = Decimal(res.baseline["projected_future_value"])
        hypo_fv = Decimal(res.hypothetical["projected_future_value"])
        diff_fv = Decimal(res.difference["additional_future_value"])

        assert hypo_fv > base_fv
        assert diff_fv == (hypo_fv - base_fv)
        assert res.difference["additional_monthly_contribution"] == "5000.00"
        assert len(res.assumptions) > 0

    def test_evaluate_sip_increase_zero_increment_raises(self):
        with pytest.raises(ValueError, match="greater than zero"):
            ScenarioEvaluator.evaluate_sip_increase(
                initial_investment=Decimal("0.00"),
                current_monthly_contribution=Decimal("10000.00"),
                additional_monthly_contribution=Decimal("0.00"),
                annual_return_percentage=Decimal("12.00"),
                duration_months=24,
            )

    def test_evaluate_return_rate_comparison_success(self):
        res = ScenarioEvaluator.evaluate_return_rate_comparison(
            initial_investment=Decimal("10000.00"),
            monthly_contribution=Decimal("5000.00"),
            duration_months=60,
            rate_baseline_percentage=Decimal("8.00"),
            rate_hypothetical_percentage=Decimal("12.00"),
        )
        assert res.scenario_type == "return_comparison"
        base_fv = Decimal(res.baseline["projected_future_value"])
        hypo_fv = Decimal(res.hypothetical["projected_future_value"])
        assert hypo_fv > base_fv
        assert Decimal(res.difference["future_value_difference"]) > Decimal("0.00")

    def test_evaluate_target_horizon_change_success(self):
        # Extending horizon lowers the required monthly SIP
        res = ScenarioEvaluator.evaluate_target_horizon_change(
            target_amount=Decimal("1000000.00"),
            initial_investment=Decimal("50000.00"),
            annual_return_percentage=Decimal("10.00"),
            current_duration_months=36,
            new_duration_months=60,
        )
        assert res.scenario_type == "target_date_change"
        base_sip = Decimal(res.baseline["required_monthly_contribution"])
        hypo_sip = Decimal(res.hypothetical["required_monthly_contribution"])
        assert hypo_sip < base_sip
        assert res.difference["months_difference"] == 24

    def test_evaluate_target_horizon_change_invalid_months_raises(self):
        with pytest.raises(ValueError, match="greater than zero"):
            ScenarioEvaluator.evaluate_target_horizon_change(
                target_amount=Decimal("500000.00"),
                initial_investment=Decimal("0.00"),
                annual_return_percentage=Decimal("10.00"),
                current_duration_months=24,
                new_duration_months=0,
            )
