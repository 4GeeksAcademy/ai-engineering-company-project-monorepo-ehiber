# Tech Context

## Monorepo Shape

- `apps/`: product applications.
- `apps/trackflow-coding-fundamentals/`: existing Milestone 2 TypeScript business logic for TrackFlow.
- `apps/trackflow-portal/`: Next.js application added for Milestone 4.
- `.agents/`: coding-agent rules and skills specific to this repository.
- `memory-bank/`: active project context that must be read before changes.

## Application Stack

- Next.js 16 with App Router
- React 19
- TypeScript 5
- Tailwind CSS 4 available in the app toolchain, with custom CSS used for TrackFlow visual identity
- `next/font/google` for brand typography

## Architectural Decisions

1. The public marketing website and the internal workspace live in the same Next.js app so future milestones can share design tokens and navigation patterns.
2. `/internal-app` uses a nested layout, separate from the public landing layout.
3. Milestone 2 logic is imported directly from `apps/trackflow-coding-fundamentals/src/index.ts`; no data utilities were copied into the Next.js app.
4. Root `package.json` proxies commands to the TrackFlow app so `npm run dev` works from the monorepo root in Codespaces.

## Technical Constraints

- External imports from the monorepo must remain relative to preserve the original source of truth for business logic.
- The TrackFlow portal must not depend on the unrelated `apps/talent-pipeline-tracker` application.
- Agent documentation has to stay business-aware, not generic.

## Verification Baseline

- `npm run typecheck` from the repo root
- `npm run lint` from the repo root
- `npm run build` from `apps/trackflow-portal` when dependency installation is available
