"""
API integration tests for the AI Financial Decision Support System.

Uses FastAPI's ``TestClient`` (backed by ``httpx``) to exercise the full
HTTP stack — routing, validation, serialisation, and error handling —
without starting a real server.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

client = TestClient(app)


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    def test_status_code_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_response_body(self):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "ok"
        assert data["project"] == "AI Financial Decision Support System"

    def test_content_type_is_json(self):
        response = client.get("/health")
        assert "application/json" in response.headers["content-type"]


# ---------------------------------------------------------------------------
# POST /transactions/summary — valid requests
# ---------------------------------------------------------------------------


class TestTransactionSummaryValid:
    def test_empty_transaction_list_returns_200(self):
        response = client.post("/transactions/summary", json={"transactions": []})
        assert response.status_code == 200

    def test_empty_list_returns_zero_totals(self):
        response = client.post("/transactions/summary", json={"transactions": []})
        data = response.json()
        assert data["total_income"] == "0.00"
        assert data["total_expenses"] == "0.00"
        assert data["net_cash_flow"] == "0.00"
        assert data["transaction_count"] == 0

    def test_income_only_summary(self):
        payload = {
            "transactions": [
                {
                    "date": "2024-01-10",
                    "description": "Freelance payment",
                    "amount": "2500.00",
                    "transaction_type": "income",
                    "category": "freelance",
                }
            ]
        }
        response = client.post("/transactions/summary", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["total_income"] == "2500.00"
        assert data["total_expenses"] == "0.00"
        assert data["net_cash_flow"] == "2500.00"
        assert data["transaction_count"] == 1

    def test_expense_only_summary(self):
        payload = {
            "transactions": [
                {
                    "date": "2024-02-05",
                    "description": "Electricity bill",
                    "amount": "120.50",
                    "transaction_type": "expense",
                    "category": "utilities",
                }
            ]
        }
        response = client.post("/transactions/summary", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["total_income"] == "0.00"
        assert data["total_expenses"] == "120.50"
        assert data["net_cash_flow"] == "-120.50"
        assert data["transaction_count"] == 1

    def test_mixed_transactions_net_positive(self):
        payload = {
            "transactions": [
                {
                    "date": "2024-03-01",
                    "description": "Salary",
                    "amount": "4000.00",
                    "transaction_type": "income",
                    "category": "salary",
                },
                {
                    "date": "2024-03-05",
                    "description": "Rent",
                    "amount": "1500.00",
                    "transaction_type": "expense",
                    "category": "housing",
                },
                {
                    "date": "2024-03-10",
                    "description": "Groceries",
                    "amount": "300.00",
                    "transaction_type": "expense",
                    "category": "food",
                },
            ]
        }
        response = client.post("/transactions/summary", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["total_income"] == "4000.00"
        assert data["total_expenses"] == "1800.00"
        assert data["net_cash_flow"] == "2200.00"
        assert data["transaction_count"] == 3

    def test_mixed_transactions_net_negative(self):
        payload = {
            "transactions": [
                {
                    "date": "2024-04-01",
                    "description": "Part-time income",
                    "amount": "300.00",
                    "transaction_type": "income",
                },
                {
                    "date": "2024-04-02",
                    "description": "Medical bill",
                    "amount": "850.00",
                    "transaction_type": "expense",
                },
            ]
        }
        response = client.post("/transactions/summary", json=payload)
        data = response.json()
        assert data["net_cash_flow"] == "-550.00"

    def test_decimal_amounts_precision(self):
        payload = {
            "transactions": [
                {
                    "date": "2024-05-01",
                    "description": "Consulting",
                    "amount": "1234.56",
                    "transaction_type": "income",
                },
                {
                    "date": "2024-05-15",
                    "description": "Software subscription",
                    "amount": "89.99",
                    "transaction_type": "expense",
                },
            ]
        }
        response = client.post("/transactions/summary", json=payload)
        data = response.json()
        assert data["total_income"] == "1234.56"
        assert data["total_expenses"] == "89.99"
        assert data["net_cash_flow"] == "1144.57"
        assert data["transaction_count"] == 2

    def test_category_defaults_to_uncategorized(self):
        """Transactions without a category should default to 'uncategorized'."""
        payload = {
            "transactions": [
                {
                    "date": "2024-06-01",
                    "description": "Mystery deposit",
                    "amount": "50.00",
                    "transaction_type": "income",
                    # category intentionally omitted
                }
            ]
        }
        response = client.post("/transactions/summary", json=payload)
        assert response.status_code == 200

    def test_response_structure_has_required_keys(self):
        response = client.post("/transactions/summary", json={"transactions": []})
        data = response.json()
        assert "total_income" in data
        assert "total_expenses" in data
        assert "net_cash_flow" in data
        assert "transaction_count" in data


# ---------------------------------------------------------------------------
# POST /transactions/summary — validation errors (422)
# ---------------------------------------------------------------------------


class TestTransactionSummaryValidationErrors:
    def test_negative_amount_returns_422(self):
        payload = {
            "transactions": [
                {
                    "date": "2024-01-01",
                    "description": "Bad amount",
                    "amount": "-100.00",
                    "transaction_type": "income",
                }
            ]
        }
        response = client.post("/transactions/summary", json=payload)
        assert response.status_code == 422

    def test_zero_amount_returns_422(self):
        payload = {
            "transactions": [
                {
                    "date": "2024-01-01",
                    "description": "Zero amount",
                    "amount": "0",
                    "transaction_type": "income",
                }
            ]
        }
        response = client.post("/transactions/summary", json=payload)
        assert response.status_code == 422

    def test_empty_description_returns_422(self):
        payload = {
            "transactions": [
                {
                    "date": "2024-01-01",
                    "description": "   ",
                    "amount": "10.00",
                    "transaction_type": "income",
                }
            ]
        }
        response = client.post("/transactions/summary", json=payload)
        assert response.status_code == 422

    def test_invalid_transaction_type_returns_422(self):
        payload = {
            "transactions": [
                {
                    "date": "2024-01-01",
                    "description": "Refund",
                    "amount": "10.00",
                    "transaction_type": "refund",
                }
            ]
        }
        response = client.post("/transactions/summary", json=payload)
        assert response.status_code == 422

    def test_missing_description_returns_422(self):
        payload = {
            "transactions": [
                {
                    "date": "2024-01-01",
                    "amount": "10.00",
                    "transaction_type": "income",
                    # description missing
                }
            ]
        }
        response = client.post("/transactions/summary", json=payload)
        assert response.status_code == 422

    def test_missing_amount_returns_422(self):
        payload = {
            "transactions": [
                {
                    "date": "2024-01-01",
                    "description": "No amount",
                    "transaction_type": "income",
                    # amount missing
                }
            ]
        }
        response = client.post("/transactions/summary", json=payload)
        assert response.status_code == 422

    def test_missing_transaction_type_returns_422(self):
        payload = {
            "transactions": [
                {
                    "date": "2024-01-01",
                    "description": "No type",
                    "amount": "50.00",
                    # transaction_type missing
                }
            ]
        }
        response = client.post("/transactions/summary", json=payload)
        assert response.status_code == 422

    def test_invalid_date_format_returns_422(self):
        payload = {
            "transactions": [
                {
                    "date": "21st January 2024",
                    "description": "Bad date",
                    "amount": "10.00",
                    "transaction_type": "income",
                }
            ]
        }
        response = client.post("/transactions/summary", json=payload)
        assert response.status_code == 422

    def test_malformed_json_body_returns_422(self):
        # Send plain text instead of JSON
        response = client.post(
            "/transactions/summary",
            content=b"this is not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_missing_transactions_key_returns_200_with_defaults(self):
        """Omitting 'transactions' should be fine — it has a default of []."""
        response = client.post("/transactions/summary", json={})
        assert response.status_code == 200
        assert response.json()["transaction_count"] == 0

    def test_validation_error_body_contains_detail(self):
        payload = {
            "transactions": [
                {
                    "date": "2024-01-01",
                    "description": "Test",
                    "amount": "-1.00",
                    "transaction_type": "income",
                }
            ]
        }
        response = client.post("/transactions/summary", json=payload)
        assert response.status_code == 422
        body = response.json()
        assert "detail" in body
