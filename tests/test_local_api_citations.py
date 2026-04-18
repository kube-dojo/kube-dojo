from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_local_api():
    module_path = Path(__file__).resolve().parent.parent / "scripts" / "local_api.py"
    spec = importlib.util.spec_from_file_location("local_api_citations", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


local_api = _load_local_api()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_build_citation_status_groups_failures_by_track(tmp_path: Path) -> None:
    docs_root = tmp_path / "src" / "content" / "docs"
    _write(
        docs_root / "ai" / "foundations" / "module-1.1-good.md",
        """---
title: Good
---

## Why This Module Matters
> **War Story: Good**
> Something happened.
> **Source**: [Example](https://example.com/incident)

Text.[^1]

## Sources
- [Example](https://example.com/incident)

[^1]: note
""",
    )
    _write(
        docs_root / "ai" / "foundations" / "module-1.2-bad.md",
        """---
title: Bad
---

## Why This Module Matters
> **War Story: Bad**
> Missing source here.
""",
    )

    payload = local_api.build_citation_status(tmp_path)

    assert payload["exists"] is True
    assert payload["total_repo_modules"] == 2
    assert payload["passes_count"] == 1
    assert payload["failing_count"] == 1
    assert payload["tracks"][0]["track"] == "ai"
    assert payload["tracks"][0]["modules"][0]["module"] == "ai/foundations/module-1.2-bad"


def test_route_request_exposes_citation_status(tmp_path: Path) -> None:
    docs_root = tmp_path / "src" / "content" / "docs"
    _write(
        docs_root / "ai" / "foundations" / "module-1.1-bad.md",
        """---
title: Bad
---

No sources yet.
""",
    )

    status_code, payload, content_type = local_api.route_request(tmp_path, "/api/citations/status")

    assert status_code == 200
    assert content_type.startswith("application/json")
    assert payload["failing_count"] == 1
