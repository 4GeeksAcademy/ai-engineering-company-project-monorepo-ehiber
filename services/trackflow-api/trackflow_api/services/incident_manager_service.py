from collections import Counter

from fastapi import HTTPException

from ..core.cache import INCIDENTS_SUMMARY_KEY, cache_get, cache_invalidate_prefix, cache_set
from ..domain.incidents.manager_config import load_manager_context
from ..repositories import incident_repository
from ..schemas.incidents_manager import IncidentCreate, IncidentPublic, IncidentSummary, IncidentStatusUpdate


class FieldValidationError(Exception):
    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(message)


INCIDENTS_SUMMARY_CACHE_TTL_SECONDS = 60


def _invalidate_incidents_summary_cache() -> None:
    cache_invalidate_prefix("incidents:")


def list_incidents(
    *,
    status: str | None = None,
    origin: str | None = None,
    branch: str | None = None,
    category: str | None = None,
) -> list[IncidentPublic]:
    context = load_manager_context()
    _validate_filter_value("status", status, context["statuses"])
    _validate_filter_value("origin", origin, context["origins"])
    _validate_filter_value("branch", branch, context["branches"])
    _validate_filter_value("category", category, context["categories"])

    records = incident_repository.list_incident_records(
        status=status,
        origin=origin,
        branch=branch,
        category=category,
    )
    return [_to_public(record) for record in records]


def get_incident(incident_id: int) -> IncidentPublic | None:
    record = incident_repository.get_incident_by_id(incident_id)
    return _to_public(record) if record else None


def create_incident(payload: IncidentCreate) -> IncidentPublic:
    context = load_manager_context()
    _validate_incident_payload(
        title=payload.title,
        description=payload.description,
        category=payload.category,
        status=payload.status,
        origin=payload.origin,
        branch=payload.branch,
        context=context,
    )

    record = incident_repository.create_incident_record(
        {
            "title": payload.title.strip(),
            "description": payload.description.strip(),
            "category": payload.category,
            "status": payload.status,
            "origin": payload.origin,
            "branch": payload.branch,
        }
    )
    _invalidate_incidents_summary_cache()
    return _to_public(record)


def update_incident_status(incident_id: int, payload: IncidentStatusUpdate) -> IncidentPublic:
    context = load_manager_context()
    record = incident_repository.get_incident_by_id(incident_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Incident not found.")

    if payload.status not in context["statuses"]:
        raise FieldValidationError("status", "Status is not allowed.")

    allowed_targets = set(context["status_transitions"].get(record["status"], []))
    if payload.status not in allowed_targets:
        raise FieldValidationError(
            "status",
            f"Cannot change status from '{record['status']}' to '{payload.status}'.",
        )

    updated = incident_repository.update_incident_record(
        incident_id,
        {"status": payload.status},
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Incident not found.")
    _invalidate_incidents_summary_cache()
    return _to_public(updated)


def get_incident_summary() -> IncidentSummary:
    cached = cache_get(INCIDENTS_SUMMARY_KEY)
    if cached is not None:
        return IncidentSummary.model_validate(cached)

    records = incident_repository.summarize_incidents()
    summary = IncidentSummary(
        total=len(records),
        by_status=dict(sorted(Counter(record["status"] for record in records).items())),
        by_category=dict(sorted(Counter(record["category"] for record in records).items())),
        by_origin=dict(sorted(Counter(record["origin"] for record in records).items())),
        by_branch=dict(sorted(Counter(record["branch"] for record in records).items())),
    )
    cache_set(INCIDENTS_SUMMARY_KEY, summary.model_dump(mode="json"), INCIDENTS_SUMMARY_CACHE_TTL_SECONDS)
    return summary


def seed_incident_from_csv_row(row: dict, *, context: dict) -> tuple[str, IncidentPublic | None]:
    category = context["csv_category_map"].get(row.get("category", ""))
    status = context["csv_status_map"].get(row.get("status", ""))
    description = (row.get("description") or "").strip()
    incident_id = (row.get("incident_id") or "").strip()
    created_at = (row.get("date") or row.get("created_at") or "").strip()

    if not category:
        return f"invalid_category:{row.get('category', '')}", None
    if not status:
        return f"invalid_status:{row.get('status', '')}", None
    if category not in context["categories"]:
        return f"invalid_category:{category}", None
    if status not in context["statuses"]:
        return f"invalid_status:{status}", None

    if incident_repository.get_incident_by_source_id(incident_id):
        return "duplicate", None

    title = incident_id or "Imported incident"
    if description:
        title = f"{incident_id}: {description[:80]}"

    timestamp = f"{created_at}T00:00:00+00:00" if created_at else incident_repository.current_timestamp()
    record = incident_repository.create_incident_record(
        {
            "title": title,
            "description": description or title,
            "category": category,
            "status": status,
            "origin": "customer",
            "branch": "central",
            "created_at": timestamp,
            "updated_at": timestamp,
            "source_incident_id": incident_id,
        }
    )
    return "inserted", _to_public(record)


def _validate_incident_payload(
    *,
    title: str,
    description: str,
    category: str,
    status: str,
    origin: str,
    branch: str,
    context: dict,
) -> None:
    if not title.strip():
        raise FieldValidationError("title", "Title is required.")
    if len(title.strip()) < 3:
        raise FieldValidationError("title", "Title must be at least 3 characters.")
    if not description.strip():
        raise FieldValidationError("description", "Description is required.")
    if len(description.strip()) < 5:
        raise FieldValidationError("description", "Description must be at least 5 characters.")
    if category not in context["categories"]:
        raise FieldValidationError("category", "Category is not allowed.")
    if status not in context["statuses"]:
        raise FieldValidationError("status", "Status is not allowed.")
    if origin not in context["origins"]:
        raise FieldValidationError("origin", "Origin is not allowed.")
    if branch not in context["branches"]:
        raise FieldValidationError("branch", "Branch is not allowed.")


def _validate_filter_value(field: str, value: str | None, allowed: list[str]) -> None:
    if value is None:
        return
    if value not in allowed:
        raise FieldValidationError(field, f"Invalid {field} filter value.")


def _to_public(record: dict) -> IncidentPublic:
    return IncidentPublic(
        id=record["id"],
        title=record["title"],
        description=record["description"],
        category=record["category"],
        status=record["status"],
        origin=record["origin"],
        branch=record["branch"],
        created_at=record["created_at"],
        updated_at=record["updated_at"],
    )
