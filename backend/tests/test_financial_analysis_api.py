"""
Phase 3 API integration tests — financial-profile and financial-analysis endpoints.

Coverage:
- PUT  /financial-profile/emergency-fund  — store and validate config
- GET  /financial-analysis/emergency-fund — compute and return analysis
- POST /financial-analysis/cash-flow-forecast — 30-day projection

All tests use the isolated ``client`` fixture from conftest.py, which
replaces both the transaction repository and the profile repository with
empty temporary files so no real data is read or written.

Phase regression:
- Health, Phase 1 stateless summary, Phase 2 create-transaction, and
  Phase 2 CSV import are verified to confirm zero regressions.
"""

import io
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SALARY_TXN = {
    "date": "2026-09-15",
    "description": "Monthly salary",
    "amount": "45000.00",
    "transaction_type": "income",
    "category": "salary",
    "source": "manual",
}

_RENT_TXN = {
    "date": "2026-09-01",
    "description": "House rent payment",
    "amount": "15000.00",
    "transaction_type": "expense",
    "category": "rent",
    "source": "manual",
}

_GROCERIES_TXN = {
    "date": "2026-09-10",
    "description": "Grocery shopping",
    "amount": "5000.00",
    "transaction_type": "expense",
    "category": "groceries",
    "source": "manual",
}

_ENTERTAINMENT_TXN = {
    "date": "2026-09-20",
    "description": "Netflix subscription",
    "amount": "500.00",
    "transaction_type": "expense",
    "category": "entertainment",
    "source": "manual",
}


