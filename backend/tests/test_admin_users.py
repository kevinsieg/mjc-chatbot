import time

import jwt as pyjwt
import pytest

SECRET = "test-secret-for-user-tests-32ch!"


def _make_token(role: str) -> str:
    return pyjwt.encode({"sub": "1", "role": role, "exp": int(time.time()) + 3600}, SECRET, algorithm="HS256")


@pytest.fixture(autouse=True)
def patch_secret(monkeypatch):
    monkeypatch.setenv("NEXTAUTH_SECRET", SECRET)


@pytest.fixture()
def admin_headers():
    return {"Authorization": f"Bearer {_make_token('admin')}"}


@pytest.fixture()
def staff_headers():
    return {"Authorization": f"Bearer {_make_token('staff')}"}


def test_list_users_requires_auth(client):
    assert client.get("/api/v1/admin/users").status_code == 401


def test_list_users_admin_only(client, staff_headers):
    resp = client.get("/api/v1/admin/users", headers=staff_headers)
    assert resp.status_code == 403


def test_create_user_requires_auth(client):
    assert client.post("/api/v1/admin/users", json={"email": "x@x.com", "password": "pass1234", "role": "staff"}).status_code == 401


def test_create_user_staff_forbidden(client, staff_headers):
    resp = client.post(
        "/api/v1/admin/users",
        json={"email": "x@x.com", "password": "pass1234", "role": "staff"},
        headers=staff_headers,
    )
    assert resp.status_code == 403


def test_patch_user_requires_auth(client):
    assert client.patch("/api/v1/admin/users/1", json={"role": "staff"}).status_code == 401


def test_patch_user_staff_forbidden(client, staff_headers):
    assert client.patch("/api/v1/admin/users/1", json={"role": "staff"}, headers=staff_headers).status_code == 403


def test_delete_user_requires_auth(client):
    assert client.delete("/api/v1/admin/users/1").status_code == 401


def test_delete_user_staff_forbidden(client, staff_headers):
    assert client.delete("/api/v1/admin/users/1", headers=staff_headers).status_code == 403


