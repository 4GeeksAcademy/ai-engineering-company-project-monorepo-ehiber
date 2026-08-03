# RFP fixtures (Hito 9)

Seed documents for the agentic RFP intake workflow.

| File | Expected classification | Departments |
| --- | --- | --- |
| `luna-cosmetics.md` / `.pdf` | Valid RFP | `warehouse`, `lastmile` |
| `modaviva.md` / `.pdf` | Valid RFP (partial) | `warehouse`, `reverse` |
| `carrier-offer.md` / `.pdf` | Not an RFP | _(discard)_ |

PDFs are generated with:

```bash
cd services/trackflow-api
python -m scripts.generate_rfp_fixtures
```

> Note: company context asks for seeds under `data/raw/`. That path is agent-protected in this monorepo, so fixtures live here and can be copied into `data/raw/` when explicitly approved.
