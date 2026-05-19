from pydantic import BaseModel


class SystemPromptResponse(BaseModel):
    """Default system prompt loaded from the repository file."""

    default: str
