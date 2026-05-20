import time

import jwt as pyjwt
import pytest

SECRET = "test-secret-for-stats-tests-32ch"


def _make_token(role: str) -> str:
    return pyjwt.encode({"sub": "1", "role": role, "exp": int(time.time()) + 3600}, SECRET, algorithm="HS256")


@pytest.fixture(autouse=True)
def patch_secret(monkeypatch):
    monkeypatch.setenv("NEXTAUTH_SECRET", SECRET)


def test_stats_overview_requires_auth(client):
    resp = client.get("/api/v1/admin/stats/overview")
    assert resp.status_code == 401  # HTTPBearer returns 401 when no bearer present


def test_stats_overview_staff_ok(client):
    token = _make_token("staff")
    resp = client.get(
        "/api/v1/admin/stats/overview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "total_sessions" in data
    assert "total_messages" in data


def test_stats_overview_wrong_role(client):
    token = _make_token("hacker")
    resp = client.get(
        "/api/v1/admin/stats/overview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_weekday_endpoint(client):
    token = _make_token("admin")
    resp = client.get(
        "/api/v1/admin/stats/weekday",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_api_usage_endpoint(client):
    token = _make_token("admin")
    resp = client.get(
        "/api/v1/admin/stats/api-usage",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_stats_overview_has_extended_fields(client):
    token = _make_token("admin")
    resp = client.get(
        "/api/v1/admin/stats/overview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "p95_latency_ms" in data
    assert "avg_messages_per_session" in data
    assert "cost_per_message" in data


def test_stats_daily_endpoint(client):
    token = _make_token("admin")
    resp = client.get(
        "/api/v1/admin/stats/daily",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    if data:
        assert "date" in data[0]
        assert "count" in data[0]


def test_stats_hourly_endpoint(client):
    token = _make_token("admin")
    resp = client.get(
        "/api/v1/admin/stats/hourly",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    if data:
        assert "hour" in data[0]
        assert "count" in data[0]


def test_stats_top_sources_endpoint(client):
    token = _make_token("admin")
    resp = client.get(
        "/api/v1/admin/stats/top-sources",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    if data:
        assert "source" in data[0]
        assert "hit_count" in data[0]


def test_stats_heatmap_requires_auth(client):
    resp = client.get("/api/v1/admin/stats/heatmap")
    assert resp.status_code == 401


def test_stats_heatmap_wrong_role(client):
    token = _make_token("hacker")
    resp = client.get(
        "/api/v1/admin/stats/heatmap",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_stats_heatmap_staff_ok(client):
    token = _make_token("staff")
    resp = client.get(
        "/api/v1/admin/stats/heatmap",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    if data:
        assert "day" in data[0]
        assert "hour" in data[0]
        assert "count" in data[0]
        assert 0 <= data[0]["day"] <= 6
        assert 0 <= data[0]["hour"] <= 23
