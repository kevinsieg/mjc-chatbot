# Roadmap

## Tasks

| Task | Description | Owner | Status |
|------|-------------|-------|--------|
| Create the initial project structure (backend, frontend, Docker, etc.) | Set up the repository foundations with backend/frontend folders, Docker Compose, Makefile commands, and base documentation. | Yohann | ✅ Finish |
| Add a data ingestion script (`make dev-data`) to vectorize knowledge with the Mistral API | Implement ingestion flow to read source files, chunk text, generate embeddings, and store vectors in pgvector. | Yohann | ✅ Finish |
| Use the Mistral API to answer based on indexed data | Connect chat flow to RAG pipeline so replies are generated from retrieved internal context plus system instructions. | Yohann | ✅ Finish |
| Do not answer in Markdown (or parse it before rendering) | Ensure chatbot output is plain text for end users, or safely interpret Markdown before display. | Unassigned | ❌ Todo |
| Improve UI with MJC IA club colors and Goellan mascot | Refresh chat interface visual identity with MJC AI club color palette and Goellan mascot assets. | Unassigned | ❌ Todo |
| Export chat widget for external websites (iframe/CDN) | Make chatbot embeddable on websites (including MJC site) via iframe or CDN widget, and redesign floating bubble/chat-tab button. | Unassigned | ❌ Todo |
| Improve knowledge data sources | Enrich indexed content with MJC organization chart, association statutes, and events. | Unassigned | ❌ Todo |
| Improve answer rendering and precision (chunking) | Tune chunk size/overlap/retrieval to improve relevance and readability of answers. | Unassigned | ❌ Todo |
| Improve system prompt (role/limits/instructions) | Refine assistant role, boundaries, and behavioral rules for safer and clearer responses. | Unassigned | ❌ Todo |
| Create a classic relational database layer for dashboard users | Add standard relational tables (possibly in same PostgreSQL instance as pgvector) with MJC user fixtures for usage/history dashboard. | Käv | ✅ Finish |
| Build dedicated dashboard UI with auth and stats | Create separate admin interface with login and chatbot usage/statistics pages. | Käv | ✅ Finish |
| Enable Cloudflare rate limiting | Configure Cloudflare protections and rate limits for chatbot/API endpoints. | Unassigned | ❌ Todo |
| Add Ansible deployment scripts | Provide automated deployment playbooks/roles for infrastructure and application rollout. | Unassigned | ❌ Todo |

Status legend = ✅ Finish, ⏳ In progress, ❌ Todo
