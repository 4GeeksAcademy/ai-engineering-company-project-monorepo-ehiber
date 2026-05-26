import argparse
import csv
import sys
from collections import Counter
from io import StringIO
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

TRACKFLOW_API_ROOT = REPO_ROOT / "services" / "trackflow-api"
if str(TRACKFLOW_API_ROOT) not in sys.path:
    sys.path.insert(0, str(TRACKFLOW_API_ROOT))

from trackflow_api.core.config import get_settings
from trackflow_api.core.errors import AnalysisInputError
from trackflow_api.domain.incidents.config import load_incidents_context
from trackflow_api.domain.incidents.manager_config import load_manager_context
from trackflow_api.domain.incidents.validators import validate_incident_row
from trackflow_api.services.incident_manager_service import seed_incident_from_csv_row


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed managed incidents from the TrackFlow historical CSV."
    )
    parser.add_argument(
        "csv_path",
        nargs="?",
        default=str(REPO_ROOT / "data" / "incidents" / "incidents-trackflow.csv"),
        help="Path to the incidents CSV file.",
    )
    return parser


def load_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    if not csv_path.exists():
        raise AnalysisInputError(f"CSV file not found: {csv_path}")

    try:
        content = csv_path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        content = csv_path.read_text(encoding="latin-1")

    reader = csv.DictReader(StringIO(content))
    if not reader.fieldnames:
        raise AnalysisInputError("The CSV file must include a header row.")

    rows: list[dict[str, str]] = []
    for raw_row in reader:
        rows.append({key: (value or "").strip() for key, value in raw_row.items() if key})
    return rows


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    csv_path = Path(args.csv_path)

    try:
        settings = get_settings()
        analysis_context = load_incidents_context(settings.incidents_context_path)
        manager_context = load_manager_context()
        rows = load_csv_rows(csv_path)
    except AnalysisInputError as exc:
        print(f"Seed error: {exc}", file=sys.stderr)
        return 1

    inserted = 0
    duplicates = 0
    invalid_analysis: Counter[str] = Counter()
    invalid_seed: Counter[str] = Counter()

    for row_index, row in enumerate(rows, start=2):
        reasons, _ = validate_incident_row(row, analysis_context)
        if reasons:
            for reason in reasons:
                invalid_analysis[reason] += 1
            print(
                f"Skipped row {row_index} ({row.get('incident_id', 'unknown')}): "
                f"{', '.join(reasons)}",
                file=sys.stderr,
            )
            continue

        outcome, _ = seed_incident_from_csv_row(row, context=manager_context)
        if outcome == "inserted":
            inserted += 1
        elif outcome == "duplicate":
            duplicates += 1
        else:
            invalid_seed[outcome] += 1
            print(
                f"Skipped row {row_index} ({row.get('incident_id', 'unknown')}): {outcome}",
                file=sys.stderr,
            )

    print("=" * 60)
    print("TRACKFLOW — INCIDENT SEED SUMMARY")
    print(f"Source file: {csv_path.name}")
    print("=" * 60)
    print(f"Rows processed ............. {len(rows)}")
    print(f"Inserted ................... {inserted}")
    print(f"Duplicates skipped ......... {duplicates}")
    print(f"Invalid analysis rows ...... {sum(invalid_analysis.values())}")
    print(f"Invalid seed mappings ...... {sum(invalid_seed.values())}")
    if invalid_analysis:
        print("\nAnalysis validation breakdown:")
        for reason, count in sorted(invalid_analysis.items()):
            print(f"  {reason}: {count}")
    if invalid_seed:
        print("\nSeed mapping breakdown:")
        for reason, count in sorted(invalid_seed.items()):
            print(f"  {reason}: {count}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
