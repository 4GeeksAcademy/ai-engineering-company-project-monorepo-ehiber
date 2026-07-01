import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

TRACKFLOW_API_ROOT = REPO_ROOT / "services" / "trackflow-api"
if str(TRACKFLOW_API_ROOT) not in sys.path:
    sys.path.insert(0, str(TRACKFLOW_API_ROOT))

from sqlmodel import Session

from trackflow_api.core.database import get_inventory_engine, init_db
from trackflow_api.domain.telemetry.report import build_telemetry_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build TrackFlow telemetry KPI report from persisted events."
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    init_db()
    engine = get_inventory_engine()
    with Session(engine) as session:
        report = build_telemetry_report(session)

    if args.pretty:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
