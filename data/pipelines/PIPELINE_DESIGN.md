# Diseño del Data Pipeline — Telemetría TrackFlow

**Documento:** respuesta al brief de diseño del CTO (fase diseño — sin orquestación)  
**Autor:** TrackFlow Tech  
**Estado:** Diseño aprobado para implementación  
**Alcance:** pipeline batch de KPIs de telemetría Fase 1  
**Referencias:**

- Plan de eventos: [`docs/telemetry/telemetry-plan.md`](../../docs/telemetry/telemetry-plan.md)
- Contrato de esquemas: [`docs/telemetry/event-schemas.json`](../../docs/telemetry/event-schemas.json)
- Lógica de transformación existente: [`services/telemetry/analysis.py`](../../services/telemetry/analysis.py)
- Pipeline concreto (implementación): [`telemetry-kpi-daily/`](./telemetry-kpi-daily/)

---

## 1. Resumen ejecutivo

TrackFlow ya captura eventos de telemetría desde la API y el backoffice, los persiste en Supabase (`telemetry_events`) y calcula KPIs bajo demanda con Pandas (`services/telemetry/analysis.py`). Ese flujo funciona para desarrollo y reportes ad hoc, pero **no cumple los requisitos de producción** que operaciones exige: idempotencia demostrable en todo el recorrido, trazabilidad de cada ejecución y capacidad de reanudar tras un fallo parcial.

Este documento define el **diseño del pipeline batch diario** que mueve datos desde la captura en aplicación hasta las métricas consumidas por dashboards y `GET /telemetry/report`. No incluye código de orquestación ni decisión de scheduler (cron, Prefect, etc.): eso se abordará **después** de cerrar arquitectura e implementación del pipeline.

**Pipeline principal:** `telemetry-kpi-daily`  
**Pipeline documentado para fase posterior:** `telemetry-stream-alerts` (eventos `processing_mode=stream`)

---

## 2. Stakeholders y preguntas que responde

| Stakeholder | Rol | Pregunta que el diseño debe responder |
| --- | --- | --- |
| Operaciones (RFP interno) | Sign-off producción | ¿Cómo fluye un evento desde la app hasta el dashboard? ¿Qué pasa si el job falla a mitad? ¿Correr dos veces el mismo día corrompe datos? |
| Ana Whitfield | Head of Warehouse Operations | ¿Las métricas diarias por almacén son consistentes y reproducibles? |
| Thomas Harry | CEO | ¿Los totales ejecutivos están segmentados por `warehouse` sin mezclar Los Ángeles y Zaragoza? |
| TrackFlow Tech | Implementación | ¿Qué tablas, stages y contratos implementar sin duplicar lógica de negocio? |

---

## 3. Flujo end-to-end

### 3.1 Diagrama de datos

```
┌─────────────────┐     ┌─────────────────┐
│  trackflow-api  │     │  backoffice-web │
│  (FastAPI)      │     │  (Next.js)      │
└────────┬────────┘     └────────┬────────┘
         │ hooks / client        │
         └──────────┬────────────┘
                    ▼
         POST /telemetry/events          ← S0 Capture + S1 Ingest
                    │
                    ▼
         ┌──────────────────────┐
         │  telemetry_events    │        ← Raw layer (90 días)
         │  (Supabase)          │
         └──────────┬───────────┘
                    │
    ┌───────────────┼───────────────────────────────┐
    │               │                               │
    ▼               ▼                               ▼
 processing_mode   processing_mode=stream            (mismo raw)
 =batch            (fase posterior)
    │               │
    ▼               ▼
 telemetry-kpi-daily     telemetry-stream-alerts
 (este documento)        (diseño resumido §10)
    │
    ▼
 S2 Extract → S3 Validate → S4 Transform → S5 Load
    │
    ▼
 ┌──────────────────────┐     ┌──────────────────────┐
 │ telemetry_kpi_daily  │     │ pipeline_runs        │
 │ (mart, 12 meses)     │     │ pipeline_watermarks  │
 └──────────┬───────────┘     └──────────────────────┘
            │
            ▼
 GET /telemetry/report  →  Dashboards Ana / Thomas
```

