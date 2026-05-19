# mjc-chatbot

mjc-chatbot is a chatbot project for MJC Fecamp

## Prerequisites

- **Docker** — container runtime
- **Make** — task automation (`Makefile` targets)
- **Docker Compose** — multi-container orchestration
- **Ansible** — deployment automation

## Launch 

### Local development (Docker)

1. Copy `.env.example` to `.env` and set **`MISTRAL_API_KEY`** (required for chat + ingestion).
2. `make dev-build` — build images
3. `make dev-run` — start PostgreSQL, API, and frontend (`http://localhost:3000`, API `http://localhost:8000`, docs `http://localhost:8000/docs`)
4. In another terminal (stack still running): `make dev-data` — chunk Markdown under `./data`, embed with Mistral, store vectors in Postgres (`document_chunks`).
5. `make dev-kill` when finished

The smoke check calls same-origin `GET /api/backend/health`; Next.js rewrites that to the FastAPI service (`BACKEND_INTERNAL_URL`, default `http://backend:8000` at image build). So the browser never needs a public URL for port 8000. To reset the database volume: `docker compose down -v` then `make dev-run` again. For `next dev` on the host only, set `BACKEND_INTERNAL_URL=http://127.0.0.1:8000` in `frontend/.env.local`.

Open the app at `/` : chat thread + `POST /api/v1/chat` (see **Chat UI & API** below).

- http://162.19.241.44:3000/ (interface chatbot test)
- http://162.19.241.44:8000/health (backend)
- http://162.19.241.44:8000/docs (endpoint documentation backend)
- TODO: administration interface (connexion user, see stats)
- http://162.19.241.44:3000/embed (script embed for other website)

```
<script src="http://162.19.241.44:3000/widget.js"></script>
``` 


## Technology

| Layer | Stack |
|--------|--------|
| **Frontend** | Next.js |
| **Backend** | FastAPI (conversation flow + RAG logic) |
| **Database** | PostgreSQL + pgvector (courses, embeddings, session state) |
| **LLM API** | **Mistral** (chat + embeddings; key in `.env`) |
| **Security** | Cloudflare (bot protection + rate limiting) |

**Flow:** user → frontend → backend → vector search → LLM → response

## Features

- **LLM:** responses are generated via the **Mistral** API (API key required); the model acts on retrieved context and system instructions, not on unconstrained web knowledge.
- **Placement:** designed to be embedded on the **MJC website** (e.g. public-facing widget or page) for visitors.
- **Grounded answers:** the assistant replies **only** from **content you provide** plus a **fixed instruction / policy layer**—no free-form answers about the organisation outside that corpus.
- **Knowledge formats:** sources are ideally **Markdown** for clean chunking and maintenance; ingestion may also support **PDF** and other document types as the pipeline evolves.
- **Admin & analytics:** a **classic relational database** backs **administrator accounts**, **sign-in** to a protected area, and access to **usage statistics** for the chatbot.

## Chat UI & API

### UI (English)

- **Component:** `frontend/components/Chat.tsx` — keeps message state, scrolls the thread, `POST`s the full history each turn.
- **Styling:** `frontend/components/Chat.module.css`.
- **Health badge:** `frontend/app/page.tsx` calls `GET /api/backend/health` once on load.

### HTTP — `POST /api/v1/chat`

Proxied from the browser as:

`POST /api/backend/api/v1/chat` → FastAPI `POST http://backend:8000/api/v1/chat`

**Request body (`application/json`):**

| Field | Type | Rules |
|--------|------|--------|
| `messages` | array | Min length `1`. Each item: `role` ∈ `user` \| `assistant` \| `system`, `content` non-empty string (max 32k chars). |
| **Contract** | | The **last** message **must** be `role: "user"` (the new user turn). |

**Example:**

```json
{
  "messages": [
    { "role": "user", "content": "Bonjour" }
  ]
}
```

**Response `200`:**

```json
{ "reply": "…assistant text…" }
```

**Current behaviour:** the backend **embeds** the last user message (`mistral-embed`), runs a **cosine nearest-neighbour** search on `document_chunks` (pgvector), injects the top `RAG_TOP_K` snippets into the system prompt, then calls **Mistral chat** (`MISTRAL_CHAT_MODEL`, default `mistral-small-latest`). If `MISTRAL_API_KEY` is missing, the API returns **`503`**. If Mistral or Postgres fails, **`502`** with a `detail` string.

**Indexing (`make dev-data`):** runs `python -m app.ingest` in a one-off backend container. It reads every `*.md` under `DATA_DIR` (Compose mounts **`./data` → `/data`**), splits text into overlapping chunks, calls Mistral embeddings, and replaces rows per file (`DELETE` by `source_path` then `INSERT`). Requires the database service to be reachable (start the stack or at least `db`).

**Errors:** `422` for validation (e.g. last message not `user`, empty `messages`). Error body follows FastAPI’s `{ "detail": … }` shape.

**OpenAPI:** `http://localhost:8000/docs` (or your host on port `8000`) lists `POST /api/v1/chat` and schemas.

## Project structure

| Path | Role |
|------|------|
| `frontend/app/` | Next.js App Router (`page.tsx`, layout, styles) |
| `frontend/components/` | `Chat` UI |
| `backend/app/main.py` | FastAPI app, CORS, lifespan (DDL) |
| `backend/app/routers/chat.py` | Chat endpoint |
| `backend/app/schemas/chat.py` | Pydantic models for chat |
| `backend/app/rag_service.py` | Chunking, retrieval, ingest pipeline |
| `backend/app/mistral_service.py` | Mistral embeddings + chat wrappers |
| `backend/app/ingest.py` | CLI: `python -m app.ingest` |
| `backend/app/db_util.py` | Postgres + pgvector helpers |
| `backend/app/settings.py` | Environment-driven settings |
| `backend/db/init.sql` | `vector` extension + `document_chunks` on first DB init |
| `data/` | Markdown sources ingested by `make dev-data` |
