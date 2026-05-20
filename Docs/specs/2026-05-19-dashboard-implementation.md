# Admin Dashboard — Design Spec

**Issue:** [#13 — Admin Dashboard](https://github.com/Club-IA-plus/mjc-chatbot/issues/13)  
**Date:** 2026-05-19  
**Status:** Implemented

---

## Overview

A password-protected admin dashboard at `/dashboard` for MJC staff and administrators. Displays usage statistics, visualises message trends, tracks RAG knowledge source usage, and lets admins manage user accounts.

Access is role-gated: `staff` can view all stats; only `admin` can manage users.

---

## Tech stack

| Layer | Technology |
|---|---|
| Auth | Auth.js v5 (Credentials provider), HS256 JWT (jose) |
| Frontend framework | Next.js 16 App Router — server components for data fetching, client components only where interactivity is needed |
| Charts | Recharts (LineChart, BarChart, custom CSS heatmap) |
| Backend | FastAPI + psycopg3, PostgreSQL `PERCENTILE_CONT`, `UNNEST` |
| Service-to-service auth | Short-lived HS256 JWT minted with `jose`, verified with PyJWT |
| Styles | CSS Modules throughout — no global class leakage |

---

## Architecture

```
Browser → Next.js App Router (/dashboard/*)
           ├── Server components: fetch data via adminFetch() → FastAPI /api/v1/admin/*
           │   └── adminFetch mints a 60 s HS256 JWT (jose) signed with NEXTAUTH_SECRET
           │       FastAPI verifies it with PyJWT + require_role()
           └── Client components (AddUserModal, UserTable): POST/PATCH/DELETE
               → Next.js Route Handlers (/api/admin/users, /api/admin/users/[id])
               → Route handlers call adminFetch() server-side (session-guarded)
               → FastAPI
```

Client components **cannot** call FastAPI directly — they have no Authorization header. All mutations go through Next.js Route Handlers, which attach the service JWT.

---

## Routes

| Route | Access | Description |
|---|---|---|
| `/dashboard/login` | Public | Credentials form — Auth.js sign-in |
| `/dashboard` | staff + admin | Stats overview, charts, heatmap |
| `/dashboard/users` | admin only | User table — add, change role, soft-delete |

Route protection is enforced in `proxy.ts` (not `middleware.ts` — Next.js 16 parse errors). Unauthenticated requests are redirected to `/dashboard/login`. Non-admins attempting `/dashboard/users` are redirected to `/dashboard`.

---

## Key files

### Backend

| File | Purpose |
|---|---|
| `app/routers/admin.py` | All `/api/v1/admin/*` endpoints — stats, user management, internal auth verify |
| `app/schemas/admin.py` | Pydantic v2 models — `UserCreate` uses `EmailStr` + `Field(min_length=8)` |
| `app/auth.py` | `bcrypt` password hashing, HS256 JWT decode, `require_role()` FastAPI dependency |
| `app/db_util.py` | `ensure_chat_logs_columns()` — idempotent `ALTER TABLE ADD COLUMN IF NOT EXISTS` for `retrieved_sources` and dropping the redundant `duration_ms` column |

### Frontend

| File | Purpose |
|---|---|
| `auth.ts` | Auth.js v5 Credentials provider — calls FastAPI `/internal/auth/verify` |
| `proxy.ts` | Route protection (replaces `middleware.ts` which causes parse errors in Next.js 16) |
| `lib/admin-api.ts` | `adminFetch<T>()` — mints 60 s JWT, calls FastAPI, throws `{ status }` on error |
| `lib/types.ts` | Single source of truth for all shared TypeScript interfaces |
| `lib/chart-constants.ts` | Shared Recharts tooltip style (`TOOLTIP_STYLE`) |
| `app/api/admin/users/route.ts` | Route Handler for `POST /api/admin/users` |
| `app/api/admin/users/[id]/route.ts` | Route Handler for `PATCH` and `DELETE` on a user |
| `app/dashboard/page.tsx` | Server component — fetches 5 endpoints in parallel, renders the full dashboard |
| `app/dashboard/layout.tsx` | Server component — nav with sign-out action; hides nav when no session (login page case) |

### Dashboard components

| Component | Type | Description |
|---|---|---|
| `StatCard` | Server | Single metric tile |
| `DailyTrendChart` | Client | Recharts LineChart — messages per day, last 30 days |
| `ActivityHeatmap` | Server | 7×24 CSS grid — activity by weekday × hour, blue intensity |
| `TopSourcesPanel` | Server | Table of top RAG source files by hit count |
| `ApiUsagePanel` | Server | Table of token usage and cost by model |
| `UserTable` | Client | User list with inline role change and soft-delete |
| `AddUserModal` | Client | Overlay form to create a new user |

---

## Database

New column added to `chat_logs`:

```sql
ALTER TABLE chat_logs ADD COLUMN IF NOT EXISTS retrieved_sources TEXT[];
```

Applied idempotently at startup via `ensure_chat_logs_columns()`. The `duration_ms` column (redundant duplicate of `latency_ms`) is dropped via the same migration.

The RAG pipeline (`rag_service.py`) populates `retrieved_sources` on every turn. The `stats/top-sources` endpoint uses `UNNEST(retrieved_sources)` to aggregate hit counts per source file.

---

## Stats endpoints

All require a valid Bearer JWT, minimum role `staff`.

| Endpoint | Description |
|---|---|
| `GET /stats/overview` | `total_sessions`, `total_messages`, `avg_latency_ms`, `p95_latency_ms`, `total_cost_eur`, `avg_messages_per_session`, `cost_per_message` |
| `GET /stats/daily` | Messages per day — last 30 days |
| `GET /stats/hourly` | Messages by hour of day (0–23) |
| `GET /stats/heatmap` | Messages by (PostgreSQL DOW, hour) for the 7×24 heatmap |
| `GET /stats/top-sources` | Top 10 RAG source files by UNNEST hit count |
| `GET /stats/api-usage` | Token counts, cost, avg latency grouped by model |

---

## Authentication flow

1. User POSTs email + password to `/dashboard/login`
2. Auth.js Credentials provider calls `POST /api/v1/admin/internal/auth/verify` with `X-Service-Token: <NEXTAUTH_SECRET>` (constant-time comparison in FastAPI)
3. On success FastAPI returns `{ id, email, role }` — Auth.js stores this in a signed JWT session cookie
4. Server components call `adminFetch()` which reads the session, mints a 60 s HS256 JWT, and attaches it as `Authorization: Bearer`
5. FastAPI verifies the JWT with PyJWT, checks role with `require_role()`

The `NEXTAUTH_SECRET` env var is shared between frontend and backend and must match exactly.

---

## Things to keep in mind

**`proxy.ts` not `middleware.ts`** — Next.js 16 throws a parse error on `middleware.ts` due to the edge runtime. Route protection lives in `proxy.ts`. Clear `.next/` cache if switching between the two.

**Frontend Docker image is baked at build time** — `BACKEND_INTERNAL_URL` and all Next.js rewrites are resolved at build, not runtime. Any frontend source change requires `make dev-build`, not just a restart.

**Client components cannot call FastAPI directly** — they have no way to attach a service JWT. All mutations from client components must go through a Next.js Route Handler (`/api/admin/*`), which uses `adminFetch()` server-side.

**`[] or None` is `None` in Python** — when storing `TEXT[]` in psycopg3, pass the list directly (`result.retrieved_sources`). `result.retrieved_sources or None` would store `NULL` for empty lists, breaking the `UNNEST` aggregate.

**Soft delete, not hard delete** — users are never removed from the DB. `deleted_at IS NULL` must be on every `SELECT` and `COUNT` query in `list_users`. The delete button is disabled in the UI for already-deleted rows.

**`email-validator` is a required pip dependency** — `EmailStr` in Pydantic v2 requires `pip install email-validator` (listed in `requirements.txt`). Missing it causes a startup crash.

**`jose` is a direct dependency** — `lib/admin-api.ts` imports from `jose` to mint service JWTs. It is a transitive dependency of `next-auth` but must be listed explicitly in `package.json` to prevent version surprises.
