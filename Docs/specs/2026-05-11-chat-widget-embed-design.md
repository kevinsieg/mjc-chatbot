# Chat Widget Embed — Design Spec

**Issue:** [#8 — Export chat widget for external websites (iframe/CDN)](https://github.com/Club-IA-plus/mjc-chatbot/issues/8)  
**Date:** 2026-05-11  
**Status:** Approved

---

## Overview

Embed the MJC chatbot as a floating bubble widget on mjcfecamp.org. The chatbot is hosted on a separate domain. Clicking the bubble opens a chat panel inside an iframe.

---

## Approach: Script tag + iframe (hybrid)

Chosen over Web Component and React bundle for the following reasons:

- No CORS changes — API calls happen inside the iframe on the chatbot domain
- One codebase, one deploy pipeline — `Chat.tsx` reused as-is
- `frame-ancestors` CSP restricts the iframe to mjcfecamp.org only
- No separate build tooling required

**Host site integration (one line):**

```html
<script src="https://chatbot.mjcfecamp.org/widget.js"></script>
```

---

## Architecture

```
mjcfecamp.org
  └── loads /widget.js (static, served from Next.js /public)
  └── widget.js injects Goëllan bubble button (fixed, bottom-right)
  └── click → creates <iframe src="https://chatbot.mjcfecamp.org/embed">
                └── Next.js serves /embed route
                └── Chat.tsx POSTs to /api/backend/api/v1/chat
                    └── Next.js rewrite → FastAPI (unchanged)
```

---

## New files

| File | Purpose |
|---|---|
| `frontend/public/widget.js` | Vanilla JS — injects bubble, manages iframe lifecycle |
| `frontend/app/embed/page.tsx` | Renders `<Chat />` with health check and error fallback |
| `frontend/app/embed/page.module.css` | Panel-specific styles |

**Files not modified:** `Chat.tsx`, `page.tsx`, `HealthBadge.tsx`, FastAPI backend.

---

## Data flow

1. Host page loads `widget.js`
2. Script injects one `<button>` (bubble) into host DOM — no iframe yet
3. First bubble click: create `<iframe src="/embed">`, append to `<body>`, show
4. Subsequent clicks: toggle iframe `display` — conversation state preserved
5. Inside iframe: `Chat.tsx` operates exactly as today, no changes
6. No `postMessage` required — open/close controlled entirely from the parent bubble

---

## Components

### `widget.js`

~50 lines of vanilla JS, no framework, no dependencies.

Responsibilities:
- Inject bubble `<button>` with Goëllan avatar (`/brand/goellan.png`) into host DOM
- Lazy-create iframe on first click
- Toggle iframe visibility on subsequent clicks
- Apply inline styles (fixed position, z-index, sizing) — no external stylesheet

### `/embed` layout (`layout.tsx`)

Minimal — strips global nav, header, and footer. Only renders `{children}`.

### `/embed` page (`page.tsx`)

- Health-checks `GET /api/backend/health` on mount
- If healthy: renders `<Chat />`
- If unhealthy: renders error fallback (Goëllan avatar + "Service temporairement indisponible. Veuillez réessayer plus tard.")
- Mid-conversation API errors are already handled by `Chat.tsx` — no changes needed

---

## Security

| Concern | Mitigation |
|---|---|
| Unauthorized sites embedding the iframe | `Content-Security-Policy: frame-ancestors https://mjcfecamp.org` on `/embed` route, set in `next.config.mjs` |
| Direct API abuse by bots | Out of scope for this feature — handled by Cloudflare rate limiting + Turnstile (separate roadmap item) |

The `frame-ancestors` header is set via `next.config.mjs` custom headers, scoped to the `/embed` path only.

---

## Error states

| Scenario | Behaviour |
|---|---|
| API down on widget open | Embed page shows error fallback (Goëllan + message) |
| API fails mid-conversation | `Chat.tsx` existing error handling — rolls back message, shows inline error |
| iframe network failure | Browser renders its default error page inside the iframe; bubble remains accessible for retry |

---

## Out of scope

- Client token / access control per embedding site
- Cloudflare Turnstile bot prevention
- Per-client rate limiting
- Widget theming via URL params
- Admin dashboard for managing embed clients

These are follow-up features that plug in cleanly on top of this foundation.

---

## Integration

Paste before `</body>` on any authorised site:

```html
<script src="https://chatbot.mjcfecamp.org/widget.js"></script>
```

To authorise a new domain, add it to `EMBED_FRAME_ANCESTORS` (space-separated) and rebuild:

```
EMBED_FRAME_ANCESTORS=https://mjcfecamp.org https://autre-site.fr
```

A local test page is available at `http://localhost:3000/widget-test.html` once the dev stack is running.
