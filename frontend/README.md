# Frontend

## Technology

**Next.js 16 (App Router)** · **TypeScript strict** · **CSS Modules**

Pages are server components by default. `Chat`, `HealthBadge`, and `HomeChatPanel` are `"use client"` — everything else renders on the server, keeping the initial payload small.

Styling is CSS Modules only — no UI framework, no utility classes. All colours and brand values are defined once in `brand/brand.ts` and injected as CSS custom properties on `<body>` in `layout.tsx`. Reskinning the UI means editing one file.

The browser never contacts the FastAPI backend directly. `next.config.mjs` rewrites `/api/backend/*` to `BACKEND_INTERNAL_URL` (default `http://backend:8000`), keeping port 8000 internal and avoiding CORS.

No external icon or animation libraries — icons are inline SVGs, animations are pure CSS keyframes.

---

## Structure

```
app/
  layout.tsx          Root layout: injects brand CSS variables, sets metadata
  page.tsx            Home page (server component): header, HomeChatPanel, footer
  globals.css         Reset, body font, background gradient
  page.module.css     Page-level layout styles
  icon.png            Browser tab favicon (512×512, auto-detected by Next.js)

components/
  Chat.tsx            Chat thread + input bar (client component)
  Chat.module.css
  HomeChatPanel.tsx   Home-only: Chat + editable system prompt (sessionStorage)
  SystemPromptEditor.tsx
  SystemPromptEditor.module.css
  HealthBadge.tsx     API health indicator in the header (client component)
  HealthBadge.module.css

brand/
  brand.ts            Single source of truth for colours, product name, asset paths

public/brand/
  goellan.png         Goëllan mascot — used as bot avatar in chat
  mjc_logo.jpg        MJC Fécamp logo — used in header
  mjc-club-ai-mascotte.png
```

---

## Components

### `Chat` — `components/Chat.tsx`

The main chat interface. Manages message state, sends turns to the backend, and renders the conversation thread.

**State**
| Name | Type | Role |
|---|---|---|
| `messages` | `UiMessage[]` | Full conversation thread |
| `draft` | `string` | Current textarea value |
| `sending` | `boolean` | True while awaiting a backend response |
| `error` | `string \| null` | Last fetch error, shown as a dismissible banner |

**`UiMessage`**
```ts
{ id: string; role: "user" | "assistant"; content: string; sentAt: Date }
```

**Behaviour**
- Sends `POST /api/backend/api/v1/chat` with the full message history on each turn
- Optional prop `systemPromptOverride`: when set (home page only), includes `system_prompt` in the request body
- On error: reverts the optimistic user message and restores the draft
- Textarea auto-resizes with content; `Enter` sends, `Shift+Enter` adds a newline
- Scrolls to the bottom on every new message or while sending

**Sub-components** (private, same file)
- `GoellanAvatar` — renders the mascot image at a given size; used both in the welcome state (large) and beside each bot bubble (small)
- `TypingDots` — animated three-dot indicator shown while `sending` is true
- `SendIcon` — inline SVG send arrow

**Welcome state**: shown when `messages` is empty. Displays a large Goëllan with a speech bubble greeting.

---

### `HealthBadge` — `components/HealthBadge.tsx`

Fires a single `GET /api/backend/health` on mount and displays the result as a colour-coded badge in the header (green = OK, red = error). Isolated as a client component so `page.tsx` can stay server-side.

---

## Brand system — `brand/brand.ts`

All design tokens live here:

```ts
brand.name          // "MJC Fécamp"
brand.productName   // "MJC Chatbot"
brand.assets        // { mascot, mjcLogo } — paths relative to /public
brand.colors        // full colour palette
```

`layout.tsx` maps every colour to a CSS custom property on `<body>` (e.g. `--brand-accent`, `--brand-text`). Components reference only the CSS variables, never the `brand` object directly in CSS — so the palette can be changed in one place without touching any stylesheet.

---

## Proxy — `next.config.mjs`

```
Browser → /api/backend/<path> → BACKEND_INTERNAL_URL/<path>
```

`BACKEND_INTERNAL_URL` is read at **build time** and baked into the Next.js image. Set it as a Docker build arg (default: `http://backend:8000`). For local dev without Docker set it in `frontend/.env.local` to `http://127.0.0.1:8000`.

---

## Dependencies

| Package | Type | Role |
|---|---|---|
| `next` | runtime | Framework — App Router, `next/image`, rewrite proxy |
| `react` + `react-dom` | runtime | UI library and DOM renderer |
| `sharp` | runtime | Image processing for `next/image` in production |
| `typescript` | dev | Type-checker (compilation is handled by Next.js/SWC) |
| `@types/react` + `@types/react-dom` | dev | JSX and React DOM type definitions |
| `@types/node` | dev | Node.js types for `process.env` in `next.config.mjs` |
