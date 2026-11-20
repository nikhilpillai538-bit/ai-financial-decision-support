"""
Unit and integration tests for Phase 9 Financial Context Gathering and Domain Detection.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai.financial_context import (
    FinancialContextService,
    ValidatedFinancialContext,
    detect_financial_domains,
)
from app.db.base import Base
from app.db.models import (
    AssetModel,
    InvestmentGoalModel,
    PortfolioHoldingModel,
    PortfolioModel,
    TransactionModel,
    UserModel,
)
from app.db.repositories.profile_repo import SQLProfileRepository
from app.db.repositories.transaction_repo import SQLTransactionRepository
from app.schemas import StoredTransaction, TransactionSource, TransactionType


class TestDomainDetection:
    def test_detect_spending_keywords(self):
        domains = detect_financial_domains("How much did I spend on groceries and rent?")
        assert "spending_and_cash_flow" in domains

    def test_detect_emergency_fund_keywords(self):
        domains = detect_financial_domains("Is my emergency fund safety net sufficient for 6 months?")
        assert "emergency_fund" in domains

    def test_detect_goals_keywords(self):
        domains = detect_financial_domains("How is my retirement goal and monthly SIP pacing?")
        assert "investment_goals" in domains

    def test_detect_portfolio_risk_keywords(self):
        domains = detect_financial_domains("What is the Sharpe ratio and volatility of my portfolio?")
        assert "portfolio_risk_and_allocation" in domains

    def test_detect_drift_and_rebalance_keywords(self):
        domains = detect_financial_domains("Has asset allocation drifted beyond the rebalance threshold?")
        assert "rebalancing_and_drift" in domains

    def test_detect_generic_query_returns_core_domains(self):
        domains = detect_financial_domains("Give me a general overview of my finances.")
        assert "spending_and_cash_flow" in domains
        assert "emergency_fund" in domains
        assert "portfolio_risk_and_allocation" in domains
        assert "investment_goals" in domains


class TestFinancialContextService:
    @pytest.fixture()
    def db_session(self) -> Session:
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        session = TestingSessionLocal()
        yield session
        session.close()

    def test_build_context_empty_records(self, db_session: Session):
        user = UserModel(
            id="empty-user-1",
            email="empty@example.com",
            password_hash="mock",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        service = FinancialContextService(db_session)
        ctx = service.build_context(user, "What is my current spending and emergency fund?")

        assert ctx.user_id == user.id
        assert "spending_and_cash_flow" in ctx.domains_retrieved
        assert "emergency_fund" in ctx.domains_retrieved
        assert len(ctx.missing_data_warnings) > 0
        assert any("No transactions recorded yet" in w for w in ctx.missing_data_warnings)

        grounded_text = ctx.to_grounded_text()
        assert "VERIFIED FINANCIAL RECORD" in grounded_text

    def test_build_context_with_populated_user_data(self, db_session: Session):
        user = UserModel(
            id="active-user-1",
            email="active@example.com",
            password_hash="mock",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        # Add transactions
        tx_repo = SQLTransactionRepository(db_session)
        tx_repo.save(
            StoredTransaction(
                id=str(uuid.uuid4()),
                date=date(2026, 10, 1),
                description="Salary",
                amount=Decimal("100000.00"),
                transaction_type=TransactionType.income,
                category="Salary",
                source=TransactionSource.manual,
            ),
            user_id=user.id,
        )
        tx_repo.save(
            StoredTransaction(
                id=str(uuid.uuid4()),
                date=date(2026, 10, 5),
                description="House Rent",
                amount=Decimal("30000.00"),
                transaction_type=TransactionType.expense,
                category="rent",
                source=TransactionSource.manual,
            ),
            user_id=user.id,
        )

        # Set emergency fund profile
        prof_repo = SQLProfileRepository(db_session)
        prof_repo.save_emergency_fund_config(
            {
                "emergency_fund_balance": "150000.00",
                "essential_categories": ["rent", "groceries", "utilities"],
                "analysis_window_months": 6,
            },
            user_id=user.id,
        )

        # Set portfolio & goal
        port = PortfolioModel(
            id="port-1",
            user_id=user.id,
            name="Wealth Portfolio",
            base_currency="INR",
        )
        db_session.add(port)
        goal = InvestmentGoalModel(
            id="goal-1",
            user_id=user.id,
            portfolio_id=port.id,
            name="Retirement Fund",
            target_amount=Decimal("5000000.00"),
            target_date=date(2036, 10, 1),
            monthly_contribution=Decimal("25000.00"),
            expected_annual_return=Decimal("0.1200"),
        )
        db_session.add(goal)
        db_session.commit()

        service = FinancialContextService(db_session)
        ctx = service.build_context(user, "Analyze my spending, emergency fund, and goals")

        assert "spending_and_cash_flow" in ctx.verified_data
        spend = ctx.verified_data["spending_and_cash_flow"]
        assert spend["total_income"] == "100000.00"
        assert spend["total_expenses"] == "30000.00"
        assert spend["net_savings"] == "70000.00"

        assert "emergency_fund" in ctx.verified_data
        ef = ctx.verified_data["emergency_fund"]
        assert ef["available_savings"] == "150000.00"

        assert "investment_goals" in ctx.verified_data
        goals = ctx.verified_data["investment_goals"]
        assert len(goals) == 1
        assert goals[0]["name"] == "Retirement Fund"

        text = ctx.to_grounded_text()
        assert "[Domain: Spending & Cash Flow]" in text
        assert "[Domain: Emergency Fund]" in text
        assert "[Domain: Investment Goals]" in text

    def test_user_data_isolation_in_context(self, db_session: Session):
        user_a = UserModel(id="user-a", email="a@example.com", password_hash="hash", is_active=True)
        user_b = UserModel(id="user-b", email="b@example.com", password_hash="hash", is_active=True)
        db_session.add_all([user_a, user_b])
        db_session.commit()

        tx_repo = SQLTransactionRepository(db_session)
        tx_repo.save(
            StoredTransaction(
                id=str(uuid.uuid4()),
                date=date(2026, 10, 1),
                description="Salary A",
                amount=Decimal("200000.00"),
                transaction_type=TransactionType.income,
                category="Salary",
                source=TransactionSource.manual,
            ),
            user_id=user_a.id,
        )

        service = FinancialContextService(db_session)
        ctx_b = service.build_context(user_b, "What is my income?")
        assert "spending_and_cash_flow" not in ctx_b.verified_data
        assert any("No transactions recorded yet" in w for w in ctx_b.missing_data_warnings)
