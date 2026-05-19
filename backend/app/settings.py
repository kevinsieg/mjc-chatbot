import os
from pathlib import Path

from dotenv import load_dotenv

# Load repo-root .env without overriding variables already set in the environment.
load_dotenv(Path(__file__).parent.parent.parent / ".env")


def _env_int(name: str, default: int) -> int:
    """Parse int env or return default."""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def get_database_url() -> str:
    """PostgreSQL connection string (required)."""
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url


def get_mistral_api_key() -> str:
    """Mistral API key; empty means chat/ingest must fail loudly."""
    return os.getenv("MISTRAL_API_KEY", "").strip()


def get_mistral_chat_model() -> str:
    """Chat completion model id."""
    return os.getenv("MISTRAL_CHAT_MODEL", "mistral-small-latest").strip()


def get_mistral_embed_model() -> str:
    """Embedding model id (must match vector(1024) column)."""
    return os.getenv("MISTRAL_EMBED_MODEL", "mistral-embed").strip()


def get_rag_top_k() -> int:
    """Number of chunks to inject into the prompt."""
    return max(1, min(20, _env_int("RAG_TOP_K", 5)))


def get_embedding_dimensions() -> int:
    """Vector column size; must match Mistral embedding length for mistral-embed."""
    return _env_int("MISTRAL_EMBED_DIM", 1024)
