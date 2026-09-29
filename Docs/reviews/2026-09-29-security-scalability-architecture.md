# mjc-chatbot review: security, scalability, architecture

Reviewed: `kevinsieg/mjc-chatbot` `main` @ `b911ee2` (fast-forwarded from upstream `Club-IA-plus/mjc-chatbot` `main`, 33 commits, no divergence). Date: 2026-09-29.

Stack: Next.js 16 + Auth.js v5 beta (frontend, dashboard, widget) → FastAPI (sync) → Postgres 16 + pgvector, Mistral for embeddings + chat. ~2k LOC.

Severity: **C** critical · **H** high · **M** medium · **L** low.

---

## 1. Security

### C1. Public chat endpoint is an open, unmetered proxy to the Mistral key
`backend/app/routers/chat.py:103`, `backend/app/schemas/chat.py`
- `POST /api/v1/chat` needs no auth and has no rate limit, quota, or request-size cap.
- The client can set `system_prompt` (up to 8000 chars) and send the **entire history**, including forged `assistant` turns. Anyone can replace the MJC persona and use the service as a free general-purpose LLM on the MJC's bill.
- `messages` has no max count; each message may be 32,000 chars. One request can carry megabytes → large token bills and slow calls.
- **Fix:** drop `system_prompt` from the public API (keep it for an authenticated admin preview endpoint only); cap `messages` (e.g. last 10 turns, 2,000 chars each, total body ≤ 64 KB); add per-IP rate limiting (e.g. `slowapi` or at the reverse proxy); set a Mistral monthly spend cap in their console as a backstop.

### C2. Frontend dependencies have known critical CVEs
`frontend/package-lock.json` (`npm audit --omit=dev`: 3 critical, 3 high, 1 moderate)
- `next 16.2.5`: middleware/proxy bypass advisories. Dashboard auth gating relies on `proxy.ts`. Data is still protected server-side (`adminFetch` → backend JWT), so impact is limited today, but it is one refactor away from exposure.
- `next-auth 5.0.0-beta.31` / `@auth/core`: "configuration errors can cause auth checks to fail open", email normalization bypass, `getToken()` crash.
- `sharp`, `postcss`, `nanoid`: libvips/libheif, XSS, DoS advisories.
- **Fix:** `npm audit fix`, bump `next` and `next-auth` to patched versions, add Dependabot. Backend `pip-audit` is clean.

### H1. Dev admin credentials are shipped enabled, and reset on every boot
`.env.example:34-35`, `backend/app/main.py:20-23`, `backend/app/admin_cli.py:10`
- `.env.example` pre-fills `SEED_ADMIN_EMAIL=admin@test.com` / `SEED_ADMIN_PASSWORD=changeme-dev-only`. Copying it to the VPS (the file already references `162.19.241.44`) creates a publicly known admin.
- The seed runs on **every startup** and `ON CONFLICT` resets the password, forces `role='admin'`, and clears `deleted_at`. Deleting or rotating that account doesn't stick.
- **Fix:** leave both empty in `.env.example`; seed only if the user doesn't exist (`ON CONFLICT DO NOTHING`); refuse to seed when an env like `APP_ENV=production` is set.

### H2. Postgres and the raw API are published on all interfaces
`docker-compose.yml:7-8, 20-21`
- `5432:5432` with default `mjc/mjc` credentials, and `8000:8000` for the backend. Docker's port publishing bypasses `ufw`, so on the VPS both are internet-facing unless the provider firewall blocks them.
- Port 8000 also exposes FastAPI `/docs` and `/openapi.json`, and lets clients skip anything added at the frontend layer.
- **Fix:** remove the `ports:` for `db` (or bind `127.0.0.1:5432:5432`), bind backend to `127.0.0.1` or drop its port (frontend reaches it on the compose network), set a strong `POSTGRES_PASSWORD`, disable docs in prod (`FastAPI(docs_url=None, redoc_url=None, openapi_url=None)`).

### H3. One secret does three jobs
`frontend/auth.ts:22,77`, `frontend/lib/admin-api.ts:5`, `backend/app/auth.py:20`, `backend/app/routers/admin.py:38,58`
- `NEXTAUTH_SECRET` is (a) the Auth.js session key, (b) sent **verbatim** as the `x-service-token` header on internal calls, and (c) the HS256 key for backend service JWTs.
- Any leak (a log line, a proxy capturing headers, the Docker build layer in M1) lets an attacker mint admin JWTs for the backend and forge sessions.
- **Fix:** separate `BACKEND_SERVICE_SECRET` for internal calls and JWT signing; stop sending a secret as a bearer value (sign a short-lived JWT for `/internal/*` too, as `adminFetch` already does); add `aud`/`iss` claims and check them.

### H4. No brute-force protection on login
`backend/app/routers/admin.py:32`, `frontend/auth.ts:13`
- Credentials login has no rate limit, lockout, or delay. The password policy is only `min_length=8`.
- Unknown emails return without running bcrypt, so response timing reveals which emails exist.
- **Fix:** per-IP + per-email rate limit on the Auth.js callback/credentials route; run a dummy bcrypt verify on unknown users; consider longer minimum or a breached-password check.

