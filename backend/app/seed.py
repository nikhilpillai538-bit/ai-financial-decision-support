"""
Automated database seeder for initial production deployment and demo readiness.
Idempotent: Only seeds if the database contains 0 registered users.
"""

import logging
import uuid
import random
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.models import (
    UserModel,
    FinancialProfileModel,
    TransactionModel,
    AssetModel,
    PortfolioModel,
    PortfolioHoldingModel,
    TargetAllocationModel,
    HistoricalPriceModel,
    InvestmentGoalModel,
)

logger = logging.getLogger("uvicorn.error")


def ensure_seed_data(engine) -> bool:
    """Check if database is unseeded; if empty, populate realistic demo financial dataset.

    Returns:
        True if seeding was performed, False if database already contains users.
    """
    with Session(engine) as session:
        user_count = session.scalar(select(func.count(UserModel.id))) or 0
        if user_count > 0:
            logger.info("Database already seeded (%d existing user accounts).", user_count)
            return False

        logger.info("Empty database detected. Auto-seeding initial demo portfolio and financial history...")

        # 1. Primary Demo User
        user = UserModel(
            id=str(uuid.uuid4()),
            email="nikhilpillai538@gmail.com",
            # Standard argon2id hash
            password_hash="$argon2id$v=19$m=65536,t=3,p=4$JKmzRRpMl+NDHhlNPPlNzQ$uF5DIAkMUCFSAXeW9+tND6Tg6r6mqoLCjczO3/svy5U",
            is_active=True,
        )
        session.add(user)
        session.flush()
        user_id = user.id

        # 2. Financial Profile & Emergency Fund Configuration
        profile = FinancialProfileModel(
            user_id=user_id,
            profile_key=f"profile-{user_id[:8]}",
            emergency_fund_balance=Decimal("250000.00"),
            min_cash_buffer=Decimal("30000.00"),
            currency="INR",
            analysis_window_months=12,
            essential_categories=["rent", "groceries", "utilities", "healthcare", "transport"],
        )
        session.add(profile)

        # 3. 90 Days of Realistic Cash Flow Transactions
        months = [(2026, 9), (2026, 10), (2026, 11)]
        tx_list = []
        for yr, mo in months:
            tx_list.append(TransactionModel(
                id=str(uuid.uuid4()), user_id=user_id, date=date(yr, mo, 1),
                description="Monthly Salary Credit - Tech Corp India",
                amount=Decimal("125000.00"), transaction_type="income", category="salary", source="manual"
            ))
            tx_list.append(TransactionModel(
                id=str(uuid.uuid4()), user_id=user_id, date=date(yr, mo, 3),
                description="Residential Apartment Rent",
                amount=Decimal("28000.00"), transaction_type="expense", category="rent", source="manual"
            ))
            tx_list.append(TransactionModel(
                id=str(uuid.uuid4()), user_id=user_id, date=date(yr, mo, 5),
                description="Systematic Investment Plan (SIP) Equity Index",
                amount=Decimal("25000.00"), transaction_type="expense", category="investment", source="manual"
            ))
            tx_list.append(TransactionModel(
                id=str(uuid.uuid4()), user_id=user_id, date=date(yr, mo, 8),
                description="Supermarket Groceries & Household Essentials",
                amount=Decimal("4250.00"), transaction_type="expense", category="groceries", source="manual"
            ))
            tx_list.append(TransactionModel(
                id=str(uuid.uuid4()), user_id=user_id, date=date(yr, mo, 10),
                description="Electricity Board & High-Speed Internet Bill",
                amount=Decimal("3850.00"), transaction_type="expense", category="utilities", source="manual"
            ))
            tx_list.append(TransactionModel(
                id=str(uuid.uuid4()), user_id=user_id, date=date(yr, mo, 12),
                description="Health & Term Insurance Premium",
                amount=Decimal("5200.00"), transaction_type="expense", category="healthcare", source="manual"
            ))
            tx_list.append(TransactionModel(
                id=str(uuid.uuid4()), user_id=user_id, date=date(yr, mo, 15),
                description="Fresh Vegetables, Dairy & Weekly Provisions",
                amount=Decimal("3600.00"), transaction_type="expense", category="groceries", source="manual"
            ))
            tx_list.append(TransactionModel(
                id=str(uuid.uuid4()), user_id=user_id, date=date(yr, mo, 17),
                description="Fuel & City Transit Recharge",
                amount=Decimal("2800.00"), transaction_type="expense", category="transport", source="manual"
            ))
            tx_list.append(TransactionModel(
                id=str(uuid.uuid4()), user_id=user_id, date=date(yr, mo, 20),
                description="Family Dining & Leisure Weekend",
                amount=Decimal("3400.00"), transaction_type="expense", category="dining", source="manual"
            ))
            if mo != 11:
                tx_list.append(TransactionModel(
                    id=str(uuid.uuid4()), user_id=user_id, date=date(yr, mo, 22),
                    description="Monthly Provisions & Supplies",
                    amount=Decimal("3900.00"), transaction_type="expense", category="groceries", source="manual"
                ))
                tx_list.append(TransactionModel(
                    id=str(uuid.uuid4()), user_id=user_id, date=date(yr, mo, 26),
                    description="Online E-commerce Purchases",
                    amount=Decimal("4600.00"), transaction_type="expense", category="shopping", source="manual"
                ))

        tx_list.append(TransactionModel(
            id=str(uuid.uuid4()), user_id=user_id, date=date(2026, 10, 15),
            description="Diwali Festival Corporate Performance Bonus",
            amount=Decimal("50000.00"), transaction_type="income", category="bonus", source="manual"
        ))
        session.add_all(tx_list)

        # 4. Global Market Instruments
        instruments = [
            {"symbol": "RELIANCE.NS", "name": "Reliance Industries Limited", "class": "equity", "type": "large_cap", "price": Decimal("2985.50"), "qty": Decimal("50"), "avg": Decimal("2820.00")},
            {"symbol": "TCS.NS", "name": "Tata Consultancy Services Limited", "class": "equity", "type": "large_cap", "price": Decimal("4140.00"), "qty": Decimal("40"), "avg": Decimal("3880.00")},
            {"symbol": "HDFCBANK.NS", "name": "HDFC Bank Limited", "class": "equity", "type": "large_cap", "price": Decimal("1695.00"), "qty": Decimal("100"), "avg": Decimal("1530.00")},
            {"symbol": "INFY.NS", "name": "Infosys Limited", "class": "equity", "type": "large_cap", "price": Decimal("1835.00"), "qty": Decimal("75"), "avg": Decimal("1680.00")},
            {"symbol": "ICICIBANK.NS", "name": "ICICI Bank Limited", "class": "equity", "type": "large_cap", "price": Decimal("1255.00"), "qty": Decimal("80"), "avg": Decimal("1120.00")},
            {"symbol": "GOLDBEES.NS", "name": "Nippon India ETF Gold BeES", "class": "commodities_gold", "type": "gold_etf", "price": Decimal("65.20"), "qty": Decimal("1500"), "avg": Decimal("56.50")},
            {"symbol": "LIQUIDBEES.NS", "name": "Nippon India ETF Nifty 1D Rate Liquid BeES", "class": "debt", "type": "liquid_fund", "price": Decimal("1000.00"), "qty": Decimal("100"), "avg": Decimal("1000.00")},
        ]

        asset_objs = {}
        for item in instruments:
            a = AssetModel(
                id=str(uuid.uuid4()), user_id=None, symbol=item["symbol"],
                name=item["name"], asset_class=item["class"], currency="INR",
                instrument_type=item["type"]
            )
            session.add(a)
            session.flush()
            asset_objs[item["symbol"]] = a

        # 5. Primary Portfolio
        portfolio = PortfolioModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name="Primary Wealth & Growth Portfolio",
            description="Core multi-asset growth portfolio combining top Indian large-caps, Gold ETF hedge, and liquid reserves.",
            base_currency="INR",
        )
        session.add(portfolio)
        session.flush()

        # 6. Portfolio Holdings
        for item in instruments:
            h = PortfolioHoldingModel(
                id=str(uuid.uuid4()),
                portfolio_id=portfolio.id,
                asset_id=asset_objs[item["symbol"]].id,
                quantity=item["qty"],
                average_purchase_price=item["avg"],
                current_price=item["price"],
                price_as_of=datetime.now(timezone.utc),
                notes=f"Core holding in {item['name']}",
            )
            session.add(h)

        # 7. Target Asset Allocation
        target = TargetAllocationModel(
            id=str(uuid.uuid4()),
            portfolio_id=portfolio.id,
            user_id=user_id,
            targets={"equity": 65.0, "debt": 15.0, "commodities_gold": 10.0, "cash": 10.0},
            is_draft=False,
            notes="Target growth allocation model for balanced long-term wealth accumulation.",
        )
        session.add(target)

        # 8. 250-Day Historical Price Series (for MPT & Backtesting)
        params = {
            "RELIANCE.NS": {"start": 2600.0, "drift": 0.0006, "vol": 0.014},
            "TCS.NS": {"start": 3650.0, "drift": 0.0005, "vol": 0.012},
            "HDFCBANK.NS": {"start": 1450.0, "drift": 0.0006, "vol": 0.013},
            "INFY.NS": {"start": 1550.0, "drift": 0.0007, "vol": 0.015},
            "ICICIBANK.NS": {"start": 1020.0, "drift": 0.0008, "vol": 0.014},
            "GOLDBEES.NS": {"start": 52.0, "drift": 0.0009, "vol": 0.008},
            "LIQUIDBEES.NS": {"start": 1000.0, "drift": 0.0000, "vol": 0.0001},
        }
        random.seed(42)
        curr_prices = {k: v["start"] for k, v in params.items()}
        cur_date = date(2025, 11, 20)
        end_date = date(2026, 11, 20)
        hist_records = []

        while cur_date <= end_date:
            if cur_date.weekday() < 5:
                for sym, cfg in params.items():
                    if sym == "LIQUIDBEES.NS":
                        p = 1000.00
                    else:
                        ret = cfg["drift"] + cfg["vol"] * random.gauss(0, 1)
                        curr_prices[sym] *= (1.0 + ret)
                        p = round(curr_prices[sym], 2)
                    hist_records.append(HistoricalPriceModel(
                        id=str(uuid.uuid4()),
                        symbol=sym,
                        date=cur_date,
                        adjusted_close=Decimal(str(p)),
                        source="cloud_seed_init",
                    ))
            cur_date += timedelta(days=1)

        session.bulk_save_objects(hist_records)

        # 9. Investment Goals
        goals = [
            InvestmentGoalModel(
                id=str(uuid.uuid4()), user_id=user_id, portfolio_id=portfolio.id,
                name="Retirement Corpus Fund", target_amount=Decimal("20000000.00"),
                target_date=date(2045, 12, 31), priority="high", status="in_progress",
                current_amount=Decimal("1500000.00"), initial_lump_sum=Decimal("500000.00"),
                monthly_contribution=Decimal("35000.00"), expected_annual_return=Decimal("0.1200"),
                notes="Primary retirement corpus with 12% equity growth expectation.",
            ),
            InvestmentGoalModel(
                id=str(uuid.uuid4()), user_id=user_id, portfolio_id=portfolio.id,
                name="Dream Home Down Payment", target_amount=Decimal("2500000.00"),
                target_date=date(2028, 6, 30), priority="high", status="in_progress",
                current_amount=Decimal("850000.00"), initial_lump_sum=Decimal("200000.00"),
                monthly_contribution=Decimal("25000.00"), expected_annual_return=Decimal("0.1000"),
                notes="Target 20% down payment for 3BHK residential home.",
            ),
            InvestmentGoalModel(
                id=str(uuid.uuid4()), user_id=user_id, portfolio_id=portfolio.id,
                name="Higher Education & Certifications", target_amount=Decimal("600000.00"),
                target_date=date(2027, 4, 30), priority="medium", status="in_progress",
                current_amount=Decimal("240000.00"), initial_lump_sum=Decimal("50000.00"),
                monthly_contribution=Decimal("15000.00"), expected_annual_return=Decimal("0.0800"),
                notes="Executive professional development and analytics program.",
            ),
        ]
        session.add_all(goals)

        session.commit()
        logger.info("Auto-seeding successfully completed for user nikhilpillai538@gmail.com.")
        return True
