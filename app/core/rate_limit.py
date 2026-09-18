"""Fixed-window API rate limiting, backed by Redis (already required for Celery).

Keyed per (client IP, current-minute, path) via Redis `INCR`+`EXPIRE`, which
is atomic enough for this purpose (a lost race just under/over-counts by one
request, not worth a Lua script). Fails OPEN: any Redis error (unreachable,
timeout) logs a warning and lets the request through rather than taking the
whole API down over a rate-limiter dependency — this also means the test
suite (which never starts Redis) runs unaffected.
"""

import time

import redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_redis_client: redis.Redis | None = None
_redis_unavailable_warned = False

# Generous enough not to interfere with legitimate use (the Jobs page polls
# GET /jobs every few seconds while a scrape is in flight), but bounds abuse
# / accidental runaway loops.
DEFAULT_LIMIT_PER_MINUTE = 120


def _get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=0.5)
    return _redis_client


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Limit each client IP to `limit_per_minute` requests/minute under `path_prefix`."""

    def __init__(self, app, path_prefix: str = "/api/v1", limit_per_minute: int = DEFAULT_LIMIT_PER_MINUTE):
        super().__init__(app)
        self.path_prefix = path_prefix
        self.limit_per_minute = limit_per_minute

    async def dispatch(self, request: Request, call_next):
        global _redis_unavailable_warned

        if not request.url.path.startswith(self.path_prefix):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        window = int(time.time() // 60)
        key = f"ratelimit:{client_ip}:{window}"

        try:
            client = _get_redis_client()
            count = client.incr(key)
            if count == 1:
                client.expire(key, 60)
        except redis.RedisError:
            if not _redis_unavailable_warned:
                logger.warning("Rate limiter: Redis unavailable, failing open (not limiting requests)")
                _redis_unavailable_warned = True
            return await call_next(request)

        if count > self.limit_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests, please slow down."},
                headers={"Retry-After": "60"},
            )

        return await call_next(request)
