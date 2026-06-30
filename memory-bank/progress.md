# Progress

## Completed

- TrackFlow business context identified in `CONTEXT.md`.
- Milestone 1 artifacts were originally created as root static HTML pages and were later retired after the migration to Next.js.
- Milestone 2 business logic located in `internal/trackflow-coding-fundamentals`.
- Milestone 4 agent infrastructure added: memory bank, `AGENTS.md`, `.agents/rules`, and `.agents/skills`.
- Next.js application created in `uis/trackflow-portal`.
- Public TrackFlow website migrated to reusable React + TypeScript components.
- `/contacto` form implemented inside Next.js with client-side validation and low-volume warning.
- `/internal-app` created with its own layout and a dashboard that renders results from the Milestone 2 module.
- `docs/ARCHITECTURE_PROPOSAL.md` added for the backend architecture milestone.
- Supplier directory API added and later consolidated into `uis/backoffice`.
- Frontend auth flows integrated in `uis/trackflow-portal` and the consolidated `uis/backoffice`, reusing JWT storage, protected views, profile, and password change patterns.
- Password reset flow added with Resend integration and `/forgot-password` + `/reset-password` pages in Next.js apps.
- `scripts/analyze.py` added and wired to the same shared incidents analysis engine used by the API, validated against `CONTEXT-trackflow.md` from the syllabus.
- Incident analysis and management UI capabilities were added and later consolidated into `uis/backoffice`.
- Incidents analyzer aligned with TrackFlow context from `ai-engineering-syllabus/content/contexts/incidents-file-analysis/`, including `incidents-trackflow.csv` and full validation rules in `data/incidents/context.json`.
- Centralized incident manager added with CRUD API, seed script, shared constants in `packages/shared/incidents/`, and later exposed through the consolidated backoffice UI.
- Cross-cutting error handling added with global API exception handlers, shared user-facing error helpers, and retry-friendly UI states.
- Auth and shared helper test suites added with `pytest` and `Jest`, documented in `TESTING.md`.
- Milestone 5 backend foundation implemented in `services/trackflow-api`: dual persistence with TinyDB (auth) + SQLModel inventory DB via `SUPABASE_URI`, new `/inventory` router, and stock rules enforcement per SKU+warehouse.
- Inventory API test coverage added for required acceptance behaviors: auth boundaries, tracking validation, insufficient stock rejection, and warehouse-scoped stock computation.
- Auth compatibility bridge started for UUID migration: TinyDB users now carry `user_uuid`, JWT now issues UUID subjects, and token decoding remains backward compatible with legacy integer subjects.
- New `uis/backoffice` Next.js app implemented with protected `/backoffice/*` routes, shared JWT auth client integration, inventory pages (`products`, `orders/inbound`, `orders/outbound`, `orders`) connected to `/inventory` API, and consolidated placeholder modules for suppliers/incidents/candidates without real data.
- Backoffice consolidation refined with active side navigation, richer local mock modules for suppliers/incidents/candidates (filters, status/rate updates, pipeline view), and full frontend validation pass (`lint`, `typecheck`, `build`) in `uis/backoffice`.
- Suppliers and incidents in `uis/backoffice` now consume the real backend APIs, replacing the temporary local mocks.
- Legacy standalone UIs `uis/application` and `uis/web` were retired after their functionality moved into `uis/backoffice`; root scripts, docs, and Docker Compose now point to the consolidated app.
- Legacy `uis/talent-pipeline-tracker` was retired after the repo standardized on `uis/backoffice` for internal UI delivery, even though the talent module continues as a lighter backoffice surface.
- Caching sprint delivered: in-process TTL cache for inventory products/orders, suppliers list, and incidents summary; timing middleware; bulk seed + benchmark scripts; `CACHING_REPORT.md`; backoffice lazy-load for candidates and reduced summary refetch on incident filter changes.
- Telemetry Phase 1 design delivered: `docs/telemetry/telemetry-plan.md` (KPI traceability, stream/batch decisions, FIFO lot rule, greenfield architecture) and `docs/telemetry/event-schemas.json` (8 event schemas with property whitelists per `docs/TELEMETRY_PHASE_1.MD`).
- Telemetry Phase 2 (capture frontend + stub backend) implemented: `TelemetryService` singleton in `uis/backoffice/lib/telemetry/` with local queue, configurable batch flush (5s / 10 events), and single `track()` function. Pages `inbound/page.tsx` and `outbound/page.tsx` instrumented with `inbound_order_submitted`, `outbound_order_submitted`, and `dispatch_form_abandoned` events. FastAPI stub endpoint `POST /api/telemetry/events` validates envelope + payload whitelist and returns 200 without persisting. URL configurable via `NEXT_PUBLIC_TELEMETRY_API_URL` env var.

## Current Risks

- The new apps need local dependencies installed before `npm run dev` or `npm run build` can execute in a fresh environment.
- Any future change to `internal/trackflow-coding-fundamentals` can affect both the console demo and the internal dashboard, so that module should remain protected.
- The current environment may not have Python installed, which blocks end-to-end verification of the FastAPI service and CLI script in some setups.
- Supabase connectivity in non-test environments now depends on `SUPABASE_URI`; startup will fail fast when missing or invalid.
- UUID migration is in compatibility phase (uuid-first token with int fallback) and still requires a future hardening phase to remove legacy subject handling.

## Next Steps

- Add screenshots and PR description assets before submission.
- Run manual `/docs` verification for auth and protected routes in an environment with Python and installed backend dependencies.
- Add inventory seed dataset required by Milestone 5 (minimum SKU/entry/exit fixtures) to the backend seed workflow.
- Execute Phase 2 UUID hardening for user-facing contracts once consumers are aligned.
