from collections import defaultdict
from time import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_calls: int = 10, period: int = 60) -> None:
        super().__init__(app)
        self.max_calls = max_calls
        self.period = period
        self._calls: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: Callable):
        ip = self._get_client_ip(request)
        now = time()
        self._calls[ip] = [t for t in self._calls[ip] if now - t < self.period]
        if len(self._calls[ip]) >= self.max_calls:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
            )
        self._calls[ip].append(now)
        return await call_next(request)
