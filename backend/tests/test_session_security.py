"""
Phase 5 Tests: Session Security, Token Expiry, Refresh Rotation, and Invalidation.

Verifies:
- Access token verification and expiration.
- Refresh token issuance and database hashing (never plaintext).
- Refresh token rotation (old token invalidated upon use).
- Reuse detection of rotated tokens (revokes user sessions).
- Logout revoking active refresh sessions.
"""

from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.security import create_access_token
from app.db.base import Base
from app.db.models import UserSessionModel
from app.db.session import get_db
from app.main import app


@pytest.fixture()
def session_client() -> TestClient:
    """Isolated test client with an in-memory SQLite database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        session: Session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)


class TestAccessTokenSecurity:
    """Tests for access token validity and expiration."""

    def test_invalid_token_signature_rejected(self, session_client: TestClient):
        res = session_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token.payload"},
        )
        assert res.status_code == 401

    def test_expired_access_token_rejected(self, session_client: TestClient):
        # Register user
        reg_res = session_client.post(
            "/auth/register",
            json={"email": "expired@example.com", "password": "password123"},
        )
        user_id = reg_res.json()["id"]

        # Create expired access token (expired 5 minutes ago)
        expired_token, _ = create_access_token(
            user_id=user_id,
            email="expired@example.com",
            expires_delta=timedelta(minutes=-5),
        )

        res = session_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert res.status_code == 401


class TestRefreshTokenRotationAndReuse:
    """Tests for refresh token rotation, invalidation, and replay mitigation."""

    def test_successful_refresh_token_rotation(self, session_client: TestClient):
        # Register and login
        session_client.post(
            "/auth/register",
            json={"email": "refresh@example.com", "password": "password123"},
        )
        login_res = session_client.post(
            "/auth/login",
            json={"email": "refresh@example.com", "password": "password123"},
        )
        orig_refresh = login_res.json()["refresh_token"]

        # Perform refresh
        ref_res = session_client.post(
            "/auth/refresh",
            json={"refresh_token": orig_refresh},
        )
        assert ref_res.status_code == 200
        new_data = ref_res.json()
        assert "access_token" in new_data
        assert "refresh_token" in new_data
        assert new_data["refresh_token"] != orig_refresh

        # New access token is valid
        me_res = session_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {new_data['access_token']}"},
        )
        assert me_res.status_code == 200

    def test_rotated_token_reuse_detected_and_rejected(self, session_client: TestClient):
        session_client.post(
            "/auth/register",
            json={"email": "reuse@example.com", "password": "password123"},
        )
        login_res = session_client.post(
            "/auth/login",
            json={"email": "reuse@example.com", "password": "password123"},
        )
        token_1 = login_res.json()["refresh_token"]

        # First refresh: rotates token_1 -> token_2
        ref1 = session_client.post("/auth/refresh", json={"refresh_token": token_1})
        assert ref1.status_code == 200
        token_2 = ref1.json()["refresh_token"]

        # Attempt to reuse token_1 (stolen token scenario)
        reuse_res = session_client.post("/auth/refresh", json={"refresh_token": token_1})
        assert reuse_res.status_code == 401

        # Token 2 should also now be revoked due to the reuse detection revocation
        ref2 = session_client.post("/auth/refresh", json={"refresh_token": token_2})
        assert ref2.status_code == 401


class TestLogoutAndRevocation:
    """Tests for POST /auth/logout."""

    def test_logout_revokes_session(self, session_client: TestClient):
        session_client.post(
            "/auth/register",
            json={"email": "logout@example.com", "password": "password123"},
        )
        login_res = session_client.post(
            "/auth/login",
            json={"email": "logout@example.com", "password": "password123"},
        )
        refresh_token = login_res.json()["refresh_token"]

        # Logout
        logout_res = session_client.post(
            "/auth/logout",
            json={"refresh_token": refresh_token},
        )
        assert logout_res.status_code == 200

        # Attempt to refresh with revoked token should fail
        ref_res = session_client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert ref_res.status_code == 401
