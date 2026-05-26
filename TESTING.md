# TrackFlow Test Plan

This repository uses two test suites:

- **Backend auth and domain logic** with `pytest` in `services/trackflow-api/tests/`
- **Shared frontend helpers** with `Jest` in `packages/shared/__tests__/`

## Planned coverage

### Authentication service

| Area | Happy path | Edge case | Failure mode |
| --- | --- | --- | --- |
| Register | Creates user and token | Duplicate email rejected | Empty password rejected |
| Login | Valid credentials return token | Wrong password rejected | Unknown email rejected |
| Token | Token encodes user id | Password hash verifies correctly | Malformed token rejected |
| Password | Change password works | Reset flow updates login | Invalid reset token rejected |

### Backoffice modules (extra)

| Area | Happy path | Edge case | Failure mode |
| --- | --- | --- | --- |
| Suppliers | Create supplier | Invalid rate rejected by schema | Missing supplier returns `None` |
| Incident manager | Status transition to `in_progress` | Final states have no transitions | Invalid reverse transition rejected |

### Shared frontend helpers

| Helper | Happy path | Failure mode |
| --- | --- | --- |
| `normalizeApiError` | Parses field-aware API errors | Maps technical JSON errors to fallback text |
| `validateIncidentForm` | Accepts valid payload | Flags missing description |
| Token storage helpers | Stores and clears session | Clears auth state safely |

## Run backend tests

```bash
cd services/trackflow-api
pip install -e ".[dev]"
pytest
pytest --cov=trackflow_api --cov-report=term-missing
```

## Run shared frontend tests

```bash
cd packages/shared
npm install
npm test
```

## Notes

- Tests focus on business logic rather than HTTP serialization.
- AI-assisted review suggested adding reverse-status transition coverage for the incident manager and malformed-token coverage for JWT decoding; both are included above.
- Password reset tests rely on the development email fallback (`data/dev-emails/`) so no external email provider is required.
