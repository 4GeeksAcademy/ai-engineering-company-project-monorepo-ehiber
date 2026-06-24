"""Simple API latency benchmark for caching decisions."""

from __future__ import annotations

import argparse
import os
import statistics
import sys
import time
from pathlib import Path
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[1]
TRACKFLOW_API_ROOT = REPO_ROOT / "services" / "trackflow-api"
DEFAULT_SQLITE_PATH = REPO_ROOT / "data" / "inventory-performance.db"

if str(TRACKFLOW_API_ROOT) not in sys.path:
    sys.path.insert(0, str(TRACKFLOW_API_ROOT))

os.environ.setdefault("SUPABASE_URI", f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}")
os.environ.setdefault("TRACKFLOW_DATABASE_PATH", str(REPO_ROOT / "data" / "app-performance.json"))
os.environ.setdefault("TRACKFLOW_JWT_SECRET_KEY", "local-benchmark-secret")

from fastapi.testclient import TestClient


DEFAULT_ENDPOINTS = [
    ("GET", "/inventory/products"),
    ("GET", "/inventory/orders"),
    ("GET", "/suppliers"),
    ("GET", "/api/incidents/summary"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark TrackFlow API read endpoints.")
    parser.add_argument("--requests", type=int, default=25, help="Requests per endpoint.")
    parser.add_argument(
        "--endpoint",
        action="append",
        default=[],
        help="Custom endpoint as METHOD:/path (repeatable).",
    )
    return parser


def _client() -> TestClient:
    from trackflow_api.main import app

    return TestClient(app)


def _auth_headers(client: TestClient) -> dict[str, str]:
    email = f"bench-{uuid4().hex[:8]}@trackflow.com"
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "securepass123"},
    )
    response.raise_for_status()
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _parse_endpoint(raw: str) -> tuple[str, str]:
    method, path = raw.split(":", 1)
    return method.upper(), path


def _request(client: TestClient, method: str, path: str, headers: dict[str, str]) -> float:
    start = time.perf_counter()
    response = client.request(method, path, headers=headers)
    elapsed_ms = (time.perf_counter() - start) * 1000
    response.raise_for_status()
    return elapsed_ms


def benchmark(endpoints: list[tuple[str, str]], requests_per_endpoint: int) -> None:
    client = _client()
    headers = _auth_headers(client)

    print(f"{'Endpoint':<40} {'p50':>8} {'p95':>8} {'max':>8}")
    print("-" * 68)

    for method, path in endpoints:
        durations: list[float] = []
        for _ in range(requests_per_endpoint):
            durations.append(_request(client, method, path, headers))

        durations.sort()
        p50 = statistics.median(durations)
        p95 = durations[max(0, int(len(durations) * 0.95) - 1)]
        max_ms = max(durations)
        label = f"{method} {path}"
        print(f"{label:<40} {p50:7.1f}ms {p95:7.1f}ms {max_ms:7.1f}ms")


def main() -> None:
    args = build_parser().parse_args()
    endpoints = [_parse_endpoint(item) for item in args.endpoint] if args.endpoint else DEFAULT_ENDPOINTS
    benchmark(endpoints, args.requests)


if __name__ == "__main__":
    main()
