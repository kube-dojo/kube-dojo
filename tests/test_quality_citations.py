"""Tests for ``scripts.quality.citations`` — the strict verify-or-remove core.

Fixtures use mocked ``fetcher`` and ``verifier`` so no network I/O and no
LLM calls happen during testing. The strict policy is exercised
explicitly: only ``SUPPORTS`` keeps; ``PARTIAL``, ``NO``, ``FETCH_FAILED``,
``VERIFIER_ERROR`` all remove.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.quality import citations  # noqa: E402
from scripts.quality.citations import CitationVerdict, SourceEntry  # noqa: E402
from scripts.quality.dispatchers import DispatchResult  # noqa: E402


# ---- bullet parser ------------------------------------------------------


def test_parse_markdown_link_with_em_dash_claim() -> None:
    e = citations._parse_bullet("- [K8s v1.29 release](https://kubernetes.io/blog/v1.29/) — 2023 release notes")
    assert e is not None
    assert e.url == "https://kubernetes.io/blog/v1.29/"
    assert e.title == "K8s v1.29 release"
    assert e.claim == "2023 release notes"


def test_parse_markdown_link_with_hyphen_claim() -> None:
    e = citations._parse_bullet("- [Title](https://example.com) - hyphen claim")
    assert e is not None
    assert e.claim == "hyphen claim"


def test_parse_markdown_link_no_claim_falls_back_to_title() -> None:
    e = citations._parse_bullet("- [Just Title](https://example.com/)")
    assert e is not None
    assert e.claim == "Just Title"


def test_parse_bare_url_bullet() -> None:
    e = citations._parse_bullet("- https://example.com/page")
    assert e is not None
    assert e.url == "https://example.com/page"
    assert e.claim == "https://example.com/page"


def test_parse_numbered_bare_url_bullet() -> None:
    e = citations._parse_bullet("1. https://example.com/page")
    assert e is not None
    assert e.url == "https://example.com/page"
    assert e.claim == "https://example.com/page"


def test_parse_asterisk_bare_url_bullet() -> None:
    e = citations._parse_bullet("* https://example.com/page")
    assert e is not None
    assert e.url == "https://example.com/page"
    assert e.claim == "https://example.com/page"


def test_parse_angle_bracketed_url() -> None:
    e = citations._parse_bullet("- [Title](<https://example.com/>) — claim")
    assert e is not None
    assert e.url == "https://example.com/"


def test_parse_non_bullet_returns_none() -> None:
    assert citations._parse_bullet("Some prose line.") is None
    assert citations._parse_bullet("") is None
    assert citations._parse_bullet("## Heading") is None


def test_parse_indented_bullet_still_matches() -> None:
    e = citations._parse_bullet("  - [Title](https://example.com/) — claim")
    assert e is not None


# ---- section parser -----------------------------------------------------


_MODULE_WITH_SOURCES = """---
title: Test
---

# Body

Some content.

## Sources

