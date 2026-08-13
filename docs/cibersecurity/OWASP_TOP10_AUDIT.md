# Auditoría OWASP Top 10 (2021) — TrackFlow

Alcance: backend (`services/trackflow-api`), frontends (`uis/backoffice`, `uis/trackflow-portal`) y sistema agéntico (CX + RAG + MCP + RFP), **por separado**. CONTEXT: [audit.md](./audit.md). NIST: [NIST_REPORT.md](./NIST_REPORT.md). Endurecimiento: [HARDENING.md](./HARDENING.md).

**Crítica** = cruce de datos entre titulares, secreto filtrado, acción CONTEXT §5 ejecutable sin humano, o servicio interno publicado a la red.

Leyenda de estado: `corregido` · `abierto` · `no aplica` · `residual` (documentado, no crítico).

## Matriz 10 × 3

### A01 Broken Access Control

| Carril | Aplica | Hallazgo | Evidencia | Sev. | Estado |
| --- | --- | --- | --- | --- | --- |
| Backend | Sí | GET inventario y CRUD suppliers eran públicos; `POST /users` creaba cuentas sin auth; `GET /users` listaba emails con cualquier JWT | Antes: `test_inventory_products_get_is_public`. Después: `list_products`/`get_product` con JWT (`routes/inventory.py` L154–204); router suppliers `Depends(get_current_user)` (`routes/suppliers.py` L24); `POST/GET /users` → `get_current_admin` (`routes/users.py` L13–24). Tests: `test_inventory_api.py`, `test_suppliers_auth.py`, `test_users_admin.py` | Crítica | corregido |
| Frontend | Sí | Guards solo en cliente (`AuthGuard`); las páginas llaman APIs con Bearer | `uis/backoffice/components/auth-guard.tsx`; `packages/shared/auth/token.ts`. El control real es la API | Media | residual |
| Agente | Sí | CONTEXT: chat B2C pidiendo pedido/dirección ajena; B2B vía tools | `authorize_tracking` + `StockExit.user_uuid`. Eval §4 caso 1: `test_eval_context_section4_jailbreak_and_foreign_order_address`. Token MCP del CX: `incidents:read`+`inventory:read` (`mcp_client.py`). Incidentes MCP **sin** filtro de marca | Crítica (tracking) / media (tenant incidentes) | tracking corregido; tenant residual |

Chequeo CONTEXT A01: cubierto para lookup de pedidos. No hay motor de devoluciones que un usuario invoque.

### A02 Cryptographic Failures

| Carril | Aplica | Hallazgo | Evidencia | Sev. | Estado |
| --- | --- | --- | --- | --- | --- |
| Backend | Sí | JWT HS256 con secreto de env; passwords `bcrypt_sha256`; TLS asumido en el edge | `core/security.py`; `TRACKFLOW_JWT_SECRET_KEY` vacío → `RuntimeError` | Alta | residual (HTTP local) |
| Frontend | Sí | JWT en `localStorage`; SSE pone token en query | `packages/shared/auth/token.ts`; `uis/backoffice/lib/realtime/types.ts` | Media | residual |
| Agente | Sí | CONTEXT: keys de carriers / LLM / webhooks solo env | `LITELLM_API_KEY` en `.env.example` vacío. Placeholder MCP rechazado en production (`INSECURE_MCP_JWT_SECRET`). No hay keys de carriers en el repo (el motor no existe) | Crítica (secreto default MCP) | corregido |

### A03 Injection

| Carril | Aplica | Hallazgo | Evidencia | Sev. | Estado |
| --- | --- | --- | --- | --- | --- |
| Backend | Parcial | SQL vía SQLModel; sin SQL crudo en routes | `routes/inventory.py` | Baja | no aplica (SQLi clásica) |
| Frontend | Parcial | React escapa JSX; no `dangerouslySetInnerHTML` en flujos de auth | — | Baja | residual |
| Agente | Sí | Prompt injection directa e indirecta (RAG/MCP) | `classify.py` `_INJECTION_PATTERNS`; `sanitize.py`; evals jailbreak + RAG envenenado + §4 caso 1 | Alta | corregido (caso 1); caso 2 N/A |

### A04 Insecure Design

| Carril | Aplica | Hallazgo | Evidencia | Sev. | Estado |
| --- | --- | --- | --- | --- | --- |
| Backend | Sí | Rate limit en el endpoint LLM; registro abierto en `/auth/register` (intencional B2B interno) | `routes/knowledge.py` L27–35; `TRACKFLOW_KNOWLEDGE_ASK_RATE_LIMIT` | Media | rate limit corregido |
| Frontend | Sí | AuthGuard del portal solo mira presencia de token | `uis/trackflow-portal/components/auth-guard.tsx` | Baja | residual |
| Agente | Sí | Excessive agency: confirmar envío / cambiar carrier | Tools de esas acciones **no existen**. HITL en RFP y memoria. Tabla en NIST Protect | Crítica si existiera la tool | no expuesta |

### A05 Security Misconfiguration

| Carril | Aplica | Hallazgo | Evidencia | Sev. | Estado |
| --- | --- | --- | --- | --- | --- |
| Backend | Sí | Contenedores root; Redis/Qdrant/Flower/MCP publicados; `/dev/token`; OpenAPI `/docs` | Dockerfiles `USER app`/`node`. Compose bind `127.0.0.1` en 6379/6333/6334/8002/5555. `MCP_AUTH_ALLOW_DEV_TOKEN` default 0 | Crítica (puertos + root + mint token) | corregido (docs residual) |
| Frontend | Sí | Next en production mode en runner | `NODE_ENV=production` + `USER node` | Baja | corregido |
| Agente | Sí | CONTEXT: agente con permiso de cambio de carrier; MCP write | Sin tool de carrier. `inventory:write` no está en `SCOPES_SUPPORTED` de concesión. Agente sin `incidents:write` | Crítica | corregido / no expuesta |

