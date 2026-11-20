"""
SQLAlchemy-backed Transaction Repository with Multi-User Isolation.

Provides persistent database operations for StoredTransaction records with exact
Decimal handling, connection safety, ACID transaction guarantees, and user scoping.
"""

from datetime import date as ISODate
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import delete, desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import TransactionModel
from app.schemas import StoredTransaction, TransactionSource, TransactionType


class SQLTransactionRepository:
    """Database-backed repository for financial transactions with user isolation.

    Args:
        session: Active SQLAlchemy database session.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def all(self, user_id: Optional[str] = None) -> List[StoredTransaction]:
        """Return all stored transactions, newest-first by date then ID.

        If user_id is provided, returns only transactions belonging to that user.
        """
        stmt = select(TransactionModel)
        if user_id is not None:
            stmt = stmt.where(TransactionModel.user_id == user_id)
        stmt = stmt.order_by(desc(TransactionModel.date), desc(TransactionModel.id))
        models = self.session.scalars(stmt).all()
        return [self._to_schema(m) for m in models]

    def get(self, transaction_id: str, user_id: Optional[str] = None) -> Optional[StoredTransaction]:
        """Return the transaction with the given ID and user_id, or None."""
        stmt = select(TransactionModel).where(TransactionModel.id == transaction_id)
        if user_id is not None:
            stmt = stmt.where(TransactionModel.user_id == user_id)
        model = self.session.scalars(stmt).first()
        return self._to_schema(model) if model else None

    def save(self, transaction: StoredTransaction, user_id: Optional[str] = None) -> StoredTransaction:
        """Persist a new transaction scoped to user_id.

        Raises:
            ValueError: If a transaction with the same ID already exists.
        """
        # Check existing ID globally
        stmt = select(TransactionModel).where(TransactionModel.id == transaction.id)
        if self.session.scalars(stmt).first() is not None:
            raise ValueError(f"Transaction ID {transaction.id!r} already exists.")

        model = self._to_model(transaction, user_id=user_id)
        try:
            self.session.add(model)
            self.session.commit()
            self.session.refresh(model)
            return self._to_schema(model)
        except IntegrityError as exc:
            self.session.rollback()
            raise ValueError(f"Failed to persist transaction {transaction.id!r}: integrity error.") from exc
        except Exception:
            self.session.rollback()
            raise

    def save_many(self, transactions: List[StoredTransaction], user_id: Optional[str] = None) -> None:
        """Persist multiple transactions atomically, scoped to user_id.

        All-or-nothing: if an ID is duplicated or an error occurs, the entire
        batch is rolled back.

        Raises:
            ValueError: If duplicate IDs are detected.
        """
        if not transactions:
            return

        new_ids = set()
        for txn in transactions:
            if txn.id in new_ids:
                raise ValueError(f"Duplicate transaction ID {txn.id!r} detected during batch save.")
            new_ids.add(txn.id)

        stmt = select(TransactionModel.id).where(TransactionModel.id.in_(list(new_ids)))
        existing = set(self.session.scalars(stmt).all())
        if existing:
            duplicate = next(iter(existing))
            raise ValueError(f"Duplicate transaction ID {duplicate!r} detected during batch save.")

        models = [self._to_model(t, user_id=user_id) for t in transactions]
        try:
            self.session.add_all(models)
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ValueError("Failed to persist transaction batch due to integrity constraint.") from exc
        except Exception:
            self.session.rollback()
            raise

    def delete(self, transaction_id: str, user_id: Optional[str] = None) -> bool:
        """Delete the transaction matching transaction_id and user_id.

        Returns:
            True if the transaction was found and deleted, False otherwise.
        """
        stmt = select(TransactionModel).where(TransactionModel.id == transaction_id)
        if user_id is not None:
            stmt = stmt.where(TransactionModel.user_id == user_id)
        model = self.session.scalars(stmt).first()
        if not model:
            return False

        try:
            self.session.delete(model)
            self.session.commit()
            return True
        except Exception:
            self.session.rollback()
            raise

    def filter(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[ISODate] = None,
        end_date: Optional[ISODate] = None,
        transaction_type: Optional[TransactionType] = None,
        category: Optional[str] = None,
    ) -> List[StoredTransaction]:
        """Query and filter stored transactions efficiently via SQL with user scoping."""
        stmt = select(TransactionModel)

        if user_id is not None:
            stmt = stmt.where(TransactionModel.user_id == user_id)
        if start_date:
            stmt = stmt.where(TransactionModel.date >= start_date)
        if end_date:
            stmt = stmt.where(TransactionModel.date <= end_date)
        if transaction_type:
            stmt = stmt.where(TransactionModel.transaction_type == transaction_type.value)
        if category:
            stmt = stmt.where(TransactionModel.category.ilike(category))

        stmt = stmt.order_by(desc(TransactionModel.date), desc(TransactionModel.id))
        models = self.session.scalars(stmt).all()
        return [self._to_schema(m) for m in models]

    def clear(self, user_id: Optional[str] = None) -> None:
        """Remove transactions. If user_id provided, removes only that user's transactions."""
        try:
            stmt = delete(TransactionModel)
            if user_id is not None:
                stmt = stmt.where(TransactionModel.user_id == user_id)
            self.session.execute(stmt)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_schema(model: TransactionModel) -> StoredTransaction:
        """Convert a SQLAlchemy TransactionModel to a Pydantic StoredTransaction."""
        return StoredTransaction(
            id=model.id,
            date=model.date,
            description=model.description,
            amount=Decimal(str(model.amount)),
            transaction_type=TransactionType(model.transaction_type),
            category=model.category,
            source=TransactionSource(model.source),
        )

    @staticmethod
    def _to_model(schema: StoredTransaction, user_id: Optional[str] = None) -> TransactionModel:
        """Convert a Pydantic StoredTransaction to a SQLAlchemy TransactionModel."""
        return TransactionModel(
            id=schema.id,
            user_id=user_id,
            date=schema.date,
            description=schema.description,
            amount=Decimal(str(schema.amount)),
            transaction_type=schema.transaction_type.value,
            category=schema.category,
            source=schema.source.value,
        )
