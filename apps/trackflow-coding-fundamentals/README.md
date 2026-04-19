# TrackFlow Coding Fundamentals

TypeScript utilities for Milestone 2 of the TrackFlow company project.

## Run

Install dependencies:

```bash
npm install
```

Validate TypeScript:

```bash
npm run typecheck
```

Run the local console demo:

```bash
npm run console
```

## Structure

- `src/types/models.ts`: TrackFlow business entities and literal types.
- `src/utils/collections.ts`: filtering and sorting helpers.
- `src/utils/search.ts`: linear and binary search helpers.
- `src/utils/transformations.ts`: reports and aggregations.
- `src/utils/validations.ts`: business validation rules.
- `src/data/sample-data.ts`: literal sample objects aligned with `CONTEXT.md`.
- `src/demo.ts`: small terminal demo of the implemented utilities.
