# `services/trackflow-api`

FastAPI backend service for TrackFlow operational workflows.

## Current scope

- JWT authentication and route protection
- User CRUD
- Supplier directory API
- Incident CSV analysis endpoints
- Password reset flow via Resend (or dev email file fallback)

## Password reset environment variables

```bash
TRACKFLOW_RESEND_API_KEY=your-resend-api-key
TRACKFLOW_PASSWORD_RESET_FROM_EMAIL=TrackFlow <onboarding@resend.dev>
TRACKFLOW_PASSWORD_RESET_APP_URL=http://localhost:3000
TRACKFLOW_PASSWORD_RESET_EXPIRE_MINUTES=30
```

When `TRACKFLOW_RESEND_API_KEY` is empty, reset links are written to `data/dev-emails/last_password_reset.txt` for local testing.

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
