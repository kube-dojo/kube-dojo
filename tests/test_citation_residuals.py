from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import citation_residuals  # noqa: E402


# ---- anchor extraction ---------------------------------------------------


def test_extract_anchors_pulls_years_and_prices() -> None:
    excerpt = (
        "In November 2023, New Relic was taken private by Francisco Partners and TPG "
        "in a massive transaction valued at $6.5 billion."
    )
    signals = ["year_reference", "price_usd", "attribution"]
    anchors = citation_residuals.extract_anchors(excerpt, signals)
    assert "2023" in anchors
    assert any("6.5 billion" in a.lower() for a in anchors)


def test_extract_anchors_respects_signals() -> None:
    # No year_reference signal → don't extract years.
    excerpt = "The 2021 outage cost $100 million."
    anchors = citation_residuals.extract_anchors(excerpt, signals=["price_usd"])
    assert "2021" not in anchors
    assert any("100 million" in a.lower() for a in anchors)


def test_anchors_present_substring_case_insensitive() -> None:
    text = "Reuters reports that IN NOVEMBER 2023 New Relic was acquired for $6.5 Billion."
    matched = citation_residuals.anchors_present_in_text(["2023", "$6.5 billion"], text)
    assert "2023" in matched
    assert any("6.5 billion" in m.lower() for m in matched)


# ---- candidate request ---------------------------------------------------


def test_request_candidates_parses_json_response() -> None:
    finding = {
        "excerpt": "Sample claim.",
        "signals": ["year_reference"],
        "search_hint": ["hint 1"],
    }

    def fake_dispatcher(_prompt: str) -> tuple[bool, str]:
        return True, json.dumps(
            {
                "candidates": [
                    {"url": "https://example.com/a", "tier": "official", "why": "supports the claim"},
                    {"url": "https://example.com/b", "tier": "press", "why": "also supports"},
                ]
            }
        )

    out = citation_residuals.request_candidates(finding, dispatcher=fake_dispatcher)
    assert len(out) == 2
    assert out[0]["url"] == "https://example.com/a"
    assert out[0]["tier"] == "official"


def test_request_candidates_handles_dispatch_failure() -> None:
    finding = {"excerpt": "x", "signals": [], "search_hint": []}

    def failing(_prompt: str) -> tuple[bool, str]:
        return False, "timeout"

    assert citation_residuals.request_candidates(finding, dispatcher=failing) == []


def test_request_candidates_rejects_non_http_urls() -> None:
    finding = {"excerpt": "x", "signals": [], "search_hint": []}

    def weird(_prompt: str) -> tuple[bool, str]:
        return True, json.dumps(
            {"candidates": [{"url": "javascript:alert(1)"}, {"url": "ftp://x"}]}
        )

    assert citation_residuals.request_candidates(finding, dispatcher=weird) == []


# ---- validate_candidate --------------------------------------------------


def test_validate_candidate_happy_path(tmp_path: Path) -> None:
    finding = {
        "excerpt": "New Relic was acquired in 2023 for $6.5 billion.",
        "signals": ["year_reference", "price_usd"],
    }
    candidate = {"url": "https://ex.com/a", "tier": "press", "why": ""}

    text_file = tmp_path / "body.txt"
    text_file.write_text(
        "Reuters reports that in November 2023, New Relic was taken private in a $6.5 billion deal.",
        encoding="utf-8",
    )

    def fake_fetcher(url: str) -> dict[str, Any]:
        return {"status": 200, "final_url": url, "allowlist_tier": "press", "bytes": 1000}

    def fake_cached_text_path(_url: str) -> Path:
        return text_file

    result = citation_residuals.validate_candidate(
        candidate, finding, fetcher=fake_fetcher, cached_text_path=fake_cached_text_path
    )
    assert result["ok"] is True
    assert result["tier"] == "press"
    assert "2023" in result["anchors_matched"]


