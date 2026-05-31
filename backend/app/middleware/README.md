# Rate Limiting Middleware

Per-IP sliding-window rate limiter. Second defense layer after Traefik.

## How it works

Every request passes through `RateLimitMiddleware`. It extracts the client IP from `X-Forwarded-For` (set by Traefik), counts requests within the last 60 seconds, and returns 429 if the count exceeds 10. Health checks (`/health`) are exempt.

Default limits: **10 requests / 60 seconds per IP**.

## Running tests

```bash
cd backend
DATABASE_URL=postgresql://mjc:mjc@127.0.0.1:5432/mjcbot .venv/bin/pytest tests/test_rate_limit_middleware.py -v
```

Tests cover: under-limit pass-through, over-limit blocking, per-IP isolation, and window expiry.

## Manual verification

**Traefik layer** (via Docker stack on port 80):

```bash
# Send 25 rapid requests — expect 429s after the burst (default burst=20)
for i in (seq 1 25)
    curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost/api/backend/api/v1/chat \
      -H "Content-Type: application/json" \
      -d '{"messages":[{"role":"user","content":"test"}]}'
end
```

**FastAPI layer** (direct on port 8000, bypassing Traefik):

```bash
for i in (seq 1 12)
    curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8000/api/v1/chat \
      -H "Content-Type: application/json" \
      -d '{"messages":[{"role":"user","content":"test"}]}'
end
```

Expect 429 after the 10th request.

## Tuning

Limits are set in `backend/app/main.py`:

```python
app.add_middleware(RateLimitMiddleware, max_calls=10, period=60)
```

Traefik limits are set via env vars (see `.env.example`):

```
TRAEFIK_RATE_LIMIT_AVERAGE=10
TRAEFIK_RATE_LIMIT_BURST=20
```

## Code review checklist

- [ ] `rate_limit.py` — sliding window logic, IP extraction, `/health` exemption
- [ ] `test_rate_limit_middleware.py` — 4 tests, monkeypatch of `time` for window expiry
- [ ] `docker-compose.yml` — Traefik service, `chat-api` router with rate limit labels
- [ ] `Docs/ops/cloudflare-setup.md` — iptables script safety (SSH first, curl guard, IPv6)
