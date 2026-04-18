import importlib.util
import sys
from pathlib import Path


def _load_check_citations():
    module_path = Path(__file__).resolve().parent.parent / "scripts" / "check_citations.py"
    spec = importlib.util.spec_from_file_location("check_citations_test", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


check_citations = _load_check_citations()
check_file = check_citations.check_file


def test_check_citations_passes_with_sources_and_war_story_source(tmp_path: Path) -> None:
    path = tmp_path / "module.md"
    path.write_text(
        """# Demo

## Why This Module Matters

> **War Story: Test Incident**
> Something happened.
> **Source**: [Example](https://example.com/story)

Body citation.[^1]

## Sources

- [Example](https://example.com/story)

[^1]: Supporting note.
""",
        encoding="utf-8",
    )

    result = check_file(path)
    assert result["passes"] is True
    assert result["issues"] == []


def test_check_citations_fails_without_sources_section(tmp_path: Path) -> None:
    path = tmp_path / "module.md"
    path.write_text(
        """# Demo

## Why This Module Matters

> **War Story: Test Incident**
> Something happened.
""",
        encoding="utf-8",
    )

    result = check_file(path)
    assert result["passes"] is False
    assert "missing_sources_section" in result["issues"]
    assert "war_story_missing_source_line" in result["issues"]
