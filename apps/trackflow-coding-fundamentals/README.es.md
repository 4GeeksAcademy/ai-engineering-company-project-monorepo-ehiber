# TrackFlow Coding Fundamentals

Utilidades TypeScript para el Hito 2 del proyecto de compañía de TrackFlow.

## Ejecutar

Instala las dependencias:

```bash
npm install
```

Valida TypeScript:

```bash
npm run typecheck
```

Ejecuta el demo de consola:

```bash
npm run console
```

## Estructura

- `src/types/models.ts`: entidades de negocio y tipos literales de TrackFlow.
- `src/utils/collections.ts`: helpers de filtrado y ordenamiento.
- `src/utils/search.ts`: helpers de búsqueda lineal y binaria.
- `src/utils/transformations.ts`: reportes y agregaciones.
- `src/utils/validations.ts`: reglas de validación de negocio.
- `src/data/sample-data.ts`: objetos literales de ejemplo alineados con `CONTEXT.md`.
- `src/demo.ts`: demo pequeña en terminal de las utilidades implementadas.