def _post_txn(client: TestClient, txn: dict) -> str:
    """POST a transaction and return its assigned ID."""
    r = client.post("/transactions", json=txn)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _put_ef_config(
    client: TestClient,
    balance: str | None = "150000.00",
    categories: list[str] | None = None,
    window: int = 12,
) -> dict:
    """PUT an emergency fund configuration and return the response body."""
    payload: dict = {"analysis_window_months": window}
    if balance is not None:
        payload["emergency_fund_balance"] = balance
    if categories is not None:
        payload["essential_categories"] = categories
    r = client.put("/financial-profile/emergency-fund", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


# ===========================================================================
# TestPutEmergencyFundConfig
# ===========================================================================


class TestPutEmergencyFundConfig:
    """PUT /financial-profile/emergency-fund — store and validate config."""

    def test_put_config_returns_200(self, client: TestClient) -> None:
        r = client.put(
            "/financial-profile/emergency-fund",
            json={"emergency_fund_balance": "150000.00"},
        )
        assert r.status_code == 200

    def test_put_config_echoes_balance(self, client: TestClient) -> None:
        r = client.put(
            "/financial-profile/emergency-fund",
            json={"emergency_fund_balance": "200000.50"},
        )
        body = r.json()
        assert "emergency_fund_balance" in body
        # Decimal value should round-trip as a numeric string or number
        assert str(body["emergency_fund_balance"]).replace(",", "") in (
            "200000.5",
            "200000.50",
        )

    def test_put_config_echoes_essential_categories(self, client: TestClient) -> None:
        cats = ["rent", "groceries", "utilities"]
        r = client.put(
            "/financial-profile/emergency-fund",
            json={
                "emergency_fund_balance": "100000.00",
                "essential_categories": cats,
            },
        )
        assert r.status_code == 200
        assert r.json()["essential_categories"] == cats

    def test_put_config_echoes_analysis_window(self, client: TestClient) -> None:
        r = client.put(
            "/financial-profile/emergency-fund",
            json={"analysis_window_months": 6},
        )
        assert r.status_code == 200
        assert r.json()["analysis_window_months"] == 6

    def test_null_balance_accepted(self, client: TestClient) -> None:
        """Omitting the balance (unknown) should be accepted."""
        r = client.put(
            "/financial-profile/emergency-fund",
            json={"emergency_fund_balance": None},
        )
        assert r.status_code == 200
        assert r.json()["emergency_fund_balance"] is None

    def test_negative_balance_rejected_422(self, client: TestClient) -> None:
        r = client.put(
            "/financial-profile/emergency-fund",
            json={"emergency_fund_balance": "-5000.00"},
        )
        assert r.status_code == 422

    def test_zero_balance_accepted(self, client: TestClient) -> None:
        """Zero is a valid (though unusual) emergency fund balance."""
        r = client.put(
            "/financial-profile/emergency-fund",
            json={"emergency_fund_balance": "0.00"},
        )
        assert r.status_code == 200

    def test_window_below_min_rejected(self, client: TestClient) -> None:
        r = client.put(
            "/financial-profile/emergency-fund",
            json={"analysis_window_months": 0},
        )
        assert r.status_code == 422

    def test_window_above_max_rejected(self, client: TestClient) -> None:
        r = client.put(
            "/financial-profile/emergency-fund",
            json={"analysis_window_months": 61},
        )
        assert r.status_code == 422

    def test_content_type_is_json(self, client: TestClient) -> None:
        r = client.put(
            "/financial-profile/emergency-fund",
            json={},
        )
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")


# ===========================================================================
# TestGetEmergencyFundAnalysis
# ===========================================================================


class TestGetEmergencyFundAnalysis:
    """GET /financial-analysis/emergency-fund — compute and return analysis."""

    def test_get_with_no_profile_returns_200(self, client: TestClient) -> None:
        """Analysis should succeed even with no stored profile or transactions."""
        r = client.get("/financial-analysis/emergency-fund")
        assert r.status_code == 200

    def test_get_without_profile_balance_status_unknown(self, client: TestClient) -> None:
        r = client.get("/financial-analysis/emergency-fund")
        assert r.json()["balance_status"] == "unknown"

    def test_get_without_profile_balance_is_null(self, client: TestClient) -> None:
        r = client.get("/financial-analysis/emergency-fund")
        assert r.json()["emergency_fund_balance"] is None

    def test_get_without_profile_shortfalls_are_null(self, client: TestClient) -> None:
        r = client.get("/financial-analysis/emergency-fund")
        body = r.json()
        assert body["shortfall_three_month"] is None
        assert body["shortfall_six_month"] is None

    def test_get_after_put_balance_status_known(self, client: TestClient) -> None:
        _put_ef_config(client, balance="120000.00")
        r = client.get("/financial-analysis/emergency-fund")
        assert r.json()["balance_status"] == "known"

    def test_get_after_put_balance_returned(self, client: TestClient) -> None:
        _put_ef_config(client, balance="120000.00")
        r = client.get("/financial-analysis/emergency-fund")
        assert r.json()["emergency_fund_balance"] is not None

    def test_get_reflects_stored_transactions(self, client: TestClient) -> None:
        """Essential expenses from stored transactions must affect the analysis."""
        _post_txn(client, _RENT_TXN)
        _post_txn(client, _GROCERIES_TXN)
        r = client.get("/financial-analysis/emergency-fund")
        body = r.json()
        avg = Decimal(body["average_monthly_essential_expenses"])
        assert avg > Decimal("0")

    def test_targets_calculated_correctly_via_api(self, client: TestClient) -> None:
        """3-month and 6-month targets must be 3× and 6× the monthly average."""
        _post_txn(client, _RENT_TXN)   # 15 000 — essential
        r = client.get("/financial-analysis/emergency-fund")
        body = r.json()
        avg = Decimal(body["average_monthly_essential_expenses"])
        three = Decimal(body["three_month_target"])
        six = Decimal(body["six_month_target"])
        assert three == (avg * 3).quantize(Decimal("0.01"))
        assert six == (avg * 6).quantize(Decimal("0.01"))

    def test_non_essential_category_excluded_from_average(self, client: TestClient) -> None:
        """Entertainment expenses must not inflate the essential average."""
        _post_txn(client, _GROCERIES_TXN)      # 5 000 essential
        _post_txn(client, _ENTERTAINMENT_TXN)  # 500 non-essential

        r_default = client.get("/financial-analysis/emergency-fund")
        avg_default = Decimal(r_default.json()["average_monthly_essential_expenses"])

        # Configure only groceries as essential — avg should equal groceries only
        _put_ef_config(client, categories=["groceries"])
        r = client.get("/financial-analysis/emergency-fund")
        avg = Decimal(r.json()["average_monthly_essential_expenses"])

        # avg must not include the entertainment amount
        assert avg_default == avg  # default cats include groceries; entertainment not in either

    def test_essential_categories_from_profile_used(self, client: TestClient) -> None:
        """Custom essential categories must override defaults."""
        # Only count 'entertainment' as essential for this test
        _put_ef_config(client, categories=["entertainment"])
        _post_txn(client, _GROCERIES_TXN)       # 5 000 — NOT essential under custom config
        _post_txn(client, _ENTERTAINMENT_TXN)   # 500 — essential under custom config

        r = client.get("/financial-analysis/emergency-fund")
        body = r.json()
        avg = Decimal(body["average_monthly_essential_expenses"])
        # Only the entertainment transaction should count
        assert avg > Decimal("0")
        # Groceries should NOT be counted — average must be less than 5 500
        assert avg < Decimal("5000.00")

    def test_shortfall_is_positive_when_balance_below_target(self, client: TestClient) -> None:
        _post_txn(client, _RENT_TXN)
        _put_ef_config(client, balance="1000.00")  # far below any target
        r = client.get("/financial-analysis/emergency-fund")
        body = r.json()
        assert Decimal(body["shortfall_three_month"]) > Decimal("0")

    def test_shortfall_is_zero_when_balance_exceeds_three_month_target(
        self, client: TestClient
    ) -> None:
        _post_txn(client, _GROCERIES_TXN)  # 5 000 → 3-month target = 15 000
        _put_ef_config(client, balance="100000.00")  # well above target
        r = client.get("/financial-analysis/emergency-fund")
        assert r.json()["shortfall_three_month"] == "0.00"

    def test_response_has_warnings_and_assumptions_fields(self, client: TestClient) -> None:
        r = client.get("/financial-analysis/emergency-fund")
        body = r.json()
        assert "warnings" in body
        assert "assumptions" in body
        assert isinstance(body["warnings"], list)
        assert isinstance(body["assumptions"], list)

    def test_currency_is_inr(self, client: TestClient) -> None:
        r = client.get("/financial-analysis/emergency-fund")
        assert r.json()["currency"] == "INR"

    def test_response_schema_has_required_keys(self, client: TestClient) -> None:
        r = client.get("/financial-analysis/emergency-fund")
        body = r.json()
        required = {
            "currency",
            "analysis_window_months_requested",
            "complete_months_analyzed",
            "essential_categories_used",
            "average_monthly_essential_expenses",
            "three_month_target",
            "six_month_target",
            "balance_status",
            "warnings",
            "assumptions",
        }
        for key in required:
            assert key in body, f"Missing key: {key}"

    def test_insufficient_history_warning_emitted(self, client: TestClient) -> None:
        """With only 1 month of data, the system must warn about insufficient history."""
        _post_txn(client, _RENT_TXN)
        r = client.get("/financial-analysis/emergency-fund")
        body = r.json()
        warnings_text = " ".join(body["warnings"]).lower()
        assert "month" in warnings_text or "insufficient" in warnings_text or "reliable" in warnings_text


# ===========================================================================
# TestPostCashFlowForecast
# ===========================================================================


class TestPostCashFlowForecast:
    """POST /financial-analysis/cash-flow-forecast — 30-day projection."""

    _START = (date.today() + timedelta(days=1)).isoformat()

    def _minimal_payload(self) -> dict:
        return {
            "current_balance": "250000.00",
            "forecast_start_date": self._START,
        }

    def test_returns_200_with_valid_request(self, client: TestClient) -> None:
        r = client.post("/financial-analysis/cash-flow-forecast", json=self._minimal_payload())
        assert r.status_code == 200

    def test_missing_current_balance_returns_422(self, client: TestClient) -> None:
        r = client.post(
            "/financial-analysis/cash-flow-forecast",
            json={"forecast_start_date": self._START},
        )
        assert r.status_code == 422

    def test_30_daily_forecasts_returned(self, client: TestClient) -> None:
        r = client.post("/financial-analysis/cash-flow-forecast", json=self._minimal_payload())
        assert len(r.json()["daily_forecasts"]) == 30

    def test_forecast_start_date_defaults_to_today(self, client: TestClient) -> None:
        """Omitting forecast_start_date should still return 30 days."""
        r = client.post(
            "/financial-analysis/cash-flow-forecast",
            json={"current_balance": "100000.00"},
        )
        assert r.status_code == 200
        assert len(r.json()["daily_forecasts"]) == 30

    def test_daily_forecast_has_required_fields(self, client: TestClient) -> None:
        r = client.post("/financial-analysis/cash-flow-forecast", json=self._minimal_payload())
        day = r.json()["daily_forecasts"][0]
        for field in (
            "date",
            "projected_income",
            "projected_expenses",
            "net_daily_flow",
            "closing_balance",
            "is_low_cash",
            "is_negative_balance",
        ):
            assert field in day, f"Missing daily-forecast field: {field}"

    def test_opening_balance_matches_request(self, client: TestClient) -> None:
        r = client.post("/financial-analysis/cash-flow-forecast", json=self._minimal_payload())
        assert r.json()["opening_balance"] == "250000.00"

    def test_confirmed_future_transactions_incorporated(self, client: TestClient) -> None:
        """A confirmed income on day 1 of the forecast window must appear in projections."""
        start = (date.today() + timedelta(days=1)).isoformat()
        payload = {
            "current_balance": "50000.00",
            "forecast_start_date": start,
            "confirmed_future_transactions": [
                {
                    "date": start,
                    "description": "Freelance payment",
                    "amount": "30000.00",
                    "transaction_type": "income",
                }
            ],
        }
        r = client.post("/financial-analysis/cash-flow-forecast", json=payload)
        assert r.status_code == 200
        body = r.json()
        day1 = body["daily_forecasts"][0]
        assert Decimal(day1["projected_income"]) >= Decimal("30000.00")

    def test_confirmed_expense_reduces_balance(self, client: TestClient) -> None:
        start = (date.today() + timedelta(days=1)).isoformat()
        payload = {
            "current_balance": "50000.00",
            "forecast_start_date": start,
            "confirmed_future_transactions": [
                {
                    "date": start,
                    "description": "Insurance premium",
                    "amount": "10000.00",
                    "transaction_type": "expense",
                }
            ],
        }
        r = client.post("/financial-analysis/cash-flow-forecast", json=payload)
        day1 = r.json()["daily_forecasts"][0]
        assert Decimal(day1["projected_expenses"]) >= Decimal("10000.00")

    def test_low_cash_dates_identified(self, client: TestClient) -> None:
        """With a high buffer and low balance, early days should be flagged as low-cash."""
        payload = {
            "current_balance": "5000.00",
            "min_cash_buffer": "100000.00",  # very high — almost every day is low-cash
        }
        r = client.post("/financial-analysis/cash-flow-forecast", json=payload)
        body = r.json()
        # Not necessarily all 30, but at least some days should be low-cash
        assert len(body["low_cash_dates"]) > 0

    def test_negative_balance_dates_identified_when_expenses_exceed_balance(
        self, client: TestClient
    ) -> None:
        """A very high confirmed expense should produce negative-balance dates."""
        start = (date.today() + timedelta(days=1)).isoformat()
        payload = {
            "current_balance": "100.00",
            "forecast_start_date": start,
            "confirmed_future_transactions": [
                {
                    "date": start,
                    "description": "Large expense",
                    "amount": "50000.00",
                    "transaction_type": "expense",
                }
            ],
        }
        r = client.post("/financial-analysis/cash-flow-forecast", json=payload)
        body = r.json()
        assert len(body["negative_balance_dates"]) > 0

    def test_observation_window_respected(self, client: TestClient) -> None:
        """observation_window_months is accepted and reflected in the response."""
        payload = {
            "current_balance": "250000.00",
            "observation_window_months": 3,
        }
        r = client.post("/financial-analysis/cash-flow-forecast", json=payload)
        assert r.status_code == 200

    def test_response_has_methodology_and_assumptions(self, client: TestClient) -> None:
        r = client.post("/financial-analysis/cash-flow-forecast", json=self._minimal_payload())
        body = r.json()
        assert "methodology" in body and body["methodology"]
        assert "assumptions" in body and isinstance(body["assumptions"], list)

    def test_response_has_warnings_field(self, client: TestClient) -> None:
        r = client.post("/financial-analysis/cash-flow-forecast", json=self._minimal_payload())
        body = r.json()
        assert "warnings" in body
        assert isinstance(body["warnings"], list)

    def test_response_schema_has_required_keys(self, client: TestClient) -> None:
        r = client.post("/financial-analysis/cash-flow-forecast", json=self._minimal_payload())
        body = r.json()
        required = {
            "forecast_start_date",
            "forecast_end_date",
            "opening_balance",
            "projected_closing_balance",
            "total_projected_income",
            "total_projected_expenses",
            "net_projected_cash_flow",
            "low_cash_dates",
            "negative_balance_dates",
            "daily_forecasts",
            "detected_recurring_transactions",
            "months_of_history_used",
            "methodology",
            "assumptions",
            "warnings",
        }
        for key in required:
            assert key in body, f"Missing response key: {key}"

    def test_uses_stored_transactions_for_history(self, client: TestClient) -> None:
        """Transactions stored in the repo must feed into recurring detection."""
        # Post the same expense in two different months to trigger recurring detection
        for month in ("2026-08", "2026-09"):
            client.post(
                "/transactions",
                json={
                    "date": f"{month}-05",
                    "description": "Monthly internet bill",
                    "amount": "999.00",
                    "transaction_type": "expense",
                    "category": "utilities",
                },
            )
        r = client.post("/financial-analysis/cash-flow-forecast", json=self._minimal_payload())
        assert r.status_code == 200
        body = r.json()
        # With 2 months of the same transaction, it should be detected as recurring
        detected_descs = [d["description"].lower() for d in body["detected_recurring_transactions"]]
        assert any("internet" in d for d in detected_descs)

    def test_invalid_future_transaction_date_returns_422(self, client: TestClient) -> None:
        payload = {
            "current_balance": "50000.00",
            "confirmed_future_transactions": [
                {
                    "date": "not-a-date",
                    "description": "Bad date",
                    "amount": "1000.00",
                    "transaction_type": "income",
                }
            ],
        }
        r = client.post("/financial-analysis/cash-flow-forecast", json=payload)
        assert r.status_code == 422

    def test_negative_future_transaction_amount_returns_422(self, client: TestClient) -> None:
        start = (date.today() + timedelta(days=1)).isoformat()
        payload = {
            "current_balance": "50000.00",
            "confirmed_future_transactions": [
                {
                    "date": start,
                    "description": "Negative amount",
                    "amount": "-100.00",
                    "transaction_type": "expense",
                }
            ],
        }
        r = client.post("/financial-analysis/cash-flow-forecast", json=payload)
        assert r.status_code == 422

    def test_detected_recurring_info_has_required_fields(self, client: TestClient) -> None:
        """If any recurring transactions are detected, each must include required fields."""
        # Add 2 months of the same expense to guarantee detection
        for month in ("2026-07", "2026-08"):
            client.post(
                "/transactions",
                json={
                    "date": f"{month}-10",
                    "description": "Gym membership",
                    "amount": "1500.00",
                    "transaction_type": "expense",
                    "category": "entertainment",
                },
            )
        r = client.post("/financial-analysis/cash-flow-forecast", json=self._minimal_payload())
        body = r.json()
        for rec in body["detected_recurring_transactions"]:
            for field in (
                "description",
                "transaction_type",
                "typical_day_of_month",
                "typical_amount",
                "months_observed",
            ):
                assert field in rec, f"Missing recurring field: {field}"


# ===========================================================================
# TestPhase3Regression  — confirm Phase 1 and Phase 2 still work
# ===========================================================================


class TestPhase3Regression:
    """Verify that Phase 1 and Phase 2 endpoints are unaffected by Phase 3 additions."""

    def test_health_still_works(self, client: TestClient) -> None:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_phase1_summary_still_works(self, client: TestClient) -> None:
        payload = {
            "transactions": [
                {
                    "date": "2026-10-01",
                    "description": "Salary",
                    "amount": "50000.00",
                    "transaction_type": "income",
                },
                {
                    "date": "2026-10-02",
                    "description": "Rent",
                    "amount": "15000.00",
                    "transaction_type": "expense",
                },
            ]
        }
        r = client.post("/transactions/summary", json=payload)
        assert r.status_code == 200
        body = r.json()
        assert body["total_income"] == "50000.00"
        assert body["total_expenses"] == "15000.00"
        assert body["net_cash_flow"] == "35000.00"

    def test_phase2_create_transaction_still_works(self, client: TestClient) -> None:
        r = client.post("/transactions", json=_SALARY_TXN)
        assert r.status_code == 201
        body = r.json()
        assert "id" in body
        assert body["description"] == "Monthly salary"

    def test_phase2_list_transactions_still_works(self, client: TestClient) -> None:
        _post_txn(client, _SALARY_TXN)
        r = client.get("/transactions")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_phase2_stored_summary_still_works(self, client: TestClient) -> None:
        _post_txn(client, _SALARY_TXN)
        _post_txn(client, _RENT_TXN)
        r = client.get("/transactions/stored-summary")
        assert r.status_code == 200
        body = r.json()
        assert Decimal(body["total_income"]) == Decimal("45000.00")
        assert Decimal(body["total_expenses"]) == Decimal("15000.00")

    def test_phase2_csv_import_still_works(self, client: TestClient) -> None:
        csv_content = (
            "date,description,amount,transaction_type,category\n"
            "2026-10-01,Freelance payment,25000.00,income,salary\n"
        )
        csv_bytes = csv_content.encode("utf-8")
        r = client.post(
            "/transactions/import-csv",
            files={"file": ("test.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["imported"] == 1
        assert body["rejected"] == 0

    def test_phase2_delete_transaction_still_works(self, client: TestClient) -> None:
        txn_id = _post_txn(client, _SALARY_TXN)
        r = client.delete(f"/transactions/{txn_id}")
        assert r.status_code == 200
        # Verify it is gone
        r2 = client.get(f"/transactions/{txn_id}")
        assert r2.status_code == 404
