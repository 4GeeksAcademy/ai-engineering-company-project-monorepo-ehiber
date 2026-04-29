# Talent Pipeline Tracker

Internal TrackFlow People & Talent tool for managing candidate records from the Tracker API.

## Environment

Create `.env.local` with:

```bash
NEXT_PUBLIC_API_URL=https://playground.4geeks.com/tracker/api/v1
```

You should also keep `.env.example` updated with the same variable.

## Commands

```bash
npm install
npm run dev
npm run typecheck
npm run lint
```

## Main features

- Candidate list with search, status filter, and stage filter.
- Candidate detail with status/stage updates.
- Internal notes create and delete.
- Candidate create and edit forms.
- Loading, success, empty, and error states across async operations.
