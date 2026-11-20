"""
Phase 2 automated tests — Transaction Management and CSV Import.

All tests use the ``client`` fixture from conftest.py which injects a
temporary, isolated repository so real transaction data is never touched.

Test coverage
-------------
- POST   /transactions (create)
- GET    /transactions (list + filters)
- GET    /transactions/{id} (get one)
- DELETE /transactions/{id}
- POST   /transactions/import-csv
- GET    /transactions/stored-summary
- app.categorization.categorize()
- Phase 1 regression (health + stateless summary)
"""

import io
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient


# ===========================================================================
# Helpers
# ===========================================================================


def _make_csv(rows: list[dict], header: list[str] | None = None) -> bytes:
    """Build a minimal CSV bytes payload from a list of row dicts."""
    if header is None:
        header = ["date", "description", "amount", "transaction_type", "category"]
    lines = [",".join(header)]
    for row in rows:
        lines.append(",".join(str(row.get(col, "")) for col in header))
    return "\n".join(lines).encode("utf-8")


def _upload_csv(client: TestClient, content: bytes, filename: str = "test.csv") -> dict:
    """POST a CSV upload and return the parsed JSON response."""
    response = client.post(
        "/transactions/import-csv",
        files={"file": (filename, io.BytesIO(content), "text/csv")},
    )
    return response


# ===========================================================================
# POST /transactions — create
# ===========================================================================


class TestCreateTransaction:
    def test_create_income_transaction_returns_201(self, client):
        payload = {
            "date": "2024-03-01",
            "description": "Monthly salary",
            "amount": "50000.00",
            "transaction_type": "income",
            "category": "salary",
        }
        r = client.post("/transactions", json=payload)
        assert r.status_code == 201

    def test_create_income_transaction_response_structure(self, client):
        payload = {
            "date": "2024-03-01",
            "description": "Monthly salary",
            "amount": "50000.00",
            "transaction_type": "income",
        }
        r = client.post("/transactions", json=payload)
        data = r.json()
        assert "id" in data
        assert data["description"] == "Monthly salary"
        assert data["transaction_type"] == "income"
        assert data["amount"] == "50000.00"
        assert data["source"] == "manual"

    def test_create_expense_transaction_returns_201(self, client):
        payload = {
            "date": "2024-03-05",
            "description": "Rent payment",
            "amount": "12000.00",
            "transaction_type": "expense",
        }
        r = client.post("/transactions", json=payload)
        assert r.status_code == 201
        assert r.json()["transaction_type"] == "expense"

    def test_auto_categorization_applied_when_no_category(self, client):
        payload = {
            "date": "2024-03-01",
            "description": "Monthly salary credit",
            "amount": "30000.00",
            "transaction_type": "income",
        }
        r = client.post("/transactions", json=payload)
        assert r.status_code == 201
        assert r.json()["category"] == "salary"

    def test_supplied_category_preserved(self, client):
        payload = {
            "date": "2024-03-01",
            "description": "Monthly salary credit",
            "amount": "30000.00",
            "transaction_type": "income",
            "category": "bonus",
        }
        r = client.post("/transactions", json=payload)
        assert r.json()["category"] == "bonus"

    def test_negative_amount_rejected_422(self, client):
        payload = {
            "date": "2024-03-01",
            "description": "Bad amount",
            "amount": "-100.00",
            "transaction_type": "income",
        }
        r = client.post("/transactions", json=payload)
        assert r.status_code == 422

    def test_zero_amount_rejected_422(self, client):
        payload = {
            "date": "2024-03-01",
            "description": "Zero",
            "amount": "0",
            "transaction_type": "income",
        }
        r = client.post("/transactions", json=payload)
        assert r.status_code == 422

    def test_empty_description_rejected_422(self, client):
        payload = {
            "date": "2024-03-01",
            "description": "   ",
            "amount": "100.00",
            "transaction_type": "income",
        }
        r = client.post("/transactions", json=payload)
        assert r.status_code == 422

    def test_invalid_date_rejected_422(self, client):
        payload = {
            "date": "not-a-date",
            "description": "Test",
            "amount": "100.00",
            "transaction_type": "income",
        }
        r = client.post("/transactions", json=payload)
        assert r.status_code == 422

    def test_invalid_transaction_type_rejected_422(self, client):
        payload = {
            "date": "2024-03-01",
            "description": "Test",
            "amount": "100.00",
            "transaction_type": "refund",
        }
        r = client.post("/transactions", json=payload)
        assert r.status_code == 422

    def test_missing_required_field_returns_422(self, client):
        # Missing amount
        payload = {
            "date": "2024-03-01",
            "description": "Test",
            "transaction_type": "income",
        }
        r = client.post("/transactions", json=payload)
        assert r.status_code == 422

    def test_created_transaction_has_uuid_id(self, client):
        payload = {
            "date": "2024-03-01",
            "description": "Check UUID",
            "amount": "1.00",
            "transaction_type": "income",
        }
        r = client.post("/transactions", json=payload)
        txn_id = r.json()["id"]
        # UUID4 format: 8-4-4-4-12 hex chars
        assert len(txn_id) == 36
        assert txn_id.count("-") == 4


