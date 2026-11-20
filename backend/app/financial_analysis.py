"""
Financial analysis router — Phase 3.

Provides two endpoint groups mounted at different URL prefixes:

``/financial-profile``   — stores user-supplied configuration
``/financial-analysis``  — returns computed analytical results

Both groups are intentionally kept separate to make it clear which
endpoints read data (GET) and which receive user configuration (PUT/POST).

All heavy computation is delegated to the pure Python modules
:mod:`app.emergency_fund` and :mod:`app.forecasting`.  This router handles
only HTTP concerns: routing, dependency injection, serialisation, and
validation errors.
"""

from datetime import date as ISODate
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.models import UserModel
from app.db.repositories.profile_repo import SQLProfileRepository
from app.db.session import get_db
from app.emergency_fund import (
    DEFAULT_ESSENTIAL_CATEGORIES,
    calculate_emergency_fund_analysis,
)
from app.forecasting import generate_cash_flow_forecast
from app.repository import ProfileRepository, TransactionRepository, default_profile_repository
from app.schemas import (
    CashFlowForecastRequest,
    CashFlowForecastResponse,
    DailyForecast,
    DetectedRecurringInfo,
    EmergencyFundAnalysisResponse,
    EmergencyFundConfig,
)
from app.transactions import get_repository

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

profile_router = APIRouter(prefix="/financial-profile", tags=["Financial Profile"])
analysis_router = APIRouter(prefix="/financial-analysis", tags=["Financial Analysis"])


# ---------------------------------------------------------------------------
# Dependency — profile repository (injectable for tests)
# ---------------------------------------------------------------------------


def get_profile_repository(db: Any = Depends(get_db)) -> Any:
    """Return the active profile repository (database-backed or fallback)."""
    if isinstance(db, Session):
        return SQLProfileRepository(db)
    return default_profile_repository


# ---------------------------------------------------------------------------
# /financial-profile endpoints
# ---------------------------------------------------------------------------


