import time
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.rate_limit import RateLimitMiddleware


def _make_app(max_calls: int = 3, period: int = 60) -> FastAPI:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, max_calls=max_calls, period=period)

    @app.post("/test")
    async def endpoint():
        return {"ok": True}

    return app


def test_allows_requests_under_limit():
    client = TestClient(_make_app(max_calls=3))
    for _ in range(3):
        r = client.post("/test", headers={"x-forwarded-for": "1.2.3.4"})
        assert r.status_code == 200


def test_blocks_requests_over_limit():
    client = TestClient(_make_app(max_calls=3))
    for _ in range(3):
        client.post("/test", headers={"x-forwarded-for": "1.2.3.4"})
    r = client.post("/test", headers={"x-forwarded-for": "1.2.3.4"})
    assert r.status_code == 429


def test_different_ips_tracked_independently():
    client = TestClient(_make_app(max_calls=2))
    for _ in range(2):
        client.post("/test", headers={"x-forwarded-for": "1.1.1.1"})
    r_blocked = client.post("/test", headers={"x-forwarded-for": "1.1.1.1"})
    r_allowed = client.post("/test", headers={"x-forwarded-for": "2.2.2.2"})
    assert r_blocked.status_code == 429
    assert r_allowed.status_code == 200


def test_window_expiry_allows_again(monkeypatch):
    fake_time = 0.0
    monkeypatch.setattr("app.middleware.rate_limit.time", lambda: fake_time)

    client = TestClient(_make_app(max_calls=2, period=60))
    for _ in range(2):
        client.post("/test", headers={"x-forwarded-for": "5.5.5.5"})

    r = client.post("/test", headers={"x-forwarded-for": "5.5.5.5"})
    assert r.status_code == 429

    fake_time = 61.0
    r = client.post("/test", headers={"x-forwarded-for": "5.5.5.5"})
    assert r.status_code == 200
