# REPORT.md

## Summary

This report documents the implemented optimizations and the measured impact on Lighthouse scores and web vitals.

## Changes Implemented

### Change 1

- What changed: Shared hooks were introduced for suppliers, incidents, and inventory products data loading.
- Why it was changed: Remove duplicated async orchestration and standardize loading/error refresh behavior.
- Files touched: backoffice hooks and page components for suppliers, incidents, inbound, and outbound orders.
- Expected KPI impact: Better maintainability, lower regression risk, and cleaner rendering flow.

### Change 2

- What changed: Global metadata was improved for public portal SEO and hardened to noindex for backoffice.
- Why it was changed: Align indexability policy with business intent (public site indexed, internal app not indexed).
- Files touched: `uis/trackflow-portal/app/layout.tsx`, `uis/backoffice/app/layout.tsx`.
- Expected KPI impact: Better SEO hygiene in portal, expected low SEO score in backoffice by policy.

### Change 3

- What changed: Audit and report artifacts were created and completed with measured evidence.
- Why it was changed: Provide formal closure and traceability for the optimization challenge.
- Files touched: `AUDIT.md`, `REPORT.md`, evidence screenshots under `docs/`.
- Expected KPI impact: No runtime impact; delivery and governance impact.

## Results (After)

| App | URL | Perf | Accessibility | Best Practices | SEO | LCP | CLS | INP/TBT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| trackflow-portal | / | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| trackflow-portal | /contacto | 96 | 100 | 100 | 63 | 1.4 s | 0 | TBT 210 ms |
| backoffice | /backoffice/login | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| backoffice | /backoffice/inventory/orders/inbound | 86 | 100 | 100 | 60 | 1.3 s | 0 | TBT 70 ms |

## Before vs After Delta

| App | URL | Perf Delta | LCP Delta | CLS Delta | INP/TBT Delta |
| --- | --- | --- | --- | --- | --- |
| trackflow-portal | / | Pending baseline | Pending baseline | Pending baseline | Pending baseline |
| trackflow-portal | /contacto | N/A in this batch | N/A in this batch | N/A in this batch | N/A in this batch |
| backoffice | /backoffice/login | Pending baseline | Pending baseline | Pending baseline | Pending baseline |
| backoffice | /backoffice/inventory/orders/inbound | N/A in this batch | N/A in this batch | N/A in this batch | N/A in this batch |

## Validation

- Functional smoke checks completed:
  - Login/logout flow
  - Filters and tables in backoffice modules
  - Form interactions in portal/contact pages
- Commands executed:
  - `npm run lint` (backoffice)
  - `npm run typecheck` (backoffice)
  - `npm run typecheck` (portal) -> blocked in current environment (`tsc` not found)

## Remaining Risks

- Lighthouse variability across local runs can affect score consistency.
- Backoffice protected routes depend on API availability and auth state for comparable runs.
- Portal verification in this environment is partially blocked until local TypeScript toolchain is available.
- Some diagnostics include browser-extension noise (DevTools extension scripts), which can inflate JS-related opportunities.

## Evidence

- Screenshots after:
  - `docs/Screenshot 2026-06-23 161218.png`
  - `docs/Screenshot 2026-06-23 161744.png`
- Raw Lighthouse exports (optional):
  - Shared in review thread for `/contacto` and `/backoffice/inventory/orders/inbound`
