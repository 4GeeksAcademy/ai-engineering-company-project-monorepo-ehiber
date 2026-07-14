#!/usr/bin/env python3
"""Index TrackFlow knowledge base documents into Qdrant."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
API_DIR = REPO_ROOT / "services" / "trackflow-api"
sys.path.insert(0, str(API_DIR))

from trackflow_api.rag.setup import setup_knowledge_base  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Index TrackFlow RAG knowledge base.")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete and recreate the Qdrant collection before indexing.",
    )
    args = parser.parse_args()

    result = setup_knowledge_base(recreate=args.recreate)
    print(
        f"Indexed {result.chunks_indexed} chunks from "
        f"{result.documents_indexed} documents into '{result.collection_name}'."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
