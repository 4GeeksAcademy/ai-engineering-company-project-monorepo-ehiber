# `services/trackflow-api`

FastAPI backend service for TrackFlow operational workflows.

## Current scope

- JWT authentication and route protection
- User CRUD
- Supplier directory API
- Incident CSV analysis endpoints
- Password reset flow via Resend (or dev email file fallback)
- Async task queue (DEV-55): Celery + Redis for long-running pipeline triggers
- RAG knowledge assistant (Hito 7): Qdrant vector store, LiteLLM embeddings/completions, `POST /api/knowledge/ask`

## RAG knowledge assistant (Hito 7)

Copy the RAG/LiteLLM/Qdrant variables from the repo root [`.env.example`](../../.env.example).

```bash
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=trackflow_knowledge
LITELLM_API_KEY=your-openrouter-api-key
LITELLM_API_BASE=https://openrouter.ai/api/v1
RAG_EMBEDDING_MODEL=openrouter/perplexity/pplx-embed-v1-0.6b
RAG_LLM_MODEL=openrouter/deepseek/deepseek-v4-flash
RAG_EMBEDDING_DIMENSION=1024
RAG_TOP_K=3
RAG_KNOWLEDGE_SOURCE_DIR=docs/rag
```

LiteLLM uses a single `LITELLM_API_KEY` (OpenRouter) for both embedding and answer generation. After changing models or dimension, reindex with `--recreate`.

### Dependencies (uv)

Source of truth: `pyproject.toml` + `uv.lock`. Docker installs with `uv sync --frozen` into `/opt/venv` (outside bind mounts so a Windows host `.venv` is never used inside Linux containers).

```bash
cd services/trackflow-api
uv sync --all-extras
```

Do not use `pip install` or `pipenv` for this service.

### Docker Compose (Qdrant + API + Backoffice)

```bash
# Core RAG stack
docker compose up -d --build qdrant redis api backoffice

# Index knowledge base once (recreates collection)
docker compose --profile rag run --rm rag-index
```

- Qdrant: `http://localhost:6333`
- API: `http://localhost:8000`
- Backoffice UI: `http://localhost:3002/backoffice/knowledge`

Inside containers, `QDRANT_URL` is forced to `http://qdrant:6333` and docs are read from `/workspace/docs/rag`.

### Index knowledge base (host / uv)

```bash
cd services/trackflow-api
uv run python ../../scripts/index_knowledge_base.py --recreate
```

### LangGraph knowledge agent

`POST /api/knowledge/ask` invokes a compiled LangGraph graph (`receive_question` → conditional → `retrieve` → conditional → `generate_*`). Milestone 7 functions are reused from [`data/pipelines/rag`](../../data/pipelines/rag/) (wrappers over `trackflow_api.rag`).

Each run returns `run_id`, `trace`, and `checkpointed`. Inspect a prior run with:

```bash
curl http://localhost:8000/api/knowledge/runs/<run_id>
```

Agent evals:

```bash
cd services/trackflow-api
uv run pytest ../../tests/pipelines/test_rag_agent_evals.py -q
```

### Ask endpoint

```bash
curl -X POST http://localhost:8000/api/knowledge/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"¿Cuál es la ventana de devolución estándar?"}'
```

### Evaluation

```bash
cd services/trackflow-api
uv run pytest tests/test_rag_*.py
uv run python ../../scripts/eval_rag.py
```

## Async task queue (DEV-55)

Copy the Redis/Celery variables from the repo root [`.env.example`](../../.env.example).

```bash
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
FLOWER_PORT=5555
```

### Docker Compose (recommended)

```bash
docker compose up redis api celery-worker flower
```

- API: `http://localhost:8000`
- Flower: `http://localhost:5555`
- `POST /telemetry/pipeline/run` returns `202 Accepted` with `{ task_id, status: "pending" }`
- `GET /tasks/{task_id}` returns `pending | started | success | failure | dead_letter`

The Celery worker runs the KPI pipeline via the direct (`--no-prefect`) path, so **Prefect Cloud is optional**.

### Local processes (without Docker)

```bash
docker compose up redis qdrant -d
cd services/trackflow-api
uv sync --all-extras
uv run celery -A trackflow_api.worker worker --loglevel=info
uv run uvicorn main:app --reload
```

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
cd services/trackflow-api
uv sync --all-extras
uv run uvicorn main:app --reload
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
