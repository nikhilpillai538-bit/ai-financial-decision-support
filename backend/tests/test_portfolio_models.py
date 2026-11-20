"""
Tests for Phase 6 database models and Pydantic validation schemas.
"""

from datetime import date as ISODate, datetime, timezone
from decimal import Decimal
import uuid

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models import (
    AssetClass,
    AssetModel,
    InvestmentGoalModel,
    PortfolioHoldingModel,
    PortfolioModel,
    TargetAllocationModel,
    UserModel,
)
from app.portfolio_schemas import (
    AssetCreate,
    HoldingCreate,
    InvestmentGoalCreate,
    PortfolioCreate,
    TargetAllocationSetRequest,
)


@pytest.fixture()
def db_session() -> Session:
    """Isolated SQLite database session for model unit tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionMaker = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionMaker()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def test_user(db_session: Session) -> UserModel:
    user = UserModel(
        id=str(uuid.uuid4()),
        email="test_portfolio_user@example.com",
        password_hash="argon2id$mockhash",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestPortfolioModelAndValidation:
    """Tests for PortfolioModel constraints and PortfolioCreate schema validation."""

    def test_valid_portfolio_model_creation(self, db_session: Session, test_user: UserModel):
        portfolio = PortfolioModel(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            name="Retirement Growth",
            description="Long-term wealth accumulation",
            base_currency="INR",
        )
        db_session.add(portfolio)
        db_session.commit()
        db_session.refresh(portfolio)

        assert portfolio.id is not None
        assert portfolio.name == "Retirement Growth"
        assert portfolio.base_currency == "INR"
        assert portfolio.user_id == test_user.id

    def test_portfolio_name_cannot_be_empty(self, db_session: Session, test_user: UserModel):
        with pytest.raises(ValidationError):
            PortfolioCreate(name="   ")

    def test_portfolio_schema_normalizes_currency(self):
        p = PortfolioCreate(name="My Portfolio", base_currency="usd")
        assert p.base_currency == "USD"


class TestAssetModelAndValidation:
    """Tests for AssetModel and AssetCreate schema validation."""

    def test_valid_asset_creation(self, db_session: Session, test_user: UserModel):
        asset = AssetModel(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            symbol="TCS",
            name="Tata Consultancy Services",
            asset_class="equity",
            currency="INR",
            instrument_type="large_cap",
        )
        db_session.add(asset)
        db_session.commit()
        db_session.refresh(asset)

        assert asset.symbol == "TCS"
        assert asset.asset_class == "equity"

    def test_asset_class_validation(self):
        # Valid asset classes
        for ac in AssetClass:
            a = AssetCreate(name="Test Asset", asset_class=ac)
            assert a.asset_class == ac

        # Invalid asset class rejected by Pydantic
        with pytest.raises(ValidationError):
            AssetCreate(name="Test Asset", asset_class="cryptocurrency")

    def test_asset_name_cannot_be_empty(self):
        with pytest.raises(ValidationError):
            AssetCreate(name="   ", asset_class=AssetClass.EQUITY)


class TestPortfolioHoldingModelAndValidation:
    """Tests for PortfolioHoldingModel, Decimal fields, and unpriced handling."""

    def test_valid_holding_with_price(self, db_session: Session, test_user: UserModel):
        portfolio = PortfolioModel(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            name="Equities",
            base_currency="INR",
        )
        asset = AssetModel(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            symbol="INFY",
            name="Infosys Ltd",
            asset_class="equity",
            currency="INR",
        )
        db_session.add_all([portfolio, asset])
        db_session.commit()

        holding = PortfolioHoldingModel(
            id=str(uuid.uuid4()),
            portfolio_id=portfolio.id,
            asset_id=asset.id,
            quantity=Decimal("50.0000"),
            average_purchase_price=Decimal("1500.00"),
            current_price=Decimal("1850.50"),
            price_as_of=datetime.now(timezone.utc),
        )
        db_session.add(holding)
        db_session.commit()
        db_session.refresh(holding)

        assert holding.quantity == Decimal("50.0000")
        assert holding.current_price == Decimal("1850.50")
        assert holding.average_purchase_price == Decimal("1500.00")

    def test_unpriced_holding_preserves_none(self, db_session: Session, test_user: UserModel):
        portfolio = PortfolioModel(id=str(uuid.uuid4()), user_id=test_user.id, name="Test", base_currency="INR")
        asset = AssetModel(id=str(uuid.uuid4()), name="Unlisted Bond", asset_class="debt", currency="INR")
        db_session.add_all([portfolio, asset])
        db_session.commit()

        holding = PortfolioHoldingModel(
            id=str(uuid.uuid4()),
            portfolio_id=portfolio.id,
            asset_id=asset.id,
            quantity=Decimal("10.0000"),
            average_purchase_price=Decimal("1000.00"),
            current_price=None,  # explicitly unpriced
        )
        db_session.add(holding)
        db_session.commit()
        db_session.refresh(holding)

        assert holding.current_price is None

    def test_holding_validation_rejects_negative_or_zero_quantity(self):
        with pytest.raises(ValidationError):
            HoldingCreate(
                asset_id=str(uuid.uuid4()),
                quantity=Decimal("0.00"),
                average_purchase_price=Decimal("100.00"),
            )
        with pytest.raises(ValidationError):
            HoldingCreate(
                asset_id=str(uuid.uuid4()),
                quantity=Decimal("-5.00"),
                average_purchase_price=Decimal("100.00"),
            )

    def test_holding_validation_rejects_negative_prices(self):
        with pytest.raises(ValidationError):
            HoldingCreate(
                asset_id=str(uuid.uuid4()),
                quantity=Decimal("10.00"),
                average_purchase_price=Decimal("-1.00"),
            )
        with pytest.raises(ValidationError):
            HoldingCreate(
                asset_id=str(uuid.uuid4()),
                quantity=Decimal("10.00"),
                average_purchase_price=Decimal("100.00"),
                current_price=Decimal("-50.00"),
            )


class TestTargetAllocationValidation:
    """Tests for target allocation validation and draft handling."""

    def test_valid_allocation_summing_to_100_passes(self):
        req = TargetAllocationSetRequest(
            targets={
                "equity": Decimal("60.00"),
                "debt": Decimal("25.00"),
                "commodities_gold": Decimal("10.00"),
                "cash": Decimal("5.00"),
            },
            is_draft=False,
        )
        assert sum(req.targets.values()) == Decimal("100.00")

    def test_allocation_not_summing_to_100_rejected_when_not_draft(self):
        with pytest.raises(ValidationError) as exc:
            TargetAllocationSetRequest(
                targets={"equity": Decimal("60.00"), "debt": Decimal("20.00")},
                is_draft=False,
            )
        assert "sum to 100.00%" in str(exc.value)

    def test_incomplete_allocation_accepted_when_draft(self):
        req = TargetAllocationSetRequest(
            targets={"equity": Decimal("50.00")},
            is_draft=True,
        )
        assert req.is_draft is True
        assert req.targets["equity"] == Decimal("50.00")

    def test_invalid_asset_class_in_target_rejected(self):
        with pytest.raises(ValidationError) as exc:
            TargetAllocationSetRequest(
                targets={"non_existent_class": Decimal("100.00")},
                is_draft=True,
            )
        assert "Invalid asset class" in str(exc.value)


class TestInvestmentGoalModelAndValidation:
    """Tests for InvestmentGoalModel and InvestmentGoalCreate validation."""

    def test_valid_goal_creation(self, db_session: Session, test_user: UserModel):
        goal = InvestmentGoalModel(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            name="Child Education",
            target_amount=Decimal("1500000.00"),
            target_date=ISODate(2035, 6, 1),
            priority="high",
        )
        db_session.add(goal)
        db_session.commit()
        db_session.refresh(goal)

        assert goal.target_amount == Decimal("1500000.00")
        assert goal.priority == "high"

    def test_goal_validation_rejects_negative_or_zero_amount(self):
        with pytest.raises(ValidationError):
            InvestmentGoalCreate(
                name="New Home",
                target_amount=Decimal("0.00"),
                target_date=ISODate(2030, 1, 1),
            )
        with pytest.raises(ValidationError):
            InvestmentGoalCreate(
                name="New Home",
                target_amount=Decimal("-50000.00"),
                target_date=ISODate(2030, 1, 1),
            )