### A06 Vulnerable and Outdated Components

| Carril | Aplica | Hallazgo | Evidencia | Sev. | Estado |
| --- | --- | --- | --- | --- | --- |
| Backend | Sí | Dependencias en `uv.lock` / `pyproject.toml` | No se hizo SCA en este ciclo | Media | abierto (no crítica) |
| Frontend | Sí | npm lockfiles | Igual | Media | abierto |
| Agente | Sí | `langgraph`, `litellm`, `mcpauth` | Igual | Media | abierto |

### A07 Identification and Authentication Failures

| Carril | Aplica | Hallazgo | Evidencia | Sev. | Estado |
| --- | --- | --- | --- | --- | --- |
| Backend | Sí | JWT 30 min; register público; login bcrypt | `routes/auth.py`; `get_current_user` | Media | residual |
| Frontend | Sí | Token persistente en localStorage | `token.ts` | Media | residual |
| Agente | Sí | `/api/knowledge/ask` exige JWT; tracking ligado a `user_uuid` | `routes/knowledge.py` L22; `auth_tracking.py` | Alta | corregido (ya existía; reforzado con eval §4) |

### A08 Software and Data Integrity Failures

| Carril | Aplica | Hallazgo | Evidencia | Sev. | Estado |
| --- | --- | --- | --- | --- | --- |
| Backend | Parcial | `uv sync --frozen` en imagen API | `services/trackflow-api/Dockerfile` | Baja | residual |
| Frontend | Parcial | Build multi-stage; no supply-chain pinning extra | Dockerfiles UI | Baja | residual |
| Agente | Sí | RAG/MCP tratados como no confiables | `wrap_rag_context` / `wrap_tool_result` | Media | corregido |

### A09 Security Logging and Monitoring Failures

| Carril | Aplica | Hallazgo | Evidencia | Sev. | Estado |
| --- | --- | --- | --- | --- | --- |
| Backend | Sí | Timing middleware; 500 genérico; JWT en URL SSE puede acabar en access logs | `core/exception_handlers.py`; `routes/realtime.py` | Media | residual |
| Frontend | Parcial | Sin telemetría de auth failures | — | Baja | abierto |
| Agente | Sí | Traces y guardrail stats | `GET /api/knowledge/runs/{run_id}`, `/guardrails/stats`; `run_trace` RFP | Media | corregido (mínimo NIST) |

### A10 Server-Side Request Forgery

| Carril | Aplica | Hallazgo | Evidencia | Sev. | Estado |
| --- | --- | --- | --- | --- | --- |
| Backend | Parcial | URL de MCP y Qdrant vienen de env, no del usuario | `TRACKFLOW_MCP_URL`, `QDRANT_URL` | Baja | no aplica (no hay fetch de URL de usuario) |
| Frontend | No | El browser no pide a la API que fetchee URLs arbitrarias | — | — | no aplica |
| Agente | Parcial | Tools MCP fijas (`get_incident`, `query_inventory`); timeout 5s | `mcp_client.py` | Baja | residual |

## Fixes críticos — evidencia antes/después

### 1. Lecturas de inventario y suppliers sin auth

**Antes:** `GET /inventory/products` → 200 anónimo (`test_inventory_products_get_is_public`). `/suppliers` CRUD sin JWT.

**Después:**

```bash
# sin token
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/inventory/products
# 401
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/suppliers
# 401
```

Tests: `test_inventory_products_get_requires_authentication`, `test_suppliers_list_requires_authentication`.

### 2. Alta y listado de usuarios

**Antes:** `POST /users` sin auth; `GET /users` con cualquier JWT.

**Después:** 401 sin token; 403 si no es admin; 201/200 con admin. Tests: `tests/test_users_admin.py`. El alta pública permanece en `POST /auth/register`.

### 3. Runtime interno publicado

**Antes:** `6379:6379`, `6333:6333`, `8002:8002`, `5555:5555`.

**Después:** `127.0.0.1:…` + `USER` no-root. Ver [HARDENING.md](./HARDENING.md).

### 4. Agente — pedido ajeno (CONTEXT A01 / §4)

**Antes:** evals de jailbreak y tracking `#45821`.

**Después:** wording literal §4 caso 1 + dirección de `#12345` de otro `user_uuid`. `pytest ../../tests/pipelines/test_agent_guardrails_evals.py::test_eval_context_section4_jailbreak_and_foreign_order_address`.

## Hallazgos no críticos (no bloquean sign-off)

SSE `access_token` en query, `localStorage`, ingest de telemetría, OpenAPI `/docs`, `docker.sock`, cron nightly root, errores `str(exc)` en incidents/RFP, SCA de dependencias, ACL de marca en incidentes MCP.

## Sign-off checklist

- [x] Runtime no corre las apps como root (salvo excepciones documentadas)
- [x] Usuario `deploy` / sshd snippet: root SSH deshabilitado
- [x] Firewall/compose: solo API + frontends públicos; internos en loopback
- [x] 10 categorías evaluadas en backend, frontend y agente
- [x] Agente auditado como carril propio
- [x] Críticas corregidas con test o comando antes/después
