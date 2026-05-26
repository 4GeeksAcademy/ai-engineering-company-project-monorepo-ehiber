import argparse
import sys
from pathlib import Path


# Allow direct execution from `scripts/` while still importing shared monorepo code.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

TRACKFLOW_API_ROOT = REPO_ROOT / "services" / "trackflow-api"
if str(TRACKFLOW_API_ROOT) not in sys.path:
    sys.path.insert(0, str(TRACKFLOW_API_ROOT))

from trackflow_api.core.config import get_settings
from trackflow_api.core.errors import AnalysisInputError
from trackflow_api.domain.incidents.config import load_incidents_context
from trackflow_api.services.incidents_service import analyze_incidents_file, export_summary_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze a TrackFlow incidents CSV file.")
    parser.add_argument("csv_path", help="Path to the incidents CSV file.")
    return parser


def print_summary(summary: dict, context: dict) -> None:
    company_name = context.get("company_name", "TrackFlow").upper()
    labels = context.get("invalid_reason_labels", {})
    valid_total = summary["totals"]["valid_records"] or 1

    print("=" * 60)
    print(f"  {company_name} — INCIDENT REPORT ANALYSIS")
    print(f"  Source file: {summary['file_name']}")
    print("=" * 60)
    print()
    print(f"TOTAL RECORDS IN FILE .......... {summary['totals']['total_records']}")
    print(f"  ├─ Valid records ................ {summary['totals']['valid_records']}")
    print(f"  └─ Invalid / incomplete .......... {summary['totals']['invalid_records']}")
    print()
    print("INVALID RECORDS BREAKDOWN")

    invalid_order = [
        "invalid_tracking_number",
        "carrier_country_mismatch",
        "invalid_category",
        "invalid_email",
        "closed_without_score",
    ]
    invalid_breakdown = summary["invalid_breakdown"]
    for index, reason_key in enumerate(invalid_order):
        prefix = "└─" if index == len(invalid_order) - 1 else "├─"
        label = labels.get(reason_key, reason_key.replace("_", " "))
        count = invalid_breakdown.get(reason_key, 0)
        print(f"  {prefix} {label.ljust(30)} {count}")

    for reason_key, count in invalid_breakdown.items():
        if reason_key not in invalid_order:
            label = labels.get(reason_key, reason_key.replace("_", " "))
            print(f"  ├─ {label.ljust(30)} {count}")

    print()
    print("BREAKDOWN BY CATEGORY (valid records)")
    _print_breakdown(summary["category_breakdown"], valid_total)
    print()
    print("BREAKDOWN BY STATUS (valid records)")
    _print_breakdown(summary["status_breakdown"], valid_total)
    print()
    print("BREAKDOWN BY COUNTRY (valid records)")
    _print_breakdown(summary.get("country_breakdown", {}), valid_total)
    print()
    print("SATISFACTION INDEX (closed incidents)")
    closed_with_score = summary["satisfaction"]["closed_cases_with_score"]
    average_score = summary["satisfaction"]["average_score"]
    print(f"  Scored incidents: {closed_with_score} of {closed_with_score}")
    print(
        "  Average score: "
        f"{average_score if average_score is not None else 'N/A'} / 5.00"
    )
    score_labels = {
        "1": "Score 1 (Very dissatisfied)",
        "2": "Score 2 (Dissatisfied)",
        "3": "Score 3 (Neutral)",
        "4": "Score 4 (Satisfied)",
        "5": "Score 5 (Very satisfied)",
    }
    distribution = summary["satisfaction"].get("score_distribution", {})
    for index, score in enumerate(["1", "2", "3", "4", "5"]):
        prefix = "└─" if index == 4 else "├─"
        print(f"  {prefix} {score_labels[score].ljust(30)} {distribution.get(score, 0)}")
    print()
    print("=" * 60)


def _print_breakdown(values: dict[str, int], valid_total: int) -> None:
    if not values:
        print("  None")
        return

    items = list(values.items())
    for index, (key, count) in enumerate(items):
        percentage = round((count / valid_total) * 100, 1)
        prefix = "└─" if index == len(items) - 1 else "├─"
        print(f"  {prefix} {key.ljust(18)} {str(count).rjust(3)}  ({percentage}%)")


def prompt_export(summary: dict) -> None:
    answer = input("Export results to CSV? [y / n]: ").strip().lower()
    if answer != "y":
        print("Export skipped.")
        return

    settings = get_settings()
    export_path = export_summary_csv(summary, settings.incidents_last_export_path)
    print(f"Results exported to {export_path}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    settings = get_settings()
    context = load_incidents_context(settings.incidents_context_path)

    try:
        summary = analyze_incidents_file(Path(args.csv_path))
    except AnalysisInputError as exc:
        print(f"Analysis error: {exc}")
        return 1

    print_summary(summary, context)
    prompt_export(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
