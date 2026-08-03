"""PDF → Markdown conversion and document-level readability metrics."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def pdf_bytes_to_markdown(pdf_bytes: bytes, *, filename: str = "document.pdf") -> str:
    """Convert PDF bytes to Markdown. Prefers MarkItDown; falls back to text extract."""
    try:
        from markitdown import MarkItDown
        import tempfile

        suffix = Path(filename).suffix or ".pdf"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(pdf_bytes)
            tmp_path = Path(tmp.name)
        try:
            result = MarkItDown().convert(str(tmp_path))
            text = (result.text_content or "").strip()
            if text:
                return text
        finally:
            tmp_path.unlink(missing_ok=True)
    except Exception:  # noqa: BLE001
        pass

    # Fallback: decode as UTF-8 if caller uploaded markdown disguised as pdf,
    # or extract printable strings from a simple text PDF.
    try:
        decoded = pdf_bytes.decode("utf-8")
        if decoded.strip().startswith("%PDF"):
            return _extract_text_from_simple_pdf(pdf_bytes)
        return decoded
    except UnicodeDecodeError:
        return _extract_text_from_simple_pdf(pdf_bytes)


def _extract_text_from_simple_pdf(pdf_bytes: bytes) -> str:
    """Best-effort extract of text from simple / uncompressed PDF streams."""
    raw = pdf_bytes.decode("latin-1", errors="ignore")
    chunks: list[str] = []
    for match in re.finditer(r"\((?:\\.|[^\\)])*\)", raw):
        token = match.group(0)[1:-1]
        token = token.replace("\\n", "\n").replace("\\r", "").replace("\\(", "(").replace("\\)", ")")
        if token.strip():
            chunks.append(token)
    if chunks:
        return "\n".join(chunks)
    # Last resort: printable runs
    printable = re.findall(r"[\x20-\x7E\n]{4,}", raw)
    return "\n".join(printable)


def compute_readability_metrics(text: str) -> dict[str, Any]:
    """Compute readability indexes used to estimate processing cost (not literary quality)."""
    cleaned = (text or "").strip()
    word_count = len(re.findall(r"\b\w+\b", cleaned))
    char_count = len(cleaned)
    metrics: dict[str, Any] = {
        "word_count": word_count,
        "char_count": char_count,
        "flesch_reading_ease": None,
        "flesch_kincaid_grade": None,
        "gunning_fog": None,
        "smog_index": None,
        "engine": "fallback",
    }
    if word_count < 10:
        return metrics

    try:
        from readability import Readability

        r = Readability(cleaned)
        try:
            metrics["flesch_reading_ease"] = round(float(r.flesch().score), 2)
        except Exception:  # noqa: BLE001
            pass
        try:
            metrics["flesch_kincaid_grade"] = round(float(r.flesch_kincaid().score), 2)
        except Exception:  # noqa: BLE001
            pass
        try:
            metrics["gunning_fog"] = round(float(r.gunning_fog().score), 2)
        except Exception:  # noqa: BLE001
            pass
        try:
            metrics["smog_index"] = round(float(r.smog().score), 2)
        except Exception:  # noqa: BLE001
            pass
        metrics["engine"] = "py-readability-metrics"
    except Exception:  # noqa: BLE001
        # Lightweight Flesch approximation when the package is unavailable.
        sentences = max(len(re.findall(r"[.!?]+", cleaned)), 1)
        syllables = max(len(re.findall(r"[aeiouyáéíóúü]+", cleaned.lower())), 1)
        metrics["flesch_reading_ease"] = round(
            206.835 - 1.015 * (word_count / sentences) - 84.6 * (syllables / word_count),
            2,
        )
        metrics["flesch_kincaid_grade"] = round(
            0.39 * (word_count / sentences) + 11.8 * (syllables / word_count) - 15.59,
            2,
        )
        metrics["engine"] = "fallback-flesch"

    return metrics


def estimate_processing_cost(metrics: dict[str, Any]) -> dict[str, Any]:
    """Map readability / size metrics to a coarse processing-cost estimate."""
    words = int(metrics.get("word_count") or 0)
    grade = metrics.get("flesch_kincaid_grade")
    fog = metrics.get("gunning_fog")
    complexity = 1.0
    if isinstance(grade, (int, float)):
        complexity += max(0.0, float(grade) - 8.0) * 0.08
    if isinstance(fog, (int, float)):
        complexity += max(0.0, float(fog) - 10.0) * 0.06

    estimated_tokens = int(words * 1.35 * complexity)
    if estimated_tokens < 2_000:
        band = "low"
        score = 1
    elif estimated_tokens < 6_000:
        band = "medium"
        score = 3
    else:
        band = "high"
        score = 5

    estimated_minutes = round(0.5 + (estimated_tokens / 4000.0) * 3.0, 1)
    return {
        "score_1_to_5": min(5, score),
        "band": band,
        "estimated_input_tokens": estimated_tokens,
        "estimated_minutes": estimated_minutes,
    }


def build_simple_pdf(text: str, *, title: str = "Document") -> bytes:
    """Build a minimal single-page text PDF (for fixtures / tests)."""
    # Escape PDF string literals
    def esc(value: str) -> str:
        return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    lines = [title, ""] + text.splitlines()
    # PDF text objects use a simple line layout
    content_lines = ["BT", "/F1 11 Tf", "50 780 Td", "14 TL"]
    first = True
    for line in lines[:60]:
        safe = esc(line[:110])
        if first:
            content_lines.append(f"({safe}) Tj")
            first = False
        else:
            content_lines.append("T*")
            content_lines.append(f"({safe}) Tj")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects: list[bytes] = []
    objects.append(b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n")
    objects.append(b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n")
    objects.append(
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>endobj\n"
    )
    objects.append(
        f"4 0 obj<< /Length {len(stream)} >>stream\n".encode("ascii")
        + stream
        + b"\nendstream\nendobj\n"
    )
    objects.append(b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n")

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(out))
        out.extend(obj)
    xref_pos = len(out)
    out.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    out.extend(
        f"trailer<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode(
            "ascii"
        )
    )
    return bytes(out)