### M1. `NEXTAUTH_SECRET` passed as a Docker build arg
`docker-compose.yml:32`, `frontend/Dockerfile:5,8`
- Build args and `ENV` are recorded in the builder stage's layer history and build cache. The final stage doesn't carry it, but the cache on the VPS/CI does.
- **Fix:** provide the secret only at runtime; if `next build` needs it because `auth.ts` reads it at import, make that read lazy or use a build-time dummy.

### M2. Plain HTTP in production
`.env.example:16` (`http://162.19.241.44:3000`), `frontend/auth.ts:103` (`trustHost: true`)
- Session cookies and admin passwords travel in clear text; cookies aren't `Secure`.
- **Fix:** put Caddy/Traefik/nginx in front with TLS on a real domain; expose only 443.

### M3. Internal error text leaks to clients
`backend/app/routers/chat.py:47-48`
- Any `RuntimeError` message is returned as `detail`. Some include `repr()` of Mistral responses (`mistral_service.py:29,84`) or file paths (`system_prompt.py:21`). The chat UI shows `detail` to end users (`Chat.tsx:160`).
- **Fix:** log the detail server-side, return a generic message.

### M4. Public home page ships admin-grade tools
`frontend/app/page.tsx`, `components/HomeChatPanel.tsx`, `components/SystemPromptEditor.tsx`
- `/` is outside the `proxy.ts` matcher, so any visitor gets the system-prompt editor and full knowledge-base viewer. Together with C1 this advertises the prompt override.
- **Fix:** move both behind `/dashboard`, or confirm `/` is never deployed publicly and only `/embed` is.

### L1. Account lifecycle gaps
`backend/app/routers/admin.py:286-337`
- An admin can delete or demote themselves and the last admin; no guard.
- Password change or deletion doesn't revoke sessions; revocation lags up to 5 min (`auth.ts:68`). Acceptable, but document it.
- `admin_audit_log` is created but never written. Either write to it in create/patch/delete, or drop it.
- Soft delete + `UNIQUE(email)` means a deleted user's email can never be re-added (409).

### L2. Other hardening
- Containers run as root (both Dockerfiles). Add a non-root `USER`.
- `/embed` defaults to `frame-ancestors *` (`next.config.mjs:4`). Fine for a public widget; set `EMBED_FRAME_ANCESTORS` to the MJC domains once known.
- `passlib` is unmaintained and needs the `bcrypt==4.0.1` pin; consider `bcrypt` directly or `argon2-cffi`. bcrypt silently truncates > 72 bytes.
- Test/dev packages (`pytest`, `httpx`) are in the production `requirements.txt`.

Positives: parameterized SQL everywhere (the one f-string in `patch_user` only interpolates whitelisted column names); `hmac.compare_digest` for the token; JWT `exp` required and algorithm pinned; server-side role checks on every admin route, not just in the UI; React renders replies as text (no `dangerouslySetInnerHTML`); chat content is not persisted, only metadata, with a retention job.

---

## 2. Scalability and performance

Current load (one youth centre, 20 KB corpus) is tiny, so none of this bites today. These are the limits you'll hit first, in order.

### S1. Sync endpoints block threads on slow LLM calls
`routers/chat.py:104`, `mistral_service.py`
- `post_chat` is `def`, so it runs in Starlette's threadpool (40 threads by default), and each request holds a thread for embedding + completion (seconds). A single uvicorn worker tops out around 40 concurrent chats; request 41 queues.
- No timeout on Mistral calls: a hung upstream pins threads indefinitely. No retry/backoff on 429 even though the code knows 429 is common.
- **Fix:** `async def` + `mistralai`'s async client (or `httpx.AsyncClient`), explicit timeouts (~30 s), retry with jitter on 429/5xx; run `uvicorn --workers N` or gunicorn.

### S2. New DB connection and new Mistral client per call
`db_util.py:9`, `mistral_service.py:48,73`
- Each request opens a fresh Postgres connection (TCP + auth) and a fresh Mistral HTTP client (TLS handshake), twice per chat turn. The dashboard fires 5 parallel queries → 5 new connections per page view.
- Postgres defaults to 100 connections; enough workers × threads will exhaust it.
- **Fix:** `psycopg_pool.ConnectionPool` created in lifespan; one module-level Mistral client reused.

### S3. Retrieval has no vector index
`db_util.py:25`, `rag_service.py:34`
- `ORDER BY embedding <=> q` is a full scan. Fine for hundreds of chunks; add `CREATE INDEX ... USING hnsw (embedding vector_cosine_ops)` when the corpus grows past ~10k chunks.

### S4. In-process scheduler duplicates with replicas
`scheduler.py`
- APScheduler runs inside every worker/replica, so the purge runs N times. Harmless now (idempotent DELETE), but it doesn't scale to heavier jobs. Move to a cron container or a Postgres advisory lock.

### S5. Dashboard stats scan all history on every load
`routers/admin.py:74-229`
- `COUNT(DISTINCT)`, `PERCENTILE_CONT`, `UNNEST` across the full table, uncached. Fine to ~1M rows (bounded by 365-day retention). Later: cache for 60 s or roll up daily aggregates.