def test_create_and_list_user(client, admin_headers, db_conn):
    resp = client.post(
        "/api/v1/admin/users",
        json={"email": "test@example.com", "name": "Test User", "password": "secret123", "role": "staff"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    user = resp.json()
    assert user["email"] == "test@example.com"
    assert user["role"] == "staff"
    assert "password_hash" not in user

    list_resp = client.get("/api/v1/admin/users", headers=admin_headers)
    assert list_resp.status_code == 200
    emails = [u["email"] for u in list_resp.json()["items"]]
    assert "test@example.com" in emails

    # cleanup
    db_conn.execute("DELETE FROM users WHERE email = 'test@example.com'")
    db_conn.commit()


def test_patch_user_role(client, admin_headers, db_conn):
    db_conn.execute("DELETE FROM users WHERE email = 'patch@example.com'")
    db_conn.commit()
    db_conn.execute(
        "INSERT INTO users (email, name, password_hash, role) VALUES ('patch@example.com', 'Patch', 'x', 'staff')"
    )
    db_conn.commit()
    with db_conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE email = 'patch@example.com'")
        user_id = cur.fetchone()[0]

    resp = client.patch(
        f"/api/v1/admin/users/{user_id}",
        json={"role": "admin"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"

    db_conn.execute("DELETE FROM users WHERE id = %s", (user_id,))
    db_conn.commit()


def test_delete_user_soft(client, admin_headers, db_conn):
    db_conn.execute("DELETE FROM users WHERE email = 'delete@example.com'")
    db_conn.commit()
    db_conn.execute(
        "INSERT INTO users (email, name, password_hash, role) VALUES ('delete@example.com', 'Del', 'x', 'staff')"
    )
    db_conn.commit()
    with db_conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE email = 'delete@example.com'")
        user_id = cur.fetchone()[0]

    resp = client.delete(f"/api/v1/admin/users/{user_id}", headers=admin_headers)
    assert resp.status_code == 204

    with db_conn.cursor() as cur:
        cur.execute("SELECT deleted_at FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
    assert row[0] is not None  # soft-deleted, not gone

    db_conn.execute("DELETE FROM users WHERE id = %s", (user_id,))
    db_conn.commit()


def test_patch_user_email(client, admin_headers, db_conn):
    db_conn.execute("DELETE FROM users WHERE email IN ('email_orig@example.com', 'email_new@example.com')")
    db_conn.commit()
    db_conn.execute(
        "INSERT INTO users (email, name, password_hash, role) VALUES ('email_orig@example.com', 'E', 'x', 'staff')"
    )
    db_conn.commit()
    with db_conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE email = 'email_orig@example.com'")
        user_id = cur.fetchone()[0]

    resp = client.patch(
        f"/api/v1/admin/users/{user_id}",
        json={"email": "email_new@example.com"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "email_new@example.com"

    db_conn.execute("DELETE FROM users WHERE id = %s", (user_id,))
    db_conn.commit()


def test_patch_user_email_duplicate(client, admin_headers, db_conn):
    db_conn.execute("DELETE FROM users WHERE email IN ('dup_a@example.com', 'dup_b@example.com')")
    db_conn.commit()
    db_conn.execute(
        "INSERT INTO users (email, name, password_hash, role) VALUES ('dup_a@example.com', 'A', 'x', 'staff'), ('dup_b@example.com', 'B', 'x', 'staff')"
    )
    db_conn.commit()
    with db_conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE email = 'dup_b@example.com'")
        user_b_id = cur.fetchone()[0]

    resp = client.patch(
        f"/api/v1/admin/users/{user_b_id}",
        json={"email": "dup_a@example.com"},
        headers=admin_headers,
    )
    assert resp.status_code == 409

    db_conn.execute("DELETE FROM users WHERE email IN ('dup_a@example.com', 'dup_b@example.com')")
    db_conn.commit()


def test_patch_user_password(client, admin_headers, db_conn):
    db_conn.execute("DELETE FROM users WHERE email = 'pwchange@example.com'")
    db_conn.commit()
    db_conn.execute(
        "INSERT INTO users (email, name, password_hash, role) VALUES ('pwchange@example.com', 'PW', 'x', 'staff')"
    )
    db_conn.commit()
    with db_conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE email = 'pwchange@example.com'")
        user_id = cur.fetchone()[0]

    resp = client.patch(
        f"/api/v1/admin/users/{user_id}",
        json={"password": "newpassword123"},
        headers=admin_headers,
    )
    assert resp.status_code == 200

    with db_conn.cursor() as cur:
        cur.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
        new_hash = cur.fetchone()[0]
    assert new_hash != "x"  # hash was updated

    db_conn.execute("DELETE FROM users WHERE id = %s", (user_id,))
    db_conn.commit()


def test_create_user_duplicate_email(client, admin_headers, db_conn):
    db_conn.execute("DELETE FROM users WHERE email = 'dup@example.com'")
    db_conn.commit()
    payload = {"email": "dup@example.com", "password": "secret123", "role": "staff"}

    first = client.post("/api/v1/admin/users", json=payload, headers=admin_headers)
    assert first.status_code == 200

    second = client.post("/api/v1/admin/users", json=payload, headers=admin_headers)
    assert second.status_code == 409
    assert "detail" in second.json()

    db_conn.execute("DELETE FROM users WHERE email = 'dup@example.com'")
    db_conn.commit()


def test_list_users_includes_deleted(client, admin_headers, db_conn):
    db_conn.execute("DELETE FROM users WHERE email = 'grey@example.com'")
    db_conn.commit()
    db_conn.execute(
        "INSERT INTO users (email, name, password_hash, role) VALUES ('grey@example.com', 'Grey', 'x', 'staff')"
    )
    db_conn.commit()
    with db_conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE email = 'grey@example.com'")
        user_id = cur.fetchone()[0]

    client.delete(f"/api/v1/admin/users/{user_id}", headers=admin_headers)

    list_resp = client.get("/api/v1/admin/users", headers=admin_headers)
    assert list_resp.status_code == 200
    users = list_resp.json()["items"]
    match = next((u for u in users if u["email"] == "grey@example.com"), None)
    assert match is not None
    assert match["deleted_at"] is not None

    db_conn.execute("DELETE FROM users WHERE id = %s", (user_id,))
    db_conn.commit()
