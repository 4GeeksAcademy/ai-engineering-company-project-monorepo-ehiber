import csv
from io import StringIO


def summary_to_csv(summary: dict) -> str:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["metric", "group", "key", "value"])

    for key, value in summary["totals"].items():
        writer.writerow(["totals", "totals", key, value])

    for key, value in summary["category_breakdown"].items():
        writer.writerow(["breakdown", "category", key, value])

    for key, value in summary["status_breakdown"].items():
        writer.writerow(["breakdown", "status", key, value])

    for key, value in summary.get("country_breakdown", {}).items():
        writer.writerow(["breakdown", "country", key, value])

    for key, value in summary["invalid_breakdown"].items():
        writer.writerow(["invalid", "reason", key, value])

    writer.writerow(
        ["satisfaction", "closed_cases_with_score", "count", summary["satisfaction"]["closed_cases_with_score"]]
    )
    writer.writerow(
        [
            "satisfaction",
            "average_score",
            "closed_cases_average",
            "" if summary["satisfaction"]["average_score"] is None else summary["satisfaction"]["average_score"],
        ]
    )

    for score, count in summary["satisfaction"].get("score_distribution", {}).items():
        writer.writerow(["satisfaction", "score_distribution", score, count])

    return output.getvalue()
