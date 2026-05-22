"""Production middleware: rate limiting."""

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int | None = None):
        super().__init__(app)
        self.limit = requests_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self.hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        if request.url.path in ("/health", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        now = time.time()
        window = self.hits[client]
        self.hits[client] = [t for t in window if now - t < 60]

        if len(self.hits[client]) >= self.limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
            )

        self.hits[client].append(now)
        return await call_next(request)
