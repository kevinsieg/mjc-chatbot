from pydantic import BaseModel


class KnowledgeFile(BaseModel):
    """One Markdown source file under DATA_DIR."""

    path: str
    content: str


class KnowledgeSourcesResponse(BaseModel):
    """All Markdown files used for RAG ingestion."""

    files: list[KnowledgeFile]
