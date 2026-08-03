# Hito 9 — Flujos de trabajo agénticos (RFP)

Ver `context.md` para departamentos, estados y seeds.

## Parte 1 (implementada)

- UI ticket-mode: `uis/backoffice` → `/backoffice/rfps`
- API: `POST/GET /api/rfp/tickets`, `POST /api/rfp/tickets/{id}/approve-intake`
- Pipeline LangGraph: ingest (MarkItDown + readability) → classifier → orchestrator → workers (paralelo) → synthesizer
- Fixtures: `fixtures/rfp/` (Markdown + PDF generables)
- Procesamiento async vía Celery (`run_rfp_intake_task`); fallback inline si el broker no está disponible

## Parte 2 (implementada)

- Tras `approve-intake`: Celery `run_rfp_part2_task` genera un borrador **por departamento** (agentes separados).
- Evaluadores en paralelo por sección: legibilidad, pertinencia, cumplimiento §5 (`trackflow_api/rfp/agents/evaluators.py`).
- Ciclo generador–evaluador con `MAX_GENERATOR_ITERATIONS=2`; fallo final → `needs_human_review` (no descarta el ticket).
- Ticket: `generando_borrador` / `en_evaluación` → handoff `esperando_aprobación` + `approval_phase=section_signoff`.
- Tests: `tests/test_rfp_part2.py` (éxito + fallo de evaluación).

## Parte 3 (implementada)

- HITL por departamento con LangGraph `interrupt` + `MemorySaver` (`trackflow_api/rfp/part3.py`).
- Thread scoped: `{ticket_id}::part3::{department_id}` — un dept no bloquea a otro.
- `MAX_HUMAN_APPROVAL_ROUNDS = 2` + nodo explícito `arbitrate`.
- FinalDocument automático solo cuando todas las secciones activas están `approved`.
- Trace estructurado (`agent`, `input`, `output`, `timestamp`) en `run_trace`.
- API: approve/reject/arbitrate section + `GET /trace`.
- Tests: `tests/test_rfp_part3.py` (interrupt/resume, límite, arbitración, E2E Luna).

### Verificación local

```bash
cd services/trackflow-api
pytest tests/test_rfp_agents.py tests/test_rfp_part2.py tests/test_rfp_part3.py -q
```

Para demos sin worker Redis: `CELERY_TASK_ALWAYS_EAGER=true`.
