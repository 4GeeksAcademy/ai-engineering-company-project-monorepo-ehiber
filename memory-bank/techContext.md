# Tech Context

## Monorepo Shape

- `uis/trackflow-portal/`: Next.js application for the corporate site and `/internal-app` workspace.
- `uis/talent-pipeline-tracker/`: internal talent operations interface.
- `uis/web/`: standalone incident analyzer browser UI.
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
- `python-jose` for JWT signing
- `passlib[bcrypt]` for password hashing
- Vite for the standalone incidents UI
- Tailwind CSS 4 available in the Next.js apps toolchain

## Architectural Decisions

1. User-facing interfaces live under `uis/`, while non-UI operational modules live under `internal/` and runtime APIs live under `services/`.
2. The public marketing website and the internal workspace live in the same Next.js app so future milestones can share design tokens and navigation patterns.
3. `/internal-app` uses a nested layout, separate from the public landing layout.
4. Milestone 2 logic is imported directly from `internal/trackflow-coding-fundamentals/src/index.ts`; no data utilities were copied into the Next.js app.
5. Root `package.json` proxies commands to the TrackFlow portal so `npm run dev` works from the monorepo root in Codespaces.
6. Incident analysis logic is framework-agnostic and reused by both `scripts/analyze.py` and the FastAPI endpoints.
7. JWT auth protects sensitive routes, and user records are stored in a local SQLite database until a production database is introduced.

## Technical Constraints

- External imports from the monorepo must remain relative to preserve the original source of truth for business logic.
- The TrackFlow portal must not depend on the unrelated `uis/talent-pipeline-tracker` application.
- Agent documentation has to stay business-aware, not generic.
- The incidents milestone still lacks the exact CSV-specific company context, so the current field map in `data/incidents/context.json` is a placeholder that must be updated when that context is provided.

## Verification Baseline

- `npm run typecheck` from the repo root
- `npm run lint` from the repo root
- `npm run build` from `uis/trackflow-portal` when dependency installation is available
- Python/FastAPI verification depends on having Python available in the environment.
