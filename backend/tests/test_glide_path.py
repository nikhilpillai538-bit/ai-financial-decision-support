"""
Unit tests for Phase 8 Risk-Aware Investment Glide Path Service.

Tests:
- Checkpoint timeline generation (ordered dates from start_date to target_date)
- Starting allocation preserved at first milestone
- Ending allocation achieved at final milestone
- Strict 100.00% sum of weights at every intermediate checkpoint
- Monotonic de-risking behavior
- Default risk-profile allocations (conservative, moderate, aggressive)
- Validation errors for invalid target dates, negative weights, invalid asset classes, and sums != 100%
- Risk level categorization and explainable commentary
"""

from datetime import date
from decimal import Decimal
import pytest

from app.glide_path import generate_glide_path
from app.goal_schemas import GlidePathRequest


class TestGlidePathService:
    """Tests for generate_glide_path."""

    def test_basic_linear_glide_path_checkpoints(self):
        start = date(2025, 1, 1)
        target = date(2030, 1, 1)  # 5 years
        start_alloc = {"equity": Decimal("80.00"), "fixed_income": Decimal("15.00"), "cash": Decimal("5.00")}
        end_alloc = {"equity": Decimal("20.00"), "fixed_income": Decimal("60.00"), "cash": Decimal("20.00")}

        req = GlidePathRequest(
            starting_allocation=start_alloc,
            ending_allocation=end_alloc,
            interval_months=12,
        )

        res = generate_glide_path(start, target, req, goal_id="g-1", goal_name="Retirement")

        assert res.goal_id == "g-1"
        assert res.start_date == start
        assert res.target_date == target
        assert res.total_horizon_years == Decimal("5.00")
        assert len(res.checkpoints) >= 5

        # Checkpoint 0: starting allocation preserved
        cp0 = res.checkpoints[0]
        assert cp0.checkpoint_date == start
        assert cp0.allocation_weights["equity"] == Decimal("80.00")
        assert cp0.risk_level == "aggressive"

        # Final checkpoint: ending allocation achieved
        cp_final = res.checkpoints[-1]
        assert cp_final.checkpoint_date == target
        assert cp_final.allocation_weights["equity"] == Decimal("20.00")
        assert cp_final.risk_level == "conservative"

        # Check all checkpoints for 100% sum and monotonic equity reduction
        prev_equity = Decimal("100.00")
        for cp in res.checkpoints:
            total_w = sum(cp.allocation_weights.values())
            assert total_w == Decimal("100.00")
            cur_equity = cp.allocation_weights["equity"]
            assert cur_equity <= prev_equity
            prev_equity = cur_equity

    def test_default_risk_profile_allocations(self):
        """When user does not supply custom weights, defaults for risk_profile are applied."""
        start = date(2025, 1, 1)
        target = date(2028, 1, 1)

        req_agg = GlidePathRequest(risk_profile="aggressive")
        res_agg = generate_glide_path(start, target, req_agg)
        assert res_agg.starting_allocation["equity"] == Decimal("85.00")

        req_con = GlidePathRequest(risk_profile="conservative")
        res_con = generate_glide_path(start, target, req_con)
        assert res_con.starting_allocation["equity"] == Decimal("50.00")

    def test_validation_target_date_before_start_date_raises_error(self):
        start = date(2025, 1, 1)
        target = date(2024, 1, 1)
        with pytest.raises(ValueError, match="must be after start date"):
            generate_glide_path(start, target, GlidePathRequest())

    def test_validation_weights_not_summing_to_100_raises_error(self):
        start = date(2025, 1, 1)
        target = date(2028, 1, 1)
        bad_alloc = {"equity": Decimal("50.00"), "fixed_income": Decimal("20.00")}  # Sums to 70%
        req = GlidePathRequest(starting_allocation=bad_alloc)
        with pytest.raises(ValueError, match="must sum to 100.00%"):
            generate_glide_path(start, target, req)

    def test_validation_negative_weight_raises_error(self):
        start = date(2025, 1, 1)
        target = date(2028, 1, 1)
        bad_alloc = {"equity": Decimal("110.00"), "fixed_income": Decimal("-10.00")}
        req = GlidePathRequest(starting_allocation=bad_alloc)
        with pytest.raises(ValueError, match="cannot be negative"):
            generate_glide_path(start, target, req)

    def test_validation_invalid_asset_class_raises_error(self):
        start = date(2025, 1, 1)
        target = date(2028, 1, 1)
        bad_alloc = {"fake_class": Decimal("50.00"), "equity": Decimal("50.00")}
        req = GlidePathRequest(starting_allocation=bad_alloc)
        with pytest.raises(ValueError, match="Invalid asset class"):
            generate_glide_path(start, target, req)
