from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.system_prompt import MAX_SYSTEM_PROMPT_LENGTH


class ChatMessage(BaseModel):
    """One turn in the conversation."""

    role: Literal["user", "assistant", "system"]
    content: str = Field(..., min_length=1, max_length=32000)


class ChatRequest(BaseModel):
    """Payload sent from the chat UI."""

    messages: list[ChatMessage] = Field(..., min_length=1)
    system_prompt: str | None = Field(
        default=None,
        max_length=MAX_SYSTEM_PROMPT_LENGTH,
        description="Optional override for base system instructions (RAG context is still appended server-side).",
    )
    session_id: str | None = Field(default=None, description="UUID tracking a user session.")
    origin: str | None = Field(default=None, max_length=253, description="Requesting domain, e.g. 'mjcfecamp.org'.")

    @field_validator("system_prompt")
    @classmethod
    def system_prompt_not_blank(cls, value: str | None) -> str | None:
        """Reject empty overrides; omit the field to use the file default."""
        if value is None:
            return None
        if not value.strip():
            raise ValueError("system_prompt must not be empty when provided")
        return value


class ChatResponse(BaseModel):
    """Assistant reply for the current turn."""

    reply: str
