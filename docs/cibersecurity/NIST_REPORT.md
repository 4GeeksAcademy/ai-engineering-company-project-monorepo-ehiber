# Informe NIST CSF 2.0 — Integración segura de IA (TrackFlow)

Framework: **NIST Cybersecurity Framework 2.0** (Govern, Identify, Protect, Detect, Respond, Recover). No se usa NIST AI RMF.

Contexto de empresa: [audit.md](./audit.md). Auditoría web: [OWASP_TOP10_AUDIT.md](./OWASP_TOP10_AUDIT.md). Runtime: [HARDENING.md](./HARDENING.md).

## Govern

**Marco regulatorio (obligatorio por CONTEXT §2 y §6):**

- **España / UE — RGPD.** Brecha con riesgo para derechos de las personas: notificación a la **AEPD en 72 horas**. Aplica a destinatarios B2C (dirección, contacto) y a datos contractuales de marcas B2B.
- **California — CCPA/CPRA** (operación en Los Ángeles en el CONTEXT de ciberseguridad). Derechos de acceso, eliminación y opt-out; notificación razonablemente rápida ante brecha. No se trata como “privacidad genérica de EE. UU.”.

**Acción concreta:** este informe nombra responsables por componente (tabla Identify) y fija que el Squad de Ingeniería de IA es accountable de controles cuando el modelo es de un tercero (LiteLLM/OpenRouter). Andrés Kim (CTO) es el owner de Govern.

## Identify

Inventario = CONTEXT §3 **unión** lo construido en este fork. Los motores de carriers y de aprobación automática de devoluciones del §3 **no existen como sistemas de IA** en el código; el riesgo residual se cubre por ausencia de tool (Protect).

| Componente | Qué hace | LLM | Owner | Tercero | Estado |
| --- | --- | --- | --- | --- | --- |
| Agente CX 24/7 | Tracking, devoluciones, incidencias | Sí (LiteLLM) | Valentina Cruz / CX + Squad Backend | OpenRouter vía LiteLLM | En fork (`trackflow_api/agent/`) |
| RAG políticas / SLA | Retrieve + generate sobre `docs/rag` | Sí (embed + completion) | Squad Backend | Qdrant, LiteLLM | En fork |
| MCP incidents/inventory | Tools HTTP :8002 | No | Squad Backend | — | En fork (`mcps/trackflow-mcp/`) |
| Memoria con consentimiento | Propose → approve/reject/edit | No | Squad Backend | — | En fork |
| Workflow RFP | Intake → generate → HITL | Opcional (`RFP_USE_LLM`) | Comercial + Squad Backend | LiteLLM si se activa | En fork |
| SSE notificaciones | Eventos dashboard | No | Squad Backend | — | En fork (no es sistema de IA) |
| Telemetría / Celery | KPIs y jobs | No | Squad Backend | Redis, Prefect opcional | En fork |
| Motor selección de carrier | CONTEXT §3 | — | — | — | **No construido** |
| Aprobación auto. de devoluciones | CONTEXT §3 | — | — | — | **No construido** |

**Acción concreta:** cada fila tiene owner; LiteLLM, Qdrant Cloud (si se usa), Resend y Prefect quedan como procesadores. En producción haría falta DPA/BAA según el mercado; hoy el contrato de proveedor no está firmado (brecha Govern/Identify, no bloqueante de código).

## Protect

Controles implementados en este ciclo (además de guardrails ya existentes):

1. **Secretos.** JWT, LiteLLM, Resend, Prefect y MCP salen de env. `TRACKFLOW_APP_ENV=production` rechaza `MCP_AUTH_JWT_SECRET` igual al placeholder (`core/config.py`). `MCP_AUTH_ALLOW_DEV_TOKEN` default **0** (`mcps/trackflow-mcp/trackflow_mcp/server.py`). Compose exige `MCP_AUTH_JWT_SECRET` y no publica el default en el YAML.
2. **Input + system vs user.** `classify_input` (injection / personal use), delimiters RAG/MCP en `wrap_rag_context` / `wrap_tool_result`.
3. **Injection indirecta.** Sanitizado de chunks y resultados de tools; eval `test_eval_poisoned_rag_context_is_sanitized_not_obeyed`.
4. **Validación de output / tools.** Guardrail de salida; MCP `inventory:write` nunca se concede; el token del agente CX ahora es `incidents:read` + `inventory:read` (`agent/tools/mcp_client.py`).
5. **Rate limit.** `POST /api/knowledge/ask` — ventana deslizante in-process por `user_uuid` (`TRACKFLOW_KNOWLEDGE_ASK_RATE_LIMIT`, default 30/60s). Test: `tests/test_rag_api.py::test_knowledge_ask_rate_limited`.
6. **Logging.** `GET /api/knowledge/runs/{run_id}` (trace de nodos), `GET /api/knowledge/guardrails/stats`, `GET /api/rfp/tickets/{id}/trace`, auditorías de memoria. Los traces del knowledge agent son in-memory (no duran un restart).
7. **HITL / acciones irreversibles (CONTEXT §5):**