### 3.2 Tabla de stages

| Stage | Nombre | Input | Output | Componente |
| --- | --- | --- | --- | --- |
| S0 | Capture | Acción de negocio | Evento con envelope | Emisores API / backoffice |
| S1 | Ingest | Batch HTTP | Fila en raw | `POST /telemetry/events` |
| S2 | Extract | Raw + watermark | Conjunto de eventos del periodo | Job `telemetry-kpi-daily` |
| S3 | Validate | Eventos extraídos | Eventos válidos + rechazos | Job `telemetry-kpi-daily` |
| S4 | Transform | Eventos válidos | Métricas agregadas | `build_metrics()` en `analysis.py` |
| S5 | Load | Métricas | Filas en mart | Job `telemetry-kpi-daily` |
| S6 | Serve | Mart (o fallback live) | JSON de reporte | `GET /telemetry/report` |

**Regla de capas:** el raw (`telemetry_events`) es inmutable salvo TTL; el mart (`telemetry_kpi_daily`) es derivado y reemplazable por re-ejecución idempotente del mismo `processing_date`.

---

## 4. Modelo de datos del pipeline

### 4.1 Raw — `telemetry_events` (existente)

Ya implementada en Fase 3. Campos relevantes para el pipeline:

| Campo | Uso en pipeline |
| --- | --- |
| `event_id` (PK) | Dedupe en ingesta y desempate en watermark |
| `event_type` | Filtro por tipo de KPI |
| `timestamp` | Ventana temporal y watermark (`occurred_at` de negocio) |
| `source`, `tags`, `payload` | Transformación |
| `processing_mode` | Enrutamiento batch vs stream |
| `created_at` | Auditoría de ingesta (no sustituye `timestamp` en KPIs) |

**Retención:** 90 días (según plan de telemetría).

### 4.2 Mart — `telemetry_kpi_daily` (nueva)

Almacena agregados listos para consumo. Una fila por combinación de métrica, fecha de negocio y segmento.

| Columna | Tipo | Descripción |
| --- | --- | --- |
| `id` | SERIAL / UUID | Surrogate key |
| `metric_name` | TEXT | `order_fulfillment_rate` \| `stock_discrepancy_frequency` \| `receiving_dispatch_cycle_time` |
| `business_date` | DATE | Día de negocio (UTC) |
| `warehouse` | TEXT | `los_angeles` \| `zaragoza` |
| `dimensions` | JSONB | Segmentos adicionales (ej. `outcome`, `sku_id` si aplica en futuras iteraciones) |
| `value` | NUMERIC | Valor principal de la métrica |
| `sample_size` | INT | Conteo subyacente cuando aplique |
| `computed_at` | TIMESTAMPTZ | Momento del cálculo |
| `pipeline_run_id` | UUID | Trazabilidad al run que produjo la fila |
| `schema_version` | TEXT | Versión del contrato de métricas (ej. `1.0`) |

**Clave natural (idempotencia en load):** `(metric_name, business_date, warehouse, dimensions)` — el upsert sobre esta clave garantiza que una re-ejecución reemplace valores, no los acumule.

**Retención:** 12 meses.

### 4.3 Ledger — `pipeline_runs` (nueva)

Registro auditable de cada ejecución del pipeline.

| Columna | Tipo | Descripción |
| --- | --- | --- |
| `run_id` | UUID PK | Identificador único del run |
| `pipeline_name` | TEXT | `telemetry-kpi-daily` |
| `processing_date` | DATE | Día de negocio procesado |
| `status` | TEXT | `pending` \| `running` \| `succeeded` \| `failed` \| `partial` |
| `started_at` | TIMESTAMPTZ | Inicio |
| `finished_at` | TIMESTAMPTZ | Fin (null si running) |
| `events_extracted` | INT | Eventos leídos del raw |
| `events_rejected` | INT | Eventos rechazados en validate |
| `metrics_written` | INT | Filas upserted en mart |
| `watermark_before` | JSONB | Estado del watermark al inicio |
| `watermark_after` | JSONB | Estado del watermark al finalizar |
| `error_summary` | TEXT | Mensaje acotado si falló |
| `triggered_by` | TEXT | `manual` \| `backfill` \| `scheduler` (cuando exista) |

