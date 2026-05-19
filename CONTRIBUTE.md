# Contributing Guide

This document explains how to contribute to `mjc-chatbot` using the branch strategy of this project.

## Branch strategy

- `main`: production branch (stable code only).
- `develop`: integration branch for ongoing development.
- `feature/*`: feature branches created from `develop`.

## Contribution workflow

1. Clone the repository:
   - `git clone https://github.com/Club-IA-plus/mjc-chatbot`
   - `cd mjc-chatbot`
2. Switch to `develop`:
   - `git checkout develop`
3. Update your local `develop` before starting:
   - `git pull origin develop`
4. Create your feature branch from `develop`, including the issue number:
   - `git checkout -b feature/<issue-number>-<short-description>` (e.g. `feature/6-no-markdown-response`)
5. Work on your changes and commit regularly.
6. Push your branch:
   - `git push -u origin feature/<short-feature-name>`
7. Open a Merge Request from `feature/<short-feature-name>` to `develop`.

## Local debugging setup (Cursor / VS Code)

Use this when you want breakpoints in the backend without rebuilding Docker images.

**Prerequisites:** Docker, Make, Python 3, Node.js.

**One-time setup**

```bash
# 1. Environment
cp .env.example .env          # then set MISTRAL_API_KEY in .env

# 2. Python venv
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt

# 3. Editor config (.vscode/ is gitignored — templates are in dev/vscode/)
cp -r dev/vscode .vscode
```

**Every session**

```bash
make dev-db-d                 # start Postgres in Docker (detached)
docker compose ps             # wait until db shows "healthy"
```

Then in Cursor/VS Code: **Run and Debug (⇧⌘D)** → select **"Backend: API (local, DB in Docker)"** → **F5**.

The API is now live at `http://localhost:8000` with hot-reload. Set breakpoints anywhere in `backend/app/`.

**Useful breakpoint locations**

| File | Line | What you see |
|---|---|---|
| `rag_service.py` | 84 | `context_block` — chunks retrieved from the DB |
| `rag_service.py` | 87 | `messages` — full prompt sent to Mistral |
| `mistral_service.py` | 76 | `content` — raw string returned by Mistral |

**Trigger a request** (single line, works in fish):

```bash
curl -s -X POST http://localhost:8000/api/v1/chat -H "Content-Type: application/json" -d '{"messages":[{"role":"user","content":"Bonjour"}]}' | python3 -m json.tool
```

**Stop when done:**

```bash
make dev-db-stop
```

> **Note:** `DATABASE_URL` is automatically overridden to `127.0.0.1` by the launch config — you do not need to edit `.env`.

## Frontend hot reload (Next.js on the host)

Run the UI locally for instant HMR on every file save. Requires the backend to be running (Cursor debugger or `make dev-backend-local`).

**One-time setup:**

```bash
cp frontend/.env.local.example frontend/.env.local
cd frontend && npm install
```

**Every session:**

```bash
cd frontend && npm run dev
```

Open `http://localhost:3000`. Any change to `frontend/` reloads the browser instantly.

> `frontend/.env.local` points the Next.js rewrite to `http://127.0.0.1:8000` so the UI reaches the host backend instead of the Docker container.

**Troubleshooting — images or styles not rendering correctly:**

If you previously ran the full Docker stack, the `.next/` cache may conflict with the local dev server. Clear it:

```bash
rm -rf frontend/.next
cd frontend && npm run dev
```

## Merge rules

- Feature branches are merged into `develop` first.
- `main` is reserved for production releases.
- Do not create direct commits on `main`.
