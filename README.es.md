# Monorepo del Proyecto de Empresa de AI Engineering

[![4Geeks Academy](https://img.shields.io/badge/4Geeks-Academy-blue)](https://4geeksacademy.com)
[![AI Engineering](https://img.shields.io/badge/track-AI%20Engineering-green)](https://4geeksacademy.com/es/coding-bootcamps/ai-engineering)

Monorepo del proyecto transversal de AI Engineering. Este repositorio centraliza interfaces de producto, servicios backend, tooling interno, documentación, recursos reutilizables y convenciones de trabajo para agentes.

## Estructura del repositorio

```text
ai-engineering-company-project-monorepo/
+-- README.md
+-- README.es.md
+-- CONTEXT.md
+-- agents/
+-- data/
+-- docs/
+-- infra/
+-- internal/
+-- mcps/
+-- packages/
¦   +-- shared/
+-- scripts/
+-- services/
+-- shared/
+-- skills/
+-- uis/
+-- workflows/
```

## Áreas actuales del producto

- `uis/trackflow-portal`: sitio corporativo y workspace interno en Next.js.
- `uis/talent-pipeline-tracker`: interfaz interna de people y talent.
- `uis/web`: interfaz del analizador de incidentes para carga y exportación.
- `services/api`: backend FastAPI con endpoints de auth, users e incidents.
- `internal/trackflow-coding-fundamentals`: módulo original de lógica de negocio en TypeScript reutilizado entre hitos.

## Comandos raíz

- `npm run dev`: levanta el portal de TrackFlow desde la raíz.
- `npm run build`: compila el portal de TrackFlow desde la raíz.
- `npm run lint`: ejecuta lint del portal de TrackFlow desde la raíz.
- `npm run typecheck`: ejecuta typecheck del portal de TrackFlow desde la raíz.
- `npm run dev:web`: levanta la UI web del analizador de incidentes.
- `npm run dev:talent`: levanta la UI del talent pipeline tracker.
- `npm run console:business-logic`: ejecuta la demo de consola de la lógica de negocio original.

## Reglas de trabajo

1. Sustituye el `CONTEXT.md` placeholder por el contexto asignado antes de construir features de hitos concretos.
2. Lee `AGENTS.md` y los archivos de `memory-bank/` antes de hacer cambios.
3. Prefiere extender los módulos de dominio existentes en lugar de duplicar lógica entre servicios e interfaces.
4. Mantén la compatibilidad con Codespaces preservando scripts ejecutables desde la raíz y ejemplos de entorno local.