**Clave de unicidad lógica:** `(pipeline_name, processing_date, run_id)` — permite múltiples intentos auditables; el mart solo refleja el último run exitoso por `processing_date`.

### 4.4 Checkpoint — `pipeline_watermarks` (nueva)

Estado incremental por pipeline para extract recuperable.

| Columna | Tipo | Descripción |
| --- | --- | --- |
| `pipeline_name` | TEXT PK | `telemetry-kpi-daily` |
| `last_occurred_at` | TIMESTAMPTZ | Último `timestamp` procesado |
| `last_event_id` | TEXT | Desempate cuando `timestamp` coincide |
| `updated_at` | TIMESTAMPTZ | Última actualización |
| `updated_by_run_id` | UUID | Run que avanzó el watermark |

---

## 5. Idempotencia

> **Definición operativa:** ejecutar el pipeline dos veces sobre el mismo `processing_date` produce exactamente las mismas filas en el mart, sin duplicados ni corrupción.

### 5.1 Por stage

| Stage | Mecanismo | Comportamiento en re-ejecución |
| --- | --- | --- |
| S1 Ingest | `event_id` UNIQUE en `telemetry_events` | Re-POST del mismo evento incrementa `rejected`, no duplica filas |
| S2 Extract | Watermark + ventana `[start, end)` por `processing_date` | Misma ventana → mismo conjunto de eventos |
| S3 Validate | Validación determinista contra `event-schemas.json` | Mismos eventos → mismos válidos/rechazados |
| S4 Transform | Funciones puras en `build_metrics()` | Misma entrada → misma salida |
| S5 Load | UPSERT en clave natural del mart | Segunda ejecución reemplaza filas del día, no suma |

### 5.2 Orden estable para KPI 3 (FIFO)

El emparejamiento recepción-despacho depende del orden de eventos. Regla de desempate:

1. Ordenar por `timestamp` ASC
2. Si empate, por `event_id` ASC (lexicográfico, UUID v4)

Documentar esta regla en tests de contrato para que re-ejecuciones sean bit-a-bit reproducibles.

### 5.3 Late data (eventos tardíos)

Eventos que llegan después de procesar un día se incorporan en:

- **Reconciliación rolling:** reprocesar los últimos **3 días** (`D-3` … `D-1`) en cada run principal, con upsert idempotente en mart.
- **Backfill manual:** CLI con rango explícito de fechas (ver §8).

---

## 6. Observabilidad y auditabilidad

> **Definición operativa:** cada ejecución deja suficiente rastro para saber qué pasó, cuándo, con qué datos y por qué falló si aplica.

### 6.1 Trazas por run

Al iniciar un run:

1. Insertar fila en `pipeline_runs` con `status=running`, `watermark_before`.
2. Emitir log estructurado JSON: `{ "run_id", "pipeline_name", "processing_date", "stage", "event" }`.

Al finalizar cada stage, actualizar contadores en memoria y loguear `{ "stage", "duration_ms", "count" }`.

Al terminar:

1. Actualizar `pipeline_runs` con `status`, contadores, `watermark_after`, `finished_at`.
2. Si `partial`: registrar en `error_summary` qué stage falló y cuántos registros se escribieron.

### 6.2 Lineage

Cada fila del mart incluye:

- `pipeline_run_id` → join a `pipeline_runs`
- `computed_at` → cuándo se calculó
- `schema_version` → versión del contrato de salida

Operaciones puede auditar: *“La tasa de cumplimiento del 2026-06-28 para `los_angeles` fue calculada en el run `abc-123` a las 02:14 UTC con 1.842 eventos extraídos.”*

### 6.3 Artefactos opcionales

Snapshot JSON del reporte en `data/process/telemetry/reports/{processing_date}.json` para auditoría offline y diff entre ejecuciones. No sustituye al mart; es evidencia complementaria.

