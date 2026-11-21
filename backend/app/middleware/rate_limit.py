"""
Rate limiting middleware using Redis
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette import status as http_status
from app.core.cache import get_redis
from app.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Global rate limiting middleware

    Uses Redis to track request counts per IP/user
    """

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/api/docs", "/api/redoc", "/api/openapi.json"]:
            return await call_next(request)

        # Get identifier (IP address)
        client_ip = request.client.host if request.client else "unknown"

        # Rate limit key
        rate_limit_key = f"rate_limit:{client_ip}"

        # Get Redis client
        redis = get_redis()

        try:
            # Get current count
            current = redis.get(rate_limit_key)

            if current is None:
                # First request in window
                redis.setex(rate_limit_key, 60, 1)  # 60 second window
            else:
                current = int(current)
                if current >= settings.RATE_LIMIT_PER_MINUTE:
                    # Rate limit exceeded
                    return JSONResponse(
                        status_code=http_status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "detail": "Rate limit exceeded. Please try again later.",
                            "retry_after": 60
                        },
                        headers={"Retry-After": "60"}
                    )
                redis.incr(rate_limit_key)

        except Exception as e:
            # If Redis fails, allow request to proceed
            # (fail open for availability)
            pass

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        try:
            remaining = settings.RATE_LIMIT_PER_MINUTE - int(redis.get(rate_limit_key) or 0)
            response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
            response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        except:
            pass

        return response
