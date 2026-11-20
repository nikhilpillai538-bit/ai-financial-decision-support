"""
SQLAlchemy-backed Financial Profile Repository with User Isolation.

Provides persistent database storage for user settings, emergency fund parameters,
and category configuration scoped to individual users.
"""

from decimal import Decimal
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import FinancialProfileModel


class SQLProfileRepository:
    """Database-backed repository for financial profile and emergency fund configuration.

    Args:
        session: Active SQLAlchemy database session.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_emergency_fund_config(
        self, user_id: Optional[str] = None, profile_key: Optional[str] = None
    ) -> Optional[dict]:
        """Return stored emergency-fund configuration as a dict, scoped to user_id or profile_key."""
        # Handle legacy or positional calls like get_emergency_fund_config("default")
        if user_id == "default" and profile_key is None:
            user_id = None
            profile_key = "default"

        stmt = select(FinancialProfileModel)
        if user_id is not None:
            stmt = stmt.where(
                (FinancialProfileModel.user_id == user_id)
                | (FinancialProfileModel.profile_key == f"user_{user_id}")
            )
        elif profile_key is not None:
            stmt = stmt.where(FinancialProfileModel.profile_key == profile_key)
        else:
            stmt = stmt.where(FinancialProfileModel.profile_key == "default")

        model = self.session.scalars(stmt).first()
        if not model:
            return None

        return {
            "emergency_fund_balance": (
                str(model.emergency_fund_balance)
                if model.emergency_fund_balance is not None
                else None
            ),
            "essential_categories": model.essential_categories,
            "analysis_window_months": model.analysis_window_months,
            "min_cash_buffer": (
                str(model.min_cash_buffer)
                if model.min_cash_buffer is not None
                else None
            ),
            "currency": model.currency,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None,
        }

    def save_emergency_fund_config(
        self,
        config: dict,
        user_id: Optional[str] = None,
        profile_key: Optional[str] = None,
    ) -> None:
        """Persist or update emergency-fund configuration for user_id or profile_key."""
        if user_id == "default" and profile_key is None:
            user_id = None
            profile_key = "default"

        stmt = select(FinancialProfileModel)
        if user_id is not None:
            stmt = stmt.where(
                (FinancialProfileModel.user_id == user_id)
                | (FinancialProfileModel.profile_key == f"user_{user_id}")
            )
            effective_key = profile_key or f"user_{user_id}"
        else:
            effective_key = profile_key or "default"
            stmt = stmt.where(FinancialProfileModel.profile_key == effective_key)

        model = self.session.scalars(stmt).first()

        raw_balance = config.get("emergency_fund_balance")
        balance = Decimal(str(raw_balance)) if raw_balance is not None else None

        raw_buffer = config.get("min_cash_buffer")
        buffer_val = Decimal(str(raw_buffer)) if raw_buffer is not None else None

        essential_categories = config.get("essential_categories")
        if essential_categories is None:
            essential_categories = ["rent", "groceries", "utilities", "healthcare", "transport"]

        window = int(config.get("analysis_window_months", 12))
        currency = config.get("currency", "INR")

        try:
            if model:
                model.emergency_fund_balance = balance
                model.essential_categories = essential_categories
                model.analysis_window_months = window
                if buffer_val is not None:
                    model.min_cash_buffer = buffer_val
                model.currency = currency
            else:
                model = FinancialProfileModel(
                    user_id=user_id,
                    profile_key=effective_key,
                    emergency_fund_balance=balance,
                    essential_categories=essential_categories,
                    analysis_window_months=window,
                    min_cash_buffer=buffer_val,
                    currency=currency,
                )
                self.session.add(model)

            self.session.commit()
            self.session.refresh(model)
        except Exception:
            self.session.rollback()
            raise

    def clear(self, user_id: Optional[str] = None, profile_key: Optional[str] = None) -> None:
        """Remove profile records. Used in testing."""
        try:
            stmt = delete(FinancialProfileModel)
            if user_id is not None:
                stmt = stmt.where(FinancialProfileModel.user_id == user_id)
            elif profile_key:
                stmt = stmt.where(FinancialProfileModel.profile_key == profile_key)
            self.session.execute(stmt)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
