# Plan de Telemetría — TrackFlow Fase 1

**Documento:** respuesta a la RFI de dirección sobre capacidad analítica del sistema de inventario  
**Autor:** TrackFlow Tech  
**Estado:** Diseño — sin instrumentación implementada  
**Referencia de contexto:** [`docs/TELEMETRY_PHASE_1.MD`](../TELEMETRY_PHASE_1.MD)  
**Esquemas:** [`event-schemas.json`](./event-schemas.json)

---

## 1. Resumen ejecutivo

TrackFlow opera un backend FastAPI con inventario relacional en Supabase bajo la regla de negocio no negociable: **el stock solo se modifica mediante `ReceivingOrder` y `DispatchOrder` trazables a un usuario**. El sistema funciona, pero el equipo de operaciones no puede responder preguntas básicas sobre volumen, errores, alertas ni fricción de uso.

Este plan define **qué eventos capturar**, **por qué**, **cómo estructurarlos** y **si procesarlos en stream o batch**, antes de escribir código de instrumentación. La telemetría es **greenfield**: no existe infraestructura previa; todo se construirá en la fase de implementación posterior.

**Decisión de alcance Fase 1:** ocho eventos — los seis de inventario del brief más `user_login_failed` (seguridad operativa) y `dispatch_form_abandoned` (fricción en despachos). El resto de candidatos de backoffice se documentan como exclusiones.

---

## 2. Stakeholders y preguntas que responde el plan

| Stakeholder | Rol | Preguntas que la telemetría debe permitir responder |
| --- | --- | --- |
| Ana Whitfield | Head of Warehouse Operations | ¿Cuántas órdenes de salida por día? ¿Qué productos acumulan más errores? ¿Cuándo se activan alertas de stock mínimo? |
| Thomas Harry | CEO | ¿Qué almacén tiene peor cumplimiento? ¿Hay riesgo SLA en despachos US? ¿Los datos están segmentados por ubicación? |
| TrackFlow Tech | Implementación | ¿Dónde instrumentar? ¿Qué envelope usar? ¿Stream o batch por evento? |

---

## 3. Modelo de dominio (referencia canónica)

El plan usa los nombres de entidad definidos en el brief. Toda instrumentación futura debe referenciarlos exactamente.

| Entidad | Descripción |
| --- | --- |
| `SKU` | Unidad de stock rastreada por almacén |
| `ReceivingOrder` | Envío entrante que incrementa stock |
| `DispatchOrder` | Entrega saliente que reduce stock |

Campos clave en payloads de eventos de inventario: `sku_id`, `sku_code`, `client_id` (opaco), `warehouse` (`los_angeles` \| `zaragoza`), `created_by` (UUID opaco de TinyDB).

---

## 4. KPIs y trazabilidad de eventos

### KPI 1 — Tasa de cumplimiento de pedidos

**Definición (brief):** proporción de `DispatchOrder` completados exitosamente frente a los rechazados **por stock insuficiente**.

| Aspecto | Decisión |
| --- | --- |
| Numerador | `dispatch_order_failed` donde `failure_reason = insufficient_stock` |
| Denominador | `dispatch_order_created` + fallos por stock insuficiente del mismo periodo |
| Excluido del KPI | Fallos por SKU desconocido, validación, warehouse mismatch — se registran como eventos pero no entran en este ratio |
| Segmentación | Por `warehouse`, `sku_id`, `client_id` |
| Procesamiento | Batch diario para dashboards; el evento fuente `dispatch_order_failed` se emite en **stream** por SLA |

**Decisión de negocio que habilita:** detectar SKUs o almacenes con problemas crónicos de disponibilidad; marcar clientes en riesgo de incumplimiento de SLA.

### KPI 2 — Frecuencia de discrepancias de stock

**Definición (brief):** número de intentos de edición directa de stock rechazados por la API por almacén por día.

| Aspecto | Decisión |
| --- | --- |
| Fuente | `direct_stock_edit_rejected` |
| Agregación | COUNT por `warehouse` y día |
| Procesamiento | **Stream** — señal de auditoría; un pico puede indicar proceso roto o formación insuficiente |

**Decisión de negocio que habilita:** identificar almacenes donde los operarios intentan atajos manuales; activar auditoría de procesos.

### KPI 3 — Tiempo de ciclo recepción-despacho

**Definición (brief):** tiempo promedio entre un `ReceivingOrder` y el primer `DispatchOrder` que consume del mismo lote de SKU.

| Aspecto | Decisión |
| --- | --- |
| Regla de lote | **FIFO por `sku_id` + `warehouse`**: cada unidad recibida forma parte de una cola; el primer despacho consume unidades de la recepción más antigua con saldo pendiente |
| Emparejamiento | Job batch nocturno que recorre movimientos ordenados por `created_at` y asigna cantidades despachadas a recepciones abiertas |
| Métrica | `AVG(dispatch_order.created_at − receiving_order.created_at)` por par emparejado, segmentado por `warehouse` |
| Eventos fuente | `receiving_order_created`, `dispatch_order_created` |
| Procesamiento | **Batch** diario — no requiere alerta en tiempo real |

