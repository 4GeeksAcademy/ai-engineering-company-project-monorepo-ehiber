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
- Telemetry Phase 3 (stub → real persistence) delivered: `TelemetryEvent` SQLModel table (`telemetry_events`) registered in Supabase via existing `init_inventory_db()`, `repositories/telemetry_repository.py` with `insert_telemetry_event()`, endpoint `POST /telemetry/events` now validates individually and persists valid events — rejects per-event with `{stored, rejected, rejected_events}` response. Frontend untouched. Idempotency via `event_id` UNIQUE constraint with savepoint rollback. 8 test cases pass (happy path, empty batch, extra payload keys, missing warehouse, wrong source, mixed partial rejection, persistence verification, duplicate id rejection).
- Telemetry Phase 4 (analysis pipeline + report endpoint) delivered: `services/telemetry/analysis.py` with Pandas KPI functions following load→filter→convert→group→aggregate, `GET /telemetry/report` with optional `start_date`/`end_date` (default 7 days), response shape `{ period, metrics }`, 60s in-memory cache with invalidation on ingest, CLI `scripts/telemetry_report.py`, and pytest coverage in `tests/test_telemetry_report.py`.
- Telemetry data pipeline design (CTO brief) delivered: `data/pipelines/PIPELINE_DESIGN.md` documents end-to-end flow capture→ingest→raw→mart→dashboard, idempotency per stage, `pipeline_runs`/`pipeline_watermarks`/`telemetry_kpi_daily` schemas, observability and recoverability strategies; `data/pipelines/telemetry-kpi-daily/README.md` stubs implementation folder. Scheduler/cron explicitly deferred until after pipeline implementation.
- Telemetry KPI daily pipeline implemented: SQLModel tables `PipelineRun`, `PipelineWatermark`, `TelemetryKpiDaily`; Prefect flows with extract/validate/transform/load tasks, retries on DB tasks, partial failure per date, 1h success skip guard; Docker service `telemetry-pipeline` with cron schedule; mart-backed `GET /telemetry/report` with live fallback; tests in `data/pipelines/telemetry-kpi-daily/tests/`.
- Pipeline rubric gaps closed: `data/pipelines/pipeline.py` canonical entrypoint, `prefect.yaml` deployments, `allow_failure=True` on validate task, `cache_key_fn`+`cache_expiration` on transform, `GET /telemetry/pipeline/runs/latest` and `POST /telemetry/pipeline/run` (imports flow from `data/pipelines/pipeline.py`).
- Pipeline Part 3 (production): subflows (`extract/validate/transform/load`), pure `phases.py` for `--no-prefect` and unit tests (A+C without Cloud), `test_transform.py` + `test_subflows.py`, Prefect Cloud worker Docker (`docker-entrypoint.sh`), `prefect.yaml` with work pool; `.env.example` updated with `PREFECT_*` vars.
- DEV-53 nightly telemetry script delivered: `scripts/nightly_telemetry.py` (independent CLI), `job_runs`/`job_locks` tables with `pending→processing→completed|failed` state machine, distributed lock, CSV export to `data/raw/telemetry_YYYY-MM-DD.csv`, direct pipeline trigger via `trigger_telemetry_kpi_daily_direct`, `TARGET_DATE` override, cron `0 2 * * *` UTC via `scripts/crontab` + `nightly-telemetry` Docker Compose service; Prefect scheduled deployment cron disabled; pytest in `tests/test_nightly_telemetry.py`.
- DEV-55 async task queue delivered: Redis broker + Celery worker + Flower in `docker-compose.yml`; `POST /telemetry/pipeline/run` returns `202` with `task_id`; `GET /tasks/{task_id}` exposes `pending|started|success|failure|dead_letter`; pipeline work runs in worker via `run_telemetry_pipeline_direct_job` (no Prefect Cloud required); `dead_letter_tasks` table records `task_id`, attempt number, and error after 3 failures; pytest in `tests/test_celery_tasks.py`.
- Hito 7 RAG knowledge assistant delivered: Qdrant service in `docker-compose.yml`; modular pipeline in `trackflow_api/rag/` (`setup`, `embed`, `retrieve`, `query`) with LiteLLM as unified provider for embeddings and generation; `POST /api/knowledge/ask`; indexing CLI `scripts/index_knowledge_base.py`; evaluation set `data/eval/test-queries.json` and `scripts/eval_rag.py`; backoffice page `/backoffice/knowledge`; pytest in `tests/test_rag_*.py`; RAG env vars added to `.env.example`.
- Python Docker images for `trackflow-api`, `telemetry-pipeline`, and `nightly-telemetry` migrated to `uv sync --frozen` (`pyproject.toml` + `uv.lock`), installing into `/opt/venv` so bind mounts do not shadow container dependencies.

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
