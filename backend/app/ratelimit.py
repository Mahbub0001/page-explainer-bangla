import time
import logging
from collections import defaultdict
from typing import Dict, List
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import get_settings
from app.errors import err_rate_limited, format_error_response

logger = logging.getLogger("bpe.ratelimit")


class SlidingWindowRateLimiter:
    def __init__(self):
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str, limit: int, window_seconds: float = 60.0) -> tuple[bool, int]:
        now = time.time()
        timestamps = self._requests[client_ip]

        # Purge timestamps outside the rolling window
        valid_timestamps = [ts for ts in timestamps if (now - ts) < window_seconds]
        self._requests[client_ip] = valid_timestamps

        if len(valid_timestamps) >= limit:
            oldest = valid_timestamps[0]
            retry_after = max(1, int(window_seconds - (now - oldest)))
            return False, retry_after

        self._requests[client_ip].append(now)
        return True, 0

    def reset(self):
        self._requests.clear()


_rate_limiter = SlidingWindowRateLimiter()


def get_rate_limiter() -> SlidingWindowRateLimiter:
    return _rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Apply rate limiter only to /api/v1/* paths
        if request.url.path.startswith("/api/v1/"):
            settings = get_settings()
            if settings.RATE_LIMIT_PER_MINUTE > 0:
                client_ip = request.client.host if request.client else "127.0.0.1"
                # Check for X-Forwarded-For header in case behind a reverse proxy
                forwarded_for = request.headers.get("x-forwarded-for")
                if forwarded_for:
                    client_ip = forwarded_for.split(",")[0].strip()

                limiter = get_rate_limiter()
                allowed, retry_after = limiter.is_allowed(
                    client_ip=client_ip,
                    limit=settings.RATE_LIMIT_PER_MINUTE,
                    window_seconds=60.0
                )
                if not allowed:
                    logger.warning(f"Rate limit exceeded for client {client_ip}")
                    error = err_rate_limited(retry_after=retry_after)
                    return format_error_response(error)

        return await call_next(request)