**Decisión de negocio que habilita:** medir velocidad de procesamiento por ubicación; identificar cuellos de botella antes de que impacten a clientes.

### Matriz KPI → eventos

| KPI | Eventos primarios | Eventos de apoyo |
| --- | --- | --- |
| 1 — Cumplimiento | `dispatch_order_created`, `dispatch_order_failed` | `stock_threshold_triggered` |
| 2 — Discrepancias | `direct_stock_edit_rejected` | — |
| 3 — Ciclo recepción-despacho | `receiving_order_created`, `dispatch_order_created` | — |
| Ops / seguridad (no KPI) | `user_login_failed`, `dispatch_form_abandoned` | `receiving_order_failed` |

---

## 5. Envelope común de eventos

Todo evento emitido por la plataforma comparte un envelope antes del payload específico. Las propiedades del envelope están definidas en [`event-schemas.json`](./event-schemas.json) bajo `envelope`.

| Campo | Tipo | Obligatorio | Descripción |
| --- | --- | --- | --- |
| `event_id` | UUID v4 | Sí | Identificador único del evento; idempotencia en ingesta |
| `event_name` | string | Sí | Nomenclatura `entity_action` |
| `event_version` | string | Sí | Versión del esquema (semver, ej. `1.0`) |
| `occurred_at` | ISO-8601 UTC | Sí | Momento en que ocurrió el hecho de negocio |
| `source` | enum | Sí | `trackflow-api` \| `backoffice-web` |
| `warehouse` | enum \| null | Condicional | Obligatorio en operaciones de almacén; null en auth |
| `correlation_id` | UUID \| null | No | Trazabilidad request HTTP o sesión de formulario |
| `processing_mode` | enum | Sí | `stream` \| `batch` — decisión de enrutamiento |
| `payload` | object | Sí | Propiedades específicas del evento (whitelist) |

**Regla de oro:** un evento solo se emite si alimenta un KPI definido o una decisión operativa documentada en este plan. Si no pasa la prueba, se excluye.

---

## 6. Catálogo de eventos incluidos

### Inventario

| Evento | Disparador | Fuente | Modo |
| --- | --- | --- | --- |
| `receiving_order_created` | `ReceivingOrder` registrado con éxito | API `/inventory` | Batch |
| `dispatch_order_created` | `DispatchOrder` registrado con éxito | API `/inventory` | Batch |
| `stock_threshold_triggered` | Stock de `SKU` ≤ `min_stock_threshold` tras un despacho | API post-commit despacho | Stream |
| `direct_stock_edit_rejected` | Intento de modificar stock fuera de un pedido bloqueado | API endpoint de edición directa | Stream |
| `dispatch_order_failed` | `DispatchOrder` rechazado | API `/inventory` | Stream |
| `receiving_order_failed` | `ReceivingOrder` rechazado | API `/inventory` | Batch |

### Backoffice

| Evento | Disparador | Fuente | Modo |
| --- | --- | --- | --- |
| `user_login_failed` | Credenciales incorrectas en login | API `/auth/login` | Batch |
| `dispatch_form_abandoned` | Usuario inicia formulario de despacho y abandona sin enviar | Backoffice web | Batch |

---

## 7. Decisiones stream vs batch

| Evento | Modo | Justificación operativa |
| --- | --- | --- |
| `dispatch_order_failed` | **Stream** | Fallos con `destination_country = US` en horas punta (Q4, Black Friday) tienen implicaciones contractuales de SLA. Requiere visibilidad inmediata para Ana y escalado a Thomas. |
| `stock_threshold_triggered` | **Stream** | Stock-out o stock mínimo en Los Ángeles para clientes de moda de alto volumen es accionable en minutos, no al día siguiente. |
| `direct_stock_edit_rejected` | **Stream** | Intentos de bypass de la regla de trazabilidad son señal de auditoría; un pico concentrado en un almacén requiere respuesta el mismo turno. |
| `receiving_order_created` | Batch | Tendencias de volumen entrante; agregación diaria suficiente para planificación. |
| `dispatch_order_created` | Batch | Volumen de salida por día/almacén; base del denominador del KPI 1. |
| `receiving_order_failed` | Batch | Errores de validación en recepción — análisis de calidad de datos, no urgencia operativa. |
| `user_login_failed` | Batch | Seguridad agregada (intentos/día); alerta solo si supera umbral configurable (ej. >20/hora/IP). |
| `dispatch_form_abandoned` | Batch | Fricción UX; identifica flujos rotos pero no requiere intervención en segundos. |

**Horas punta (referencia SLA):** 08:00–20:00 hora local del almacén (`America/Los_Angeles` para `los_angeles`, `Europe/Madrid` para `zaragoza`), especialmente Q4 y Black Friday.

---

## 8. Arquitectura propuesta (greenfield)

No existe telemetría implementada. La fase de implementación construirá:

