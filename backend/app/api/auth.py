"""
Clinexa — JWT Authentication Middleware & Dependency

Validates Supabase-issued JWTs on every protected route.
Supabase signs JWTs with the project JWT secret (HS256).
"""
from __future__ import annotations

from typing import Optional

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings

log = structlog.get_logger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    """Extracted claims from a validated Supabase JWT."""
    user_id: str
    email: Optional[str] = None
    role: Optional[str] = None


def decode_supabase_jwt(token: str) -> dict:
    """
    Decode and verify a Supabase JWT.
    Supabase uses HS256 with the project JWT secret.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},  # Supabase does not always set aud
        )
        return payload
    except JWTError as exc:
        log.warning("jwt.invalid", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "invalid_token", "message": "Invalid or expired token."}},
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> CurrentUser:
    """FastAPI dependency — validates JWT and returns current user claims."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "missing_token", "message": "Authorization header is required."}},
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_supabase_jwt(credentials.credentials)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "invalid_token", "message": "Token missing subject claim."}},
        )

    return CurrentUser(
        user_id=user_id,
        email=payload.get("email"),
        role=payload.get("role"),
    )


async def get_current_admin(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Dependency that also asserts admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "forbidden", "message": "Admin access required."}},
        )
    return current_user
