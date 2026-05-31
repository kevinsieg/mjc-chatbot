import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db_util import ensure_schema_at_startup
from app.middleware.rate_limit import RateLimitMiddleware
from app.routers import chat as chat_router
from app.system_prompt import load_default_system_prompt


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run DDL migrations on startup (idempotent)."""
    await asyncio.to_thread(ensure_schema_at_startup)
    await asyncio.to_thread(load_default_system_prompt)
    yield


app = FastAPI(title="mjc-chatbot API", version="0.1.0", lifespan=lifespan)
app.add_middleware(RateLimitMiddleware, max_calls=10, period=60)
app.include_router(chat_router.router, prefix="/api/v1", tags=["chat"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe for orchestration and the frontend smoke check."""
    return {"status": "ok"}
