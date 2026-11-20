"""
Database repository for Phase 6: Portfolios, Assets, Holdings, Goals, and Allocations.

Encapsulates all database interactions behind clean methods, ensuring strict
user_id scoping and ACID compliance.
"""

from datetime import date as DateType, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    AssetModel,
    HistoricalPriceModel,
    InvestmentGoalModel,
    OptimizationRunModel,
    PortfolioHoldingModel,
    PortfolioModel,
    TargetAllocationModel,
)


class SQLPortfolioRepository:
    """Repository handling all database persistence for investment portfolios."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # -----------------------------------------------------------------------
    # Portfolio CRUD
    # -----------------------------------------------------------------------

    def create_portfolio(
        self,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        base_currency: str = "INR",
    ) -> PortfolioModel:
        """Create a new portfolio owned by user_id."""
        portfolio = PortfolioModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name.strip(),
            description=description.strip() if description else None,
            base_currency=base_currency.strip().upper(),
        )
        self.session.add(portfolio)
        self.session.commit()
        self.session.refresh(portfolio)
        return portfolio

    def get_portfolio(self, portfolio_id: str, user_id: str) -> Optional[PortfolioModel]:
        """Fetch a portfolio by ID, strictly verifying user ownership."""
        stmt = (
            select(PortfolioModel)
            .where(PortfolioModel.id == portfolio_id, PortfolioModel.user_id == user_id)
            .options(joinedload(PortfolioModel.holdings).joinedload(PortfolioHoldingModel.asset))
        )
        return self.session.scalars(stmt).unique().first()

    def list_portfolios(self, user_id: str) -> List[PortfolioModel]:
        """List all portfolios owned by user_id."""
        stmt = (
            select(PortfolioModel)
            .where(PortfolioModel.user_id == user_id)
            .options(joinedload(PortfolioModel.holdings))
            .order_by(PortfolioModel.created_at.desc())
        )
        return list(self.session.scalars(stmt).unique().all())

    def update_portfolio(
        self,
        portfolio_id: str,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        base_currency: Optional[str] = None,
    ) -> Optional[PortfolioModel]:
        """Update an existing portfolio owned by user_id."""
        portfolio = self.get_portfolio(portfolio_id, user_id)
        if not portfolio:
            return None

        if name is not None:
            portfolio.name = name.strip()
        if description is not None:
            portfolio.description = description.strip() if description else None
        if base_currency is not None:
            portfolio.base_currency = base_currency.strip().upper()

        portfolio.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(portfolio)
        return portfolio

    def delete_portfolio(
        self, portfolio_id: str, user_id: str, cascade: bool = False
    ) -> Tuple[bool, str]:
        """Delete a portfolio.

        If cascade is False and the portfolio contains active holdings or goals,
        the deletion is rejected to prevent accidental data loss.
        """
        portfolio = self.get_portfolio(portfolio_id, user_id)
        if not portfolio:
            return False, "Portfolio not found."

        holdings_count = len(portfolio.holdings) if portfolio.holdings else 0
        goals_stmt = select(InvestmentGoalModel).where(InvestmentGoalModel.portfolio_id == portfolio_id)
        goals_count = len(list(self.session.scalars(goals_stmt).all()))

        if not cascade and (holdings_count > 0 or goals_count > 0):
            return (
                False,
                f"Portfolio contains {holdings_count} active holding(s) and {goals_count} linked goal(s). "
                "Pass 'cascade=true' parameter to permanently delete the portfolio and all its contents.",
            )

        self.session.delete(portfolio)
        self.session.commit()
        return True, "Portfolio deleted successfully."

    # -----------------------------------------------------------------------
    # Asset Instrument CRUD
    # -----------------------------------------------------------------------

    def create_asset(
        self,
        name: str,
        asset_class: str,
        user_id: Optional[str] = None,
        symbol: Optional[str] = None,
        currency: str = "INR",
        instrument_type: Optional[str] = None,
    ) -> AssetModel:
        """Register a new asset instrument.

        If user_id is provided, it is owned by that user.
        If user_id is None, it is a global reference instrument.
        """
        clean_symbol = symbol.strip().upper() if symbol else None
        clean_currency = currency.strip().upper()

        # Check for duplicate instrument for this user
        if clean_symbol:
            query = select(AssetModel).where(
                AssetModel.symbol == clean_symbol,
                AssetModel.currency == clean_currency,
                (AssetModel.user_id == user_id) | (AssetModel.user_id.is_(None)),
            )
            existing = self.session.scalars(query).first()
            if existing:
                # Return existing rather than error, or raise if user tries to recreate identical
                return existing

        asset = AssetModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            symbol=clean_symbol,
            name=name.strip(),
            asset_class=asset_class.strip().lower(),
            currency=clean_currency,
            instrument_type=instrument_type.strip().lower() if instrument_type else None,
        )
        self.session.add(asset)
        self.session.commit()
        self.session.refresh(asset)
        return asset

    def get_asset(self, asset_id: str, user_id: Optional[str] = None) -> Optional[AssetModel]:
        """Fetch asset by ID if it is global (user_id IS NULL) or owned by the user."""
        stmt = select(AssetModel).where(AssetModel.id == asset_id)
        if user_id is not None:
            stmt = stmt.where((AssetModel.user_id.is_(None)) | (AssetModel.user_id == user_id))
        return self.session.scalars(stmt).first()

    def list_assets(
        self,
        user_id: Optional[str] = None,
        asset_class: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> List[AssetModel]:
        """List accessible assets (global + user's own), with optional filters."""
        stmt = select(AssetModel)
        if user_id is not None:
            stmt = stmt.where((AssetModel.user_id.is_(None)) | (AssetModel.user_id == user_id))
        if asset_class:
            stmt = stmt.where(AssetModel.asset_class == asset_class.strip().lower())
        if symbol:
            stmt = stmt.where(AssetModel.symbol == symbol.strip().upper())
        stmt = stmt.order_by(AssetModel.name.asc())
        return list(self.session.scalars(stmt).all())

    def update_asset(
        self,
        asset_id: str,
        user_id: str,
        name: Optional[str] = None,
        asset_class: Optional[str] = None,
        symbol: Optional[str] = None,
        currency: Optional[str] = None,
        instrument_type: Optional[str] = None,
    ) -> Optional[AssetModel]:
        """Update a custom asset owned by user_id. Users cannot update global reference assets."""
        stmt = select(AssetModel).where(AssetModel.id == asset_id, AssetModel.user_id == user_id)
        asset = self.session.scalars(stmt).first()
        if not asset:
            return None

        if name is not None:
            asset.name = name.strip()
        if asset_class is not None:
            asset.asset_class = asset_class.strip().lower()
        if symbol is not None:
            asset.symbol = symbol.strip().upper() if symbol else None
        if currency is not None:
            asset.currency = currency.strip().upper()
        if instrument_type is not None:
            asset.instrument_type = instrument_type.strip().lower() if instrument_type else None

        asset.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(asset)
        return asset

    # -----------------------------------------------------------------------
    # Portfolio Holdings CRUD
    # -----------------------------------------------------------------------

    def add_holding(
        self,
        portfolio_id: str,
        user_id: str,
        asset_id: str,
        quantity: Decimal,
        average_purchase_price: Decimal,
        current_price: Optional[Decimal] = None,
        price_as_of: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> PortfolioHoldingModel:
        """Add a holding to a user's portfolio."""
        portfolio = self.get_portfolio(portfolio_id, user_id)
        if not portfolio:
            raise ValueError("Portfolio not found or access denied.")

        asset = self.get_asset(asset_id, user_id)
        if not asset:
            raise ValueError("Asset instrument not found or access denied.")

        # Check for duplicate holding of the same asset in this portfolio
        existing_stmt = select(PortfolioHoldingModel).where(
            PortfolioHoldingModel.portfolio_id == portfolio_id,
            PortfolioHoldingModel.asset_id == asset_id,
        )
        if self.session.scalars(existing_stmt).first():
            raise ValueError(
                "A holding for this asset already exists in the portfolio. "
                "Update the existing holding's quantity and price instead."
            )

        holding = PortfolioHoldingModel(
            id=str(uuid.uuid4()),
            portfolio_id=portfolio_id,
            asset_id=asset_id,
            quantity=quantity,
            average_purchase_price=average_purchase_price,
            current_price=current_price,
            price_as_of=price_as_of or (datetime.now(timezone.utc) if current_price is not None else None),
            notes=notes.strip() if notes else None,
        )
        self.session.add(holding)
        self.session.commit()
        self.session.refresh(holding)
        return holding

    def get_holding(
        self, holding_id: str, portfolio_id: str, user_id: str
    ) -> Optional[PortfolioHoldingModel]:
        """Fetch a holding, verifying portfolio ownership."""
        portfolio = self.get_portfolio(portfolio_id, user_id)
        if not portfolio:
            return None

        stmt = (
            select(PortfolioHoldingModel)
            .where(
                PortfolioHoldingModel.id == holding_id,
                PortfolioHoldingModel.portfolio_id == portfolio_id,
            )
            .options(joinedload(PortfolioHoldingModel.asset))
        )
        return self.session.scalars(stmt).first()

    def list_holdings(self, portfolio_id: str, user_id: str) -> List[PortfolioHoldingModel]:
        """List all holdings in a portfolio, verifying ownership."""
        portfolio = self.get_portfolio(portfolio_id, user_id)
        if not portfolio:
            return []

        stmt = (
            select(PortfolioHoldingModel)
            .where(PortfolioHoldingModel.portfolio_id == portfolio_id)
            .options(joinedload(PortfolioHoldingModel.asset))
            .order_by(PortfolioHoldingModel.created_at.asc())
        )
        return list(self.session.scalars(stmt).all())

    def update_holding(
        self,
        holding_id: str,
        portfolio_id: str,
        user_id: str,
        quantity: Optional[Decimal] = None,
        average_purchase_price: Optional[Decimal] = None,
        current_price: Optional[Decimal] = None,
        price_as_of: Optional[datetime] = None,
        notes: Optional[str] = None,
    ) -> Optional[PortfolioHoldingModel]:
        """Update a holding's quantity, prices, or notes."""
        holding = self.get_holding(holding_id, portfolio_id, user_id)
        if not holding:
            return None

        if quantity is not None:
            holding.quantity = quantity
        if average_purchase_price is not None:
            holding.average_purchase_price = average_purchase_price
        if current_price is not None:
            holding.current_price = current_price
            holding.price_as_of = price_as_of or datetime.now(timezone.utc)
        elif price_as_of is not None:
            holding.price_as_of = price_as_of

        if notes is not None:
            holding.notes = notes.strip() if notes else None

        holding.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(holding)
        return holding

    def delete_holding(self, holding_id: str, portfolio_id: str, user_id: str) -> bool:
        """Delete a holding from a portfolio."""
        holding = self.get_holding(holding_id, portfolio_id, user_id)
        if not holding:
            return False

        self.session.delete(holding)
        self.session.commit()
        return True

    # -----------------------------------------------------------------------
    # Target Asset Allocation CRUD
    # -----------------------------------------------------------------------

    def set_target_allocation(
        self,
        portfolio_id: str,
        user_id: str,
        targets: Dict[str, Any],
        is_draft: bool = False,
        notes: Optional[str] = None,
    ) -> TargetAllocationModel:
        """Create or update target asset allocation for a portfolio."""
        portfolio = self.get_portfolio(portfolio_id, user_id)
        if not portfolio:
            raise ValueError("Portfolio not found or access denied.")

        stmt = select(TargetAllocationModel).where(TargetAllocationModel.portfolio_id == portfolio_id)
        allocation = self.session.scalars(stmt).first()

        clean_targets = {k: str(v) for k, v in targets.items()}

        if allocation:
            allocation.targets = clean_targets
            allocation.is_draft = is_draft
            allocation.notes = notes.strip() if notes else None
            allocation.updated_at = datetime.now(timezone.utc)
        else:
            allocation = TargetAllocationModel(
                id=str(uuid.uuid4()),
                portfolio_id=portfolio_id,
                user_id=user_id,
                targets=clean_targets,
                is_draft=is_draft,
                notes=notes.strip() if notes else None,
            )
            self.session.add(allocation)

        self.session.commit()
        self.session.refresh(allocation)
        return allocation

    def get_target_allocation(
        self, portfolio_id: str, user_id: str
    ) -> Optional[TargetAllocationModel]:
        """Fetch target allocation for a portfolio."""
        portfolio = self.get_portfolio(portfolio_id, user_id)
        if not portfolio:
            return None

        stmt = select(TargetAllocationModel).where(
            TargetAllocationModel.portfolio_id == portfolio_id,
            TargetAllocationModel.user_id == user_id,
        )
        return self.session.scalars(stmt).first()

    # -----------------------------------------------------------------------
    # Investment Goals CRUD
    # -----------------------------------------------------------------------

    def create_goal(
        self,
        user_id: str,
        name: str,
        target_amount: Decimal,
        target_date: DateType,
        portfolio_id: Optional[str] = None,
        priority: str = "medium",
        status: str = "in_progress",
        current_amount: Optional[Decimal] = None,
        initial_lump_sum: Optional[Decimal] = None,
        expected_annual_return: Optional[Decimal] = None,
        monthly_contribution: Optional[Decimal] = None,
        notes: Optional[str] = None,
    ) -> InvestmentGoalModel:
        """Create an investment goal for user_id."""
        if portfolio_id:
            portfolio = self.get_portfolio(portfolio_id, user_id)
            if not portfolio:
                raise ValueError(f"Linked portfolio '{portfolio_id}' not found or access denied.")

        goal = InvestmentGoalModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            portfolio_id=portfolio_id,
            name=name.strip(),
            target_amount=target_amount,
            target_date=target_date,
            priority=priority.strip().lower(),
            status=status.strip().lower() if status else "in_progress",
            current_amount=current_amount,
            initial_lump_sum=initial_lump_sum,
            expected_annual_return=expected_annual_return,
            monthly_contribution=monthly_contribution,
            notes=notes.strip() if notes else None,
        )
        self.session.add(goal)
        self.session.commit()
        self.session.refresh(goal)
        return goal

    def get_goal(self, goal_id: str, user_id: str) -> Optional[InvestmentGoalModel]:
        """Fetch an investment goal by ID for user_id."""
        stmt = (
            select(InvestmentGoalModel)
            .where(InvestmentGoalModel.id == goal_id, InvestmentGoalModel.user_id == user_id)
            .options(joinedload(InvestmentGoalModel.portfolio))
        )
        return self.session.scalars(stmt).first()

    def list_goals(
        self, user_id: str, portfolio_id: Optional[str] = None
    ) -> List[InvestmentGoalModel]:
        """List goals for user_id, optionally filtered by portfolio_id."""
        stmt = (
            select(InvestmentGoalModel)
            .where(InvestmentGoalModel.user_id == user_id)
            .options(joinedload(InvestmentGoalModel.portfolio))
        )
        if portfolio_id:
            stmt = stmt.where(InvestmentGoalModel.portfolio_id == portfolio_id)
        stmt = stmt.order_by(InvestmentGoalModel.target_date.asc())
        return list(self.session.scalars(stmt).all())

    def update_goal(
        self,
        goal_id: str,
        user_id: str,
        name: Optional[str] = None,
        target_amount: Optional[Decimal] = None,
        target_date: Optional[DateType] = None,
        portfolio_id: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        current_amount: Optional[Decimal] = None,
        initial_lump_sum: Optional[Decimal] = None,
        expected_annual_return: Optional[Decimal] = None,
        monthly_contribution: Optional[Decimal] = None,
        notes: Optional[str] = None,
    ) -> Optional[InvestmentGoalModel]:
        """Update an investment goal."""
        goal = self.get_goal(goal_id, user_id)
        if not goal:
            return None

        if portfolio_id is not None:
            if portfolio_id:
                p = self.get_portfolio(portfolio_id, user_id)
                if not p:
                    raise ValueError(f"Portfolio '{portfolio_id}' not found or access denied.")
                goal.portfolio_id = portfolio_id
            else:
                goal.portfolio_id = None

        if name is not None:
            goal.name = name.strip()
        if target_amount is not None:
            goal.target_amount = target_amount
        if target_date is not None:
            goal.target_date = target_date
        if priority is not None:
            goal.priority = priority.strip().lower()
        if status is not None:
            goal.status = status.strip().lower()
        if current_amount is not None:
            goal.current_amount = current_amount
        if initial_lump_sum is not None:
            goal.initial_lump_sum = initial_lump_sum
        if expected_annual_return is not None:
            goal.expected_annual_return = expected_annual_return
        if monthly_contribution is not None:
            goal.monthly_contribution = monthly_contribution
        if notes is not None:
            goal.notes = notes.strip() if notes else None

        goal.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(goal)
        return goal

    def delete_goal(self, goal_id: str, user_id: str) -> bool:
        """Delete an investment goal."""
        goal = self.get_goal(goal_id, user_id)
        if not goal:
            return False

        self.session.delete(goal)
        self.session.commit()
        return True

    # -----------------------------------------------------------------------
    # Historical Prices & Optimization Runs (Phase 7)
    # -----------------------------------------------------------------------

    def save_historical_prices(
        self, price_rows: List[Any], source: str = "csv_import"
    ) -> Tuple[int, int]:
        """Save historical price observations, skipping duplicates.

        Returns:
            Tuple of (imported_count, skipped_count).
        """
        imported = 0
        skipped = 0

        for row in price_rows:
            sym = row.symbol.strip().upper()
            dt = row.date
            price = row.adjusted_close

            # Check existing observation
            stmt = select(HistoricalPriceModel).where(
                HistoricalPriceModel.symbol == sym, HistoricalPriceModel.date == dt
            )
            existing = self.session.scalars(stmt).first()
            if existing:
                skipped += 1
                continue

            record = HistoricalPriceModel(
                id=str(uuid.uuid4()),
                symbol=sym,
                date=dt,
                adjusted_close=price,
                source=getattr(row, "source", source),
            )
            self.session.add(record)
            imported += 1

        self.session.commit()
        return imported, skipped

    def get_historical_prices(
        self,
        symbols: List[str],
        start_date: Optional[DateType] = None,
        end_date: Optional[DateType] = None,
    ) -> List[HistoricalPriceModel]:
        """Fetch historical price records for requested symbols, ordered chronologically."""
        clean_symbols = [s.strip().upper() for s in symbols]
        stmt = select(HistoricalPriceModel).where(HistoricalPriceModel.symbol.in_(clean_symbols))

        if start_date:
            stmt = stmt.where(HistoricalPriceModel.date >= start_date)
        if end_date:
            stmt = stmt.where(HistoricalPriceModel.date <= end_date)

        stmt = stmt.order_by(HistoricalPriceModel.date.asc(), HistoricalPriceModel.symbol.asc())
        return list(self.session.scalars(stmt).all())

    def save_optimization_run(
        self,
        portfolio_id: str,
        user_id: str,
        strategy: str,
        risk_free_rate: Decimal,
        expected_return: Decimal,
        expected_volatility: Decimal,
        sharpe_ratio: Decimal,
        weights: Dict[str, Any],
        metadata_info: Dict[str, Any],
    ) -> OptimizationRunModel:
        """Persist an optimization run audit record."""
        clean_weights = {k: str(v) for k, v in weights.items()}
        run_record = OptimizationRunModel(
            id=str(uuid.uuid4()),
            portfolio_id=portfolio_id,
            user_id=user_id,
            strategy=strategy,
            risk_free_rate=risk_free_rate,
            expected_return=expected_return,
            expected_volatility=expected_volatility,
            sharpe_ratio=sharpe_ratio,
            weights=clean_weights,
            metadata_info=metadata_info,
        )
        self.session.add(run_record)
        self.session.commit()
        self.session.refresh(run_record)
        return run_record

    def list_optimization_runs(
        self, portfolio_id: str, user_id: str
    ) -> List[OptimizationRunModel]:
        """List past optimization runs for a portfolio, verifying ownership."""
        portfolio = self.get_portfolio(portfolio_id, user_id)
        if not portfolio:
            return []

        stmt = (
            select(OptimizationRunModel)
            .where(
                OptimizationRunModel.portfolio_id == portfolio_id,
                OptimizationRunModel.user_id == user_id,
            )
            .order_by(OptimizationRunModel.created_at.desc())
        )
        return list(self.session.scalars(stmt).all())
