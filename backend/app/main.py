import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.admin_cli import seed_admin
from app.db_util import ensure_schema_at_startup
from app.routers import admin as admin_router
from app.routers import chat as chat_router
from app.scheduler import start_scheduler, stop_scheduler
from app.settings import get_cors_origins, get_seed_admin_email, get_seed_admin_password
from app.system_prompt import load_default_system_prompt


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run DDL migrations on startup (idempotent)."""
    await asyncio.to_thread(ensure_schema_at_startup)
    seed_email = get_seed_admin_email()
    seed_password = get_seed_admin_password()
    if seed_email and seed_password:
        await asyncio.to_thread(seed_admin, seed_email, seed_password)
    await asyncio.to_thread(load_default_system_prompt)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="mjc-chatbot API", version="0.1.0", lifespan=lifespan)
app.include_router(chat_router.router, prefix="/api/v1", tags=["chat"])
app.include_router(admin_router.router, prefix="/api/v1/admin", tags=["admin"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe for orchestration and the frontend smoke check."""
    return {"status": "ok"}
