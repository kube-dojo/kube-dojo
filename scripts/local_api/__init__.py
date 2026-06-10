"""Local API package namespace for extracted route modules."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

_MONOLITH_EXPORTS = {
    "build_quality_board",
    "build_quality_scores",
    "render_quality_board_page_html",
}


def _load_local_api_monolith() -> Any:
    module_name = "_scripts_local_api_monolith"
    loaded = sys.modules.get(module_name)
    if loaded is not None:
        return loaded
    module_path = Path(__file__).resolve().parent.parent / "local_api.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load local_api monolith from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def __getattr__(name: str) -> Any:
    if name in _MONOLITH_EXPORTS:
        return getattr(_load_local_api_monolith(), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = sorted(_MONOLITH_EXPORTS)
