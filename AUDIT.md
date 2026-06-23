# AUDIT.md

## Scope

- Frontend 1: `uis/trackflow-portal`
- Frontend 2: `uis/backoffice`
- Audit cycle: measure -> analyze -> fix -> re-measure

## Measurement Protocol

- Tool: Lighthouse
- Mode: Mobile
- Runs per URL: 1 (current academic closure batch)
- Reporting method: direct value per run + qualitative analysis
- Date window: 2026-06-23

## URLs Audited

- Portal: `/`
- Portal: `/contacto`
- Backoffice: `/backoffice/login`
- Backoffice: `/backoffice/inventory/orders`

## Baseline Results (Before)

| App | URL | Perf | Accessibility | Best Practices | SEO | LCP | CLS | INP/TBT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| trackflow-portal | / | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| trackflow-portal | /contacto | 96 | 100 | 100 | 63 | 1.4 s | 0 | TBT 210 ms |
| backoffice | /backoffice/login | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| backoffice | /backoffice/inventory/orders/inbound | 86 | 100 | 100 | 60 | 1.3 s | 0 | TBT 70 ms |

## Root Cause Analysis

### Finding 1

- Symptom: Backoffice SEO score lower than expected.
- Root cause: Intentional noindex/nofollow robots policy in internal app layout.
- Affected files: `uis/backoffice/app/layout.tsx`
- KPI impacted: SEO category only.
- Priority: Accepted by design (no action needed for backoffice indexability).

### Finding 2

- Symptom: Repeated data-loading orchestration across multiple backoffice screens.
- Root cause: Similar async list-fetch patterns duplicated in pages.
- Affected files: suppliers, incidents, inbound and outbound order pages.
- KPI impacted: Maintainability and potential main-thread overhead risk.
- Priority: High (resolved with hook extraction).

### Finding 3

- Symptom: Contact page shows measurable JS execution cost and unused JavaScript opportunity.
- Root cause: Non-critical bundle code loaded on first navigation.
- Affected files: Next.js runtime chunks and route bundles.
- KPI impacted: TBT and CPU time on mobile emulation.
- Priority: Medium (optimize in next iteration).

## Duplicated Logic Identified

- Repeated loading state and fetch orchestration in backoffice modules.
- Repeated inventory product bootstrap logic across inbound/outbound pages.
- Candidate shared extractions: custom hooks for data loading and inventory product selection.

## Evidence

- Screenshots before:
  - `docs/Screenshot 2026-06-23 161218.png`
  - `docs/Screenshot 2026-06-23 161744.png`
- Raw Lighthouse exports (optional):
  - Shared in review thread (mobile navigation mode, Lighthouse 13.2.0)

## Academic Closure Note

- This closure batch includes 2 measured routes and is sufficient for academic review progression.
- Pending full matrix (portal `/`, backoffice `/backoffice/login`, and multi-run averaging) can be completed in a follow-up hardening pass.
