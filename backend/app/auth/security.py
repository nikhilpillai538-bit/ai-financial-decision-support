"""
Security, password hashing, token generation, and rate limiting utilities.

Uses Argon2id for password hashing and HMAC-SHA256 (PyJWT) for signed access tokens.
Refresh tokens are cryptographically random strings whose SHA-256 hashes are stored in the DB.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import os
import secrets
import threading
from typing import Any, Dict, Optional, Tuple

import argon2
from argon2.exceptions import VerifyMismatchError
from dotenv import load_dotenv
import jwt

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration (loaded from environment with secure defaults)
# ---------------------------------------------------------------------------

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-insecure-secret-key-change-in-production-min32chars")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Rate limiting settings for login attempts
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOGIN_LOCKOUT_SECONDS = int(os.getenv("LOGIN_LOCKOUT_SECONDS", "300"))  # 5 minutes

# Initialize Argon2id password hasher with OWASP-recommended parameters
_ph = argon2.PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    type=argon2.Type.ID,
)


# ---------------------------------------------------------------------------
# Password Hashing & Verification
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    return _ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against an Argon2id hash."""
    try:
        return _ph.verify(password_hash, password)
    except (VerifyMismatchError, Exception):
        return False


def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """Validate password length and basic constraints."""
    if not password:
        return False, "Password cannot be empty."
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if len(password) > 128:
        return False, "Password cannot exceed 128 characters."
    if not password.strip():
        return False, "Password cannot consist solely of whitespace."
    return True, None


# ---------------------------------------------------------------------------
# Access Tokens (JWT)
# ---------------------------------------------------------------------------


def create_access_token(
    user_id: str,
    email: str,
    expires_delta: Optional[timedelta] = None,
) -> Tuple[str, int]:
    """Create a signed JWT access token.

    Returns:
        Tuple of (token_string, expires_in_seconds).
    """
    now = datetime.now(timezone.utc)
    delta = expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = now + delta

    payload = {
        "sub": user_id,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    expires_in = int(delta.total_seconds())
    return token, expires_in


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT access token.

    Returns:
        The decoded payload dict if valid, or None if expired or invalid.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except (jwt.PyJWTError, Exception):
        return None


# ---------------------------------------------------------------------------
# Refresh Tokens
# ---------------------------------------------------------------------------


def generate_refresh_token() -> str:
    """Generate a high-entropy cryptographically random URL-safe token."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """Hash a refresh token using SHA-256 for persistent database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# In-Memory Login Rate Limiter (Brute-Force Protection)
# ---------------------------------------------------------------------------


class LoginRateLimiter:
    """Thread-safe rate limiter to mitigate credential-stuffing and brute-force attacks."""

    def __init__(self, max_attempts: int = MAX_LOGIN_ATTEMPTS, lockout_seconds: int = LOGIN_LOCKOUT_SECONDS):
        self.max_attempts = max_attempts
        self.lockout_seconds = lockout_seconds
        self._attempts: Dict[str, list[datetime]] = {}
        self._lock = threading.Lock()

    def is_locked(self, key: str) -> bool:
        """Return True if the key (e.g. IP or email) has exceeded max attempts."""
        with self._lock:
            now = datetime.now(timezone.utc)
            attempts = self._attempts.get(key, [])
            # Keep only attempts within the sliding lockout window
            cutoff = now - timedelta(seconds=self.lockout_seconds)
            recent = [t for t in attempts if t > cutoff]
            self._attempts[key] = recent
            return len(recent) >= self.max_attempts

    def record_failure(self, key: str) -> None:
        """Record a failed login attempt for the key."""
        with self._lock:
            now = datetime.now(timezone.utc)
            if key not in self._attempts:
                self._attempts[key] = []
            self._attempts[key].append(now)

    def record_success(self, key: str) -> None:
        """Clear failed attempts upon successful login."""
        with self._lock:
            self._attempts.pop(key, None)

    def reset(self) -> None:
        """Reset all rate limiter state (used in testing)."""
        with self._lock:
            self._attempts.clear()


login_limiter = LoginRateLimiter()