### 6.4 Métricas operativas (post-implementación)

| Métrica | Umbral sugerido |
| --- | --- |
| Duración total del run | Alerta si > 15 min |
| `events_rejected / events_extracted` | Alerta si > 5% |
| Runs con `status=failed` consecutivos | Alerta si ≥ 2 |
| Freshness mart | Métricas de D-1 disponibles antes de 04:00 UTC |

---

## 7. Recuperabilidad

> **Definición operativa:** si el pipeline falla a mitad, la siguiente ejecución sabe dónde reanudar sin duplicar ni omitir datos.

### 7.1 Checkpoint por stage

```
extract_done → validate_done → transform_done → load_done
```

| Punto de fallo | Estado de side effects | Acción de recovery |
| --- | --- | --- |
| Antes de `extract_done` | Ninguno | Re-run completo; watermark sin cambios |
| Tras extract, antes de load | Run en `running` o `failed` | Re-run desde extract; mart del día no tocado o rollback transaccional |
| Durante load | Posible escritura parcial | Transacción por `processing_date`: commit solo al finalizar upsert del día |
| Tras load exitoso | Mart + watermark actualizados | Re-run idempotente (upsert) si se necesita corrección |

### 7.2 Watermark incremental

Consulta de extract para modo incremental (complementa ventana por `processing_date`):

```sql
WHERE timestamp > :last_occurred_at
   OR (timestamp = :last_occurred_at AND event_id > :last_event_id)
ORDER BY timestamp ASC, event_id ASC
```

El watermark solo avanza al finalizar un run con `status=succeeded` (o `partial` con load completado y documentado).

### 7.3 Runs huérfanos

Si un run queda en `running` > 30 min (proceso muerto):

1. Marcar como `failed` con `error_summary=timeout_orphan`.
2. Permitir nuevo run para el mismo `processing_date`.
3. No avanzar watermark del run huérfano.

### 7.4 Backfill

Interfaz prevista (implementación en fase siguiente al diseño):

```bash
python -m data.pipelines.telemetry_kpi_daily.run \
  --start-date 2026-06-01 \
  --end-date 2026-06-07 \
  --triggered-by backfill
```

Cada día del rango genera un `run_id` distinto en `pipeline_runs`. El mart queda idempotente por día.

---

## 8. Métricas y transformaciones

Reutilizar **`services/telemetry/analysis.py`** sin duplicar lógica de negocio. Mapeo KPI → función:

| KPI | `metric_name` | Función | Eventos fuente |
| --- | --- | --- | --- |
| 1 — Tasa de cumplimiento | `order_fulfillment_rate` | `compute_fulfillment_rate()` | `dispatch_order_created`, `dispatch_order_failed` |
| 2 — Discrepancias de stock | `stock_discrepancy_frequency` | `compute_stock_discrepancy_frequency()` | `direct_stock_edit_rejected` |
| 3 — Ciclo recepción-despacho | `receiving_dispatch_cycle_time` | `compute_receiving_dispatch_cycle_time()` | `receiving_order_created`, `dispatch_order_created` |

**Segmentación obligatoria:** toda agregación incluye `warehouse`. Los dashboards de Thomas nunca mezclan totales sin desglose (restricción de negocio del plan de telemetría).

### 8.1 Evolución de `GET /telemetry/report`

| Modo | Comportamiento |
| --- | --- |
| Mart disponible para el periodo | Leer `telemetry_kpi_daily` |
| Mart ausente (dev, primer deploy) | Fallback a cálculo live vía `build_metrics()` (comportamiento actual) |
| `force_refresh=true` | Ignorar cache en memoria; preferir mart si existe |

---

## 9. Estructura en el monorepo

```
data/pipelines/
  PIPELINE_DESIGN.md              ← este documento
  README.md                       ← índice de pipelines
  telemetry-kpi-daily/
    README.md                     ← cómo ejecutar el pipeline (dev/staging/prod)
    config.yaml                   ← ventana, late-data days, nombres de métricas
    run.py                        ← entry point (fase implementación)
    stages/
      extract.py
      validate.py
      load.py

services/telemetry/
  analysis.py                     ← transform (sin mover lógica de negocio)

services/trackflow-api/
  trackflow_api/routes/telemetry.py   ← ingest + serve
  trackflow_api/models.py             ← TelemetryEvent + tablas pipeline (fase implementación)
```

