# Backend Architecture Proposal

## Scope

This proposal is for **TrackFlow**, the binational logistics operator described in [`CONTEXT.md`](c:/Users/ehibe/Documents/4geeks/Projects/ai-engineering-company-project-monorepo/CONTEXT.md). TrackFlow operates warehouses, last-mile delivery flows, reverse logistics, and commercial lead intake across **Mexico** and **Spain**. The backend therefore needs to support both:

- public-site workflows such as lead capture
- internal operational workflows such as logistics incidents, clients, and service requests

This is not a generic e-commerce backend. It is an operations-oriented B2B platform with sensitive business data, cross-country rules, and growing internal tooling needs.

## Recommended architectural pattern

I recommend a **domain-oriented modular monolith in FastAPI**, organized with layered boundaries inside one API service.

### Why this fits TrackFlow

TrackFlow is not yet at the stage where splitting everything into microservices is justified. The current system needs:

- fast iteration from one engineering team
- strong consistency between operational domains
- reuse of shared business rules
- a backend that can grow without becoming one giant file

A modular monolith gives TrackFlow the best balance between structure and delivery speed:

1. **Operations are connected**. Leads, incidents, warehouse operations, returns, and customer accounts are related. Starting with separate services would add network and deployment complexity before business value appears.
2. **The company is still building the first internal platform layer**. Right now, clarity of code ownership matters more than horizontal scale.
3. **FastAPI works especially well with modular packages and router separation**, so the framework naturally supports this pattern.

### Why not MVC as the main organizing principle

A traditional MVC framing is less useful here because most of TrackFlow's backend work will be API-first and domain-heavy, not server-rendered page heavy. The important boundaries are not "controller vs view", but:

- HTTP layer
- business rules
- persistence
- shared infrastructure

### Why not microservices yet

Microservices would be premature because they would introduce:

- duplicated authentication concerns
- multiple deployment surfaces
- more environment configuration
- harder local development for students and coding agents

TrackFlow should start with one API, but keep clean domain seams so modules can be extracted later if real scale or org structure demands it.

## Proposed backend structure

The backend should live in `services/trackflow-api` and use a FastAPI package structure aligned with the official "Bigger Applications - Multiple Files" guidance:

```text
services/
  api/
    app/
      main.py
      api/
        routers/
          health.py
          auth.py
          users.py
          incidents.py
          leads.py
      core/
        config.py
        database.py
        security.py
        errors.py
      domain/
        incidents/
          analyzer.py
          exporters.py
          storage.py
        leads/
          ...
      repositories/
        user_repository.py
      schemas/
        auth.py
        users.py
        incidents.py
      services/
        auth_service.py
        user_service.py
        incidents_service.py
    requirements.txt
```

### Separation criteria

The separation rule is **business domain first, technical role second**:

- `api/routers/` handles transport concerns only
- `services/` orchestrates use cases
- `domain/` keeps reusable business logic
- `repositories/` handles database access
- `schemas/` defines request and response contracts
- `core/` holds infrastructure concerns such as configuration, DB wiring, and auth primitives

This is the right split for TrackFlow because the same business logic may need to be reused by:

- CLI scripts
- HTTP endpoints
- internal dashboards
- future automations or agents

## FastAPI conventions that influence the proposal

This proposal follows standard FastAPI structure from the official docs:

- multiple files instead of one large `main.py`
- `APIRouter` for route grouping
- Python packages with `__init__.py`
- configuration loaded from environment variables

The official FastAPI guidance on larger applications recommends splitting routers and dependencies into modules instead of centralizing all endpoints in one file. That directly supports TrackFlow's need to keep incidents, users, leads, and future operations modules clearly separated.

The official settings guidance also matters here: environment-driven config is the correct way to manage values that differ across local, Codespaces, and deployment environments.

For frontend/backend separation, Starlette's CORS middleware guidance is also relevant. Because the browser UI and the API may run on different origins, the backend must explicitly define allowed origins and respond correctly to preflight requests.

## Endpoint and router organization

### Base grouping

The API should be grouped by domain under stable prefixes:

- `/api/health`
- `/auth/*`
- `/users/*`
- `/api/incidents/*`
- `/api/leads/*`

### Incidents domain

For TrackFlow's support and returns operations, the incidents router should expose:

