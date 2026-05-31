# Rate Limiting — Traefik + Cloudflare Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Protect the chatbot API from bot abuse and excessive usage with layered rate limiting across Cloudflare, Traefik, and FastAPI.

**Architecture:** Three-layer defense — Cloudflare hides the origin IP and blocks known bots at the edge; Traefik enforces per-IP rate limits at the Docker network boundary; a FastAPI middleware enforces per-IP limits at the application level as a backstop in case traffic reaches port 8000 directly. No Redis required for a single-instance deployment.

**Tech Stack:** Traefik v3, Cloudflare (free tier), FastAPI middleware (stdlib only — `collections`, `time`)

---

## Scope

This plan covers:
1. Adding Traefik as a reverse proxy in `docker-compose.yml`
2. Rate limiting the `/api/v1/chat` endpoint via Traefik middleware
3. Locking down direct port exposure (backend + frontend stop binding to host)
4. In-process FastAPI rate limiting middleware as a second layer
5. Cloudflare DNS + Bot Fight Mode setup (manual steps, documented here)
6. OVH firewall rules to only accept traffic from Cloudflare IPs (manual steps, documented here)

Redis caching of Mistral embeddings is **out of scope** — tracked separately.

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `docker-compose.yml` | Add Traefik service, remove direct port bindings from backend/frontend, add Traefik labels |
| Modify | `.env.example` | Add `TRAEFIK_RATE_LIMIT_AVERAGE`, `TRAEFIK_RATE_LIMIT_BURST` |
| Create | `backend/app/middleware/rate_limit.py` | In-process per-IP sliding-window rate limiter |
| Modify | `backend/app/main.py` | Register rate limit middleware |
| Create | `backend/tests/test_rate_limit_middleware.py` | Unit tests for the middleware |
| Create | `Docs/ops/cloudflare-setup.md` | Manual Cloudflare + OVH firewall runbook |

---

## Task 1: Add Traefik to docker-compose.yml

**Files:**
- Modify: `docker-compose.yml`
- Modify: `.env.example`

- [ ] **Step 1: Add Traefik service and labels to docker-compose.yml**

Replace the current `docker-compose.yml` with the following. Key changes:
- Add `traefik` service on port 80 (and 443 when TLS is added later)
- Remove `ports` from `backend` (port 8000 must not be exposed to the host in production)
- Remove `ports` from `frontend` — Traefik exposes it via labels
- Add Traefik labels to `frontend` for routing and rate limiting
- Keep `db` port binding for local dev (Postgres is not proxied)

```yaml
services:
  traefik:
    image: traefik:v3
    command:
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--log.level=INFO"
    ports:
      - "80:80"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    restart: unless-stopped

  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-mjc}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-mjc}
      POSTGRES_DB: ${POSTGRES_DB:-mjcbot}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./backend/db/init.sql:/docker-entrypoint-initdb.d/01-pgvector.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-mjc} -d ${POSTGRES_DB:-mjcbot}"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    # No host port binding — only reachable via Docker network
    environment:
      DATABASE_URL: ${DATABASE_URL:-postgresql://mjc:mjc@db:5432/mjcbot}
      MISTRAL_API_KEY: ${MISTRAL_API_KEY:-}
      MISTRAL_CHAT_MODEL: ${MISTRAL_CHAT_MODEL:-mistral-small-latest}
      MISTRAL_EMBED_MODEL: ${MISTRAL_EMBED_MODEL:-mistral-embed}
      RAG_TOP_K: ${RAG_TOP_K:-5}
      MISTRAL_EMBED_DIM: ${MISTRAL_EMBED_DIM:-1024}
      DATA_DIR: /data
    volumes:
      - ./data:/data:ro
    depends_on:
      db:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
      args:
        BACKEND_INTERNAL_URL: http://backend:8000
        NEXT_PUBLIC_WIDGET_BASE_URL: ${NEXT_PUBLIC_WIDGET_BASE_URL:-http://localhost:3000}
    # No host port binding — Traefik handles external traffic
    depends_on:
      - backend
    labels:
      - "traefik.enable=true"
      # Route all traffic to the frontend on port 3000
      - "traefik.http.routers.frontend.rule=PathPrefix(`/`)"
      - "traefik.http.routers.frontend.entrypoints=web"
      - "traefik.http.services.frontend.loadbalancer.server.port=3000"
      # Rate limit middleware: 10 requests/minute average, burst of 20
      - "traefik.http.middlewares.chat-limit.ratelimit.average=${TRAEFIK_RATE_LIMIT_AVERAGE:-10}"
      - "traefik.http.middlewares.chat-limit.ratelimit.burst=${TRAEFIK_RATE_LIMIT_BURST:-20}"
      - "traefik.http.middlewares.chat-limit.ratelimit.period=1m"
      - "traefik.http.routers.frontend.middlewares=chat-limit"

volumes:
  pgdata:
```

