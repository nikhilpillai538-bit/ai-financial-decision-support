"""
Phase 5 Tests: Account Management, Registration, Login, and Credential Security.

Verifies:
- Successful registration with email normalization.
- Rejection of duplicate email registrations.
- Validation of email format and password strength.
- Argon2id password hashing (no plaintext or hashes in responses).
- Generic login error messages (no email existence leakage).
- Brute-force rate limiting on failed login attempts.
- Protected /auth/me endpoint behavior.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.security import hash_password, login_limiter, verify_password
from app.db.base import Base
from app.db.models import UserModel
from app.db.session import get_db
from app.main import app


@pytest.fixture()
def auth_client() -> TestClient:
    """Isolated test client with a clean in-memory database and fresh rate limiter."""
    login_limiter.reset()
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
    login_limiter.reset()


class TestUserRegistration:
    """Tests for POST /auth/register."""

    def test_successful_registration(self, auth_client: TestClient):
        res = auth_client.post(
            "/auth/register",
            json={"email": "NewUser@Example.COM", "password": "securepassword123"},
        )
        assert res.status_code == 201
        data = res.json()
        assert "id" in data
        assert data["email"] == "newuser@example.com"  # Normalized to lowercase
        assert data["is_active"] is True
        assert "password" not in data
        assert "password_hash" not in data

    def test_duplicate_registration_rejected(self, auth_client: TestClient):
        payload = {"email": "duplicate@example.com", "password": "password123"}
        res1 = auth_client.post("/auth/register", json=payload)
        assert res1.status_code == 201

        res2 = auth_client.post("/auth/register", json=payload)
        assert res2.status_code == 409
        assert "already exists" in res2.json()["detail"]

    def test_invalid_email_format_rejected(self, auth_client: TestClient):
        res = auth_client.post(
            "/auth/register",
            json={"email": "not-an-email", "password": "password123"},
        )
        assert res.status_code == 422

    def test_short_password_rejected(self, auth_client: TestClient):
        res = auth_client.post(
            "/auth/register",
            json={"email": "valid@example.com", "password": "short"},
        )
        assert res.status_code == 422

    def test_whitespace_password_rejected(self, auth_client: TestClient):
        res = auth_client.post(
            "/auth/register",
            json={"email": "valid@example.com", "password": "        "},
        )
        assert res.status_code == 422


class TestArgon2PasswordHashing:
    """Tests verifying cryptographic password hashing properties."""

    def test_argon2_hash_and_verify(self):
        pwd = "MySecretPassword123"
        pwd_hash = hash_password(pwd)
        assert pwd_hash.startswith("$argon2id$")
        assert verify_password(pwd, pwd_hash) is True
        assert verify_password("WrongPassword", pwd_hash) is False

    def test_argon2_unique_salts(self):
        pwd = "SamePassword"
        hash1 = hash_password(pwd)
        hash2 = hash_password(pwd)
        assert hash1 != hash2  # Different unique salts each time


class TestUserLogin:
    """Tests for POST /auth/login."""

    def test_successful_login(self, auth_client: TestClient):
        auth_client.post(
            "/auth/register",
            json={"email": "loginuser@example.com", "password": "correctpassword"},
        )
        res = auth_client.post(
            "/auth/login",
            json={"email": "LoginUser@Example.com", "password": "correctpassword"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    def test_invalid_password_returns_generic_401(self, auth_client: TestClient):
        auth_client.post(
            "/auth/register",
            json={"email": "user@example.com", "password": "correctpassword"},
        )
        res = auth_client.post(
            "/auth/login",
            json={"email": "user@example.com", "password": "wrongpassword"},
        )
        assert res.status_code == 401
        assert res.json()["detail"] == "Invalid email or password."

    def test_nonexistent_email_returns_identical_generic_401(self, auth_client: TestClient):
        res = auth_client.post(
            "/auth/login",
            json={"email": "ghost@example.com", "password": "anypassword"},
        )
        assert res.status_code == 401
        # Exactly identical message to prevent user enumeration
        assert res.json()["detail"] == "Invalid email or password."

    def test_login_rate_limiting_locks_out_after_failures(self, auth_client: TestClient):
        login_limiter.reset()
        email = "bruteforce@example.com"
        for _ in range(5):
            res = auth_client.post("/auth/login", json={"email": email, "password": "bad"})
            assert res.status_code == 401

        # 6th attempt should be blocked with 429
        locked_res = auth_client.post("/auth/login", json={"email": email, "password": "bad"})
        assert locked_res.status_code == 429
        assert "Too many failed login attempts" in locked_res.json()["detail"]


class TestGetMeEndpoint:
    """Tests for GET /auth/me."""

    def test_get_me_authenticated(self, auth_client: TestClient):
        auth_client.post(
            "/auth/register",
            json={"email": "me@example.com", "password": "password123"},
        )
        login_res = auth_client.post(
            "/auth/login",
            json={"email": "me@example.com", "password": "password123"},
        )
        token = login_res.json()["access_token"]

        me_res = auth_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_res.status_code == 200
        data = me_res.json()
        assert data["email"] == "me@example.com"
        assert "password" not in data

    def test_get_me_unauthenticated_returns_401(self, auth_client: TestClient):
        res = auth_client.get("/auth/me")
        assert res.status_code == 401
