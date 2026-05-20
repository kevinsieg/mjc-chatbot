import time

import pytest
import jwt as pyjwt
from app.auth import hash_password, verify_password, decode_service_token


def test_password_round_trip():
    h = hash_password("correct-horse-battery")
    assert verify_password("correct-horse-battery", h) is True
    assert verify_password("wrong", h) is False


def test_decode_service_token_valid(monkeypatch):
    monkeypatch.setenv("NEXTAUTH_SECRET", "test-secret-32-chars-paddddddddddd")
    secret = "test-secret-32-chars-paddddddddddd"
    token = pyjwt.encode({"sub": "1", "role": "admin", "exp": int(time.time()) + 3600}, secret, algorithm="HS256")
    payload = decode_service_token(token)
    assert payload["sub"] == "1"
    assert payload["role"] == "admin"


def test_decode_service_token_wrong_secret(monkeypatch):
    monkeypatch.setenv("NEXTAUTH_SECRET", "correct-secret-32-chars-padddddddd")
    token = pyjwt.encode({"sub": "1", "role": "admin"}, "wrong-secret", algorithm="HS256")
    with pytest.raises(pyjwt.PyJWTError):
        decode_service_token(token)
