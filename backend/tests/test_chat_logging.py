import uuid
import pytest
from unittest.mock import patch
from app.models import ChatResult


def test_chat_log_row_inserted(client, db_conn):
    """Posting to /chat with session_id should insert a chat_logs row."""
    session_id = str(uuid.uuid4())
    fake_result = ChatResult(
        content="Bonjour!", prompt_tokens=50, completion_tokens=20, latency_ms=300
    )
    with patch("app.routers.chat.answer_chat_turn", return_value=fake_result):
        resp = client.post(
            "/api/v1/chat",
            json={
                "messages": [{"role": "user", "content": "Bonjour"}],
                "session_id": session_id,
                "origin": "mjcfecamp.org",
            },
        )
    assert resp.status_code == 200
    assert resp.json()["reply"] == "Bonjour!"

    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT session_id, origin FROM chat_logs WHERE session_id = %s::uuid",
            (session_id,),
        )
        row = cur.fetchone()
    assert row is not None
    assert row[1] == "mjcfecamp.org"
