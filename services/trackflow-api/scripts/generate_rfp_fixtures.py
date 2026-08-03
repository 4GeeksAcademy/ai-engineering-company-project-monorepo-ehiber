"""Generate simple PDF fixtures from Markdown seeds (Hito 9)."""

from __future__ import annotations

from pathlib import Path

from trackflow_api.core.config import REPO_ROOT
from trackflow_api.rfp.ingest import build_simple_pdf

FIXTURES = REPO_ROOT / "docs" / "agentic-workflow" / "fixtures" / "rfp"

SEED_FILES = (
    "luna-cosmetics.md",
    "modaviva.md",
    "carrier-offer.md",
)


def main() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for name in SEED_FILES:
        md_path = FIXTURES / name
        text = md_path.read_text(encoding="utf-8")
        title = md_path.stem.replace("-", " ").title()
        pdf_bytes = build_simple_pdf(text, title=title)
        out = md_path.with_suffix(".pdf")
        out.write_bytes(pdf_bytes)
        print(f"Wrote {out} ({len(pdf_bytes)} bytes)")


if __name__ == "__main__":
    main()
