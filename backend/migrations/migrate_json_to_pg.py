"""
Data migration script: JSON file storage -> PostgreSQL database.

Reads existing JSON data (transactions and financial profile), validates all records,
imports them into the database, reports detailed statistics, and safely handles idempotency.
Preserves original files without modifying or deleting them.

Usage:
    # Dry run (preview without writing to DB):
    python migrations/migrate_json_to_pg.py --dry-run

    # Execute migration:
    python migrations/migrate_json_to_pg.py
"""

import argparse
import json
import sys
from datetime import date as ISODate
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.db.base import Base
from app.db.models import FinancialProfileModel, TransactionModel
from app.db.session import create_db_engine, get_database_url, mask_database_url
from app.schemas import TransactionSource, TransactionType
from sqlalchemy.orm import Session, sessionmaker


def migrate_data(
    data_dir: Path,
    db_url: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Execute validation and migration of JSON records into the database.

    Args:
        data_dir: Path to directory containing transactions.json and financial_profile.json.
        db_url: Target database URL.
        dry_run: If True, validate and report without writing to the database.

    Returns:
        Summary dict containing counts of processed, imported, skipped, and rejected records.
    """
    target_url = db_url or get_database_url()
    masked_url = mask_database_url(target_url)

    report: Dict[str, Any] = {
        "target_database": masked_url,
        "dry_run": dry_run,
        "transactions": {
            "total_found": 0,
            "imported": 0,
            "skipped_existing": 0,
            "rejected": 0,
            "errors": [],
        },
        "financial_profile": {
            "found": False,
            "imported": False,
            "skipped_or_updated": False,
            "rejected": False,
            "error": None,
        },
    }

    # Connect to DB engine and ensure tables exist
    engine = create_db_engine(target_url)
    if not dry_run:
        Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session: Session = SessionLocal()

    try:
        # -------------------------------------------------------------
        # 1. Migrate Transactions
        # -------------------------------------------------------------
        tx_file = data_dir / "transactions.json"
        if tx_file.exists():
            try:
                raw_tx_text = tx_file.read_text(encoding="utf-8").strip()
                raw_tx_list = json.loads(raw_tx_text) if raw_tx_text else []
            except Exception as e:
                report["transactions"]["errors"].append(f"Failed to read/parse {tx_file}: {e}")
                raw_tx_list = []

            report["transactions"]["total_found"] = len(raw_tx_list)

            # Query existing transaction IDs in DB to prevent duplicates on rerun
            existing_ids = set()
            if not dry_run:
                try:
                    existing_ids = set(session.query(TransactionModel.id).all())
                    existing_ids = {item[0] for item in existing_ids}
                except Exception:
                    existing_ids = set()

            to_add: List[TransactionModel] = []
            for idx, item in enumerate(raw_tx_list, start=1):
                is_valid, validated_or_err = validate_transaction_record(item, idx)
                if not is_valid:
                    report["transactions"]["rejected"] += 1
                    report["transactions"]["errors"].append(validated_or_err)
                    continue

                tx_data = validated_or_err  # type: ignore
                tx_id = tx_data["id"]

                if tx_id in existing_ids:
                    report["transactions"]["skipped_existing"] += 1
                    continue

                existing_ids.add(tx_id)
                model = TransactionModel(
                    id=tx_id,
                    date=tx_data["date"],
                    description=tx_data["description"],
                    amount=tx_data["amount"],
                    transaction_type=tx_data["transaction_type"],
                    category=tx_data["category"],
                    source=tx_data["source"],
                )
                to_add.append(model)
                report["transactions"]["imported"] += 1

            if not dry_run and to_add:
                session.add_all(to_add)
                session.commit()

        # -------------------------------------------------------------
        # 2. Migrate Financial Profile
        # -------------------------------------------------------------
        profile_file = data_dir / "financial_profile.json"
        if profile_file.exists():
            report["financial_profile"]["found"] = True
            try:
                raw_prof_text = profile_file.read_text(encoding="utf-8").strip()
                prof_data = json.loads(raw_prof_text) if raw_prof_text else {}
            except Exception as e:
                report["financial_profile"]["rejected"] = True
                report["financial_profile"]["error"] = f"Failed to parse {profile_file}: {e}"
                prof_data = {}

            ef_config = prof_data.get("emergency_fund")
            if ef_config:
                is_valid, prof_or_err = validate_profile_record(ef_config)
                if not is_valid:
                    report["financial_profile"]["rejected"] = True
                    report["financial_profile"]["error"] = prof_or_err
                elif not dry_run:
                    valid_prof = prof_or_err  # type: ignore
                    existing_prof = (
                        session.query(FinancialProfileModel)
                        .filter(FinancialProfileModel.profile_key == "default")
                        .first()
                    )
                    if existing_prof:
                        existing_prof.emergency_fund_balance = valid_prof["emergency_fund_balance"]
                        existing_prof.essential_categories = valid_prof["essential_categories"]
                        existing_prof.analysis_window_months = valid_prof["analysis_window_months"]
                        report["financial_profile"]["skipped_or_updated"] = True
                    else:
                        new_prof = FinancialProfileModel(
                            profile_key="default",
                            emergency_fund_balance=valid_prof["emergency_fund_balance"],
                            essential_categories=valid_prof["essential_categories"],
                            analysis_window_months=valid_prof["analysis_window_months"],
                            currency="INR",
                        )
                        session.add(new_prof)
                        report["financial_profile"]["imported"] = True
                    session.commit()
                else:
                    report["financial_profile"]["imported"] = True

    except Exception as exc:
        session.rollback()
        raise exc
    finally:
        session.close()

    return report


def validate_transaction_record(
    item: Dict[str, Any], idx: int
) -> Tuple[bool, Any]:
    """Validate a single transaction item from JSON."""
    if not isinstance(item, dict):
        return False, f"Record #{idx}: Expected dict, got {type(item).__name__}"

    tx_id = str(item.get("id", "")).strip()
    if not tx_id:
        return False, f"Record #{idx}: Missing transaction ID"

    date_str = str(item.get("date", "")).strip()
    try:
        tx_date = ISODate.fromisoformat(date_str)
    except Exception:
        return False, f"Record #{idx} ({tx_id}): Invalid date format {date_str!r}"

    desc = str(item.get("description", "")).strip()
    if not desc:
        return False, f"Record #{idx} ({tx_id}): Description cannot be empty"

    amt_str = str(item.get("amount", "")).strip()
    try:
        amount = Decimal(amt_str)
        if amount <= Decimal("0"):
            return False, f"Record #{idx} ({tx_id}): Amount must be > 0, got {amount}"
    except (InvalidOperation, ValueError):
        return False, f"Record #{idx} ({tx_id}): Invalid amount value {amt_str!r}"

    tx_type_str = str(item.get("transaction_type", "")).strip().lower()
    if tx_type_str not in ("income", "expense"):
        return False, f"Record #{idx} ({tx_id}): Invalid transaction_type {tx_type_str!r}"

    category = str(item.get("category", "")).strip() or "uncategorized"
    source = str(item.get("source", "")).strip() or "manual"
    if source not in ("manual", "csv_import"):
        source = "manual"

    return True, {
        "id": tx_id,
        "date": tx_date,
        "description": desc,
        "amount": amount,
        "transaction_type": tx_type_str,
        "category": category,
        "source": source,
    }


def validate_profile_record(item: Dict[str, Any]) -> Tuple[bool, Any]:
    """Validate financial profile emergency fund configuration."""
    raw_balance = item.get("emergency_fund_balance")
    balance = None
    if raw_balance is not None:
        try:
            balance = Decimal(str(raw_balance))
            if balance < Decimal("0"):
                return False, f"Emergency fund balance cannot be negative: {balance}"
        except (InvalidOperation, ValueError):
            return False, f"Invalid emergency fund balance format: {raw_balance}"

    cats = item.get("essential_categories")
    if not isinstance(cats, list) or not cats:
        cats = ["rent", "groceries", "utilities", "healthcare", "transport"]

    window = item.get("analysis_window_months", 12)
    try:
        window = int(window)
        if not (1 <= window <= 60):
            return False, f"analysis_window_months must be between 1 and 60, got {window}"
    except ValueError:
        return False, f"Invalid analysis_window_months: {window}"

    return True, {
        "emergency_fund_balance": balance,
        "essential_categories": cats,
        "analysis_window_months": window,
    }


def main():
    parser = argparse.ArgumentParser(description="Migrate JSON data to PostgreSQL/database.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=backend_dir / "data",
        help="Path to data directory containing JSON files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migration without modifying the database",
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="Database URL (defaults to DATABASE_URL environment variable)",
    )

    args = parser.parse_args()

    print("=================================================================")
    print("  AI Financial Decision Support System — JSON Data Migration")
    print("=================================================================")
    print(f"Data directory:   {args.data_dir}")
    print(f"Dry run:          {args.dry_run}")

    report = migrate_data(args.data_dir, db_url=args.db_url, dry_run=args.dry_run)

    print(f"Target Database:  {report['target_database']}")
    print("\n--- Transactions ---")
    tx_rep = report["transactions"]
    print(f"Total found:      {tx_rep['total_found']}")
    print(f"Imported:         {tx_rep['imported']}")
    print(f"Skipped existing: {tx_rep['skipped_existing']}")
    print(f"Rejected:         {tx_rep['rejected']}")
    if tx_rep["errors"]:
        print("\nErrors/Rejections:")
        for err in tx_rep["errors"]:
            print(f"  - {err}")

    print("\n--- Financial Profile ---")
    prof_rep = report["financial_profile"]
    print(f"Found:            {prof_rep['found']}")
    print(f"Imported:         {prof_rep['imported']}")
    print(f"Updated/Skipped:  {prof_rep['skipped_or_updated']}")
    print(f"Rejected:         {prof_rep['rejected']}")
    if prof_rep["error"]:
        print(f"Error:            {prof_rep['error']}")

    print("\nMigration completed successfully.")


if __name__ == "__main__":
    main()