| Acción CONTEXT §5 | Estado | Evidencia |
| --- | --- | --- |
| Aprobar devolución sobre umbral | No expuesta | El CX no tiene tool de aprobación; RAG solo explica política |
| Confirmar despacho de alto valor | No expuesta | Outbound de inventario es API JWT, no tool del agente |
| Cambiar carrier en tránsito | No expuesta | No hay motor/tool de carrier |
| Compartir volumen/incidentes B2B entre marcas | Parcial | ACL de tracking por `user_uuid`; incidentes MCP **no** están filtrados por marca (brecha pendiente) |
| Aprobar sección RFP | HITL | LangGraph `interrupt` en `rfp/part3.py` |
| Consolidar memoria del agente | HITL | approve/reject/edit explícito |

**Caso CONTEXT §4 (prompt injection):**

- Caso 1 (jailbreak + dirección de pedido ajeno): `tests/pipelines/test_agent_guardrails_evals.py::test_eval_context_section4_jailbreak_and_foreign_order_address`. El wording con “Ignora tus instrucciones…” cae en `detect_injection`; la variante “dirección del pedido #12345” cae en `authorize_tracking`.
- Caso 2 (nota de almacén → motor de carriers): **N/A**. El motor no está en el fork. Control = tool no expuesta.

**A01 API (también OWASP):** JWT en GET inventario, JWT en `/suppliers/*`, admin en `POST/GET /users`. Alta pública sigue en `/auth/register`.

**Acción concreta Protect:** rate limit + secretos MCP + auth de lecturas internas + eval §4 caso 1.

## Detect

**Acción concreta:** `GET /api/knowledge/guardrails/stats` expone contadores `structural|content|security` y por nombre de guardrail. Un pico de `detect_injection` o `authorize_tracking` es la señal de abuso del chat.

Pendiente: persistir métricas y alertar (p. ej. umbral 10 rechazos/min). Hoy el contador es in-process.

## Respond

**Acción concreta (plan, plazos del CONTEXT):**

1. Contener: rotar `TRACKFLOW_JWT_SECRET_KEY`, `MCP_AUTH_JWT_SECRET`, `LITELLM_API_KEY`; revocar sesiones.
2. Notificar AEPD **antes de 72 horas** si hay riesgo para interesados (direcciones B2C o datos de marca).
3. Notificar afectados CCPA/CPRA en California de forma razonablemente rápida.
4. Registrar el incidente (quién, qué componente, si el agente filtró PII).

No hay playbook automatizado en el repo; el plazo de 72 h es el control Respond exigible.

## Recover

**Acción concreta:** restaurar API/front desde git + `docker compose up`; reindexar RAG (`scripts/index_knowledge_base.py`); SQLite/TinyDB y volumen `qdrant_data` deben entrar en backup de host (aún no hay job de backup — brecha documentada). Tras rotar secretos, redeploy con `.env` nuevo. Plantilla de permisos: `infra/hardening/permissions/layout.md`.

## Brechas que no se cerraron en este ciclo

| Riesgo | Mitigación propuesta |
| --- | --- |
| JWT del SSE en query (`access_token`) | Pasar a header cuando haya WebSocket (Parte 2) o cookie httpOnly |
| Token en `localStorage` | Cookie httpOnly + CSRF |
| `POST /telemetry/events` sin JWT | Auth de servicio o ingest interno only |
| `/docs` OpenAPI en development | Desactivar si `TRACKFLOW_APP_ENV=production` |
| `docker.sock` en telemetry-pipeline | Worker sin socket o socket proxy |
| Incidentes MCP sin ACL de marca | Filtrar por `client_name` / tenant |
| Traces del agente no duraderos | Sqlite/Postgres checkpointer |
| Caso §4-2 (carriers) | No construir el motor; mantener tools fuera del agente |
| Nightly cron como root | Usuario dedicado cuando el cron se mueva a host |

## Verificación

```bash
cd services/trackflow-api
uv run pytest tests/test_inventory_api.py tests/test_suppliers_auth.py tests/test_users_admin.py tests/test_rag_api.py tests/test_mcp_secret_production.py tests/test_cache.py -q
uv run pytest ../../tests/pipelines/test_agent_guardrails_evals.py -q
cd ../../mcps/trackflow-mcp
uv run pytest tests/test_mcp_auth.py -q
```
