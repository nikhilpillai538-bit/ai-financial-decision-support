"""
JSON-file repository for transaction persistence.

Keeps all I/O behind a single ``TransactionRepository`` class so that
Phase 3 can swap it for a PostgreSQL implementation without touching any
business-logic or router code.

Storage format
--------------
A single JSON file (``data/transactions.json`` by default) holds a list
of transaction objects.  Decimal amounts are stored as strings to avoid
precision loss when serialising to JSON.

Thread safety
-------------
The repository uses a module-level ``threading.Lock`` to serialise
concurrent writes within a single process.  It is *not* safe across
multiple worker processes; that concern belongs to Phase 3.
"""

import json
import threading
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from app.schemas import StoredTransaction

# ---------------------------------------------------------------------------
# Default storage path (relative to the working directory where uvicorn runs)
# ---------------------------------------------------------------------------

_DEFAULT_DATA_DIR = Path("data")
_DEFAULT_FILE = _DEFAULT_DATA_DIR / "transactions.json"

_lock = threading.Lock()


class TransactionRepository:
    """Read/write stored transactions from/to a local JSON file.

    Args:
        filepath: Path to the JSON file used as the backing store.  The
            directory is created automatically on first write if it does
            not exist.

    Example::

        repo = TransactionRepository()
        repo.save(transaction)
        all_txns = repo.all()
    """

    def __init__(self, filepath: Path = _DEFAULT_FILE) -> None:
        self._filepath = filepath

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def all(self, user_id: Optional[str] = None) -> List[StoredTransaction]:
        """Return all stored transactions, newest-first by date then ID."""
        raw = self._load_raw()
        if user_id is not None:
            raw = [item for item in raw if item.get("user_id") in (user_id, None)]
        transactions = [StoredTransaction(**{k: v for k, v in item.items() if k != "user_id"}) for item in raw]
        return sorted(transactions, key=lambda t: (t.date, t.id), reverse=True)

    def get(self, transaction_id: str, user_id: Optional[str] = None) -> Optional[StoredTransaction]:
        """Return the transaction with the given ID, or ``None``."""
        for item in self._load_raw():
            if item.get("id") == transaction_id:
                if user_id is not None and item.get("user_id") not in (user_id, None):
                    return None
                clean_item = {k: v for k, v in item.items() if k != "user_id"}
                return StoredTransaction(**clean_item)
        return None

    def save(self, transaction: StoredTransaction, user_id: Optional[str] = None) -> StoredTransaction:
        """Append a new transaction and persist to disk.

        Raises:
            ValueError: If a transaction with the same ID already exists.
        """
        with _lock:
            raw = self._load_raw()
            if any(item.get("id") == transaction.id for item in raw):
                raise ValueError(f"Transaction ID {transaction.id!r} already exists.")
            d = self._to_dict(transaction)
            if user_id is not None:
                d["user_id"] = user_id
            raw.append(d)
            self._write_raw(raw)
        return transaction

    def save_many(self, transactions: List[StoredTransaction], user_id: Optional[str] = None) -> None:
        """Append multiple transactions atomically.

        All-or-nothing within the list: if a duplicate ID is detected among
        the new records themselves, nothing is written.
        """
        with _lock:
            raw = self._load_raw()
            existing_ids = {item.get("id") for item in raw}
            new_ids: set = set()
            for txn in transactions:
                if txn.id in existing_ids or txn.id in new_ids:
                    raise ValueError(
                        f"Duplicate transaction ID {txn.id!r} detected during batch save."
                    )
                new_ids.add(txn.id)
            for txn in transactions:
                d = self._to_dict(txn)
                if user_id is not None:
                    d["user_id"] = user_id
                raw.append(d)
            self._write_raw(raw)

    def delete(self, transaction_id: str, user_id: Optional[str] = None) -> bool:
        """Delete the transaction with the given ID.

        Returns:
            ``True`` if the transaction was found and deleted, ``False`` otherwise.
        """
        with _lock:
            raw = self._load_raw()
            target = next((item for item in raw if item.get("id") == transaction_id), None)
            if not target:
                return False
            if user_id is not None and target.get("user_id") not in (user_id, None):
                return False
            new_raw = [item for item in raw if item.get("id") != transaction_id]
            self._write_raw(new_raw)
        return True

    def clear(self) -> None:
        """Remove all stored transactions.  Used in testing only."""
        with _lock:
            self._write_raw([])

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_raw(self) -> List[dict]:
        """Return the raw list of transaction dicts from disk."""
        if not self._filepath.exists():
            return []
        try:
            text = self._filepath.read_text(encoding="utf-8").strip()
            if not text:
                return []
            return json.loads(text)
        except json.JSONDecodeError:
            # Damaged file — return empty rather than crashing the service.
            return []

    def _write_raw(self, data: List[dict]) -> None:
        """Write data to the JSON file, creating the directory if needed."""
        self._filepath.parent.mkdir(parents=True, exist_ok=True)
        self._filepath.write_text(
            json.dumps(data, indent=2, default=str),
            encoding="utf-8",
        )

    @staticmethod
    def _to_dict(transaction: StoredTransaction) -> dict:
        """Serialise a ``StoredTransaction`` to a JSON-safe dict."""
        return {
            "id": transaction.id,
            "date": transaction.date.isoformat(),
            "description": transaction.description,
            "amount": str(transaction.amount),
            "transaction_type": transaction.transaction_type.value,
            "category": transaction.category,
            "source": transaction.source,
        }