- [ ] **Step 2: Add rate limit env vars to .env.example**

Add to `.env.example`:

```
# Traefik rate limiting (requests per minute per IP)
TRAEFIK_RATE_LIMIT_AVERAGE=10
TRAEFIK_RATE_LIMIT_BURST=20
```

- [ ] **Step 3: Verify the stack starts cleanly**

```bash
make dev-build
make dev-run
```

Expected: Traefik, db, backend, and frontend all show as healthy/running in `docker compose ps`. The app is accessible at `http://localhost:80` (not 3000).

- [ ] **Step 4: Verify rate limiting is active**

Send 25 rapid requests to the chat endpoint and confirm 429s appear after the burst:

```bash
for i in (seq 1 25)
    curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost/api/backend/api/v1/chat \
      -H "Content-Type: application/json" \
      -d '{"messages":[{"role":"user","content":"test"}]}'
end
```

Expected: first ~20 return 200 (or 422/503 from app logic), remaining return 429.

- [ ] **Step 5: Update local backend dev docs**

The `dev-backend-local` make target bypasses Traefik (API runs on host port 8000 directly). This is intentional for local development. Verify it still works:

```bash
make dev-kill
make dev-db-d
make dev-backend-local
```

Test with:
```bash
curl -s -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Bonjour"]}' | python3 -m json.tool
```

- [ ] **Step 6: Commit**

```bash
git add docker-compose.yml .env.example
git commit -m "feat: add Traefik reverse proxy with rate limiting middleware"
```

---

## Task 2: FastAPI in-process rate limiting middleware

This is the second layer. It catches requests that bypass Traefik (direct access to port 8000, internal services, misconfiguration). Uses only stdlib — no new dependencies.

**Files:**
- Create: `backend/app/middleware/rate_limit.py`
- Create: `backend/app/middleware/__init__.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_rate_limit_middleware.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_rate_limit_middleware.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.middleware.rate_limit import RateLimitMiddleware


def _make_app(max_calls: int = 3, period: int = 60) -> FastAPI:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, max_calls=max_calls, period=period)

    @app.post("/test")
    async def endpoint():
        return {"ok": True}

    return app


def test_allows_requests_under_limit():
    client = TestClient(_make_app(max_calls=3))
    for _ in range(3):
        r = client.post("/test", headers={"x-forwarded-for": "1.2.3.4"})
        assert r.status_code == 200


def test_blocks_requests_over_limit():
    client = TestClient(_make_app(max_calls=3))
    for _ in range(3):
        client.post("/test", headers={"x-forwarded-for": "1.2.3.4"})
    r = client.post("/test", headers={"x-forwarded-for": "1.2.3.4"})
    assert r.status_code == 429


def test_different_ips_tracked_independently():
    client = TestClient(_make_app(max_calls=2))
    for _ in range(2):
        client.post("/test", headers={"x-forwarded-for": "1.1.1.1"})
    # 1.1.1.1 is blocked, 2.2.2.2 is not
    r_blocked = client.post("/test", headers={"x-forwarded-for": "1.1.1.1"})
    r_allowed = client.post("/test", headers={"x-forwarded-for": "2.2.2.2"})
    assert r_blocked.status_code == 429
    assert r_allowed.status_code == 200


def test_window_expiry_allows_again(monkeypatch):
    """After the time window expires, requests are allowed again."""
    import time
    fake_time = 0.0

    monkeypatch.setattr(time, "time", lambda: fake_time)

    client = TestClient(_make_app(max_calls=2, period=60))
    for _ in range(2):
        client.post("/test", headers={"x-forwarded-for": "5.5.5.5"})

    r = client.post("/test", headers={"x-forwarded-for": "5.5.5.5"})
    assert r.status_code == 429

    fake_time = 61.0  # advance past the window
    r = client.post("/test", headers={"x-forwarded-for": "5.5.5.5"})
    assert r.status_code == 200
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
docker compose exec backend pytest backend/tests/test_rate_limit_middleware.py -v
```

Expected: `ImportError` — `app.middleware.rate_limit` does not exist yet.

- [ ] **Step 3: Create the middleware package**

Create `backend/app/middleware/__init__.py` (empty):

```python
```

Create `backend/app/middleware/rate_limit.py`:

