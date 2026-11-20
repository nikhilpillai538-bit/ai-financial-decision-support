"""
Authentication router for the AI Financial Decision Support System.

Endpoints:
- POST /auth/register: User account creation and isolated profile initialization.
- POST /auth/login: Credential verification, brute-force mitigation, and token issuance.
- GET  /auth/me: Retrieve authenticated account details.
- POST /auth/refresh: Secure refresh token rotation and reuse detection.
- POST /auth/logout: Refresh session revocation.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.schemas import (
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.auth.security import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    login_limiter,
    validate_password_strength,
    verify_password,
)
from app.db.models import UserModel
from app.db.repositories.profile_repo import SQLProfileRepository
from app.db.repositories.user_repo import SQLUserRepository
from app.db.session import get_db

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description=(
        "Registers a new user with a normalized email and Argon2id hashed password. "
        "Initializes a dedicated user-scoped financial profile. "
        "Note: In development mode, email verification is not performed."
    ),
)
def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    """Register a new account."""
    is_valid, err = validate_password_strength(request.password)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=err)

    user_repo = SQLUserRepository(db)
    existing = user_repo.get_by_email(request.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    # Hash password with Argon2id
    pwd_hash = hash_password(request.password)
    new_user = user_repo.create_user(email=request.email, password_hash=pwd_hash)

    # Initialize user's dedicated financial profile (never shared with 'default')
    profile_repo = SQLProfileRepository(db)
    profile_repo.save_emergency_fund_config(
        config={
            "emergency_fund_balance": None,
            "essential_categories": ["rent", "groceries", "utilities", "healthcare", "transport"],
            "analysis_window_months": 12,
            "currency": "INR",
        },
        user_id=new_user.id,
        profile_key=f"user_{new_user.id}",
    )

    return UserResponse.model_validate(new_user)


@auth_router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user credentials",
    description="Authenticates email and password, returning an access token and refresh token.",
)
@auth_router.post(
    "/token",
    response_model=TokenResponse,
    include_in_schema=False,
)
def login(
    login_data: UserLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Verify credentials and issue access + refresh tokens."""
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"{client_ip}:{login_data.email}"

    if login_limiter.is_locked(rate_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please wait before retrying.",
        )

    user_repo = SQLUserRepository(db)
    user = user_repo.get_by_email(login_data.email)

    if not user or not verify_password(login_data.password, user.password_hash):
        login_limiter.record_failure(rate_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    login_limiter.record_success(rate_key)

    # Issue short-lived access token
    access_token, expires_in = create_access_token(user_id=user.id, email=user.email)

    # Issue refresh token and store hash
    raw_refresh = generate_refresh_token()
    token_hash = hash_refresh_token(raw_refresh)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    user_agent = request.headers.get("user-agent")
    user_repo.create_session(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=client_ip,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        token_type="bearer",
        expires_in=expires_in,
    )


@auth_router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user details",
    description="Retrieve the authenticated caller's account details.",
)
def get_me(
    current_user: UserModel = Depends(get_current_user),
) -> UserResponse:
    """Return caller's safe account information."""
    return UserResponse.model_validate(current_user)


@auth_router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access session",
    description=(
        "Exchange a valid refresh token for a new access token and rotated refresh token. "
        "Detects and mitigates refresh token reuse."
    ),
)
def refresh_session(
    refresh_data: RefreshRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Validate and rotate refresh token."""
    raw_token = refresh_data.refresh_token.strip()
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token must not be empty.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    incoming_hash = hash_refresh_token(raw_token)
    user_repo = SQLUserRepository(db)
    session_record = user_repo.get_session_by_token_hash(incoming_hash)

    now = datetime.now(timezone.utc)

    # If session not found or already revoked, check for potential replay/reuse
    if not session_record or session_record.revoked_at is not None:
        if session_record:
            # Token reuse detected! Invalidate all sessions for this user for security
            user_repo.revoke_all_user_sessions(session_record.user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check expiration
    exp = session_record.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp < now:
        user_repo.revoke_session(session_record)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = user_repo.get_by_id(session_record.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Rotate refresh token: revoke current and issue new
    new_raw_refresh = generate_refresh_token()
    new_token_hash = hash_refresh_token(new_raw_refresh)
    new_expires_at = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")

    user_repo.rotate_session(
        old_session=session_record,
        new_token_hash=new_token_hash,
        new_expires_at=new_expires_at,
        user_agent=user_agent,
        ip_address=client_ip,
    )

    access_token, expires_in = create_access_token(user_id=user.id, email=user.email)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_raw_refresh,
        token_type="bearer",
        expires_in=expires_in,
    )


@auth_router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user session",
    description="Revoke the provided refresh token session.",
)
def logout(
    logout_data: LogoutRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Revoke refresh session."""
    if logout_data.refresh_token:
        token_hash = hash_refresh_token(logout_data.refresh_token.strip())
        user_repo = SQLUserRepository(db)
        session_record = user_repo.get_session_by_token_hash(token_hash)
        if session_record:
            user_repo.revoke_session(session_record)

    return MessageResponse(message="Successfully logged out.")
