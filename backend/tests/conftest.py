import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db_util import ensure_schema_at_startup, get_connection


@pytest.fixture(scope="session", autouse=True)
def setup_schema():
    """Run DDL once per test session against the real test DB."""
    ensure_schema_at_startup()


@pytest.fixture()
def client():
    """FastAPI TestClient — synchronous, no event loop needed."""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db_conn():
    """Live psycopg3 connection for direct DB assertions."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()
