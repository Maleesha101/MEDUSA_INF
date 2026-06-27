from __future__ import annotations

import time
from typing import Optional

import aioredis
from fastapi import Request, HTTPException, status

from ..config import settings

# ── Redis client (lazy init) ───────────────────────────────────────
_redis: Optional[aioredis.Redis] = None


async def _get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(settings.REDIS_DSN, decode_responses=True)
    return _redis


# Exception that the FastAPI app catches to return 429
class RateLimitException(HTTPException):
    def __init__(self, retry_after: int):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded. Retry after {retry_after}s")
        self.retry_after = retry_after


async def limit(request: Request, *, tokens: int = 1, period_seconds: int = 60, burst: int = 5) -> None:
    """
    Token‑bucket limiter keyed by user ID (or IP if unauthenticated).
    * `tokens` – how many tokens this request consumes.
    * `period_seconds` – refill interval.
    * `burst` – max tokens that can accumulate.
    """
    redis = await _get_redis()
    key = f"rl:{request.state.team_id or request.client.host}"
    now = int(time.time())

    # Lua script atomically updates bucket and returns remaining tokens / ttl
    script = """
    local key, now, tokens, period, burst = KEYS[1], tonumber(ARGV[1]), tonumber(ARGV[2]), tonumber(ARGV[3]), tonumber(ARGV[4])
    local data = redis.call('HMGET', key, 'tokens', 'ts')
    local last = tonumber(data[2]) or now
    local tokens_left = tonumber(data[1]) or burst

    local elapsed = now - last
    local refill = math.floor(elapsed / period) * tokens
    tokens_left = math.min(burst, tokens_left + refill)

    if tokens_left < tokens then
        redis.call('HMSET', key, 'tokens', tokens_left, 'ts', now)
        redis.call('EXPIRE', key, period * 2)
        return {0, period - (elapsed % period)}  -- not enough, return retry after
    else
        tokens_left = tokens_left - tokens
        redis.call('HMSET', key, 'tokens', tokens_left, 'ts', now)
        redis.call('EXPIRE', key, period * 2)
        return {1, 0}
    end
    """
    allowed, retry = await redis.eval(
        script,
        1,
        key,
        now,
        tokens,
        period_seconds,
        burst,
    )
    if not allowed:
        raise RateLimitException(retry_after=int(retry))