```python
from collections import defaultdict
from time import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_calls: int = 10, period: int = 60) -> None:
        super().__init__(app)
        self.max_calls = max_calls
        self.period = period
        self._calls: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: Callable):
        ip = self._get_client_ip(request)
        now = time()
        window = self._calls[ip]
        self._calls[ip] = [t for t in window if now - t < self.period]
        if len(self._calls[ip]) >= self.max_calls:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
            )
        self._calls[ip].append(now)
        return await call_next(request)
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
docker compose exec backend pytest backend/tests/test_rate_limit_middleware.py -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Register the middleware in main.py**

In `backend/app/main.py`, add after the existing imports and before `app = FastAPI(...)`:

```python
from app.middleware.rate_limit import RateLimitMiddleware
```

And after `app = FastAPI(...)`:

```python
app.add_middleware(RateLimitMiddleware, max_calls=10, period=60)
```

- [ ] **Step 6: Run the full test suite**

```bash
docker compose exec backend pytest backend/tests/ -v
```

Expected: all existing tests pass, 4 new tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend/app/middleware/ backend/tests/test_rate_limit_middleware.py backend/app/main.py
git commit -m "feat: add in-process FastAPI rate limiting middleware"
```

---

## Task 3: Cloudflare + OVH firewall runbook

This is manual infrastructure configuration. Document it so any team member can replicate it.

**Files:**
- Create: `Docs/ops/cloudflare-setup.md`

- [ ] **Step 1: Create the ops runbook**

Create `Docs/ops/cloudflare-setup.md`:

```markdown
# Cloudflare + OVH Firewall Setup

## Prerequisites
- Domain DNS managed in Cloudflare (free account)
- OVH server admin access (firewall rules via OVH Control Panel or `iptables`)

## 1. Cloudflare DNS

1. Log in to Cloudflare → select your domain
2. DNS → Add record:
   - Type: `A`
   - Name: `@` (or `www`)
   - IPv4 address: your OVH server IP
   - **Proxy status: Proxied (orange cloud)** ← required, do not set to DNS-only
3. Verify the record shows "Proxied" (not "DNS only")

## 2. Enable Bot Fight Mode

1. Cloudflare dashboard → Security → Bots
2. Enable **Bot Fight Mode** (free tier)
3. This blocks known bad bots (scrapers, credential stuffers) before they reach your server

## 3. Rate limiting (Cloudflare Pro — optional)

The free tier does not support custom rate limiting rules. Rate limiting is handled by Traefik (see docker-compose.yml). If you upgrade to Pro ($20/mo), you can add a Cloudflare rule:
- Path: `/api/backend/api/v1/chat`
- Threshold: 10 requests / 1 minute per IP
- Action: Block

## 4. Lock OVH firewall to Cloudflare IPs only

This is critical. Without it, attackers can bypass Cloudflare by hitting your OVH IP directly.

Cloudflare publishes its IP ranges at:
- https://www.cloudflare.com/ips-v4
- https://www.cloudflare.com/ips-v6

### Via iptables (run as root on OVH server)

```bash
# Allow SSH first (do not lock yourself out)
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow Cloudflare IPv4 ranges on port 80
for ip in $(curl -s https://www.cloudflare.com/ips-v4); do
  iptables -A INPUT -p tcp --dport 80 -s $ip -j ACCEPT
done

# Drop all other traffic on port 80
iptables -A INPUT -p tcp --dport 80 -j DROP

# Persist rules (Debian/Ubuntu)
apt-get install iptables-persistent -y
netfilter-persistent save
```

### Verify

From a machine NOT behind Cloudflare, try to connect directly:
```bash
curl -v http://<OVH-IP>/
```
Expected: connection refused or timeout (not a response from the app).

From a browser via the domain:
```bash
curl -v http://<your-domain>/
```
Expected: 200 response served through Cloudflare.

## 5. Verify full chain

1. Browser → `https://<your-domain>/` → should load the chatbot UI
2. Send a chat message → should work (200)
3. Send 25 rapid messages → should get 429 from Traefik after the burst
4. Direct IP access `http://<OVH-IP>/` → should be blocked by firewall

## Cloudflare IP ranges (as of 2026-05)

Always fetch fresh from https://www.cloudflare.com/ips-v4 — do not hardcode these in scripts.
```

- [ ] **Step 2: Create the ops directory if it doesn't exist and commit**

```bash
git add Docs/ops/cloudflare-setup.md
git commit -m "docs: add Cloudflare and OVH firewall setup runbook"
```

---

## Acceptance criteria checklist

- [ ] `docker compose ps` shows traefik, db, backend, frontend — all running
- [ ] App accessible at port 80, not 3000 (Traefik is the entry point)
- [ ] 25 rapid requests to `/api/backend/api/v1/chat` triggers 429 after burst
- [ ] Backend port 8000 is not bound to the host in production
- [ ] `pytest backend/tests/` passes (including new rate limit tests)
- [ ] Cloudflare runbook exists at `Docs/ops/cloudflare-setup.md`
- [ ] Local dev workflow (`make dev-backend-local`) still works

---

## Out of scope

- TLS/HTTPS termination in Traefik (separate ticket — add Let's Encrypt acme resolver)
- Redis embedding cache (separate ticket)
- Per-user rate limits (requires auth on the chat endpoint)
