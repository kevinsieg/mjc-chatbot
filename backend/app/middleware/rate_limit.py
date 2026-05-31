from collections import defaultdict
from collections.abc import Callable
from time import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_calls: int = 10, period: int = 60) -> None:
        super().__init__(app)
        self.max_calls = max_calls
        self.period = period
        # grows proportional to unique IPs seen; acceptable for single-instance deployments
        self._calls: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # Leftmost IP is the real client when Traefik is configured with trustedIPs
            # (Traefik strips client-supplied XFF from untrusted peers, then prepends the real peer IP).
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: Callable):
        if request.url.path in ("/health", "/health/"):
            return await call_next(request)
        ip = self._get_client_ip(request)
        now = time()
        self._calls[ip] = [t for t in self._calls[ip] if now - t < self.period]
        if len(self._calls[ip]) >= self.max_calls:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
                headers={"Retry-After": str(self.period)},
            )
        self._calls[ip].append(now)
        return await call_next(request)
