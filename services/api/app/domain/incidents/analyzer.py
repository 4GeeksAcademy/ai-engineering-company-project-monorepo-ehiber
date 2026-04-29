import csv
from collections import Counter
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

from ...core.errors import AnalysisInputError
from .models import AnalysisSummary, InvalidRecord, SatisfactionSummary


def analyze_csv_file(file_path: str | Path, config: dict) -> AnalysisSummary:
    path = Path(file_path)
    if not path.exists():
        raise AnalysisInputError(f"CSV file not found: {path}")

    try:
        content = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        content = path.read_text(encoding="latin-1")

    return analyze_csv_content(path.name, content, config)


def analyze_csv_bytes(file_name: str, payload: bytes, config: dict) -> AnalysisSummary:
    if not payload:
        raise AnalysisInputError("The uploaded file is empty.")

    try:
        content = payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            content = payload.decode("latin-1")
        except UnicodeDecodeError as exc:
            raise AnalysisInputError("The uploaded file could not be decoded as text CSV.") from exc

    return analyze_csv_content(file_name, content, config)


def analyze_csv_content(file_name: str, content: str, config: dict) -> AnalysisSummary:
    reader = csv.DictReader(StringIO(content))
    if not reader.fieldnames:
        raise AnalysisInputError("The CSV file must include a header row.")

    fieldnames = [field.strip() for field in reader.fieldnames if field]
    required_fields = config["required_fields"]
    missing_headers = [field for field in required_fields if field not in fieldnames]
    if missing_headers:
        raise AnalysisInputError(
            "The CSV header does not include the required fields: " + ", ".join(missing_headers)
        )

    category_field = config["category_field"]
    status_field = config["status_field"]
    satisfaction_field = config["satisfaction_field"]
    allowed_categories = set(config["allowed_categories"])
    allowed_statuses = set(config["allowed_statuses"])
    closed_statuses = set(config["closed_statuses"])

    category_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    invalid_reason_counts: Counter[str] = Counter()
    invalid_details: list[InvalidRecord] = []
    satisfaction_values: list[float] = []
    total_records = 0
    valid_records = 0

    for row_index, raw_row in enumerate(reader, start=2):
        row = {key: (value or "").strip() for key, value in raw_row.items() if key is not None}
        total_records += 1
        reasons: list[str] = []

        for required_field in required_fields:
            if not row.get(required_field, ""):
                reasons.append(f"missing_required_field:{required_field}")

        category_value = row.get(category_field, "")
        if category_value and category_value not in allowed_categories:
            reasons.append(f"invalid_category:{category_value}")

        status_value = row.get(status_field, "")
        if status_value and status_value not in allowed_statuses:
            reasons.append(f"invalid_status:{status_value}")

        satisfaction_value = row.get(satisfaction_field, "")
        parsed_satisfaction: float | None = None
        if satisfaction_value:
            try:
                parsed_satisfaction = float(satisfaction_value)
            except ValueError:
                reasons.append(f"invalid_satisfaction_score:{satisfaction_value}")

        if reasons:
            for reason in reasons:
                invalid_reason_counts[reason] += 1
            invalid_details.append(
                InvalidRecord(row_number=row_index, reasons=reasons, raw_record=row)
            )
            continue

        valid_records += 1
        category_counts[category_value] += 1
        status_counts[status_value] += 1

        if status_value in closed_statuses and parsed_satisfaction is not None:
            satisfaction_values.append(parsed_satisfaction)

    average_score = None
    if satisfaction_values:
        average_score = round(sum(satisfaction_values) / len(satisfaction_values), 2)

    return AnalysisSummary(
        file_name=file_name,
        processed_at=datetime.now(timezone.utc).isoformat(),
        totals={
            "total_records": total_records,
            "valid_records": valid_records,
            "invalid_records": total_records - valid_records,
        },
        category_breakdown=dict(sorted(category_counts.items())),
        status_breakdown=dict(sorted(status_counts.items())),
        invalid_breakdown=dict(sorted(invalid_reason_counts.items())),
        invalid_details=invalid_details,
        satisfaction=SatisfactionSummary(
            closed_cases_with_score=len(satisfaction_values),
            average_score=average_score,
        ),
    )
