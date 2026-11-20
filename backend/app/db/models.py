"""
SQLAlchemy ORM models for the AI Financial Decision Support System.

Phase 4 & 5 Models:
- UserModel: authenticated user credentials, normalization, and status.
- UserSessionModel: secure refresh token sessions with hash storage and rotation tracking.
- TransactionModel: persistent financial transaction records scoped to user_id.
- FinancialProfileModel: user settings and emergency fund parameters scoped to user_id.

Phase 6 Models:
- PortfolioModel: investment portfolios owned by authenticated users.
- AssetModel: reference and user-defined investment instruments with asset class categorization.
- PortfolioHoldingModel: asset holdings within a portfolio with quantity, purchase price, and current price.
- InvestmentGoalModel: financial/investment objectives linked optionally to portfolios.
- TargetAllocationModel: desired asset allocation percentages by asset class per portfolio.
"""

from datetime import date as DateType, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AssetClass(str, Enum):
    """Supported asset classes for investment instruments."""

    EQUITY = "equity"
    DEBT = "debt"
    MUTUAL_FUND = "mutual_fund"
    ETF = "etf"
    CASH = "cash"
    COMMODITIES_GOLD = "commodities_gold"
    OTHER = "other"


class UserModel(Base):
    """SQLAlchemy model for the users table.

    Stores normalized emails and securely hashed passwords (Argon2id).
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        doc="Unique user identifier (UUID).",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="Normalized (lowercase, trimmed) user email address.",
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Argon2id password hash.",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Account active status.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of account creation.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp of last account update.",
    )

    # Relationships
    transactions: Mapped[List["TransactionModel"]] = relationship(
        "TransactionModel", back_populates="user", cascade="all, delete-orphan"
    )
    profile: Mapped[Optional["FinancialProfileModel"]] = relationship(
        "FinancialProfileModel", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    sessions: Mapped[List["UserSessionModel"]] = relationship(
        "UserSessionModel", back_populates="user", cascade="all, delete-orphan"
    )
    portfolios: Mapped[List["PortfolioModel"]] = relationship(
        "PortfolioModel", back_populates="user", cascade="all, delete-orphan"
    )
    assets: Mapped[List["AssetModel"]] = relationship(
        "AssetModel", back_populates="user", cascade="all, delete-orphan"
    )
    investment_goals: Mapped[List["InvestmentGoalModel"]] = relationship(
        "InvestmentGoalModel", back_populates="user", cascade="all, delete-orphan"
    )
    target_allocations: Mapped[List["TargetAllocationModel"]] = relationship(
        "TargetAllocationModel", back_populates="user", cascade="all, delete-orphan"
    )
    optimization_runs: Mapped[List["OptimizationRunModel"]] = relationship(
        "OptimizationRunModel", back_populates="user", cascade="all, delete-orphan"
    )
    ai_conversations: Mapped[List["AIConversationModel"]] = relationship(
        "AIConversationModel", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<UserModel(id={self.id!r}, email={self.email!r}, is_active={self.is_active})>"


class UserSessionModel(Base):
    """SQLAlchemy model for refresh token sessions.

    Stores SHA-256 hashes of refresh tokens rather than plaintext tokens.
    Supports revocation, expiration, and rotation tracking for reuse detection.
    """

    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        doc="Unique session record ID (UUID).",
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Associated user ID.",
    )
    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        doc="SHA-256 hash of the issued refresh token.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Session creation timestamp.",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Refresh token expiration timestamp.",
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when session was revoked, or NULL if active.",
    )
    replaced_by_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        doc="Token hash of the replacement token after rotation (for reuse detection).",
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Client user-agent string.",
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        doc="Client IP address.",
    )

    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<UserSessionModel(id={self.id!r}, user_id={self.user_id!r}, revoked={self.revoked_at is not None})>"


class TransactionModel(Base):
    """SQLAlchemy model for the transactions table.

    Stores income and expense records with exact monetary amounts using NUMERIC(18, 2),
    scoped to a user_id for multi-user isolation.
    """

    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        doc="Unique transaction identifier (UUID).",
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Owner user ID. Nullable for legacy unassociated records.",
    )
    date: Mapped[DateType] = mapped_column(
        Date,
        nullable=False,
        index=True,
        doc="Transaction date (YYYY-MM-DD).",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Non-empty transaction description.",
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        doc="Positive transaction amount in exact Decimal representation.",
    )
    transaction_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        doc="'income' or 'expense'.",
    )
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="uncategorized",
        index=True,
        doc="Categorization label.",
    )
    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="manual",
        doc="'manual' or 'csv_import'.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of transaction creation.",
    )

    # Relationship
    user: Mapped[Optional["UserModel"]] = relationship("UserModel", back_populates="transactions")

    __table_args__ = (
        CheckConstraint("amount > 0", name="positive_amount"),
        CheckConstraint("transaction_type IN ('income', 'expense')", name="valid_transaction_type"),
        CheckConstraint("length(trim(description)) > 0", name="non_empty_description"),
        Index("idx_transactions_date_type", "date", "transaction_type"),
        Index("idx_transactions_user_date", "user_id", "date"),
    )

    def __repr__(self) -> str:
        return (
            f"<TransactionModel(id={self.id!r}, user_id={self.user_id!r}, date={self.date}, "
            f"type={self.transaction_type!r}, amount={self.amount})>"
        )


class FinancialProfileModel(Base):
    """SQLAlchemy model for user financial settings and emergency fund configuration.

    Stores settings scoped to user_id. Legacy records use profile_key='default'.
    """

    __tablename__ = "financial_profiles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Internal primary key.",
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        unique=True,
        index=True,
        doc="Owner user ID. Nullable for legacy unassociated records.",
    )
    profile_key: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        default="default",
        index=True,
        doc="Profile identifier string.",
    )
    emergency_fund_balance: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        doc="Explicitly known emergency fund balance (NULL = unknown).",
    )
    essential_categories: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: ["rent", "groceries", "utilities", "healthcare", "transport"],
        doc="List of category strings treated as essential for emergency fund analysis.",
    )
    analysis_window_months: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=12,
        doc="Analysis window in months (1 to 60).",
    )
    min_cash_buffer: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        doc="Minimum cash buffer for cash-flow forecasting.",
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="INR",
        doc="Currency symbol or code.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp of last update.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of creation.",
    )

    # Relationship
    user: Mapped[Optional["UserModel"]] = relationship("UserModel", back_populates="profile")

    __table_args__ = (
        CheckConstraint(
            "emergency_fund_balance IS NULL OR emergency_fund_balance >= 0",
            name="non_negative_ef_balance",
        ),
        CheckConstraint(
            "analysis_window_months >= 1 AND analysis_window_months <= 60",
            name="valid_analysis_window",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<FinancialProfileModel(profile_key={self.profile_key!r}, user_id={self.user_id!r}, "
            f"emergency_fund_balance={self.emergency_fund_balance})>"
        )


class PortfolioModel(Base):
    """SQLAlchemy model for investment portfolios.

    Each portfolio belongs to exactly one user. Users may create multiple portfolios.
    All operations are strictly scoped to user_id.
    """

    __tablename__ = "portfolios"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        doc="Unique portfolio identifier (UUID).",
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Owner user ID.",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="User-defined portfolio name.",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Optional portfolio description.",
    )
    base_currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="INR",
        doc="Base currency for portfolio valuation (default INR).",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of creation.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp of last update.",
    )

    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="portfolios")
    holdings: Mapped[List["PortfolioHoldingModel"]] = relationship(
        "PortfolioHoldingModel", back_populates="portfolio", cascade="all, delete-orphan"
    )
    allocation_target: Mapped[Optional["TargetAllocationModel"]] = relationship(
        "TargetAllocationModel", back_populates="portfolio", uselist=False, cascade="all, delete-orphan"
    )
    goals: Mapped[List["InvestmentGoalModel"]] = relationship(
        "InvestmentGoalModel", back_populates="portfolio"
    )
    optimization_runs: Mapped[List["OptimizationRunModel"]] = relationship(
        "OptimizationRunModel", back_populates="portfolio", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="non_empty_portfolio_name"),
        Index("idx_portfolios_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<PortfolioModel(id={self.id!r}, user_id={self.user_id!r}, name={self.name!r})>"


class AssetModel(Base):
    """SQLAlchemy model for investment asset instruments.

    Supports global reference instruments (user_id IS NULL) and user-defined custom instruments (user_id IS NOT NULL).
    Users can only update or delete their own custom instruments.
    """

    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        doc="Unique asset identifier (UUID).",
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Owner user ID. NULL indicates a system/reference instrument.",
    )
    symbol: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        doc="Ticker or instrument symbol (e.g. TCS, HDFCBANK, NIFTYBEES).",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Descriptive name of the instrument.",
    )
    asset_class: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Controlled asset class (equity, debt, mutual_fund, etf, cash, commodities_gold, other).",
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="INR",
        doc="Instrument trading/denomination currency (default INR).",
    )
    instrument_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Specific classification (e.g. large_cap, government_bond, liquid_fund).",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of creation.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp of last update.",
    )

    # Relationships
    user: Mapped[Optional["UserModel"]] = relationship("UserModel", back_populates="assets")
    holdings: Mapped[List["PortfolioHoldingModel"]] = relationship(
        "PortfolioHoldingModel", back_populates="asset"
    )

    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="non_empty_asset_name"),
        Index("idx_assets_user_symbol", "user_id", "symbol"),
    )

    def __repr__(self) -> str:
        return f"<AssetModel(id={self.id!r}, symbol={self.symbol!r}, name={self.name!r}, class={self.asset_class!r})>"


class PortfolioHoldingModel(Base):
    """SQLAlchemy model for a holding within an investment portfolio.

    Records position quantity, average acquisition cost, and latest user-supplied price.
    Holdings with unknown current prices remain explicitly NULL (never defaulted to 0).
    """

    __tablename__ = "portfolio_holdings"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        doc="Unique holding identifier (UUID).",
    )
    portfolio_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Associated portfolio ID.",
    )
    asset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("assets.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Associated instrument ID.",
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        doc="Holding quantity in units/shares (must be > 0).",
    )
    average_purchase_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        doc="Weighted average acquisition cost per unit (>= 0).",
    )
    current_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        doc="Latest user-supplied price per unit. NULL if unpriced.",
    )
    price_as_of: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp or date when the current price was recorded.",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Optional notes.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of creation.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp of last update.",
    )

    # Relationships
    portfolio: Mapped["PortfolioModel"] = relationship("PortfolioModel", back_populates="holdings")
    asset: Mapped["AssetModel"] = relationship("AssetModel", back_populates="holdings")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="positive_holding_quantity"),
        CheckConstraint("average_purchase_price >= 0", name="non_negative_purchase_price"),
        CheckConstraint("current_price IS NULL OR current_price >= 0", name="non_negative_current_price"),
        Index("idx_holdings_portfolio_asset", "portfolio_id", "asset_id", unique=True),
    )

    def __repr__(self) -> str:
        return (
            f"<PortfolioHoldingModel(id={self.id!r}, portfolio_id={self.portfolio_id!r}, "
            f"asset_id={self.asset_id!r}, qty={self.quantity}, price={self.current_price})>"
        )


class InvestmentGoalModel(Base):
    """SQLAlchemy model for user investment goals.

    Defines financial targets, deadlines, and optional portfolio linkage.
    """

    __tablename__ = "investment_goals"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        doc="Unique goal identifier (UUID).",
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Owner user ID.",
    )
    portfolio_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("portfolios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Optional portfolio linked to this goal.",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Goal title (e.g. Higher Education, Home Down Payment).",
    )
    target_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        doc="Target monetary amount (> 0).",
    )
    target_date: Mapped[DateType] = mapped_column(
        Date,
        nullable=False,
        doc="Target milestone completion date.",
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
        doc="Goal priority ('low', 'medium', 'high').",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="in_progress",
        server_default="in_progress",
        doc="Goal status ('in_progress', 'achieved', 'paused', 'behind', 'on_track').",
    )
    current_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        doc="Optional manually-tracked current amount saved toward the goal.",
    )
    initial_lump_sum: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        doc="Optional initial lump-sum invested.",
    )
    expected_annual_return: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(6, 4),
        nullable=True,
        doc="User-supplied expected annual return rate (e.g. 0.1200 for 12%).",
    )
    monthly_contribution: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        doc="Optional planned recurring monthly contribution.",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Optional notes.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of creation.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp of last update.",
    )

    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="investment_goals")
    portfolio: Mapped[Optional["PortfolioModel"]] = relationship("PortfolioModel", back_populates="goals")

    __table_args__ = (
        CheckConstraint("target_amount > 0", name="positive_goal_target_amount"),
        CheckConstraint("length(trim(name)) > 0", name="non_empty_goal_name"),
        CheckConstraint("current_amount IS NULL OR current_amount >= 0", name="non_negative_goal_current_amount"),
        CheckConstraint("initial_lump_sum IS NULL OR initial_lump_sum >= 0", name="non_negative_goal_initial_lump_sum"),
        CheckConstraint("monthly_contribution IS NULL OR monthly_contribution >= 0", name="non_negative_goal_monthly_contribution"),
        CheckConstraint("expected_annual_return IS NULL OR expected_annual_return >= -1.0", name="valid_goal_expected_return"),
        Index("idx_investment_goals_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<InvestmentGoalModel(id={self.id!r}, user_id={self.user_id!r}, name={self.name!r}, target={self.target_amount})>"


class TargetAllocationModel(Base):
    """SQLAlchemy model for portfolio target asset allocation.

    Stores target percentage by asset class per portfolio.
    Incomplete drafts are explicitly flagged with is_draft=True.
    """

    __tablename__ = "target_allocations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        doc="Unique target allocation record ID (UUID).",
    )
    portfolio_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        doc="Associated portfolio ID (1-to-1).",
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Owner user ID for fast isolation queries.",
    )
    targets: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        doc="Dictionary of asset_class -> target percentage (e.g. {'equity': 60.0, 'debt': 25.0, ...}).",
    )
    is_draft: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="True if this is an incomplete draft allocation, False if ready/validated.",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Optional notes or rationale.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of creation.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp of last update.",
    )

    # Relationships
    portfolio: Mapped["PortfolioModel"] = relationship("PortfolioModel", back_populates="allocation_target")
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="target_allocations")

    __table_args__ = (
        Index("idx_target_allocations_user_portfolio", "user_id", "portfolio_id"),
    )

    def __repr__(self) -> str:
        return f"<TargetAllocationModel(id={self.id!r}, portfolio_id={self.portfolio_id!r}, is_draft={self.is_draft})>"


class HistoricalPriceModel(Base):
    """SQLAlchemy model for historical asset prices.

    Stores time series of adjusted closing prices for return and covariance estimation.
    """

    __tablename__ = "historical_prices"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        doc="Unique record identifier (UUID).",
    )
    symbol: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Ticker or instrument symbol (uppercase).",
    )
    date: Mapped[DateType] = mapped_column(
        Date,
        nullable=False,
        index=True,
        doc="Trading date (YYYY-MM-DD).",
    )
    adjusted_close: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        doc="Adjusted closing price in instrument currency.",
    )
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="csv_import",
        doc="Data origin ('csv_import', 'manual', etc.).",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of creation.",
    )

    __table_args__ = (
        CheckConstraint("adjusted_close > 0", name="positive_historical_price"),
        Index("idx_historical_prices_symbol_date", "symbol", "date", unique=True),
    )

    def __repr__(self) -> str:
        return f"<HistoricalPriceModel(symbol={self.symbol!r}, date={self.date}, price={self.adjusted_close})>"


class OptimizationRunModel(Base):
    """SQLAlchemy model for portfolio optimization execution history.

    Maintains audit logs of portfolio optimization runs, mathematical parameters,
    and recommended rebalancing allocations.
    """

    __tablename__ = "optimization_runs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        doc="Unique run identifier (UUID).",
    )
    portfolio_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Target portfolio ID.",
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Owner user ID for isolation.",
    )
    strategy: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Optimization strategy ('min_volatility', 'max_sharpe', 'target_return', etc.).",
    )
    risk_free_rate: Mapped[Decimal] = mapped_column(
        Numeric(8, 4),
        nullable=False,
        default=Decimal("0.0600"),
        doc="Annualized risk-free rate used.",
    )
    expected_return: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        doc="Annualized expected return of optimized portfolio.",
    )
    expected_volatility: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        doc="Annualized expected volatility (standard deviation).",
    )
    sharpe_ratio: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        doc="Annualized Sharpe ratio of optimized portfolio.",
    )
    weights: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        doc="Dictionary of symbol -> optimal weight.",
    )
    metadata_info: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        doc="Audit metadata (date range, observation count, rebalancing delta, assumptions).",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Execution timestamp.",
    )

    # Relationships
    portfolio: Mapped["PortfolioModel"] = relationship("PortfolioModel", back_populates="optimization_runs")
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="optimization_runs")

    __table_args__ = (
        Index("idx_optimization_runs_user_portfolio", "user_id", "portfolio_id"),
    )

    def __repr__(self) -> str:
        return f"<OptimizationRunModel(id={self.id!r}, strategy={self.strategy!r}, sharpe={self.sharpe_ratio})>"


class AIConversationModel(Base):
    """SQLAlchemy model for AI financial assistant conversations.

    Maintains conversational thread metadata scoped strictly to the authenticated user.
    """

    __tablename__ = "ai_conversations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        doc="Unique conversation identifier (UUID).",
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Owner user ID for isolation.",
    )
    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        default="Financial Assistant Conversation",
        doc="Title/topic of the conversation thread.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Creation timestamp.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Last activity timestamp.",
    )

    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="ai_conversations")
    messages: Mapped[List["AIMessageModel"]] = relationship(
        "AIMessageModel",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AIMessageModel.created_at.asc()",
    )

    __table_args__ = (
        Index("idx_ai_conversations_user_updated", "user_id", "updated_at"),
    )

    def __repr__(self) -> str:
        return f"<AIConversationModel(id={self.id!r}, user_id={self.user_id!r}, title={self.title!r})>"


class AIMessageModel(Base):
    """SQLAlchemy model for individual messages within an AI conversation.

    Stores user prompts and grounded assistant answers along with cited data source keys.
    """

    __tablename__ = "ai_messages"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        doc="Unique message identifier (UUID).",
    )
    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ai_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Associated conversation thread ID.",
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Owner user ID for strict access verification.",
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Message author role: 'user', 'assistant', or 'system'.",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Message text content.",
    )
    data_sources: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        doc="List of internal deterministic data sources cited (e.g. ['portfolio_valuation', 'cash_flow_forecast']).",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Message creation timestamp.",
    )

    # Relationships
    conversation: Mapped["AIConversationModel"] = relationship("AIConversationModel", back_populates="messages")
    user: Mapped["UserModel"] = relationship("UserModel")

    __table_args__ = (
        Index("idx_ai_messages_conv_created", "conversation_id", "created_at"),
        Index("idx_ai_messages_user_conv", "user_id", "conversation_id"),
    )

    def __repr__(self) -> str:
        return f"<AIMessageModel(id={self.id!r}, role={self.role!r}, conv={self.conversation_id!r})>"


# ---------------------------------------------------------------------------
# Phase 10: Financial News & Sentiment Analysis Models
# ---------------------------------------------------------------------------

class NewsSourceModel(Base):
    """SQLAlchemy model for financial news publishers and RSS feed sources."""

    __tablename__ = "news_sources"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        doc="Unique source identifier (UUID).",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        doc="Publisher or institution name (e.g. 'Federal Reserve Press', 'Reuters Financial').",
    )
    feed_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
        doc="Canonical RSS/Atom feed URL (validated against approved domains).",
    )
    site_url: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Publisher website URL for attribution.",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Description of source coverage.",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Flag indicating if the source should be included in ingestion runs.",
    )
    refresh_interval_minutes: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False,
        doc="Target polling interval in minutes.",
    )
    last_fetched_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of most recent successful feed fetch.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Record creation timestamp.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Record update timestamp.",
    )

    # Relationships
    articles: Mapped[List["NewsArticleModel"]] = relationship(
        "NewsArticleModel",
        back_populates="source",
        cascade="all, delete-orphan",
        order_by="NewsArticleModel.published_at.desc()",
    )

    def __repr__(self) -> str:
        return f"<NewsSourceModel(id={self.id!r}, name={self.name!r}, is_active={self.is_active})>"


class NewsArticleModel(Base):
    """SQLAlchemy model for ingested financial news articles and FinBERT sentiment."""

    __tablename__ = "news_articles"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        doc="Unique article identifier (UUID).",
    )
    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("news_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Publishing news source ID.",
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Article headline.",
    )
    canonical_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
        doc="Original canonical article URL for source attribution and deduplication.",
    )
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Short description or permitted article excerpt.",
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="Normalized UTC publication timestamp.",
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="Timestamp when article was ingested.",
    )
    headline_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="SHA-256 hash of normalized lowercase title for fast deduplication.",
    )
    sentiment_label: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        index=True,
        doc="FinBERT classification: 'positive', 'negative', or 'neutral'.",
    )
    sentiment_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
        doc="Normalized compound sentiment score on [-1.0000, +1.0000] scale.",
    )
    sentiment_probabilities: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Detailed FinBERT class probabilities e.g. {'positive': 0.85, 'neutral': 0.10, 'negative': 0.05}.",
    )
    sentiment_model: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Model identifier and version (e.g. 'ProsusAI/finbert').",
    )
    sentiment_analyzed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when sentiment inference was performed.",
    )
    relevance_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Matched assets, tickers, company names, or sectors e.g. {'matched_symbols': ['AAPL'], 'sectors': ['Technology']}.",
    )

    # Relationships
    source: Mapped["NewsSourceModel"] = relationship("NewsSourceModel", back_populates="articles")

    __table_args__ = (
        Index("idx_news_articles_pub_sent", "published_at", "sentiment_label"),
        Index("idx_news_articles_source_pub", "source_id", "published_at"),
        Index("idx_news_articles_hash", "headline_hash"),
    )

    def __repr__(self) -> str:
        return f"<NewsArticleModel(id={self.id!r}, title={self.title[:30]!r}, sentiment={self.sentiment_label})>"

