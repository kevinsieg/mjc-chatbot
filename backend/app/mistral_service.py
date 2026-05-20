from typing import Any

try:
    from mistralai.client import Mistral
except ImportError:  # pragma: no cover - depends on mistralai wheel layout
    from mistralai import Mistral

from app.models import ChatResult
from app.settings import (
    get_embedding_dimensions,
    get_mistral_api_key,
    get_mistral_chat_model,
    get_mistral_embed_model,
)


def _embedding_vectors(response: Any) -> list[list[float]]:
    """Extract list of embedding vectors from a Mistral embeddings response."""
    items = getattr(response, "data", None)
    if items is None:
        items = getattr(response, "embeddings", None)
    if not items:
        raise RuntimeError(f"Unexpected Mistral embedding response shape: {response!r}")
    out: list[list[float]] = []
    for item in items:
        vec = getattr(item, "embedding", None)
        if vec is None:
            raise RuntimeError(f"Missing embedding field on item: {item!r}")
        out.append([float(x) for x in vec])
    return out


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Call Mistral embeddings for a batch of strings (same order as input)."""
    if not texts:
        return []
    key = get_mistral_api_key()
    if not key:
        raise RuntimeError("MISTRAL_API_KEY is not set")
    model = get_mistral_embed_model()
    with Mistral(api_key=key) as client:
        response = client.embeddings.create(model=model, inputs=texts)
    vectors = _embedding_vectors(response)
    if len(vectors) != len(texts):
        raise RuntimeError(
            f"Embedding count mismatch: got {len(vectors)}, expected {len(texts)}"
        )
    expected = get_embedding_dimensions()
    for i, vec in enumerate(vectors):
        if len(vec) != expected:
            raise RuntimeError(
                f"Embedding dim {len(vec)} at index {i} != MISTRAL_EMBED_DIM {expected}"
            )
    return vectors


def chat_complete(messages: list[dict[str, str]]) -> ChatResult:
    """Run one non-streaming chat completion and return a ChatResult."""
    key = get_mistral_api_key()
    if not key:
        raise RuntimeError("MISTRAL_API_KEY is not set")
    model = get_mistral_chat_model()
    with Mistral(api_key=key) as client:
        response = client.chat.complete(
            model=model,
            messages=messages,
            stream=False,
            response_format={"type": "text"},
        )
    choices = getattr(response, "choices", None)
    if not choices:
        raise RuntimeError(f"Mistral returned no choices: {response!r}")
    message = choices[0].message
    content = getattr(message, "content", None)
    if isinstance(content, list):
        content = "".join(str(part) for part in content)
    if content is None or str(content).strip() == "":
        raise RuntimeError("Mistral returned an empty assistant message")
    usage = getattr(response, "usage", None)
    prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
    completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
    return ChatResult(
        content=str(content),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        latency_ms=0,  # caller measures wall time
    )
