"""
Pydantic schemas for authentication and user account management.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    """Payload for POST /auth/register."""

    email: EmailStr = Field(..., description="Valid email address.")
    password: str = Field(..., min_length=8, max_length=128, description="Password (8-128 chars).")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        return str(v).strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Password cannot consist solely of whitespace.")
        return v


class UserLoginRequest(BaseModel):
    """Payload for POST /auth/login."""

    email: EmailStr = Field(..., description="User email address.")
    password: str = Field(..., description="User password.")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        return str(v).strip().lower()


class UserResponse(BaseModel):
    """Safe user profile representation returned by /auth/register and /auth/me."""

    id: str = Field(..., description="Unique user identifier (UUID).")
    email: str = Field(..., description="Normalized user email.")
    is_active: bool = Field(..., description="Account active status.")
    created_at: datetime = Field(..., description="Account creation timestamp.")

    model_config = {
        "from_attributes": True,
    }


class TokenResponse(BaseModel):
    """Response returned upon successful login or session refresh."""

    access_token: str = Field(..., description="JWT bearer access token.")
    refresh_token: str = Field(..., description="Opaque refresh token string.")
    token_type: str = Field(default="bearer", description="Token type.")
    expires_in: int = Field(..., description="Access token lifetime in seconds.")


class RefreshRequest(BaseModel):
    """Payload for POST /auth/refresh."""

    refresh_token: str = Field(..., description="Current refresh token.")


class LogoutRequest(BaseModel):
    """Optional payload for POST /auth/logout."""

    refresh_token: Optional[str] = Field(default=None, description="Refresh token to revoke.")


class MessageResponse(BaseModel):
    """Generic message response envelope."""

    message: str = Field(..., description="Status message.")