**Principio:** el pipeline orquesta stages; la lógica KPI permanece en `services/telemetry/`.

---

## 10. Pipeline stream (fase posterior — solo diseño)

Eventos con `processing_mode=stream` (`dispatch_order_failed`, `stock_threshold_triggered`, `direct_stock_edit_rejected`) **no pasan por `telemetry-kpi-daily`**. Pipeline separado:

| Aspecto | Decisión |
| --- | --- |
| Nombre | `telemetry-stream-alerts` |
| Trigger | Poll o webhook post-ingest (TBD en implementación) |
| Idempotencia | Tabla `alert_deliveries` con UNIQUE `(event_id, channel)` |
| Observabilidad | Log por evento + contador de alertas emitidas |
| Recoverability | Reprocesar eventos stream no entregados desde cursor en raw |

Fuera del alcance de implementación inmediata; documentado para completitud del flujo que operaciones preguntó en la RFP.

---

## 11. Restricciones y garantías

| Restricción | Implementación en pipeline |
| --- | --- |
| Sin PII en métricas | Solo agregados; payloads no se copian al mart |
| Aislamiento por almacén | `warehouse` en clave natural del mart |
| Contrato de eventos | Validate stage rechaza claves no declaradas en `event-schemas.json` |
| Retención | Raw 90 días; mart 12 meses |

| Garantía | Valor objetivo |
| --- | --- |
| RPO (pérdida de eventos aceptados) | 0 — PK en ingesta + commit explícito |
| Idempotencia de re-run | 100% para mismo `processing_date` |
| Late data | Ventana rolling de 3 días |
| Freshness | Métricas D-1 antes de 04:00 UTC (una vez exista scheduler) |

**Scheduler / cron:** explícitamente **fuera de alcance** de este documento. Se definirá cuando la arquitectura e implementación del pipeline estén completas.

---

## 12. Plan de implementación (post-diseño)

Orden sugerido para la fase de código (sin orquestación):

1. Migraciones SQL: `telemetry_kpi_daily`, `pipeline_runs`, `pipeline_watermarks`.
2. Stages `extract`, `validate`, `load` bajo `data/pipelines/telemetry-kpi-daily/`.
3. Entry point `run.py` con flags `--processing-date`, `--start-date`/`--end-date` (backfill).
4. Integrar serve path: `GET /telemetry/report` lee mart con fallback live.
5. Tests: idempotencia (doble run mismo día), watermark, late data, orphan run.
6. Verificación manual: comparar salida mart vs `scripts/telemetry_report.py` para ventana fija.

---

## 13. Verificación del diseño (checklist CTO)

- [x] Flujo captura → ingest → raw → transform → mart → dashboard documentado
- [x] Idempotencia definida por stage con claves naturales
- [x] Schema de auditoría (`pipeline_runs`, watermarks, lineage en mart)
- [x] Estrategia de watermark, backfill y late data
- [x] Manejo de fallos y runs huérfanos
- [x] Reutilización de `analysis.py` y `event-schemas.json`
- [x] Scheduler explícitamente diferido
- [ ] Implementación de stages (siguiente fase)
- [ ] Tests de contrato de idempotencia (siguiente fase)

---

## Referencias

- [`docs/telemetry/telemetry-plan.md`](../../docs/telemetry/telemetry-plan.md)
- [`docs/telemetry/event-schemas.json`](../../docs/telemetry/event-schemas.json)
- [`services/telemetry/analysis.py`](../../services/telemetry/analysis.py)
- [`services/trackflow-api/trackflow_api/routes/telemetry.py`](../../services/trackflow-api/trackflow_api/routes/telemetry.py)
- [`scripts/telemetry_report.py`](../../scripts/telemetry_report.py)
