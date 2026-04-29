import argparse
from pathlib import Path

from services.api.app.core.config import get_settings
from services.api.app.core.errors import AnalysisInputError
from services.api.app.services.incidents_service import analyze_incidents_file, export_summary_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze a TrackFlow incidents CSV file.")
    parser.add_argument("csv_path", help="Path to the incidents CSV file.")
    return parser


def print_summary(summary: dict) -> None:
    separator = "=" * 72
    print(separator)
    print("INCIDENT ANALYSIS SUMMARY")
    print(separator)
    print(f"File: {summary['file_name']}")
    print(f"Processed at: {summary['processed_at']}")
    print(separator)
    print("Totals")
    print(f"  Total records:   {summary['totals']['total_records']}")
    print(f"  Valid records:   {summary['totals']['valid_records']}")
    print(f"  Invalid records: {summary['totals']['invalid_records']}")
    print(separator)
    print("Breakdown by category")
    _print_mapping(summary["category_breakdown"])
    print(separator)
    print("Breakdown by status")
    _print_mapping(summary["status_breakdown"])
    print(separator)
    print("Invalid records by reason")
    _print_mapping(summary["invalid_breakdown"])
    print(separator)
    print("Satisfaction")
    print(f"  Closed cases with score: {summary['satisfaction']['closed_cases_with_score']}")
    print(
        "  Average score:           "
        f"{summary['satisfaction']['average_score'] if summary['satisfaction']['average_score'] is not None else 'N/A'}"
    )
    print(separator)

    if summary["invalid_details"]:
        print("Invalid record details")
        for record in summary["invalid_details"]:
            reasons = ", ".join(record["reasons"])
            print(f"  Row {record['row_number']}: {reasons}")
        print(separator)


def _print_mapping(values: dict[str, int]) -> None:
    if not values:
        print("  None")
        return

    width = max(len(key) for key in values)
    for key, value in values.items():
        print(f"  {key.ljust(width)} : {value}")


def prompt_export(summary: dict) -> None:
    answer = input("Export results to CSV? [y / n] ").strip().lower()
    if answer != "y":
        print("Export skipped.")
        return

    settings = get_settings()
    export_path = export_summary_csv(summary, settings.incidents_last_export_path)
    print(f"Results exported to {export_path}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        summary = analyze_incidents_file(Path(args.csv_path))
    except AnalysisInputError as exc:
        print(f"Analysis error: {exc}")
        return 1

    print_summary(summary)
    prompt_export(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
