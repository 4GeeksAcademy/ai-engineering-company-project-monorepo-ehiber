"""Ensure monorepo + trackflow_api are importable when running the MCP server."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()


def _find_repo_root() -> Path:
    """Resolve repo root across local runs and containerized paths."""
    # 1) Respect explicit env override when provided.
    env_root = os.getenv("TRACKFLOW_REPO_ROOT", "").strip()
    if env_root:
        candidate = Path(env_root).resolve()
        if (candidate / "services" / "trackflow-api").exists():
            return candidate

    # 2) Walk up from this file until we find the monorepo marker path.
    for parent in (_HERE, *_HERE.parents):
        if (parent / "services" / "trackflow-api").exists():
            return parent

    # 3) Docker compose mounts the repo at /workspace.
    workspace_root = Path("/workspace")
    if (workspace_root / "services" / "trackflow-api").exists():
        return workspace_root

    # 4) Safe fallback for unusual environments.
    return Path.cwd().resolve()


_REPO_ROOT = _find_repo_root()
_API_ROOT = _REPO_ROOT / "services" / "trackflow-api"

for path in (_REPO_ROOT, _API_ROOT):
    text = str(path)
    if path.exists() and text not in sys.path:
        sys.path.insert(0, text)