# ===========================================================================
# GET /transactions — list
# ===========================================================================


class TestListTransactions:
    def _create(self, client, description, amount, txn_type, txn_date, category=None):
        payload = {
            "date": txn_date,
            "description": description,
            "amount": str(amount),
            "transaction_type": txn_type,
        }
        if category:
            payload["category"] = category
        return client.post("/transactions", json=payload).json()

    def test_empty_store_returns_empty_list(self, client):
        r = client.get("/transactions")
        assert r.status_code == 200
        assert r.json() == []

    def test_lists_created_transactions(self, client):
        self._create(client, "Salary", "5000", "income", "2024-01-01")
        self._create(client, "Rent", "1200", "expense", "2024-01-05")
        r = client.get("/transactions")
        assert len(r.json()) == 2

    def test_filter_by_transaction_type_income(self, client):
        self._create(client, "Salary", "5000", "income", "2024-01-01")
        self._create(client, "Rent", "1200", "expense", "2024-01-05")
        r = client.get("/transactions?transaction_type=income")
        assert all(t["transaction_type"] == "income" for t in r.json())
        assert len(r.json()) == 1

    def test_filter_by_transaction_type_expense(self, client):
        self._create(client, "Salary", "5000", "income", "2024-01-01")
        self._create(client, "Rent", "1200", "expense", "2024-01-05")
        r = client.get("/transactions?transaction_type=expense")
        assert len(r.json()) == 1
        assert r.json()[0]["transaction_type"] == "expense"

    def test_filter_by_start_date(self, client):
        self._create(client, "Old income", "100", "income", "2023-12-01")
        self._create(client, "New income", "200", "income", "2024-06-01")
        r = client.get("/transactions?start_date=2024-01-01")
        assert all(t["date"] >= "2024-01-01" for t in r.json())
        assert len(r.json()) == 1

    def test_filter_by_end_date(self, client):
        self._create(client, "Old income", "100", "income", "2023-12-01")
        self._create(client, "New income", "200", "income", "2024-06-01")
        r = client.get("/transactions?end_date=2024-01-01")
        assert len(r.json()) == 1
        assert r.json()[0]["date"] <= "2024-01-01"

    def test_filter_by_category(self, client):
        self._create(client, "Monthly salary", "5000", "income", "2024-01-01")
        self._create(client, "Rent", "1200", "expense", "2024-01-05", category="rent")
        r = client.get("/transactions?category=salary")
        data = r.json()
        assert len(data) == 1
        assert data[0]["category"] == "salary"

    def test_invalid_date_range_returns_422(self, client):
        r = client.get("/transactions?start_date=2024-12-01&end_date=2024-01-01")
        assert r.status_code == 422


# ===========================================================================
# GET /transactions/{id}
# ===========================================================================


