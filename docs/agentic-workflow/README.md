# Hito 9 — Flujos de trabajo agénticos (RFP)

Ver `context.md` para departamentos, estados y seeds.

## Parte 1 (implementada)

- UI ticket-mode: `uis/backoffice` → `/backoffice/rfps`
- API: `POST/GET /api/rfp/tickets`, `POST /api/rfp/tickets/{id}/approve-intake`
- Pipeline LangGraph: ingest (MarkItDown + readability) → classifier → orchestrator → workers (paralelo) → synthesizer
- Fixtures: `fixtures/rfp/` (Markdown + PDF generables)
- Procesamiento async vía Celery (`run_rfp_intake_task`); fallback inline si el broker no está disponible

### Verificación local

```bash
cd services/trackflow-api
uv sync
python scripts/generate_rfp_fixtures.py
pytest tests/test_rfp_agents.py -q
```

Para demos sin worker Redis: `CELERY_TASK_ALWAYS_EAGER=true`.
