from __future__ import annotations

import io
import json
from pathlib import Path
from urllib.error import URLError

import pytest

from scripts import run_section_v3


class _FakeResponse(io.BytesIO):
    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def _seed_module(repo_root: Path, module_key: str, *, title: str) -> None:
    module_path = repo_root / "src" / "content" / "docs" / f"{module_key}.md"
    module_path.parent.mkdir(parents=True, exist_ok=True)
    module_path.write_text(
        f"---\n"
        f"title: {title}\n"
        f"sidebar:\n"
        f"  order: 1\n"
        f"---\n\n"
        f"Body.\n",
        encoding="utf-8",
    )


def _quality_payload(module_label: str, primary_issue: str) -> dict:
    entry = {
        "module": module_label,
        "primary_issue": primary_issue,
        "score": 1.5,
        "track": "AI Foundations",
    }
    return {
        "critical": [entry],
        "modules": [entry],
    }


def _configure_docs_root(monkeypatch, tmp_path: Path) -> None:
    docs_root = tmp_path / "src" / "content" / "docs"
    monkeypatch.setattr(run_section_v3, "DOCS_ROOT", docs_root)
    monkeypatch.setattr(run_section_v3, "_QUALITY_ISSUE_CACHE", None)
    monkeypatch.setattr(run_section_v3, "_QUALITY_ISSUE_CACHE_LOADED", False)


def _stub_scores_fetch(monkeypatch, payload: dict) -> None:
    monkeypatch.setattr(
        run_section_v3,
        "urlopen",
        lambda url, timeout=5.0: _FakeResponse(json.dumps(payload).encode("utf-8")),
    )


def test_content_stable_gate_passes_exact_no_citations(tmp_path: Path, monkeypatch) -> None:
    module_key = "ai/foundations/module-1.1-what-is-ai"
    _seed_module(tmp_path, module_key, title="What Is AI?")
    _configure_docs_root(monkeypatch, tmp_path)
    _stub_scores_fetch(monkeypatch, _quality_payload("AI Foundations: What Is AI?", "no citations"))

    kept = run_section_v3._content_stable_modules([module_key], log_skips=True)
    assert kept == [module_key]


@pytest.mark.parametrize("primary_issue", ["no citations, no quiz", "thin, no quiz", "thin"])
def test_content_stable_gate_skips_non_exact_primary_issues(
    tmp_path: Path,
    monkeypatch,
    capsys,
    primary_issue: str,
) -> None:
    module_key = "ai/foundations/module-1.1-what-is-ai"
    _seed_module(tmp_path, module_key, title="What Is AI?")
    _configure_docs_root(monkeypatch, tmp_path)
    _stub_scores_fetch(monkeypatch, _quality_payload("AI Foundations: What Is AI?", primary_issue))

    kept = run_section_v3._content_stable_modules([module_key], log_skips=True)
    assert kept == []
    out = capsys.readouterr().out
    assert f"skip: {module_key} primary_issue={primary_issue} — parks for v4" in out


def test_content_stable_gate_unknown_module_fails_open(tmp_path: Path, monkeypatch, capsys) -> None:
    module_key = "ai/foundations/module-1.1-what-is-ai"
    _seed_module(tmp_path, module_key, title="What Is AI?")
    _configure_docs_root(monkeypatch, tmp_path)
    _stub_scores_fetch(monkeypatch, _quality_payload("AI Foundations: Different Module", "no citations"))

    kept = run_section_v3._content_stable_modules([module_key], log_skips=True)
    assert kept == [module_key]
    err = capsys.readouterr().err
    assert "missing from /api/quality/scores" in err


def test_content_stable_gate_api_unreachable_fails_open(tmp_path: Path, monkeypatch, capsys) -> None:
    module_key = "ai/foundations/module-1.1-what-is-ai"
    _seed_module(tmp_path, module_key, title="What Is AI?")
    _configure_docs_root(monkeypatch, tmp_path)
    monkeypatch.setattr(
        run_section_v3,
        "urlopen",
        lambda url, timeout=5.0: (_ for _ in ()).throw(URLError("offline")),
    )

    kept = run_section_v3._content_stable_modules([module_key], log_skips=True)
    assert kept == [module_key]
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "content-stable gate failed open" in captured.err