### S6. Streaming
- Non-streaming completions mean the user sees nothing for the whole generation. SSE streaming would cut perceived latency and free the UI sooner; pair it with S1's async rewrite.

---

## 3. Architecture and correctness

### A1. Analytics are wrong today
- The frontend never sends `session_id` or `origin` (`Chat.tsx:147-154`), so the backend generates a new UUID per message (`chat.py:59`). **Every message counts as a new session**: "Sessions totales" = messages, "Msgs / session" = 1.0, origin always null.
- The default model `open-mistral-nemo` isn't in `get_model_cost_map()` (`settings.py:84`), so **all costs are recorded as €0**. Prices are also hardcoded and averaged prompt/completion.
- A malformed `session_id` fails the `::uuid` cast and the row is silently dropped (`chat.py:80`, `except Exception: pass` with no logging).
- Stats group by UTC (`DATE(timestamp)`, `EXTRACT(HOUR ...)`), so heatmap hours are 1–2 h off for Fécamp. Use `timestamp AT TIME ZONE 'Europe/Paris'`.
- **Fix:** generate a session UUID in the widget (sessionStorage) and send it with `origin`; validate `session_id` as `UUID` in the schema; add the actual model's prices (separate prompt/completion); log failures.

### A2. RAG quality limits
- Only the last user message is embedded (`rag_service.py:83`). Follow-ups like "et le samedi ?" retrieve poorly. Condense history into a standalone query, or embed the last 2–3 turns.
- Character-based chunking (1200/200) cuts mid-word and mid-table. Markdown-heading-aware splitting would fit these activity/calendar files better.
- Ingest never removes chunks for files deleted from `data/` (`rag_service.py:113`), so stale answers persist. Delete `source_path NOT IN (current files)` at the end of ingest.
- Ingest is manual (`make dev-data`); nothing checks the index matches `data/` at startup.
- Retrieved context goes in the system message with no delimiting against injection. Low risk while `data/` is curated, but keep it in mind if sources ever come from outside.

### A3. Schema management
- DDL lives in three places: `db/init.sql`, `ensure_*` functions run on every boot, and ad-hoc `ALTER ... IF NOT EXISTS` / `DROP COLUMN IF EXISTS`. `init.sql` hardcodes `vector(1024)` while code reads `MISTRAL_EMBED_DIM`.
- Every replica runs DDL at startup concurrently.
- **Fix:** adopt Alembic (or a single versioned `migrations/` folder) run as a one-shot job; drop the table creation from `init.sql` beyond `CREATE EXTENSION`.

### A4. Layering
- Routers hold raw SQL and business logic (`admin.py` is 337 lines of SQL + mapping). A thin repository/service layer would make the stats queries testable without HTTP and simplify the async migration.
- Settings are scattered `os.getenv` getters evaluated per call; `pydantic-settings` would validate once at startup and fail fast on bad config.
- Two auth paths coexist (service-token header vs. service JWT). Unify on one (see H3).
- The `/api/backend/:path*` rewrite (`next.config.mjs:24`) forwards **every** backend route, including `/internal/*` and `/docs`. Allow-list only `/health`, `/api/v1/chat`, and the public read endpoints.

### A5. Delivery and ops
- No CI (only a PR template). Add a workflow: backend pytest against a Postgres service container, `next build`, `npm audit`, `pip-audit`.
- Tests run against whatever `DATABASE_URL` is in `.env` and issue `DELETE FROM users` (`tests/test_admin_users.py`). Point them at a dedicated test DB and refuse to run otherwise.
- Logging is mixed `print` and `logging`; no request IDs, no structured logs, no metrics. At minimum: JSON logs with request ID, latency, and Mistral status.
- `/health` doesn't check the DB or Mistral config; add a readiness endpoint that does.
- Frontend image copies the full `node_modules`; use `output: "standalone"` for a ~5× smaller image.
- `tsconfig.tsbuildinfo` is committed; add to `.gitignore`.
- `next-auth` is a beta in production; pin an exact version and track releases.

---

## 4. Suggested order of work

1. C1 (cap and rate-limit chat, remove public `system_prompt`) and set a Mistral spend limit.
2. H1 + H2 (seed creds, closed ports, strong DB password), M2 (TLS).
3. C2 (`npm audit fix`, bump next / next-auth).
4. H3 + H4 (split secrets, login rate limit).
5. A1 (fix analytics so the dashboard means something).
6. S1 + S2 (async, pooling, timeouts) before any real traffic growth.
7. A3 + A5 (migrations, CI), then the rest.

---

## Assumptions
- Target deployment is the single VPS referenced in `.env.example` via `docker compose`, with no reverse proxy or firewall config in the repo; if a provider firewall or TLS proxy exists outside the repo, H2 and M2 drop in severity.
- `/` (home page with prompt editor) is a demo surface; `/embed` + `widget.js` is the public product.
- Review covers `main` only; upstream feature branches (`develop`, `feat/9-*`, `feat-23-*`) were not reviewed.
- Dependency findings come from `npm audit` and `pip-audit` on 2026-09-29; the app was not run and no live exploitation was attempted.
