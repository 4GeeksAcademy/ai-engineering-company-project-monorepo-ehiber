#!/usr/bin/env python3
"""Evaluate TrackFlow RAG retrieval recall against the golden query set."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
API_DIR = REPO_ROOT / "services" / "trackflow-api"
sys.path.insert(0, str(API_DIR))

from trackflow_api.rag.retrieve import retrieve  # noqa: E402


def load_queries(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_recall_at_k(queries: list[dict], top_k: int) -> dict:
    hits = 0
    results = []

    for item in queries:
        chunks = retrieve(item["question"], top_k=top_k)
        sources = [chunk.source_document for chunk in chunks]
        matched = item["expected_source"] in sources
        hits += int(matched)
        results.append(
            {
                "id": item["id"],
                "question": item["question"],
                "expected_source": item["expected_source"],
                "retrieved_sources": sources,
                "matched": matched,
            }
        )

    total = len(queries)
    recall = hits / total if total else 0.0
    return {
        "top_k": top_k,
        "total": total,
        "hits": hits,
        "recall_at_k": recall,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate RAG recall@k.")
    parser.add_argument(
        "--queries",
        default=str(REPO_ROOT / "data" / "eval" / "test-queries.json"),
        help="Path to the evaluation query set.",
    )
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--min-recall", type=float, default=0.8)
    args = parser.parse_args()

    queries = load_queries(Path(args.queries))
    report = evaluate_recall_at_k(queries, top_k=args.top_k)

    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(
        f"\nRecall@{report['top_k']}: {report['recall_at_k']:.0%} "
        f"({report['hits']}/{report['total']})"
    )

    if report["recall_at_k"] < args.min_recall:
        print(f"FAIL: recall below threshold {args.min_recall:.0%}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