@profile_router.put(
    "/emergency-fund",
    response_model=EmergencyFundConfig,
    summary="Set emergency fund balance and analysis configuration",
    description=(
        "Store the user's explicitly known emergency fund balance and "
        "configuration for the emergency fund analysis. "
        "Supply null or omit emergency_fund_balance if the balance is unknown."
    ),
)
def put_emergency_fund_config(
    config: EmergencyFundConfig,
    current_user: UserModel = Depends(get_current_user),
    profile_repo: Any = Depends(get_profile_repository),
) -> EmergencyFundConfig:
    """Persist the emergency fund configuration for the current user and return it as stored."""
    # Serialise for storage: Decimal -> str, date -> isoformat
    config_dict = {
        "emergency_fund_balance": (
            str(config.emergency_fund_balance)
            if config.emergency_fund_balance is not None
            else None
        ),
        "essential_categories": config.essential_categories,
        "analysis_window_months": config.analysis_window_months,
        "updated_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    profile_repo.save_emergency_fund_config(config_dict, user_id=current_user.id)
    return config


# ---------------------------------------------------------------------------
# /financial-analysis endpoints
# ---------------------------------------------------------------------------


@analysis_router.get(
    "/emergency-fund",
    response_model=EmergencyFundAnalysisResponse,
    summary="Retrieve emergency fund analysis",
    description=(
        "Compute an emergency fund analysis from stored transactions and the "
        "user profile set via PUT /financial-profile/emergency-fund. "
        "If no profile has been saved, sensible defaults are used and the "
        "balance status is returned as 'unknown'."
    ),
)
def get_emergency_fund_analysis(
    current_user: UserModel = Depends(get_current_user),
    txn_repo: Any = Depends(get_repository),
    profile_repo: Any = Depends(get_profile_repository),
) -> EmergencyFundAnalysisResponse:
    """Return a structured emergency fund analysis scoped to the authenticated user."""
    stored = profile_repo.get_emergency_fund_config(user_id=current_user.id)

    if stored:
        raw_balance = stored.get("emergency_fund_balance")
        balance = Decimal(str(raw_balance)) if raw_balance is not None else None
        essential_categories: List[str] = stored.get(
            "essential_categories", list(DEFAULT_ESSENTIAL_CATEGORIES)
        )
        window: int = int(stored.get("analysis_window_months", 12))
    else:
        balance = None
        essential_categories = list(DEFAULT_ESSENTIAL_CATEGORIES)
        window = 12

    transactions = txn_repo.all(user_id=current_user.id)
    result = calculate_emergency_fund_analysis(
        transactions=transactions,
        emergency_fund_balance=balance,
        essential_categories=essential_categories,
        analysis_window_months=window,
    )
    return EmergencyFundAnalysisResponse(**result)


@analysis_router.post(
    "/cash-flow-forecast",
    response_model=CashFlowForecastResponse,
    summary="Generate 30-day cash-flow forecast",
    description=(
        "Generate a deterministic day-by-day cash-flow projection for the "
        "next 30 days. Requires the user's current cash balance. "
        "Optionally accepts confirmed future transactions and a minimum cash buffer."
    ),
)
def post_cash_flow_forecast(
    request: CashFlowForecastRequest,
    current_user: UserModel = Depends(get_current_user),
    txn_repo: Any = Depends(get_repository),
) -> CashFlowForecastResponse:
    """Produce a 30-day cash-flow forecast scoped to the authenticated user."""
    start = request.forecast_start_date or ISODate.today()
    buffer = request.min_cash_buffer if request.min_cash_buffer is not None else Decimal("0")

    transactions = txn_repo.all(user_id=current_user.id)
    result = generate_cash_flow_forecast(
        transactions=transactions,
        current_balance=request.current_balance,
        forecast_start_date=start,
        min_cash_buffer=buffer,
        confirmed_future_transactions=request.confirmed_future_transactions,
        observation_window_months=request.observation_window_months,
    )

    # Map daily forecast dicts to Pydantic models
    daily = [DailyForecast(**d) for d in result.pop("daily_forecasts")]
    recurring = [DetectedRecurringInfo(**r) for r in result.pop("detected_recurring_transactions")]

    return CashFlowForecastResponse(
        **result,
        daily_forecasts=daily,
        detected_recurring_transactions=recurring,
    )


@analysis_router.get(
    "/cash-flow-forecast",
    response_model=CashFlowForecastResponse,
    summary="Retrieve 30-day cash-flow forecast",
    description="Deterministic day-by-day cash-flow projection using user's recorded liquid balance or baseline.",
)
def get_cash_flow_forecast(
    forecast_days: int = 30,
    current_user: UserModel = Depends(get_current_user),
    txn_repo: Any = Depends(get_repository),
    profile_repo: Any = Depends(get_profile_repository),
) -> CashFlowForecastResponse:
    """Produce a 30-day cash-flow forecast via GET using user profile's liquid balance."""
    stored = profile_repo.get_emergency_fund_config(user_id=current_user.id)
    balance = Decimal("0.00")
    if stored and stored.get("emergency_fund_balance") is not None:
        balance = Decimal(str(stored["emergency_fund_balance"]))

    start = ISODate.today()
    transactions = txn_repo.all(user_id=current_user.id)
    result = generate_cash_flow_forecast(
        transactions=transactions,
        current_balance=balance,
        forecast_start_date=start,
        min_cash_buffer=Decimal("0.00"),
        confirmed_future_transactions=[],
        observation_window_months=6,
    )

    daily = [DailyForecast(**d) for d in result.pop("daily_forecasts")]
    recurring = [DetectedRecurringInfo(**r) for r in result.pop("detected_recurring_transactions")]

    return CashFlowForecastResponse(
        **result,
        daily_forecasts=daily,
        detected_recurring_transactions=recurring,
    )

