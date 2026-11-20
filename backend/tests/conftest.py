"""
Shared pytest fixtures for the AI Financial Decision Support System test suite.

Phase 5 update
--------------
The ``client`` fixture provides an authenticated test user context so that
all existing Phase 1, 2, and 3 tests continue to pass without regression.
Dedicated Phase 5 tests directly test authentication, session rotation,
and multi-user data isolation.
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.db.models import UserModel
from app.financial_analysis import get_profile_repository
from app.main import app
from app.repository import ProfileRepository, TransactionRepository
from app.transactions import get_repository

MOCK_TEST_USER = UserModel(
    id="test-user-legacy-uuid",
    email="testuser@example.com",
    password_hash="mockhash",
    is_active=True,
    created_at=datetime.now(timezone.utc),
    updated_at=datetime.now(timezone.utc),
)


@pytest.fixture()
def tmp_repo(tmp_path: Path) -> TransactionRepository:
    """TransactionRepository backed by a temporary file (auto-deleted)."""
    return TransactionRepository(filepath=tmp_path / "test_transactions.json")


@pytest.fixture()
def tmp_profile_repo(tmp_path: Path) -> ProfileRepository:
    """ProfileRepository backed by a temporary file (auto-deleted)."""
    return ProfileRepository(filepath=tmp_path / "test_profile.json")


@pytest.fixture()
def client(tmp_repo: TransactionRepository, tmp_profile_repo: ProfileRepository) -> TestClient:
    """TestClient wired to isolated temporary repositories and a default authenticated user."""
    app.dependency_overrides[get_repository] = lambda: tmp_repo
    app.dependency_overrides[get_profile_repository] = lambda: tmp_profile_repo
    app.dependency_overrides[get_current_user] = lambda: MOCK_TEST_USER
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_repository, None)
    app.dependency_overrides.pop(get_profile_repository, None)
    app.dependency_overrides.pop(get_current_user, None)
