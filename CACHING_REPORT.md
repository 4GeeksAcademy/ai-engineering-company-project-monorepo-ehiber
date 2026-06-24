# CACHING_REPORT.md — TrackFlow

Informe técnico del sprint de caching aplicado al monorepo TrackFlow (`services/trackflow-api` + `uis/backoffice`).

## Resumen ejecutivo

Se implementó caching deliberado en los endpoints de lectura con mayor impacto operativo, junto con optimización de consultas en inventario, middleware de timing, invalidación explícita en escrituras y mejoras frontend en backoffice: **2 rutas con lazy loading**, **useMemo en filtrado de historial de órdenes** y reducción de refetch en incidentes. La medición se realizó con datos de carga realista (~500 SKUs, ~5000 movimientos, ~200 suppliers, ~500 incidentes).

## Metodología de medición

1. **Seed de volumen**: `python scripts/seed_performance_data.py`
2. **Benchmark API**: `python scripts/benchmark_api.py --requests 30`
3. **Middleware de timing** en `trackflow_api/main.py` (logger `api.timing`)
4. Entorno local SQLite (`data/inventory-performance.db`) + TinyDB (`data/app-performance.json`)

### Volumen de datos (después del seed)

| Recurso | Filas aprox. |
|---------|--------------|
| SKUs | 500 |
| Movimientos (in+out) | 5000 |
| Suppliers | 200 |
| Incidentes gestionados | 500 |

## Candidatos evaluados y descartados

| Recurso | Decisión | Motivo |
|---------|----------|--------|
| `POST /auth/login` | No cachear | Respuesta por sesión; riesgo de seguridad |
| `POST /api/incidents/analyze` | No cachear | Upload + cálculo único por archivo |
| `GET /api/incidents/results/latest` | No cachear | Ya lee JSON persistido; bajo ROI |
| `GET /inventory/products/{id}` | No cachear | Baja frecuencia vs listado completo |
| `GET /api/incidents` (list) | No cachear (solo TTL implícito vía UI) | Alta variabilidad por filtros; beneficio menor que summary |
| Página Candidates | Lazy load | Modulo mock; no esta en flujo inicial del backoffice |
| Página Incidents | Lazy load | Formulario + tabla + hooks API; no necesario en carga inicial |

## Decisiones implementadas

| Recurso | ms antes (cold / p50*) | ms después (cached p50) | TTL | Invalidación | Trade-off |
|---------|------------------------|-------------------------|-----|--------------|-----------|
| `GET /inventory/products` | ~69 ms (1ª petición) | ~5 ms | 20 s | `POST /products`, inbound/outbound | Stock puede estar desfasado ≤20 s |
| `GET /inventory/orders` | ~245 ms (1ª petición) | ~178 ms** | 30 s | inbound/outbound | Payload grande; caché evita joins DB |
| `GET /suppliers` | ~22 ms (1ª petición) | ~6 ms | 60 s | create/update/delete supplier | Tarifas/estado pueden tardar ≤60 s |
| `GET /api/incidents/summary` | ~20 ms (1ª petición) | ~12 ms | 60 s | create/update incident | Dashboard no instantáneo tras mutación |

\*Benchmark con caché activa; la 1ª petición por endpoint simula cold start dentro de la ventana de prueba.  
\*\*El listado de órdenes cacheado sigue costando deserializar ~5000 movimientos; el beneficio principal es evitar joins SQL repetidos.

### Backend — detalle técnico

- **`trackflow_api/core/cache.py`**: caché en proceso con TTL e invalidación por prefijo.
- **`GET /inventory/products`**: agregación batch de stock (`GROUP BY`) + caché TTL 20 s.
- **`GET /inventory/orders`**: caché TTL 30 s del historial consolidado.
- **`list_suppliers()`**: caché por clave `(country, category)`.
- **`get_incident_summary()`**: caché TTL 60 s; invalidación en create/update.
- **`trackflow_api/core/timing.py`**: middleware HTTP de latencia.

### Frontend — detalle técnico

#### Lazy loading (2 rutas)

| Ruta | Archivo | Justificación |
|------|---------|---------------|
| `/backoffice/candidates` | `candidates/page.tsx` → `candidates-page-content.tsx` | Modulo mock de pipeline de talento; no forma parte del flujo operativo inicial (inventory/suppliers). Diferir su JS reduce el bundle de la shell protegida. |
| `/backoffice/incidents` | `incidents/page.tsx` → `incidents-page-content.tsx` | Pantalla pesada: formulario de alta, snapshot, tabla con selects de status y hook `useIncidentsData`. Solo se visita bajo demanda desde la navegacion lateral. |

Verificacion: en DevTools → Network, el chunk de cada modulo aparece al navegar a la ruta, no en la primera carga de `/backoffice/inventory/products`.

#### useMemo — filtrado local de historial de ordenes

En `inventory/orders/page.tsx`, `filteredOrders` memoiza el filtrado sobre el listado completo devuelto por `GET /inventory/orders`:

- **Calculo no trivial**: con seed de performance (~5000 movimientos), cada filtro recorre miles de filas aplicando fecha, tipo, warehouse y busqueda por SKU/nombre.
- **Dependencias**: `[fromDate, movementType, orders, skuQuery, toDate, warehouse]` — solo recalcula cuando cambia un filtro o llega un nuevo payload de API, no en cada render del formulario de fechas u otros estados de UI ajenos.
- **Beneficio medido en Profiler**: evita repetir O(n) en re-renders causados por interacciones que no alteran criterios de filtro.

#### Reduccion de peticiones — incidentes

**`useIncidentsData`**: al cambiar filtros solo se refetcha el listado; el summary se carga en mount y tras mutaciones (`refresh` / `loadSummary`).

### Privacidad de claves de cache

Ninguna clave incluye JWT, email, `user_uuid` ni identificadores de sesion. Solo recursos compartidos de catalogo/operaciones:

- `inventory:products`, `inventory:orders`
- `suppliers:list:country=*:category=*`
- `incidents:summary`

Los endpoints protegidos por auth devuelven datos operativos globales del backoffice, no respuestas personalizadas por usuario.

## Qué NO se cacheó y por qué

- Endpoints de autenticación y mutación: integridad y seguridad.
- Listados altamente parametrizados (`GET /api/incidents` con 4 filtros): clave de caché explosiva; se priorizó summary.
- Análisis CSV: operación puntual, no repetitiva en ráfaga.

## Riesgos y límites

| Riesgo | Mitigación actual | Evolución |
|--------|-------------------|-----------|
| Caché en memoria (single process) | Aceptable en dev/MVP | Redis para multi-réplica |
| Stale stock en UI | TTL corto (20 s) + invalidación en movimientos | WebSocket/push en producción |
| Payload grande en orders cache | TTL + invalidación | Paginación server-side |

## Verificación

```bash
# Tests backend (incluye invalidación de caché)
cd services/trackflow-api && python -m pytest tests/test_cache.py -q

# Seed + benchmark local
python scripts/seed_performance_data.py
python scripts/benchmark_api.py --requests 30
```

**Estado**: 25 tests pytest passing (incl. 3 tests de caché).

## Scripts añadidos

- `scripts/seed_performance_data.py` — bulk seed para benchmarks locales
- `scripts/benchmark_api.py` — latencia p50/p95 por endpoint
