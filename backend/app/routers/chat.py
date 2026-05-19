from fastapi import APIRouter, HTTPException

from app.knowledge_sources import load_knowledge_markdown_files
from app.rag_service import answer_chat_turn
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.knowledge_sources import KnowledgeSourcesResponse
from app.schemas.system_prompt import SystemPromptResponse
from app.system_prompt import load_default_system_prompt

router = APIRouter()


@router.get("/system-prompt", response_model=SystemPromptResponse)
def get_system_prompt() -> SystemPromptResponse:
    """Return the file-based default system prompt for the chat UI."""
    try:
        return SystemPromptResponse(default=load_default_system_prompt())
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/knowledge-sources", response_model=KnowledgeSourcesResponse)
def get_knowledge_sources() -> KnowledgeSourcesResponse:
    """Return Markdown files from DATA_DIR (read-only, for the home page viewer)."""
    try:
        rows = load_knowledge_markdown_files()
        return KnowledgeSourcesResponse(files=rows)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/chat", response_model=ChatResponse)
def post_chat(body: ChatRequest) -> ChatResponse:
    """Run one chat turn: RAG retrieval + Mistral completion."""
    last = body.messages[-1]
    if last.role != "user":
        raise HTTPException(
            status_code=422,
            detail="The last message must have role 'user'.",
        )
    if not last.content.strip():
        raise HTTPException(status_code=422, detail="User message is empty.")
    try:
        reply = answer_chat_turn(body)
    except ValueError as exc:
        msg = str(exc)
        if "MISTRAL_API_KEY" in msg:
            raise HTTPException(status_code=503, detail=msg) from exc
        raise HTTPException(status_code=422, detail=msg) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Mistral or database error: {exc!s}",
        ) from exc
    return ChatResponse(reply=reply)
