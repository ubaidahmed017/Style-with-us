"""
Authentication middleware and RBAC dependencies.
"""

import base64
import json
from typing import Optional
from fastapi import Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

import app.core.firebase as firebase
from app.core.firebase import verify_id_token
from app.core.database import get_db
from app.models import User, UserRole


class DecodedToken(BaseModel):
    """Decoded Firebase ID token."""
    uid: str
    email: Optional[str] = None


def _decode_jwt_unverified(token: str) -> Optional[dict]:
    """Decode a JWT payload WITHOUT verifying its signature.

    Only used as a last resort in verify-only/degraded mode (no valid service
    account key) so local development can still authenticate. NEVER trusted
    when a real credential is available.
    """
    try:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)  # restore padding
        return json.loads(base64.urlsafe_b64decode(payload_b64))
    except Exception:
        return None


async def verify_firebase_token(
    authorization: str = Header(None, alias="Authorization"),
) -> DecodedToken:
    """
    Verify Firebase ID token from Authorization header.

    Args:
        authorization: Authorization header value (Bearer <token>)

    Returns:
        DecodedToken with user UID and email

    Raises:
        HTTPException: 401 if token is missing, invalid, expired, or revoked
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format"
        )

    token = authorization[7:].strip()  # Remove "Bearer " prefix

    try:
        decoded = verify_id_token(token, check_revoked=True)
        return DecodedToken(
            uid=decoded.get("uid"),
            email=decoded.get("email")
        )
    except Exception as e:
        # Dev-only last resort: with no valid service-account key (verify-only
        # mode), accept a well-formed Firebase JWT by reading its payload
        # without signature verification. Disabled the moment a real key exists.
        if firebase.DEGRADED_MODE:
            claims = _decode_jwt_unverified(token)
            uid = claims and (claims.get("user_id") or claims.get("sub"))
            if uid:
                print(
                    "[AUTH] WARNING: accepting token via UNVERIFIED decode "
                    f"(verify-only dev mode) for {claims.get('email')!r}."
                )
                return DecodedToken(uid=uid, email=claims.get("email"))

        error_detail = str(e)
        if "expired" in error_detail.lower():
            detail = "Token expired"
        elif "revoked" in error_detail.lower():
            detail = "Token revoked"
        elif "invalid" in error_detail.lower():
            detail = "Invalid token"
        else:
            detail = "Token verification failed"

        raise HTTPException(status_code=401, detail=detail)


def require_role(required_role: UserRole):
    """
    RBAC dependency factory - requires user to have a specific role.

    Args:
        required_role: The role required to access the endpoint

    Returns:
        FastAPI dependency that verifies role
    """
    async def dependency(
        user: DecodedToken = Depends(verify_firebase_token),
        db: AsyncSession = Depends(get_db),
    ) -> DecodedToken:
        # Get user from database
        from sqlalchemy import select

        stmt = select(User).where(User.firebase_uid == user.uid)
        result = await db.execute(stmt)
        db_user = result.scalar_one_or_none()

        if not db_user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Admin users bypass all role checks
        if db_user.role == UserRole.ADMIN:
            return user

        # Check if user has required role
        if db_user.role != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"This action requires {required_role.value} role"
            )

        return user

    return dependency


async def get_current_user(
    user: DecodedToken = Depends(verify_firebase_token),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from database.

    Args:
        user: Decoded Firebase token
        db: Database session

    Returns:
        User model

    Raises:
        HTTPException: 404 if user not found
    """
    from sqlalchemy import select

    stmt = select(User).where(User.firebase_uid == user.uid)
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return db_user
