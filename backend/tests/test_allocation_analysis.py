"""
Unit tests for deterministic asset allocation analysis.
"""

from decimal import Decimal
import uuid

import pytest

from app.allocation_analysis import calculate_allocation_analysis
from app.db.models import (
    AssetModel,
    PortfolioHoldingModel,
    PortfolioModel,
    TargetAllocationModel,
)


def _make_portfolio(base_currency: str = "INR") -> PortfolioModel:
    return PortfolioModel(
        id=str(uuid.uuid4()),
        user_id="user-456",
        name="Retirement Allocation",
        base_currency=base_currency,
        holdings=[],
    )


def _add_holding(p: PortfolioModel, name: str, asset_class: str, value: str, currency: str = "INR"):
    asset = AssetModel(id=str(uuid.uuid4()), name=name, asset_class=asset_class, currency=currency)
    # 1 unit at value
    h = PortfolioHoldingModel(
        id=str(uuid.uuid4()),
        portfolio_id=p.id,
        asset_id=asset.id,
        quantity=Decimal("1.00"),
        average_purchase_price=Decimal(value),
        current_price=Decimal(value),
        asset=asset,
    )
    p.holdings.append(h)


def _make_target(p_id: str, targets: dict, is_draft: bool = False) -> TargetAllocationModel:
    return TargetAllocationModel(
        id=str(uuid.uuid4()),
        portfolio_id=p_id,
        user_id="user-456",
        targets={k: str(v) for k, v in targets.items()},
        is_draft=is_draft,
    )


class TestAssetAllocationAnalysis:
    """Tests for calculate_allocation_analysis."""

    def test_overweight_and_underweight_identification(self):
        p = _make_portfolio()
        # Current: 7000 equity (70%), 3000 debt (30%)
        _add_holding(p, "Equities ETF", "equity", "7000.00")
        _add_holding(p, "Bonds ETF", "debt", "3000.00")

        # Target: 60% equity, 40% debt
        target = _make_target(p.id, {"equity": 60.00, "debt": 40.00}, is_draft=False)

        res = calculate_allocation_analysis(p, target)

        assert res.has_target_allocation is True
        assert res.is_target_draft is False
        assert res.is_analysis_reliable is True

        cmp_map = {c.asset_class: c for c in res.comparisons}
        assert cmp_map["equity"].status == "overweight"
        assert cmp_map["equity"].difference_percentage_points == Decimal("10.00")
        assert cmp_map["debt"].status == "underweight"
        assert cmp_map["debt"].difference_percentage_points == Decimal("-10.00")

        assert "equity" in res.overweight_classes
        assert "debt" in res.underweight_classes

    def test_missing_holding_class_identified(self):
        p = _make_portfolio()
        # 100% equity
        _add_holding(p, "Equities", "equity", "10000.00")

        # Target: 80% equity, 20% commodities_gold
        target = _make_target(p.id, {"equity": 80.00, "commodities_gold": 20.00})

        res = calculate_allocation_analysis(p, target)

        assert "commodities_gold" in res.missing_holding_classes
        gold_cmp = next(c for c in res.comparisons if c.asset_class == "commodities_gold")
        assert gold_cmp.current_market_value == Decimal("0.00")
        assert gold_cmp.difference_percentage_points == Decimal("-20.00")
        assert gold_cmp.status == "underweight"

    def test_unspecified_target_class_identified(self):
        p = _make_portfolio()
        _add_holding(p, "Equities", "equity", "8000.00")
        _add_holding(p, "Crypto/NFT", "other", "2000.00")

        # Target only has equity
        target = _make_target(p.id, {"equity": 100.00})

        res = calculate_allocation_analysis(p, target)

        assert "other" in res.unspecified_target_classes
        other_cmp = next(c for c in res.comparisons if c.asset_class == "other")
        assert other_cmp.status == "unspecified_target"
        assert other_cmp.difference_percentage_points is None

    def test_draft_target_flagged_as_unreliable(self):
        p = _make_portfolio()
        _add_holding(p, "Equities", "equity", "5000.00")
        target = _make_target(p.id, {"equity": 50.00}, is_draft=True)

        res = calculate_allocation_analysis(p, target)

        assert res.is_target_draft is True
        assert res.is_analysis_reliable is False
        assert any("draft" in w.lower() for w in res.warnings)

    def test_unpriced_holdings_flagged_as_unreliable(self):
        p = _make_portfolio()
        _add_holding(p, "Equities", "equity", "5000.00")
        # Add unpriced holding
        asset_unpriced = AssetModel(id=str(uuid.uuid4()), name="Private Equity", asset_class="equity", currency="INR")
        p.holdings.append(
            PortfolioHoldingModel(
                id=str(uuid.uuid4()),
                portfolio_id=p.id,
                asset_id=asset_unpriced.id,
                quantity=Decimal("1.00"),
                average_purchase_price=Decimal("1000.00"),
                current_price=None,
                asset=asset_unpriced,
            )
        )
        target = _make_target(p.id, {"equity": 100.00})

        res = calculate_allocation_analysis(p, target)

        assert res.is_analysis_reliable is False
        assert res.valuation_coverage_percentage == Decimal("50.00")
        assert any("coverage" in w.lower() for w in res.warnings)

    def test_no_target_allocation(self):
        p = _make_portfolio()
        _add_holding(p, "Equities", "equity", "5000.00")

        res = calculate_allocation_analysis(p, None)

        assert res.has_target_allocation is False
        assert res.is_analysis_reliable is False
        assert any("no target allocation" in w.lower() for w in res.warnings)

    def test_empty_portfolio_allocation_analysis(self):
        p = _make_portfolio()
        target = _make_target(p.id, {"equity": 60.00, "debt": 40.00})

        res = calculate_allocation_analysis(p, target)

        assert res.is_analysis_reliable is False
        for c in res.comparisons:
            assert c.status == "no_holdings"
            assert c.difference_percentage_points is None