def test_validate_candidate_rejects_off_allowlist(tmp_path: Path) -> None:
    finding = {"excerpt": "any", "signals": []}
    candidate = {"url": "https://ex.com/a"}

    def fake_fetcher(url: str) -> dict[str, Any]:
        return {"status": 200, "final_url": url, "allowlist_tier": None}

    def fake_cached_text_path(_url: str) -> Path:
        return tmp_path / "never-read.txt"

    result = citation_residuals.validate_candidate(
        candidate, finding, fetcher=fake_fetcher, cached_text_path=fake_cached_text_path
    )
    assert result["ok"] is False
    assert result["reason"] == "off_allowlist"


def test_validate_candidate_rejects_when_anchors_missing(tmp_path: Path) -> None:
    finding = {
        "excerpt": "New Relic was acquired in 2023 for $6.5 billion.",
        "signals": ["year_reference", "price_usd"],
    }
    candidate = {"url": "https://ex.com/a"}

    text_file = tmp_path / "body.txt"
    text_file.write_text("Completely unrelated content about Kubernetes.", encoding="utf-8")

    def fake_fetcher(url: str) -> dict[str, Any]:
        return {"status": 200, "final_url": url, "allowlist_tier": "official"}

    def fake_cached_text_path(_url: str) -> Path:
        return text_file

    result = citation_residuals.validate_candidate(
        candidate, finding, fetcher=fake_fetcher, cached_text_path=fake_cached_text_path
    )
    assert result["ok"] is False
    assert result["reason"] == "no_anchor_match"


# ---- inject_source -------------------------------------------------------


def test_inject_source_appends_to_existing_section() -> None:
    module = "# Title\n\nBody.\n\n## Sources\n\n- [a](https://a.example) — note\n"
    out, changed = citation_residuals.inject_source(
        module, "- [b](https://b.example) — new note"
    )
    assert changed is True
    assert "- [a](https://a.example) — note" in out
    assert out.rstrip().endswith("- [b](https://b.example) — new note")


def test_inject_source_creates_section_if_missing() -> None:
    module = "# Title\n\nBody.\n"
    out, changed = citation_residuals.inject_source(
        module, "- [a](https://a.example) — note"
    )
    assert changed is True
    assert "## Sources" in out
    assert "- [a](https://a.example) — note" in out


def test_inject_source_idempotent_when_line_already_present() -> None:
    line = "- [a](https://a.example) — note"
    module = f"# Title\n\n## Sources\n\n{line}\n"
    out, changed = citation_residuals.inject_source(module, line)
    assert changed is False
    assert out == module


# ---- resolve_module (end-to-end with fakes) ------------------------------


