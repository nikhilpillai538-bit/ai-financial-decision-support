"""
Unit tests for Phase 9 Explainable Financial Insights Service.
"""

from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai.insights_service import FinancialHealthReport, FinancialInsightsService, InsightItem
from app.db.base import Base
from app.db.models import UserModel


class TestFinancialInsightsService:
    @pytest.fixture()
    def db_session(self) -> Session:
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        session = TestingSession()
        yield session
        session.close()

    def test_evaluate_spending_negative_savings(self, db_session: Session):
        service = FinancialInsightsService(db_session)
        item = service._evaluate_spending({
            "total_income": "40000.00",
            "total_expenses": "55000.00",
            "net_savings": "-15000.00",
            "savings_rate_percentage": "0.00",
            "top_spending_categories": {"rent": "30000.00"},
        })
        assert item is not None
        assert item.severity == "alert"
        assert "Negative Monthly Net Savings" in item.title
        assert len(item.recommendations) > 0

    def test_evaluate_spending_positive_savings(self, db_session: Session):
        service = FinancialInsightsService(db_session)
        item = service._evaluate_spending({
            "total_income": "100000.00",
            "total_expenses": "60000.00",
            "net_savings": "40000.00",
            "savings_rate_percentage": "40.00",
            "top_spending_categories": {"groceries": "15000.00"},
        })
        assert item is not None
        assert item.severity == "positive"
        assert "Healthy Savings Rate" in item.title

    def test_evaluate_emergency_fund_critical(self, db_session: Session):
        service = FinancialInsightsService(db_session)
        item = service._evaluate_emergency_fund({
            "available_savings": "10000.00",
            "monthly_essential_expenses": "40000.00",
            "months_of_coverage": "0.25",
            "target_3_months": "120000.00",
            "shortfall_3_months": "110000.00",
            "target_6_months": "240000.00",
            "shortfall_6_months": "230000.00",
        })
        assert item is not None
        assert item.severity == "alert"
        assert "Critical Emergency Reserve Deficiency" in item.title

    def test_evaluate_emergency_fund_robust(self, db_session: Session):
        service = FinancialInsightsService(db_session)
        item = service._evaluate_emergency_fund({
            "available_savings": "300000.00",
            "monthly_essential_expenses": "40000.00",
            "months_of_coverage": "7.5",
            "target_3_months": "120000.00",
            "shortfall_3_months": "0.00",
            "target_6_months": "240000.00",
            "shortfall_6_months": "0.00",
        })
        assert item is not None
        assert item.severity == "positive"
        assert "Robust Emergency Fund Coverage" in item.title

    def test_evaluate_goals_with_shortfall(self, db_session: Session):
        service = FinancialInsightsService(db_session)
        goals = [
            {
                "name": "Home Down Payment",
                "status_assessment": "behind",
                "planned_monthly_contribution": "10000.00",
                "required_monthly_contribution": "18000.00",
            }
        ]
        item = service._evaluate_goals(goals)
        assert item is not None
        assert item.severity == "warning"
        assert "Trailing Target Pace" in item.title
        assert item.metrics["total_monthly_sip_shortfall"] == "8000.00"

    def test_evaluate_drift_exceeded(self, db_session: Session):
        service = FinancialInsightsService(db_session)
        item = service._evaluate_drift({
            "portfolio_exceeds_threshold": True,
            "max_drift_percentage_points": "8.50",
            "drift_threshold_percentage_points": "5.00",
            "drifted_classes": ["Equity", "Debt"],
            "illustrative_rebalancing_trades": [
                {"action": "SELL", "trade_amount": "50000.00", "asset_class": "Equity"}
            ],
        })
        assert item is not None
        assert item.severity == "warning"
        assert "Exceeds 5.00% Threshold" in item.title
        assert len(item.recommendations) >= 1

    def test_generate_report_overall_synthesis(self, db_session: Session):
        user = UserModel(id="u-report", email="r@example.com", password_hash="hash", is_active=True)
        db_session.add(user)
        db_session.commit()

        service = FinancialInsightsService(db_session)
        report = service.generate_report(user)
        assert isinstance(report, FinancialHealthReport)
        assert report.user_id == user.id
        assert report.overall_status in ["healthy", "attention_needed", "critical", "insufficient_data"]
        report_dict = report.to_dict()
        assert "executive_summary" in report_dict
        assert "insights" in report_dict