- [Official K8s docs](https://kubernetes.io/docs/) — official reference
- [Blog post](https://example.com/blog/) — community deep-dive

## Next Module

Link to next.
"""


def test_parse_sources_section_finds_boundaries() -> None:
    parsed = citations.parse_sources_section(_MODULE_WITH_SOURCES)
    assert parsed is not None
    start, end, entries = parsed
    lines = _MODULE_WITH_SOURCES.splitlines()
    assert lines[start] == "## Sources"
    assert lines[end] == "## Next Module"
    assert len(entries) == 2
    assert entries[0].url == "https://kubernetes.io/docs/"


def test_parse_sources_handles_eof_without_next_heading() -> None:
    text = """---
title: Test
---

Body.

## Sources

- [Only](https://example.com/)
"""
    parsed = citations.parse_sources_section(text)
    assert parsed is not None
    start, end, entries = parsed
    assert end == len(text.splitlines())  # ran to EOF
    assert len(entries) == 1


def test_parse_no_sources_section_returns_none() -> None:
    text = "---\ntitle: T\n---\n\nJust a body.\n"
    assert citations.parse_sources_section(text) is None


def test_parse_references_heading_also_matches() -> None:
    text = "# Body\n\n## References\n\n- [Link](https://example.com/)\n"
    parsed = citations.parse_sources_section(text)
    assert parsed is not None
    _, _, entries = parsed
    assert len(entries) == 1


# ---- verify_citation (fake fetcher + verifier) --------------------------


def _verdict_result(verdict: str, reasoning: str = "ok", excerpt: str = "") -> DispatchResult:
    """Build a DispatchResult whose stdout is a valid verdict JSON."""
    import json
    body = json.dumps({"verdict": verdict, "reasoning": reasoning, "excerpt": excerpt})
    return DispatchResult(
        ok=True, stdout=body, stderr="", returncode=0,
        duration_sec=0.1, agent="gemini", model="gemini-3-flash-preview",
    )


_URL_RE = re.compile(r"https?://[^\s)]+")


def _contains_url_host(text: str, host: str) -> bool:
    target = host.lower()
    for item in _URL_RE.findall(text):
        parsed = urlsplit(item)
        if parsed.hostname and parsed.hostname.lower() == target:
            return True
    return False


def test_verify_returns_supports_when_llm_says_supports() -> None:
    entry = SourceEntry(
        raw_line="- [T](https://example.com/)", url="https://example.com/", title="T", claim="a claim"
    )
    result = citations.verify_citation(
        entry,
        verifier=lambda _p: _verdict_result("supports", excerpt="direct quote"),
        fetcher=lambda _u: "page content",
    )
    assert result.verdict == CitationVerdict.SUPPORTS
    assert result.excerpt == "direct quote"


def test_verify_treats_partial_as_remove_signal() -> None:
    """Strict policy: PARTIAL is removed, not kept."""
    entry = SourceEntry("-", "https://example.com/", "T", "claim")
    result = citations.verify_citation(
        entry,
        verifier=lambda _p: _verdict_result("partial", reasoning="only tangentially related"),
        fetcher=lambda _u: "page content",
    )
    assert result.verdict == CitationVerdict.PARTIAL


def test_verify_fetch_failure_becomes_fetch_failed() -> None:
    entry = SourceEntry("-", "https://example.com/", "T", "claim")
    result = citations.verify_citation(
        entry,
        verifier=lambda _p: _verdict_result("supports"),
        fetcher=lambda _u: None,
    )
    assert result.verdict == CitationVerdict.FETCH_FAILED


def test_verify_verifier_nonzero_becomes_verifier_error() -> None:
    entry = SourceEntry("-", "https://example.com/", "T", "claim")

    def bad_verifier(_prompt):
        return DispatchResult(
            ok=False, stdout="", stderr="subprocess crash", returncode=1,
            duration_sec=0.1, agent="gemini", model=None,
        )

    result = citations.verify_citation(entry, verifier=bad_verifier, fetcher=lambda _u: "page")
    assert result.verdict == CitationVerdict.VERIFIER_ERROR


def test_verify_malformed_json_becomes_verifier_error() -> None:
    entry = SourceEntry("-", "https://example.com/", "T", "claim")

    def malformed(_prompt):
        return DispatchResult(
            ok=True, stdout="not json at all", stderr="", returncode=0,
            duration_sec=0.1, agent="gemini", model=None,
        )

    result = citations.verify_citation(entry, verifier=malformed, fetcher=lambda _u: "page")
    assert result.verdict == CitationVerdict.VERIFIER_ERROR


def test_verify_unknown_verdict_value_becomes_verifier_error() -> None:
    entry = SourceEntry("-", "https://example.com/", "T", "claim")

    def bad_verdict(_prompt):
        return _verdict_result("maybe")

    result = citations.verify_citation(entry, verifier=bad_verdict, fetcher=lambda _u: "page")
    assert result.verdict == CitationVerdict.VERIFIER_ERROR


def test_verify_exception_in_dispatcher_becomes_verifier_error() -> None:
    """DispatcherUnavailable or any other dispatcher raise must not
    bubble up — citations.verify_citation always returns a verdict."""
    entry = SourceEntry("-", "https://example.com/", "T", "claim")

    def boom(_prompt):
        raise RuntimeError("network down")

    result = citations.verify_citation(entry, verifier=boom, fetcher=lambda _u: "page")
    assert result.verdict == CitationVerdict.VERIFIER_ERROR
    assert "network down" in result.reasoning


# ---- rebuild_section ----------------------------------------------------


def test_rebuild_drops_heading_when_no_entries_kept() -> None:
    text = _MODULE_WITH_SOURCES
    parsed = citations.parse_sources_section(text)
    assert parsed is not None
    start, end, _ = parsed
    new_text, dropped = citations.rebuild_section(text, start, end, kept_entries=[])
    assert dropped is True
    assert "## Sources" not in new_text
    # Blank padding line before the heading also removed to avoid double
    # blank-line in the output.
    assert "## Next Module" in new_text


def test_rebuild_keeps_only_listed_urls() -> None:
    text = _MODULE_WITH_SOURCES
    parsed = citations.parse_sources_section(text)
    assert parsed is not None
    start, end, entries = parsed
    keep = [entries[0]]  # keep only the first
    new_text, dropped = citations.rebuild_section(text, start, end, keep)
    assert dropped is False
    assert _contains_url_host(new_text, "kubernetes.io")
    assert not _contains_url_host(new_text, "example.com")
    assert "## Sources" in new_text
    assert "## Next Module" in new_text


def test_rebuild_all_kept_is_idempotent() -> None:
    text = _MODULE_WITH_SOURCES
    parsed = citations.parse_sources_section(text)
    assert parsed is not None
    start, end, entries = parsed
    new_text, dropped = citations.rebuild_section(text, start, end, entries)
    assert dropped is False
    assert new_text == text


def test_rebuild_preserves_non_bullet_prose_inside_section() -> None:
    text = """---
title: T
---

## Sources

These are curated sources:

- [Keep](https://keep.example/) — good
- [Drop](https://drop.example/) — bad

Supplementary note.

## Next
"""
    parsed = citations.parse_sources_section(text)
    assert parsed is not None
    start, end, entries = parsed
    keep = [e for e in entries if "keep" in e.url]
    new_text, _ = citations.rebuild_section(text, start, end, keep)
    assert "These are curated sources:" in new_text
    assert "Supplementary note." in new_text
    assert "drop.example" not in new_text


# ---- full process_module_citations --------------------------------------


@pytest.fixture
def module_file(tmp_path: Path) -> Path:
    mod = tmp_path / "mod.md"
    mod.write_text(_MODULE_WITH_SOURCES)
    return mod


def test_process_no_sources_is_no_op(tmp_path: Path) -> None:
    mod = tmp_path / "mod.md"
    mod.write_text("---\ntitle: T\n---\n\nBody only.\n")
    result = citations.process_module_citations(
        mod,
        verifier=lambda _p: _verdict_result("supports"),
        fetcher=lambda _u: "page",
    )
    assert result.had_sources_section is False
    assert result.changed is False
    assert result.new_text == mod.read_text()


def test_process_all_supports_keeps_section_verbatim(module_file: Path) -> None:
    result = citations.process_module_citations(
        module_file,
        verifier=lambda _p: _verdict_result("supports", excerpt="ok"),
        fetcher=lambda _u: "page content",
    )
    assert result.had_sources_section is True
    assert len(result.kept) == 2
    assert len(result.removed) == 0
    assert result.changed is False
    assert result.new_text == module_file.read_text()


def test_process_all_partial_drops_section(module_file: Path) -> None:
    """Strict: partial = remove. All partial = heading dropped."""
    result = citations.process_module_citations(
        module_file,
        verifier=lambda _p: _verdict_result("partial"),
        fetcher=lambda _u: "page",
    )
    assert len(result.kept) == 0
    assert len(result.removed) == 2
    assert result.section_dropped is True
    assert "## Sources" not in result.new_text


def test_process_mixed_keeps_only_supports(module_file: Path) -> None:
    # First URL supports, second partial.
    def fake_verifier(prompt: str) -> DispatchResult:
        if _contains_url_host(prompt, "kubernetes.io"):
            return _verdict_result("supports")
        return _verdict_result("partial")

    result = citations.process_module_citations(
        module_file,
        verifier=fake_verifier,
        fetcher=lambda _u: "page",
    )
    assert len(result.kept) == 1
    assert result.kept[0].entry.url == "https://kubernetes.io/docs/"
    assert len(result.removed) == 1
    assert result.removed[0].verdict == CitationVerdict.PARTIAL
    assert _contains_url_host(result.new_text, "kubernetes.io")
    assert not _contains_url_host(result.new_text, "example.com")


def test_process_fetch_failure_treated_as_remove(module_file: Path) -> None:
    result = citations.process_module_citations(
        module_file,
        verifier=lambda _p: _verdict_result("supports"),
        fetcher=lambda _u: None,  # simulate every fetch failing
    )
    assert len(result.kept) == 0
    assert len(result.removed) == 2
    for r in result.removed:
        assert r.verdict == CitationVerdict.FETCH_FAILED
    assert result.section_dropped is True


def test_process_strict_never_keeps_anything_but_supports(module_file: Path) -> None:
    """Spot-check every non-supports verdict is treated as remove."""
    for bad in ("partial", "no"):
        result = citations.process_module_citations(
            module_file,
            verifier=lambda _p, v=bad: _verdict_result(v),
            fetcher=lambda _u: "page",
        )
        assert len(result.kept) == 0, f"{bad!r} was incorrectly kept"
        assert len(result.removed) == 2


# ---- Codex v2-review must #6: strict policy for unparseable Sources --


def test_rebuild_drops_non_bullet_url_lines() -> None:
    """Codex must #6 regression guard.

    A line like ``See https://... for details`` that the bullet parser
    skipped is still an unverified URL. Strict policy: remove it.
    """
    text = """---
title: T
---

## Sources

Intro prose.

- [Verified](https://keep.example/) — good
See https://sneaky.example/ for details

## Next
"""
    parsed = citations.parse_sources_section(text)
    assert parsed is not None
    start, end, entries = parsed
    # All entries verify as supports.
    new_text, dropped = citations.rebuild_section(text, start, end, entries)
    assert "keep.example" in new_text
    # The prose line with the URL is UNVERIFIED — must be dropped.
    assert "sneaky.example" not in new_text
    # Pure intro prose (no URL) survives.
    assert "Intro prose." in new_text


def test_process_drops_section_with_only_unparseable_urls(tmp_path: Path) -> None:
    """Codex must #6: if ## Sources has no parseable bullets but has
    URLs embedded in prose, the whole section must go."""
    mod = tmp_path / "mod.md"
    mod.write_text("""---
title: T
---

# Body

## Sources

See more at https://example.com/a and https://example.com/b for context.

## Next
""")
    result = citations.process_module_citations(
        mod,
        verifier=lambda _p: _verdict_result("supports"),
        fetcher=lambda _u: "page",
    )
    # No bullets were verified, but the section had URLs → section dropped.
    assert result.had_sources_section is True
    assert result.section_dropped is True
    assert "## Sources" not in result.new_text
    assert "example.com/a" not in result.new_text


def test_process_preserves_pure_prose_sources_section(tmp_path: Path) -> None:
    """Edge case of #6: if ## Sources has no bullets AND no URLs (pure
    prose like 'Adapted from Kleppmann's DDIA'), leaving it is fine —
    there's nothing to verify and nothing to mis-publish."""
    mod = tmp_path / "mod.md"
    mod.write_text("""---
title: T
---

## Sources

Adapted from Kleppmann's DDIA and personal production experience.

## Next
""")
    result = citations.process_module_citations(
        mod,
        verifier=lambda _p: _verdict_result("supports"),
        fetcher=lambda _u: "page",
    )
    assert result.had_sources_section is True
    assert result.section_dropped is False
    assert "Kleppmann's DDIA" in result.new_text
