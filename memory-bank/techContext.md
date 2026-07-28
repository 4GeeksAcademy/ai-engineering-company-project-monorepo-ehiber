# Tech Context

## Monorepo Shape

- `uis/trackflow-portal/`: Next.js application for the corporate site and `/internal-app` workspace.
- `uis/backoffice/`: Next.js application for consolidated internal operations under `/backoffice`.
- `internal/trackflow-coding-fundamentals/`: existing Milestone 2 TypeScript business logic for TrackFlow.
- `services/trackflow-api/`: FastAPI backend service for auth, suppliers, and incidents workflows.
- `scripts/`: CLI entry points and script-level documentation.
- `.agents/`: coding-agent rules and skills specific to this repository.
- `memory-bank/`: active project context that must be read before changes.

## Application Stack

- Next.js 16 with App Router
- React 19
- TypeScript 5
- FastAPI for backend APIs
- SQLite for initial local persistence
- Redis + Celery for async background tasks (DEV-55)
- Qdrant + LiteLLM for RAG knowledge assistant (Hito 7)
- `python-jose` for JWT signing
- `passlib[bcrypt]` for password hashing
- Tailwind CSS 4 available in the Next.js apps toolchain

## Architectural Decisions

1. User-facing interfaces live under `uis/`, while non-UI operational modules live under `internal/` and runtime APIs live under `services/`.
2. The public marketing website and the internal workspace live in the same Next.js app so future milestones can share design tokens and navigation patterns.
3. `/internal-app` uses a nested layout, separate from the public landing layout.
4. Milestone 2 logic is imported directly from `internal/trackflow-coding-fundamentals/src/index.ts`; no data utilities were copied into the Next.js app.
5. Root `package.json` proxies commands to the TrackFlow portal so `npm run dev` works from the monorepo root in Codespaces.
6. Incident analysis logic is framework-agnostic and reused by both `scripts/analyze.py` and the FastAPI endpoints.
7. JWT auth protects sensitive routes, and user records are stored in a local SQLite database until a production database is introduced.
8. Long-running API work (telemetry pipeline manual trigger) is enqueued to Celery with Redis as broker; workers use the direct (`--no-prefect`) pipeline path so Prefect Cloud remains optional.
9. Commercial knowledge assistant (Hito 7) uses Qdrant for vector retrieval and LiteLLM (`LITELLM_API_KEY`) for both embeddings and answer generation; `retrieve` and `query` stay separate so raw chunks are never returned as final answers.
10. Knowledge ask flow is orchestrated by a compiled LangGraph graph with `MemorySaver` checkpointing and queryable per-run traces; RAG primitives are reused via `data/pipelines/rag` wrappers.
11. **MCP Variant B (`mcp-auth` branch):** company tools (incidents + read-only inventory) are exposed by an independent Streamable HTTP MCP server under `mcps/trackflow-mcp/` on port **8002**. Authorization uses the **[MCP Auth](https://mcp-auth.dev/)** Python library (`mcpauth`) — protected resource metadata, Bearer JWT validation, and OAuth scopes (`incidents:read|write`, `inventory:read`). FastMCP hosts tools only; it does **not** use FastMCP `auth=` providers. The LangGraph agent calls tools via `langchain-mcp-adapters` (`MultiServerMCPClient`) and must not import incident/inventory services in tool nodes. Inventory writes are always rejected (`insufficient_scope`); `inventory:write` is never granted.
12. **Agent guardrails harness:** the LangGraph knowledge agent is wrapped with input/output/security guardrails under `trackflow_api/agent/guardrails/`. Failure types (`structural|content|security`) are logged and summarized via `GET /api/knowledge/guardrails/stats`. Tracking lookups bind to the authenticated JWT `user_uuid` against `StockExit.user_uuid`. Untrusted RAG/tool text is sanitized and delimited so it cannot act as system instructions. Domain persona is CX first-line (Valentina Cruz): tracking, returns/SLA by country (US vs ES), incidents.
13. **Consent-based agent memory:** after generation, the agent may propose a memory; only explicit approve/reject/edit consolidates into `agent_memory_entries` (keyed by carrier|country|topic). Ambiguous replies never approve. Approved memories are injected as non-instructional evidence on later turns. Sensitive B2B/B2C location data and warehouse routes are blocked from memory.

## Technical Constraints

- External imports from the monorepo must remain relative to preserve the original source of truth for business logic.
- Agent documentation has to stay business-aware, not generic.
- Milestone-specific field maps and seed data must come from the matching folder under `ai-engineering-syllabus/content/contexts/` (for TrackFlow incidents: `contexts/incidents-file-analysis/CONTEXT-trackflow.md`).

## Verification Baseline

- `npm run typecheck` from the repo root
- `npm run lint` from the repo root
- `npm run build` from `uis/trackflow-portal` when dependency installation is available
- Python/FastAPI dependency management uses `uv` (`pyproject.toml` + `uv.lock`); Docker images run `uv sync --frozen` into `/opt/venv`.
