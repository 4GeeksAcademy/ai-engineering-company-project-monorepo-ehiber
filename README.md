# AI Engineering Company Project Monorepo

[![4Geeks Academy](https://img.shields.io/badge/4Geeks-Academy-blue)](https://4geeksacademy.com)
[![AI Engineering](https://img.shields.io/badge/track-AI%20Engineering-green)](https://4geeksacademy.com/en/coding-bootcamps/ai-engineering)

Monorepo for the transversal AI Engineering company project. This repository centralizes product interfaces, backend services, internal tooling, documentation, reusable assets, and agent workflow conventions.

## Repository structure

```text
ai-engineering-company-project-monorepo/
+-- README.md
+-- README.es.md
+-- CONTEXT.md
+-- agents/
+-- data/
+-- docs/
+-- infra/
+-- internal/
+-- mcps/
+-- packages/
�   +-- shared/
+-- scripts/
+-- services/
+-- shared/
+-- skills/
+-- uis/
+-- workflows/
```

## Current product areas

- `uis/trackflow-portal`: corporate website and internal Next.js workspace.
- `uis/backoffice`: dedicated internal operations workspace for inventory, suppliers, and incidents.
- `uis/talent-pipeline-tracker`: internal people and talent interface.
- `services/trackflow-api`: FastAPI backend with auth, users, suppliers, and incidents endpoints.
- `internal/trackflow-coding-fundamentals`: original TypeScript business logic module reused across milestones.

## Root commands

- `npm run dev`: run the TrackFlow portal from the repo root.
- `npm run build`: build the TrackFlow portal from the repo root.
- `npm run lint`: lint the TrackFlow portal from the repo root.
- `npm run typecheck`: type-check the TrackFlow portal from the repo root.
- `npm run dev:backoffice`: run the consolidated backoffice UI.
- `npm run dev:talent`: run the talent pipeline tracker UI.
- `npm run console:business-logic`: run the original business logic console demo.

## Working rules

1. Replace the placeholder `CONTEXT.md` with the assigned company context before building milestone-specific features.
2. Read `AGENTS.md` and the `memory-bank/` files before making changes.
3. Prefer extending the existing domain modules instead of duplicating logic across services and interfaces.
4. Keep Codespaces compatibility by preserving runnable root-level scripts and local environment examples.