- `POST /api/incidents/analyze`
  Receives a CSV file, validates rows, computes metrics, and returns a JSON summary.
- `GET /api/incidents/results/latest`
  Returns the last generated summary for the current environment.
- `GET /api/incidents/results/export`
  Returns the last summary as downloadable CSV.

### Auth and users

To protect operational data, auth should be explicit and separated:

- `POST /auth/login`
- `POST /auth/register`
- `GET /auth/me`
- `POST /users`
- `GET /users`
- `GET /users/{id}`
- `PUT /users/{id}`
- `DELETE /users/{id}`

This aligns with the idea that auth is a cross-cutting concern while user CRUD remains its own resource area.

### Future TrackFlow business routers

Given the company context, likely next routers include:

- `POST /api/leads/contact`
- `GET /api/coverage/countries`
- `GET /api/services`
- `GET /api/returns/*`
- `GET /api/warehouse/*`

They should also be grouped by operational domain, not by UI page or HTTP verb.

## Frontend and backend as separate systems

Even inside one monorepo, the backend and frontend should be treated as **separate runtime systems**.

### Recommended organization

For this repo, a monorepo is still the best choice because:

- the milestones are connected
- TrackFlow shares business vocabulary across apps
- scripts, docs, and internal tools benefit from living together

But the communication boundary should remain HTTP, not direct runtime imports from UI to API internals.

### API communication assumptions

The UI should communicate with the API using:

- JSON responses for structured summaries and user data
- `multipart/form-data` for CSV uploads
- bearer tokens in the `Authorization` header for protected routes

### Environment variables

The backend should own:

- database path or database URL
- JWT secret
- token expiry window
- allowed CORS origins
- file storage paths for generated exports

The frontend should own:

- API base URL

That separation keeps Codespaces and production deployments flexible without hardcoding URLs or secrets into source code.

### CORS

TrackFlow's frontend and backend may run on different origins in development, preview, or production. That means the backend must:

- explicitly list allowed origins
- support `OPTIONS` preflight requests
- avoid permissive wildcards once authenticated requests exist

## Initial technical decisions

These are the first concrete decisions I would make:

1. Start with one FastAPI service in `services/trackflow-api`.
2. Use SQLite for the first protected user/auth flow if a production database is not yet in place, but keep repository boundaries so storage can be replaced later.
3. Use JWT bearer authentication with hashed passwords and env-based secret management.
4. Keep the incident analysis engine framework-agnostic so the same logic can power both the script and the API.
5. Store generated analysis artifacts in a predictable data location until a full database-backed reporting layer is needed.

## Risks and points of attention

### Risk 1: mixing all business rules into route handlers

If the team places validation, persistence, auth checks, and business calculations directly inside route files, the API will become difficult to extend and impossible to reuse safely from scripts or future automations.

### Risk 2: duplicated incident logic

If the CSV analysis logic is implemented once in the script and again in the API, TrackFlow could generate different operational summaries depending on how the same file is processed. That would break trust in support reporting.

### Risk 3: weak auth boundaries

If user resolution, JWT decoding, and route protection are handled inconsistently, operational endpoints could leak client or support data. For TrackFlow, that is especially risky because incidents and returns may include business-sensitive customer information.

### Risk 4: confusing UI/API boundaries

If the frontend starts depending on internal backend code instead of API contracts, later deployment and scaling will become painful. The browser app and the API must stay independently runnable.

## Recommendation summary

TrackFlow should move forward with a **domain-oriented modular FastAPI monolith** under `services/trackflow-api`, with:

- routers grouped by domain
- reusable domain and service layers
- env-based settings
- explicit CORS
- JWT authentication
- shared incident analysis logic reused by both script and API

This gives the team a backend that is structured enough for operational growth without overengineering the platform too early.

## Sources consulted

- FastAPI, "Bigger Applications - Multiple Files": https://fastapi.tiangolo.com/tutorial/bigger-applications/
- FastAPI, "Settings and Environment Variables": https://fastapi.tiangolo.com/advanced/settings/
- FastAPI, "OAuth2 with Password and Bearer": https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
- FastAPI, "OAuth2 with Password and JWT": https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
- Starlette, "Middleware / CORSMiddleware": https://www.starlette.io/middleware/
