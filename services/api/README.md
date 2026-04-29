# `services/api`

FastAPI backend service for TrackFlow operational workflows.

## Current scope

- JWT authentication and route protection
- User CRUD
- Incident CSV analysis endpoints

## Suggested local run

```bash
pip install -r services/api/requirements.txt
uvicorn services.api.app.main:app --reload
```

If you are already inside `services/api`, use:

```bash
uvicorn main:app --reload
```
