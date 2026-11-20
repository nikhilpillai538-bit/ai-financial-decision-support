"""
SQLAlchemy-backed User and Session Repository.

Handles user creation, lookup, and session/refresh-token lifecycle management
including rotation, reuse detection, and revocation.
"""

from datetime import datetime, timezone
import uuid
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db.models import UserModel, UserSessionModel


class SQLUserRepository:
    """Repository for user accounts and refresh token sessions."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # User Operations
    # ------------------------------------------------------------------

    def get_by_id(self, user_id: str) -> Optional[UserModel]:
        """Fetch user by primary key ID."""
        stmt = select(UserModel).where(UserModel.id == user_id)
        return self.session.scalars(stmt).first()

    def get_by_email(self, email: str) -> Optional[UserModel]:
        """Fetch user by normalized email address."""
        norm_email = email.strip().lower()
        stmt = select(UserModel).where(UserModel.email == norm_email)
        return self.session.scalars(stmt).first()

    def create_user(self, email: str, password_hash: str) -> UserModel:
        """Create and persist a new user."""
        norm_email = email.strip().lower()
        user = UserModel(
            id=str(uuid.uuid4()),
            email=norm_email,
            password_hash=password_hash,
            is_active=True,
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    # ------------------------------------------------------------------
    # Session / Refresh Token Operations
    # ------------------------------------------------------------------

    def create_session(
        self,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> UserSessionModel:
        """Create and persist a new refresh token session."""
        session_record = UserSessionModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self.session.add(session_record)
        self.session.commit()
        self.session.refresh(session_record)
        return session_record

    def get_session_by_token_hash(self, token_hash: str) -> Optional[UserSessionModel]:
        """Find a session by the SHA-256 hash of its refresh token."""
        stmt = select(UserSessionModel).where(UserSessionModel.token_hash == token_hash)
        return self.session.scalars(stmt).first()

    def rotate_session(
        self,
        old_session: UserSessionModel,
        new_token_hash: str,
        new_expires_at: datetime,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> UserSessionModel:
        """Revoke the old session and create a new one linked via replaced_by_hash.

        This enables detection of stolen/replayed refresh tokens.
        """
        now = datetime.now(timezone.utc)
        old_session.revoked_at = now
        old_session.replaced_by_hash = new_token_hash

        new_session = UserSessionModel(
            id=str(uuid.uuid4()),
            user_id=old_session.user_id,
            token_hash=new_token_hash,
            expires_at=new_expires_at,
            user_agent=user_agent or old_session.user_agent,
            ip_address=ip_address or old_session.ip_address,
        )
        self.session.add(new_session)
        self.session.commit()
        self.session.refresh(new_session)
        return new_session

    def revoke_session(self, session_record: UserSessionModel) -> None:
        """Revoke a single session."""
        if not session_record.revoked_at:
            session_record.revoked_at = datetime.now(timezone.utc)
            self.session.commit()

    def revoke_all_user_sessions(self, user_id: str) -> None:
        """Revoke all active sessions for a user (security measure upon token reuse)."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(UserSessionModel)
            .where(UserSessionModel.user_id == user_id, UserSessionModel.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        self.session.execute(stmt)
        self.session.commit()
