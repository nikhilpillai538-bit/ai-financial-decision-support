"""
Unit tests for the Phase 6 optimization readiness validation service.
"""

from decimal import Decimal
import uuid

import pytest

from app.db.models import (
    AssetModel,
    PortfolioHoldingModel,
    PortfolioModel,
    TargetAllocationModel,
)
from app.optimization_validator import validate_optimization_readiness


def _make_ready_portfolio() -> tuple[PortfolioModel, TargetAllocationModel]:
    p = PortfolioModel(
        id=str(uuid.uuid4()),
        user_id="user-ready",
        name="Ready Portfolio",
        base_currency="INR",
        holdings=[],
    )

    a1 = AssetModel(id=str(uuid.uuid4()), name="Equity Stock A", asset_class="equity", currency="INR")
    a2 = AssetModel(id=str(uuid.uuid4()), name="Debt Bond B", asset_class="debt", currency="INR")

    h1 = PortfolioHoldingModel(
        id=str(uuid.uuid4()),
        portfolio_id=p.id,
        asset_id=a1.id,
        quantity=Decimal("10.00"),
        average_purchase_price=Decimal("100.00"),
        current_price=Decimal("120.00"),
        asset=a1,
    )
    h2 = PortfolioHoldingModel(
        id=str(uuid.uuid4()),
        portfolio_id=p.id,
        asset_id=a2.id,
        quantity=Decimal("20.00"),
        average_purchase_price=Decimal("50.00"),
        current_price=Decimal("55.00"),
        asset=a2,
    )
    p.holdings = [h1, h2]

    target = TargetAllocationModel(
        id=str(uuid.uuid4()),
        portfolio_id=p.id,
        user_id="user-ready",
        targets={"equity": "60.00", "debt": "40.00"},
        is_draft=False,
    )

    return p, target


class TestOptimizationReadinessValidator:
    """Tests for validate_optimization_readiness."""

    def test_fully_ready_portfolio(self):
        p, target = _make_ready_portfolio()
        res = validate_optimization_readiness(p, target)

        assert res.is_ready_for_optimization is True
        assert res.readiness_status == "ready"
        assert len(res.blockers) == 0
        assert all(c.passed for c in res.checks)

    def test_blocked_by_unpriced_holdings(self):
        p, target = _make_ready_portfolio()
        # Make h2 unpriced
        p.holdings[1].current_price = None

        res = validate_optimization_readiness(p, target)

        assert res.is_ready_for_optimization is False
        assert any("missing user-supplied current prices" in b.lower() for b in res.blockers)

    def test_blocked_by_mixed_currencies(self):
        p, target = _make_ready_portfolio()
        # Change a2 currency to USD
        p.holdings[1].asset.currency = "USD"

        res = validate_optimization_readiness(p, target)

        assert res.is_ready_for_optimization is False
        assert any("mixed currencies" in b.lower() for b in res.blockers)

    def test_blocked_by_missing_target_allocation(self):
        p, _ = _make_ready_portfolio()
        res = validate_optimization_readiness(p, None)

        assert res.is_ready_for_optimization is False
        assert any("target asset allocation" in b.lower() for b in res.blockers)

    def test_blocked_by_draft_target_allocation(self):
        p, target = _make_ready_portfolio()
        target.is_draft = True

        res = validate_optimization_readiness(p, target)

        assert res.is_ready_for_optimization is False
        assert any("incomplete draft" in b.lower() for b in res.blockers)

    def test_blocked_by_empty_portfolio(self):
        p = PortfolioModel(id=str(uuid.uuid4()), user_id="u", name="Empty", base_currency="INR", holdings=[])
        target = TargetAllocationModel(id=str(uuid.uuid4()), portfolio_id=p.id, user_id="u", targets={"equity": "100.00"}, is_draft=False)

        res = validate_optimization_readiness(p, target)

        assert res.is_ready_for_optimization is False
        assert any("contains no holdings" in b.lower() for b in res.blockers)
