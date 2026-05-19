"""Load and validate the default chat system prompt from a repository file."""

from pathlib import Path

_PROMPT_FILE = Path(__file__).resolve().parent.parent / "system_prompt.txt"
MAX_SYSTEM_PROMPT_LENGTH = 8000
_cached_default: str | None = None


def get_system_prompt_file_path() -> Path:
    """Return the path to the default system prompt file."""
    return _PROMPT_FILE


def load_default_system_prompt() -> str:
    """Load the default system prompt from disk (cached after first read)."""
    global _cached_default
    if _cached_default is not None:
        return _cached_default
    if not _PROMPT_FILE.is_file():
        raise RuntimeError(f"System prompt file not found: {_PROMPT_FILE}")
    text = _PROMPT_FILE.read_text(encoding="utf-8").strip()
    if not text:
        raise RuntimeError(f"System prompt file is empty: {_PROMPT_FILE}")
    _cached_default = text
    return text


def validate_system_prompt_override(value: str) -> str:
    """Validate a client-provided system prompt override."""
    stripped = value.strip()
    if not stripped:
        raise ValueError("system_prompt must not be empty")
    if len(stripped) > MAX_SYSTEM_PROMPT_LENGTH:
        raise ValueError(
            f"system_prompt exceeds maximum length ({MAX_SYSTEM_PROMPT_LENGTH})"
        )
    return stripped


def resolve_system_prompt(override: str | None) -> str:
    """Return the override when set, otherwise the file-based default."""
    if override is None:
        return load_default_system_prompt()
    return validate_system_prompt_override(override)
