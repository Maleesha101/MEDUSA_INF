from __future__ import annotations

import datetime
from typing import Any, Dict, Optional

import bcrypt
import jwt
from fastapi import HTTPException, status

from ..config import settings
from ..db import db as db_mod


# ── Password hashing ───────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ── JWT creation / verification ─────────────────────────────────────
def _now() -> datetime.datetime:
    return datetime.datetime.utcnow()


def _create_token(
    subject: str,
    team_id: str,
    *,
    expires_delta: datetime.timedelta,
    token_type: str,
) -> str:
    payload: Dict[str, Any] = {
        "sub": subject,
        "team_id": team_id,
        "type": token_type,
        "iat": _now(),
        "exp": _now() + expires_delta,
        "jti": jwt.utils.base64url_encode(jwt.utils.random_bytes(16)).decode(),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(*, subject: str, team_id: str, expires_delta: Optional[datetime.timedelta] = None) -> str:
    delta = expires_delta or datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(subject, team_id, expires_delta=delta, token_type="access")


def create_refresh_token(*, subject: str, team_id: str) -> str:
    delta = datetime.timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token(subject, team_id, expires_delta=delta, token_type="refresh")


def decode_jwt(token: str, *, verify_type: str = "access") -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != verify_type:
            raise jwt.InvalidTokenError("Wrong token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# ── Token revocation (simple Redis blacklist) ───────────────────────
import aioredis

_redis: Optional[aioredis.Redis] = None


async def _get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(settings.REDIS_DSN, decode_responses=True)
    return _redis


async def revoke_token(jti: str, ttl_seconds: int = 86400) -> None:
    redis = await _get_redis()
    await redis.setex(f"revoked:{jti}", ttl_seconds, "1")


async def is_token_revoked(jti: str, db=None) -> bool:  # db param kept for legacy call signature
    redis = await _get_redis()
    return bool(await redis.get(f"revoked:{jti}"))


# ── Audit logging helper ───────────────────────────────────────────
async def log_action(
    *,
    team_id: Optional[str],
    user_id: Optional[str],
    action: str,
    ip_address: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    """Insert a row into the audit_logs table (non‑blocking)."""
    async with db_mod.engine.begin() as conn:
        await conn.execute(
            """
            INSERT INTO audit_logs (team_id, user_id, action, ip_address, payload)
            VALUES (:team_id, :user_id, :action, :ip_address, :payload)
            """,
            {
                "team_id": team_id,
                "user_id": user_id,
                "action": action,
                "ip_address": ip_address,
                "payload": payload,
            },
        )

