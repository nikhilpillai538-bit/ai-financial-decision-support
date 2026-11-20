"""
Authentication dependencies for FastAPI route protection and user identity resolution.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.db.models import UserModel
from app.db.repositories.user_repo import SQLUserRepository
from app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserModel:
    """Resolve and authenticate the calling user from the Bearer JWT token.

    Raises:
        HTTPException 401: If token is missing, invalid, expired, or user not found/inactive.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise credentials_exception

    user_id = payload["sub"]
    user_repo = SQLUserRepository(db)
    user = user_repo.get_by_id(user_id)

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[UserModel]:
    """Resolve user if a valid token is present; return None otherwise."""
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        return None
    user_repo = SQLUserRepository(db)
    user = user_repo.get_by_id(payload["sub"])
    if user and user.is_active:
        return user
    return None
