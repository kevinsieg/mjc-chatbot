from app.models import ChatResult


def test_chat_result_fields():
    r = ChatResult(content="hi", prompt_tokens=10, completion_tokens=5, latency_ms=320)
    assert r.content == "hi"
    assert r.prompt_tokens == 10
    assert r.completion_tokens == 5
    assert r.latency_ms == 320
