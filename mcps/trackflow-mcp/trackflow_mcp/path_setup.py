"""Ensure monorepo + trackflow_api are importable when running the MCP server."""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
# .../mcps/trackflow-mcp/trackflow_mcp/path_setup.py → repo root is parents[3]
_REPO_ROOT = _HERE.parents[3]
_API_ROOT = _REPO_ROOT / "services" / "trackflow-api"

for path in (_REPO_ROOT, _API_ROOT):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)
