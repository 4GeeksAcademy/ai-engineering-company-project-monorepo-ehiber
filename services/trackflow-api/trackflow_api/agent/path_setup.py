from __future__ import annotations

import sys

from ..core.config import find_repo_root


def ensure_repo_root_on_path() -> None:
    root = str(find_repo_root())
    if root not in sys.path:
        sys.path.insert(0, root)


ensure_repo_root_on_path()