```
┌─────────────────┐     ┌─────────────────┐
│  trackflow-api  │     │  backoffice-web │
│  (FastAPI)      │     │  (Next.js)      │
└────────┬────────┘     └────────┬────────┘
         │ hooks en rutas        │ telemetry client
         └──────────┬────────────┘
                    ▼
         POST /telemetry/events  (nuevo)
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
  processing_mode=stream   processing_mode=batch
         │                     │
         ▼                     ▼
  alert worker (Fase 2)    Supabase telemetry_events
  log + webhook hook       + job agregación diaria
```

| Componente | Responsabilidad |
| --- | --- |
| Emisor API | Middleware + hooks post-validación en rutas `/inventory` y `/auth/login` |
| Emisor web | Cliente compartido en backoffice; captura abandono de formulario y filtros |
| Ingesta | Endpoint `POST /telemetry/events` valida envelope + whitelist por `event_name` |
| Persistencia | Tabla `telemetry_events` en Supabase (JSONB + índices por `event_name`, `warehouse`, `occurred_at`) |
| Stream | Worker que consume eventos con `processing_mode=stream` y escribe alerta estructurada (Slack/email en Fase 2) |
| Batch | Job nocturno: agregaciones KPI, emparejamiento FIFO KPI 3, dashboards para Ana/Thomas — diseño detallado en [`data/pipelines/PIPELINE_DESIGN.md`](../../data/pipelines/PIPELINE_DESIGN.md) |

**Retención:** 90 días eventos raw; 12 meses agregados KPI.

**Consumidores:**

- **Ana:** dashboards operativos diarios por `warehouse` — volumen, errores, alertas, ciclo recepción-despacho.
- **Thomas:** vista ejecutiva con **segmentación obligatoria por `warehouse`**; nunca mezcla Los Ángeles y Zaragoza en un único total sin desglose.

---

## 9. Restricciones de negocio en telemetría

| Restricción | Implementación |
| --- | --- |
| Doble almacén | Campo `warehouse` obligatorio en todo evento de operación de almacén; dashboards filtrables |
| Aislamiento de cliente | Solo `client_id` opaco en payloads; nunca nombres de marca |
| Sin PII | `created_by` y `user_uuid` como UUIDs opacos; nunca email ni nombre de operario |
| SLA US | `dispatch_order_failed` en stream; payload incluye `destination_country` y flag `is_peak_hours` |

---

## 10. Eventos descartados y exclusiones

| Evento / módulo | Decisión | Motivo |
| --- | --- | --- |
| `user_login_succeeded` | Descartado Fase 1 | Bajo valor analítico vs ruido; el volumen de logins no alimenta ningún KPI |
| `session_expired` | Descartado Fase 1 | Redundante con `user_login_failed` para seguridad agregada |
| `sku_list_viewed` | Descartado Fase 1 | Navegación pasiva; no alimenta KPIs ni decisiones operativas urgentes |
| `warehouse_filter_applied` | Descartado Fase 1 | `warehouse` ya está en eventos de inventario; duplicaría señal |
| Módulo suppliers | Excluido Fase 1 | Fuera del alcance de KPIs de inventario de almacén |
| Módulo incidents | Excluido Fase 1 | Dominio separado; requiere plan de telemetría propio |
| Módulo candidates | Excluido Fase 1 | Pipeline de talento no relacionado con operaciones de almacén |

---

## 11. Riesgos

| Riesgo | Mitigación |
| --- | --- |
| Mezcla de almacenes en dashboards | Campo `warehouse` obligatorio; validación en ingesta; Thomas exige desglose |
| Fuga de datos entre clientes | Whitelist estricta; solo `client_id` opaco; revisión en PR de nuevos campos |
| PII accidental en payloads | Lint de esquema en CI; rechazo en ingesta si aparece clave no declarada |
| KPI 3 impreciso sin lote físico | Documentar regla FIFO como aproximación; iterar si TrackFlow adopta lotes explícitos |
| Volumen de eventos batch | Particionar tabla por mes; TTL 90 días en raw |
| `min_stock_threshold` y edición directa no implementados aún | Instrumentación depende de esos endpoints/campos; incluir en mismo sprint de telemetría |

---

## 12. Plan de implementación (Fase 2 — post-revisión)

1. Añadir `min_stock_threshold` a `SKU` y endpoint de edición directa rechazado (409).
2. Crear módulo `trackflow_api/core/telemetry.py` con emisor y validación de whitelist.
3. Exponer `POST /telemetry/events` y tabla Supabase `telemetry_events`.
4. Instrumentar rutas `/inventory` y `/auth/login`.
5. Añadir cliente de telemetría en `uis/backoffice` para `dispatch_form_abandoned`.
6. Implementar worker stream y job batch KPI.
7. Tests de contrato contra `event-schemas.json`.

---

## Referencias

- Brief: [`docs/TELEMETRY_PHASE_1.MD`](../TELEMETRY_PHASE_1.MD)
- Esquemas: [`docs/telemetry/event-schemas.json`](./event-schemas.json)
- Pipeline batch (diseño producción): [`data/pipelines/PIPELINE_DESIGN.md`](../../data/pipelines/PIPELINE_DESIGN.md)
