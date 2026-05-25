# `services/trackflow-api`

FastAPI backend service for TrackFlow operational workflows.

## Current scope

- JWT authentication and route protection
- User CRUD
- Supplier directory API
- Incident CSV analysis endpoints

## Suggested local run

```bash
pip install -r services/trackflow-api/requirements.txt
cd services/trackflow-api
uvicorn main:app --reload
```

The folder name uses kebab-case like the UI apps (`uis/trackflow-portal`). The Python package inside is `trackflow_api` because import paths cannot contain hyphens.

## Layout

```text
services/trackflow-api/
  main.py                 # uvicorn entrypoint
  trackflow_api/          # Python application package
    main.py               # FastAPI app factory
    routes/               # HTTP endpoints
    services/             # business logic
    repositories/         # TinyDB access
    domain/               # domain rules
    core/                 # config, security, database
```