# ---------------------------------------------------------------------------
# Module-level default instance — routers import this directly.
# Override in tests via dependency injection or by constructing a new instance
# pointing at a temporary file.
# ---------------------------------------------------------------------------

default_repository = TransactionRepository()


# ---------------------------------------------------------------------------
# Phase 3 — Financial Profile Repository
# ---------------------------------------------------------------------------

_DEFAULT_PROFILE_FILE = _DEFAULT_DATA_DIR / "financial_profile.json"


class ProfileRepository:
    """Read/write user financial-profile settings from a local JSON file.

    Currently stores:
    - ``emergency_fund``: the emergency-fund configuration set via
      ``PUT /financial-profile/emergency-fund``.

    The file is created automatically on first write.  If it is absent or
    damaged the repository returns safe defaults rather than raising errors.

    Args:
        filepath: Path to the profile JSON file.
    """

    def __init__(self, filepath: Path = _DEFAULT_PROFILE_FILE) -> None:
        self._filepath = filepath

    # ------------------------------------------------------------------
    # Emergency-fund config
    # ------------------------------------------------------------------

    def get_emergency_fund_config(
        self, user_id: Optional[str] = None, profile_key: str = "default"
    ) -> Optional[dict]:
        """Return the stored emergency-fund configuration, or ``None``."""
        data = self._load()
        if user_id is not None:
            return data.get(f"user_{user_id}", data.get("emergency_fund"))
        return data.get(profile_key, data.get("emergency_fund"))

    def save_emergency_fund_config(
        self,
        config: dict,
        user_id: Optional[str] = None,
        profile_key: Optional[str] = None,
    ) -> None:
        """Persist an emergency-fund configuration dict.

        ``config`` must already have Decimal values serialised to strings
        by the caller before this method is invoked.
        """
        with _lock:
            data = self._load()
            key = f"user_{user_id}" if user_id is not None else (profile_key or "emergency_fund")
            data[key] = config
            data["emergency_fund"] = config
            self._write(data)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load(self) -> dict:
        if not self._filepath.exists():
            return {}
        try:
            text = self._filepath.read_text(encoding="utf-8").strip()
            return json.loads(text) if text else {}
        except (json.JSONDecodeError, OSError):
            return {}

    def _write(self, data: dict) -> None:
        self._filepath.parent.mkdir(parents=True, exist_ok=True)
        self._filepath.write_text(
            json.dumps(data, indent=2, default=str),
            encoding="utf-8",
        )


default_profile_repository = ProfileRepository()