class TestGetTransaction:
    def test_get_existing_transaction_returns_200(self, client):
        created = client.post("/transactions", json={
            "date": "2024-03-01", "description": "Test", "amount": "100", "transaction_type": "income"
        }).json()
        r = client.get(f"/transactions/{created['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == created["id"]

    def test_get_nonexistent_transaction_returns_404(self, client):
        r = client.get("/transactions/nonexistent-id-12345")
        assert r.status_code == 404

    def test_get_returns_correct_data(self, client):
        created = client.post("/transactions", json={
            "date": "2024-05-10",
            "description": "Electric bill",
            "amount": "250.50",
            "transaction_type": "expense",
        }).json()
        r = client.get(f"/transactions/{created['id']}")
        data = r.json()
        assert data["description"] == "Electric bill"
        assert data["amount"] == "250.50"


# ===========================================================================
# DELETE /transactions/{id}
# ===========================================================================


class TestDeleteTransaction:
    def test_delete_existing_transaction_returns_200(self, client):
        created = client.post("/transactions", json={
            "date": "2024-03-01", "description": "Delete me", "amount": "10", "transaction_type": "income"
        }).json()
        r = client.delete(f"/transactions/{created['id']}")
        assert r.status_code == 200
        assert r.json()["transaction_id"] == created["id"]

    def test_deleted_transaction_no_longer_retrievable(self, client):
        created = client.post("/transactions", json={
            "date": "2024-03-01", "description": "Delete me", "amount": "10", "transaction_type": "income"
        }).json()
        client.delete(f"/transactions/{created['id']}")
        r = client.get(f"/transactions/{created['id']}")
        assert r.status_code == 404

    def test_delete_nonexistent_returns_404(self, client):
        r = client.delete("/transactions/does-not-exist")
        assert r.status_code == 404


# ===========================================================================
# GET /transactions/stored-summary
# ===========================================================================


class TestStoredSummary:
    def test_empty_store_returns_zero_summary(self, client):
        r = client.get("/transactions/stored-summary")
        assert r.status_code == 200
        data = r.json()
        assert data["total_income"] == "0.00"
        assert data["total_expenses"] == "0.00"
        assert data["net_cash_flow"] == "0.00"
        assert data["transaction_count"] == 0

    def test_summary_uses_phase1_calculator(self, client):
        client.post("/transactions", json={
            "date": "2024-01-01", "description": "Salary", "amount": "3000", "transaction_type": "income"
        })
        client.post("/transactions", json={
            "date": "2024-01-05", "description": "Rent", "amount": "1000", "transaction_type": "expense"
        })
        r = client.get("/transactions/stored-summary")
        data = r.json()
        assert data["total_income"] == "3000.00"
        assert data["total_expenses"] == "1000.00"
        assert data["net_cash_flow"] == "2000.00"
        assert data["transaction_count"] == 2

    def test_summary_filtered_by_type(self, client):
        client.post("/transactions", json={
            "date": "2024-01-01", "description": "Income A", "amount": "500", "transaction_type": "income"
        })
        client.post("/transactions", json={
            "date": "2024-01-02", "description": "Expense A", "amount": "200", "transaction_type": "expense"
        })
        r = client.get("/transactions/stored-summary?transaction_type=income")
        data = r.json()
        assert data["total_income"] == "500.00"
        assert data["total_expenses"] == "0.00"
        assert data["transaction_count"] == 1

    def test_summary_invalid_date_range_returns_422(self, client):
        r = client.get("/transactions/stored-summary?start_date=2024-12-01&end_date=2024-01-01")
        assert r.status_code == 422


# ===========================================================================
# POST /transactions/import-csv
# ===========================================================================


class TestCSVImport:
    # -----------------------------------------------------------------------
    # Valid files
    # -----------------------------------------------------------------------

    def test_valid_csv_returns_200(self, client):
        csv_data = _make_csv([
            {"date": "2024-01-01", "description": "Salary", "amount": "5000", "transaction_type": "income"},
        ])
        r = _upload_csv(client, csv_data)
        assert r.status_code == 200

    def test_valid_csv_import_report_counts(self, client):
        csv_data = _make_csv([
            {"date": "2024-01-01", "description": "Salary", "amount": "5000", "transaction_type": "income"},
            {"date": "2024-01-05", "description": "Rent", "amount": "1200", "transaction_type": "expense"},
        ])
        r = _upload_csv(client, csv_data)
        data = r.json()
        assert data["total_rows"] == 2
        assert data["imported"] == 2
        assert data["duplicates_skipped"] == 0
        assert data["rejected"] == 0

    def test_imported_transactions_are_persisted(self, client):
        csv_data = _make_csv([
            {"date": "2024-02-01", "description": "Freelance work", "amount": "8000", "transaction_type": "income"},
        ])
        _upload_csv(client, csv_data)
        r = client.get("/transactions")
        assert len(r.json()) == 1
        assert r.json()[0]["source"] == "csv_import"

    def test_csv_auto_categorizes_when_category_absent(self, client):
        csv_data = _make_csv(
            [{"date": "2024-01-01", "description": "Swiggy order dinner", "amount": "350", "transaction_type": "expense"}],
            header=["date", "description", "amount", "transaction_type"],  # no category column
        )
        r = _upload_csv(client, csv_data)
        assert r.status_code == 200
        list_r = client.get("/transactions")
        assert list_r.json()[0]["category"] == "dining"

    def test_csv_preserves_supplied_category(self, client):
        csv_data = _make_csv([
            {"date": "2024-01-01", "description": "Swiggy order", "amount": "350", "transaction_type": "expense", "category": "personal"},
        ])
        _upload_csv(client, csv_data)
        txns = client.get("/transactions").json()
        assert txns[0]["category"] == "personal"

    # -----------------------------------------------------------------------
    # Invalid file types / structure
    # -----------------------------------------------------------------------

    def test_non_csv_file_returns_415(self, client):
        r = client.post(
            "/transactions/import-csv",
            files={"file": ("data.xlsx", io.BytesIO(b"fake"), "application/vnd.ms-excel")},
        )
        assert r.status_code == 415

    def test_empty_file_returns_400(self, client):
        r = client.post(
            "/transactions/import-csv",
            files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")},
        )
        assert r.status_code == 400

    def test_missing_required_column_returns_422(self, client):
        # Missing 'amount' column
        csv_data = b"date,description,transaction_type\n2024-01-01,Test,income"
        r = _upload_csv(client, csv_data)
        assert r.status_code == 422
        assert "amount" in r.json()["detail"].lower()

    def test_header_only_csv_returns_zero_rows(self, client):
        csv_data = b"date,description,amount,transaction_type\n"
        r = _upload_csv(client, csv_data)
        assert r.status_code == 200
        assert r.json()["total_rows"] == 0
        assert r.json()["imported"] == 0

    # -----------------------------------------------------------------------
    # Row-level validation errors
    # -----------------------------------------------------------------------

    def test_invalid_date_in_row_reported(self, client):
        csv_data = _make_csv([
            {"date": "bad-date", "description": "Test", "amount": "100", "transaction_type": "income"},
        ])
        r = _upload_csv(client, csv_data)
        data = r.json()
        assert data["rejected"] == 1
        assert data["imported"] == 0
        assert data["errors"][0]["row"] == 1

    def test_negative_amount_in_row_reported(self, client):
        csv_data = _make_csv([
            {"date": "2024-01-01", "description": "Test", "amount": "-500", "transaction_type": "income"},
        ])
        r = _upload_csv(client, csv_data)
        data = r.json()
        assert data["rejected"] == 1

    def test_zero_amount_in_row_reported(self, client):
        csv_data = _make_csv([
            {"date": "2024-01-01", "description": "Test", "amount": "0", "transaction_type": "income"},
        ])
        r = _upload_csv(client, csv_data)
        assert r.json()["rejected"] == 1

    def test_invalid_transaction_type_in_row_reported(self, client):
        csv_data = _make_csv([
            {"date": "2024-01-01", "description": "Test", "amount": "100", "transaction_type": "refund"},
        ])
        r = _upload_csv(client, csv_data)
        assert r.json()["rejected"] == 1

    def test_empty_description_in_row_reported(self, client):
        csv_data = _make_csv([
            {"date": "2024-01-01", "description": "", "amount": "100", "transaction_type": "income"},
        ])
        r = _upload_csv(client, csv_data)
        assert r.json()["rejected"] == 1

    def test_row_number_reported_correctly(self, client):
        csv_data = _make_csv([
            {"date": "2024-01-01", "description": "Good row", "amount": "100", "transaction_type": "income"},
            {"date": "bad-date", "description": "Bad row", "amount": "100", "transaction_type": "income"},
        ])
        r = _upload_csv(client, csv_data)
        data = r.json()
        assert data["imported"] == 1
        assert data["rejected"] == 1
        assert data["errors"][0]["row"] == 2  # second data row

    def test_partial_import_valid_rows_imported_despite_errors(self, client):
        csv_data = _make_csv([
            {"date": "2024-01-01", "description": "Valid row", "amount": "500", "transaction_type": "income"},
            {"date": "not-a-date", "description": "Invalid", "amount": "100", "transaction_type": "income"},
            {"date": "2024-01-03", "description": "Also valid", "amount": "300", "transaction_type": "expense"},
        ])
        r = _upload_csv(client, csv_data)
        data = r.json()
        assert data["imported"] == 2
        assert data["rejected"] == 1
        assert len(client.get("/transactions").json()) == 2

    # -----------------------------------------------------------------------
    # Duplicate detection
    # -----------------------------------------------------------------------

    def test_duplicate_within_same_batch_skipped(self, client):
        csv_data = _make_csv([
            {"date": "2024-01-01", "description": "Salary", "amount": "5000", "transaction_type": "income"},
            {"date": "2024-01-01", "description": "Salary", "amount": "5000", "transaction_type": "income"},
        ])
        r = _upload_csv(client, csv_data)
        data = r.json()
        assert data["imported"] == 1
        assert data["duplicates_skipped"] == 1

    def test_duplicate_against_existing_record_skipped(self, client):
        # Create a transaction manually first
        client.post("/transactions", json={
            "date": "2024-01-01",
            "description": "Salary",
            "amount": "5000",
            "transaction_type": "income",
        })
        # Now import the same record via CSV
        csv_data = _make_csv([
            {"date": "2024-01-01", "description": "Salary", "amount": "5000.00", "transaction_type": "income"},
        ])
        r = _upload_csv(client, csv_data)
        data = r.json()
        assert data["duplicates_skipped"] == 1
        assert data["imported"] == 0

    def test_failed_import_does_not_corrupt_existing_data(self, client):
        """A completely invalid CSV must not affect already-stored transactions."""
        client.post("/transactions", json={
            "date": "2024-01-01", "description": "Existing", "amount": "1000", "transaction_type": "income"
        })
        # Upload a CSV with no valid rows
        csv_data = _make_csv([
            {"date": "bad-date", "description": "Bad", "amount": "-50", "transaction_type": "income"},
        ])
        _upload_csv(client, csv_data)
        txns = client.get("/transactions").json()
        assert len(txns) == 1
        assert txns[0]["description"] == "Existing"


# ===========================================================================
# Categorization unit tests
# ===========================================================================


class TestCategorization:
    def test_salary_keywords(self):
        from app.categorization import categorize
        assert categorize("Monthly salary credit") == "salary"
        assert categorize("Payroll disbursement") == "salary"
        assert categorize("Wages received") == "salary"

    def test_rent_keywords(self):
        from app.categorization import categorize
        assert categorize("Rent payment to landlord") == "rent"
        assert categorize("House rent for December") == "rent"

    def test_groceries_keywords(self):
        from app.categorization import categorize
        assert categorize("DMart grocery shopping") == "groceries"
        assert categorize("Reliance Fresh vegetables") == "groceries"

    def test_utilities_keywords(self):
        from app.categorization import categorize
        assert categorize("Electricity bill payment") == "utilities"
        assert categorize("Water bill") == "utilities"
        assert categorize("Internet bill broadband") == "utilities"

    def test_transport_keywords(self):
        from app.categorization import categorize
        assert categorize("Uber ride to office") == "transport"
        assert categorize("Petrol fill-up") == "transport"

    def test_dining_keywords(self):
        from app.categorization import categorize
        assert categorize("Swiggy food delivery order") == "dining"
        assert categorize("Zomato lunch") == "dining"

    def test_entertainment_keywords(self):
        from app.categorization import categorize
        assert categorize("Netflix subscription") == "entertainment"
        assert categorize("Movie ticket booking") == "entertainment"

    def test_unknown_description_returns_uncategorized(self):
        from app.categorization import categorize
        assert categorize("XYZ random payment 12345") == "uncategorized"

    def test_user_supplied_category_preserved(self):
        from app.categorization import categorize
        assert categorize("Monthly salary credit", "bonus") == "bonus"

    def test_uncategorized_supplied_triggers_auto_categorize(self):
        from app.categorization import categorize
        assert categorize("Monthly salary credit", "uncategorized") == "salary"

    def test_case_insensitive_matching(self):
        from app.categorization import categorize
        assert categorize("MONTHLY SALARY CREDIT") == "salary"
        assert categorize("Electricity Bill") == "utilities"


# ===========================================================================
# Phase 1 regression tests
# ===========================================================================


class TestPhase1Regression:
    """Ensure Phase 1 behaviour is completely preserved."""

    def test_health_endpoint_still_works(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_stateless_summary_still_works(self, client):
        payload = {
            "transactions": [
                {"date": "2024-01-01", "description": "Salary", "amount": "3000", "transaction_type": "income"},
                {"date": "2024-01-05", "description": "Rent", "amount": "1000", "transaction_type": "expense"},
            ]
        }
        r = client.post("/transactions/summary", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data["total_income"] == "3000.00"
        assert data["total_expenses"] == "1000.00"
        assert data["net_cash_flow"] == "2000.00"
        assert data["transaction_count"] == 2

    def test_stateless_summary_empty_list(self, client):
        r = client.post("/transactions/summary", json={"transactions": []})
        assert r.status_code == 200
        assert r.json()["transaction_count"] == 0