def _write_queue_file(
    path: Path,
    module_key: str,
    findings: list[dict[str, Any]],
) -> None:
    path.write_text(
        json.dumps(
            {
                "module_key": module_key,
                "status": "residuals_queued",
                "queued_findings": {
                    "overstated_unfixed": [],
                    "needs_citation": findings,
                    "off_topic_unfixed": [],
                    "overstatement_queued": [],
                    "off_topic_delete_queued": [],
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def test_resolve_module_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Stand up a fake module tree under tmp_path and point REPO_ROOT helpers at it.
    content_dir = tmp_path / "src" / "content" / "docs" / "ai" / "demo"
    content_dir.mkdir(parents=True)
    module_key = "ai/demo/module-1.0-test"
    module_path = content_dir / "module-1.0-test.md"
    module_path.write_text("# Demo\n\nIn 2023 something happened.\n", encoding="utf-8")

    monkeypatch.setattr(citation_residuals, "REPO_ROOT", tmp_path)

    def fake_module_path_from_key(mk: str) -> Path:
        return tmp_path / "src" / "content" / "docs" / (mk + ".md")

    monkeypatch.setattr(citation_residuals, "module_path_from_key", fake_module_path_from_key)

    queue_dir = tmp_path / ".pipeline" / "v3" / "human-review"
    queue_dir.mkdir(parents=True)
    queue_path = queue_dir / "ai-demo-module-1.0-test.json"
    _write_queue_file(
        queue_path,
        module_key,
        [
            {
                "line": 3,
                "signals": ["year_reference"],
                "excerpt": "In 2023 something happened that changed things.",
                "search_hint": ["2023 event"],
            }
        ],
    )

    def fake_dispatcher(_prompt: str) -> tuple[bool, str]:
        return True, json.dumps(
            {"candidates": [{"url": "https://official.example/story", "tier": "official"}]}
        )

    def fake_fetcher(url: str) -> dict[str, Any]:
        return {"status": 200, "final_url": url, "allowlist_tier": "official"}

    body_file = tmp_path / "cached-body.txt"
    body_file.write_text("Story about 2023 event that changed things.", encoding="utf-8")

    def fake_cached_text_path(_url: str) -> Path:
        return body_file

    stats = citation_residuals.resolve_module(
        queue_path,
        dispatcher=fake_dispatcher,
        fetcher=fake_fetcher,
        cached_text_path=fake_cached_text_path,
    )
    assert stats["considered"] == 1
    assert stats["resolved"] == 1
    assert stats["unresolvable"] == 0
    assert stats["module_edited"] is True

    # Module got a Sources section with the resolved URL.
    updated = module_path.read_text(encoding="utf-8")
    assert "## Sources" in updated
    assert "https://official.example/story" in updated

    # Queue file was updated: needs_citation empty, resolved_findings has one.
    data = json.loads(queue_path.read_text())
    assert data["queued_findings"]["needs_citation"] == []
    assert len(data["resolved_findings"]) == 1
    assert data["resolved_findings"][0]["url"] == "https://official.example/story"


def test_resolve_module_marks_unresolvable_when_no_candidates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    content_dir = tmp_path / "src" / "content" / "docs" / "ai" / "demo"
    content_dir.mkdir(parents=True)
    module_key = "ai/demo/module-1.0-test"
    module_path = content_dir / "module-1.0-test.md"
    module_path.write_text("# Demo\n\nBody.\n", encoding="utf-8")

    monkeypatch.setattr(citation_residuals, "REPO_ROOT", tmp_path)

    def fake_module_path_from_key(mk: str) -> Path:
        return tmp_path / "src" / "content" / "docs" / (mk + ".md")

    monkeypatch.setattr(citation_residuals, "module_path_from_key", fake_module_path_from_key)

    queue_dir = tmp_path / ".pipeline" / "v3" / "human-review"
    queue_dir.mkdir(parents=True)
    queue_path = queue_dir / "ai-demo-module-1.0-test.json"
    _write_queue_file(
        queue_path,
        module_key,
        [{"line": 1, "signals": [], "excerpt": "Unsupportable claim.", "search_hint": []}],
    )

    def empty_dispatcher(_prompt: str) -> tuple[bool, str]:
        return True, json.dumps({"candidates": []})

    stats = citation_residuals.resolve_module(
        queue_path,
        dispatcher=empty_dispatcher,
        fetcher=lambda _u: {"status": 200, "allowlist_tier": "official"},
        cached_text_path=lambda _u: tmp_path / "never.txt",
    )
    assert stats["resolved"] == 0
    assert stats["unresolvable"] == 1

    data = json.loads(queue_path.read_text())
    assert data["queued_findings"]["needs_citation"] == []
    assert data["unresolvable_findings"][0]["unresolvable_reason"] == "no_candidates_returned"


# ---- source_line rendering -----------------------------------------------


def test_build_source_line_safe_title_and_summary() -> None:
    finding = {
        "excerpt": "Amazon scrapped its AI recruiting tool in 2018. Further details here.",
        "signals": ["year_reference"],
    }
    line = citation_residuals.build_source_line(
        "https://www.reuters.com/article/idUSKCN1MK08G", finding
    )
    assert line.startswith("- [")
    assert "https://www.reuters.com/article/idUSKCN1MK08G" in line
    # Summary uses first sentence only.
    assert "Further details" not in line
    assert "Amazon scrapped its AI recruiting tool in 2018." in line
