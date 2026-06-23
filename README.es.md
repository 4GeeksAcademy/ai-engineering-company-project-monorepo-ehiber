# Monorepo del Proyecto de Empresa de AI Engineering

[![4Geeks Academy](https://img.shields.io/badge/4Geeks-Academy-blue)](https://4geeksacademy.com)
[![AI Engineering](https://img.shields.io/badge/track-AI%20Engineering-green)](https://4geeksacademy.com/es/coding-bootcamps/ai-engineering)

Monorepo del proyecto transversal de AI Engineering. Este repositorio centraliza interfaces de producto, servicios backend, tooling interno, documentaci�n, recursos reutilizables y convenciones de trabajo para agentes.

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
�   +-- shared/
+-- scripts/
+-- services/
+-- shared/
+-- skills/
+-- uis/
+-- workflows/
```

## �reas actuales del producto

- `uis/trackflow-portal`: sitio corporativo y workspace interno en Next.js.
- `uis/backoffice`: workspace dedicado de operaciones internas para inventario, suppliers, incidents y seguimiento de candidates.
- `services/trackflow-api`: backend FastAPI con endpoints de auth, users, suppliers e incidents.
- `internal/trackflow-coding-fundamentals`: m�dulo original de l�gica de negocio en TypeScript reutilizado entre hitos.

## Comandos ra�z

- `npm run dev`: levanta el portal de TrackFlow desde la ra�z.
- `npm run build`: compila el portal de TrackFlow desde la ra�z.
- `npm run lint`: ejecuta lint del portal de TrackFlow desde la ra�z.
- `npm run typecheck`: ejecuta typecheck del portal de TrackFlow desde la ra�z.
- `npm run dev:backoffice`: levanta la UI consolidada de backoffice.
- `npm run console:business-logic`: ejecuta la demo de consola de la l�gica de negocio original.

## Reglas de trabajo

1. Sustituye el `CONTEXT.md` placeholder por el contexto asignado antes de construir features de hitos concretos.
2. Lee `AGENTS.md` y los archivos de `memory-bank/` antes de hacer cambios.
3. Prefiere extender los m�dulos de dominio existentes en lugar de duplicar l�gica entre servicios e interfaces.
4. Mant�n la compatibilidad con Codespaces preservando scripts ejecutables desde la ra�z y ejemplos de entorno local.
