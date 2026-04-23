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

    out = citation_residuals.request_candidates(
        finding,
        dispatcher=fake_dispatcher,
        allowlist_tier=lambda _u: "official",
        head_checker=lambda _u: True,
    )
    assert len(out) == 2
    assert out[0]["url"] == "https://example.com/a"
    assert out[0]["tier"] == "official"


def test_request_candidates_handles_dispatch_failure() -> None:
    finding = {"excerpt": "x", "signals": [], "search_hint": []}

    def failing(_prompt: str) -> tuple[bool, str]:
        return False, "timeout"

    assert (
        citation_residuals.request_candidates(
            finding,
            dispatcher=failing,
            allowlist_tier=lambda _u: "official",
            head_checker=lambda _u: True,
        )
        == []
    )


def test_request_candidates_rejects_non_http_urls() -> None:
    finding = {"excerpt": "x", "signals": [], "search_hint": []}

    def weird(_prompt: str) -> tuple[bool, str]:
        return True, json.dumps(
            {"candidates": [{"url": "javascript:alert(1)"}, {"url": "ftp://x"}]}
        )

    assert (
        citation_residuals.request_candidates(
            finding,
            dispatcher=weird,
            allowlist_tier=lambda _u: "official",
            head_checker=lambda _u: True,
        )
        == []
    )


def test_request_candidates_filters_off_allowlist(tmp_path: Path) -> None:
    """#356 Part 1: hallucinated off-allowlist URLs never reach the fetch
    path. Gemini occasionally suggests press domains despite the
    prompt's allowlist constraint — this filter drops them."""
    finding = {"excerpt": "x", "signals": [], "search_hint": []}

    def dispatcher(_prompt: str) -> tuple[bool, str]:
        return True, json.dumps(
            {
                "candidates": [
                    {"url": "https://reuters.com/article"},
                    {"url": "https://en.wikipedia.org/wiki/X"},
                ]
            }
        )

    head_calls: list[str] = []

    def fake_head(u: str) -> bool:
        head_calls.append(u)
        return True

    def fake_allowlist_tier(url: str) -> str | None:
        return "general" if "wikipedia" in url else None

    out = citation_residuals.request_candidates(
        finding,
        dispatcher=dispatcher,
        allowlist_tier=fake_allowlist_tier,
        head_checker=fake_head,
    )
    assert len(out) == 1
    assert out[0]["url"] == "https://en.wikipedia.org/wiki/X"
    # head_check must not be invoked on off-allowlist URLs (wasteful).
    assert head_calls == ["https://en.wikipedia.org/wiki/X"]


def test_request_candidates_filters_404_urls() -> None:
    """#356 Part 1: URLs that 404 never make it past the filter, even if
    on allowlist."""
    finding = {"excerpt": "x", "signals": [], "search_hint": []}

    def dispatcher(_prompt: str) -> tuple[bool, str]:
        return True, json.dumps(
            {
                "candidates": [
                    {"url": "https://en.wikipedia.org/wiki/Real"},
                    {"url": "https://en.wikipedia.org/wiki/Hallucinated_404"},
                ]
            }
        )

    def fake_head(u: str) -> bool:
        return "Real" in u

    out = citation_residuals.request_candidates(
        finding,
        dispatcher=dispatcher,
        allowlist_tier=lambda _u: "general",
        head_checker=fake_head,
    )
    assert len(out) == 1
    assert out[0]["url"] == "https://en.wikipedia.org/wiki/Real"


def test_head_check_accepts_200(monkeypatch: pytest.MonkeyPatch) -> None:
    import urllib.request

    class _FakeResponse:
        status = 200

        def __enter__(self) -> "_FakeResponse":
            return self

        def __exit__(self, *_args: Any) -> None:
            pass

    def fake_urlopen(req: Any, timeout: float = 0) -> _FakeResponse:
        return _FakeResponse()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    assert citation_residuals.head_check("https://ex.com/a") is True


def test_head_check_rejects_404(monkeypatch: pytest.MonkeyPatch) -> None:
    import urllib.error
    import urllib.request

    def fake_urlopen(req: Any, timeout: float = 0) -> Any:
        raise urllib.error.HTTPError("url", 404, "Not Found", {}, None)  # type: ignore[arg-type]

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    assert citation_residuals.head_check("https://ex.com/gone") is False


def test_head_check_falls_back_to_get_range_on_405(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Some well-behaved sites reject HEAD with 405 but accept GET. The
    fallback is a range-limited GET so we don't pull the whole page."""
    import urllib.error
    import urllib.request

    call_log: list[tuple[str, dict[str, str]]] = []

    class _FakeResponse:
        status = 200

        def __enter__(self) -> "_FakeResponse":
            return self

        def __exit__(self, *_args: Any) -> None:
            pass

    def fake_urlopen(req: Any, timeout: float = 0) -> Any:
        call_log.append((req.get_method(), dict(req.headers)))
        if req.get_method() == "HEAD":
            raise urllib.error.HTTPError("url", 405, "Method Not Allowed", {}, None)  # type: ignore[arg-type]
        return _FakeResponse()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    assert citation_residuals.head_check("https://ex.com/a") is True
    methods = [m for m, _ in call_log]
    assert methods == ["HEAD", "GET"]
    # The GET retry must carry a Range header so we don't pull the full page.
    get_headers = call_log[1][1]
    assert get_headers.get("Range") == "bytes=0-0"


def test_head_check_rejects_on_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    import socket
    import urllib.request

    def fake_urlopen(req: Any, timeout: float = 0) -> Any:
        raise socket.timeout("timed out")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    assert citation_residuals.head_check("https://ex.com/slow", timeout=0.01) is False


def test_head_check_escalates_to_plain_get_when_range_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#357 Codex review nit #1: WAFs/CDNs that 405 HEAD AND reject
    range GET with 403/416/501 would serve a plain GET. Must escalate
    rather than return False."""
    import urllib.error
    import urllib.request

    methods_seen: list[tuple[str, str | None]] = []

    class _FakeResponse:
        status = 200

        def __enter__(self) -> "_FakeResponse":
            return self

        def __exit__(self, *_args: Any) -> None:
            pass

    def fake_urlopen(req: Any, timeout: float = 0) -> Any:
        method = req.get_method()
        range_header = req.headers.get("Range") or req.headers.get("range")
        methods_seen.append((method, range_header))
        if method == "HEAD":
            raise urllib.error.HTTPError("u", 405, "no HEAD", {}, None)  # type: ignore[arg-type]
        if method == "GET" and range_header:
            raise urllib.error.HTTPError("u", 416, "no range", {}, None)  # type: ignore[arg-type]
        return _FakeResponse()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    assert citation_residuals.head_check("https://ex.com/a") is True
    assert [m for m, _ in methods_seen] == ["HEAD", "GET", "GET"]
    assert methods_seen[1][1] == "bytes=0-0"
    assert methods_seen[2][1] is None


def test_head_check_does_not_escalate_on_unrelated_range_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If range GET fails with a non-Range-specific status (e.g. 404),
    don't waste another request on a plain GET — the URL is dead."""
    import urllib.error
    import urllib.request

    methods_seen: list[str] = []

    def fake_urlopen(req: Any, timeout: float = 0) -> Any:
        methods_seen.append(req.get_method())
        if req.get_method() == "HEAD":
            raise urllib.error.HTTPError("u", 405, "no HEAD", {}, None)  # type: ignore[arg-type]
        raise urllib.error.HTTPError("u", 404, "gone", {}, None)  # type: ignore[arg-type]

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    assert citation_residuals.head_check("https://ex.com/gone") is False
    assert methods_seen == ["HEAD", "GET"]


def test_head_check_reraises_unexpected_exceptions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#357 Codex review nit #2: unexpected (non-transport) exceptions
    must NOT be swallowed — that would silently convert coding
    regressions into 'dead URL' drops."""
    import urllib.request

    def fake_urlopen(req: Any, timeout: float = 0) -> Any:
        raise RuntimeError("simulated coding bug")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(RuntimeError, match="simulated coding bug"):
        citation_residuals.head_check("https://ex.com/a")


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
        candidate,
        finding,
        fetcher=fake_fetcher,
        cached_text_path=fake_cached_text_path,
        allowlist_tier=lambda _u: "press",
    )
    assert result["ok"] is True
    assert result["tier"] == "press"
    assert "2023" in result["anchors_matched"]


def test_validate_candidate_rejects_off_allowlist_before_fetch(tmp_path: Path) -> None:
    """Regression for Codex review of #355: off-allowlist URLs must be
    rejected before any network call so we don't leak traffic to
    prohibited hosts. Earlier code fetched first, then checked tier."""
    finding = {"excerpt": "In 2023 X happened.", "signals": ["year_reference"]}
    candidate = {"url": "https://reuters.com/article"}

    fetch_calls: list[str] = []

    def fake_fetcher(url: str) -> dict[str, Any]:
        fetch_calls.append(url)
        return {"status": 200, "final_url": url, "allowlist_tier": "press"}

    def fake_cached_text_path(_url: str) -> Path:
        return tmp_path / "never-read.txt"

    def fake_allowlist_tier(_url: str) -> str | None:
        return None  # host NOT on allowlist

    result = citation_residuals.validate_candidate(
        candidate,
        finding,
        fetcher=fake_fetcher,
        cached_text_path=fake_cached_text_path,
        allowlist_tier=fake_allowlist_tier,
    )
    assert result["ok"] is False
    assert result["reason"] == "off_allowlist"
    assert fetch_calls == [], "off-allowlist URL must not be fetched"


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
        candidate,
        finding,
        fetcher=fake_fetcher,
        cached_text_path=fake_cached_text_path,
        allowlist_tier=lambda _u: "official",
    )
    assert result["ok"] is False
    assert result["reason"] == "no_anchor_match"


def test_validate_candidate_rejects_finding_with_no_verification_signal(
    tmp_path: Path,
) -> None:
    """Regression for #355 Codex review, updated for #356 Part 2: a
    finding with only named_incident/attribution signals AND a
    candidate that provides no expected_quote has nothing to verify
    against. Must reject pre-fetch with no_verification_signal."""
    finding = {
        "excerpt": "Amazon scrapped its project after concerns.",
        "signals": ["named_incident", "attribution"],
    }
    # No expected_quote — and no anchors extractable from named_incident.
    candidate = {"url": "https://en.wikipedia.org/wiki/Random_topic"}

    fetch_calls: list[str] = []

    def fake_fetcher(url: str) -> dict[str, Any]:
        fetch_calls.append(url)
        return {"status": 200, "final_url": url, "allowlist_tier": "general"}

    result = citation_residuals.validate_candidate(
        candidate,
        finding,
        fetcher=fake_fetcher,
        cached_text_path=lambda _u: tmp_path / "never.txt",
        allowlist_tier=lambda _u: "general",
    )
    assert result["ok"] is False
    assert result["reason"] == "no_verification_signal"
    assert fetch_calls == [], "anchorless+quoteless finding must not trigger a fetch"


# ---- #356 Part 2: quote-match verification -------------------------------


def test_quote_present_whitespace_and_case_normalized() -> None:
    assert citation_residuals.quote_present_in_text(
        "Amazon scrapped its hiring tool in 2018",
        "Reports AMAZON\nscrapped  its HIRING tool in 2018 — full story follows.",
    ) is True


def test_quote_present_rejects_too_short_quote() -> None:
    """The LLM hedging with 'maybe' or 'see there' must not pass."""
    assert citation_residuals.quote_present_in_text(
        "see there",
        "You can see there are some references to Amazon here.",
    ) is False


def test_quote_present_tolerates_minor_internal_drift() -> None:
    """The start-AND-end-window fallback tolerates LLM drift in the
    middle of the quote as long as both bookends match on the page."""
    assert citation_residuals.quote_present_in_text(
        "Amazon scrapped its AI recruiting tool after discovering bias against women",
        "Amazon scrapped its AI recruiting tool after engineers saw bias against women in training data.",
    ) is True


def test_quote_present_rejects_end_changed() -> None:
    """#360 Codex review, must-fix #2: the old prefix-only fallback
    accepted end-changed quotes. Now both ends must match."""
    assert citation_residuals.quote_present_in_text(
        "Amazon scrapped its AI recruiting tool after discovering bias against women",
        "Amazon scrapped its AI recruiting tool after finding serious issues in testing.",
    ) is False


def test_quote_present_rejects_generic_lead_in_with_different_subject() -> None:
    """#360 Codex review, must-fix #2 (concrete adversarial example):
    a boilerplate lead-in like 'According to the article...' cannot
    carry a match when the claim-specific tail differs."""
    quote = (
        "According to the article published on the company's website earlier "
        "this year, Amazon scrapped its AI"
    )
    body_with_kubernetes_instead = (
        "According to the article published on the company's website earlier "
        "this year, Kubernetes changed its default scheduler."
    )
    assert citation_residuals.quote_present_in_text(
        quote, body_with_kubernetes_instead
    ) is False


def test_quote_present_rejects_unrelated_text() -> None:
    assert citation_residuals.quote_present_in_text(
        "Microsoft acquired GitHub for $7.5 billion",
        "This page is about Kubernetes pod lifecycle and has nothing to do with Microsoft.",
    ) is False


def test_validate_candidate_accepts_via_expected_quote_when_no_anchors(
    tmp_path: Path,
) -> None:
    """#356 Part 2 core: a finding with only named_incident signals now
    resolves when the LLM provides an expected_quote that's on the page."""
    finding = {
        "excerpt": "Amazon scrapped its AI recruiting tool after bias concerns.",
        "signals": ["named_incident", "attribution"],
    }
    candidate = {
        "url": "https://en.wikipedia.org/wiki/Amazon_recruiting_AI",
        "expected_quote": "Amazon scrapped its AI recruiting tool",
    }

    text_file = tmp_path / "body.txt"
    text_file.write_text(
        "Reuters reports that Amazon scrapped its AI recruiting tool after engineers "
        "discovered bias against women in training data.",
        encoding="utf-8",
    )

    result = citation_residuals.validate_candidate(
        candidate,
        finding,
        fetcher=lambda u: {"status": 200, "final_url": u, "allowlist_tier": "general"},
        cached_text_path=lambda _u: text_file,
        allowlist_tier=lambda _u: "general",
    )
    assert result["ok"] is True
    assert result["verified_via"] == "expected_quote"
    assert result["quote_matched"] is True


def test_validate_candidate_rejects_quote_not_on_page(tmp_path: Path) -> None:
    """Core #356 Part 2: if LLM invents a quote that's not on the fetched
    page, reject with quote_not_in_page (catches URL-content
    hallucination)."""
    finding = {
        "excerpt": "Some claim about an incident.",
        "signals": ["named_incident"],
    }
    candidate = {
        "url": "https://en.wikipedia.org/wiki/Real_page",
        "expected_quote": "A hallucinated sentence that is not on the page at all",
    }

    text_file = tmp_path / "body.txt"
    text_file.write_text(
        "This is a page about Kubernetes pod lifecycle and networking.",
        encoding="utf-8",
    )

    result = citation_residuals.validate_candidate(
        candidate,
        finding,
        fetcher=lambda u: {"status": 200, "final_url": u, "allowlist_tier": "general"},
        cached_text_path=lambda _u: text_file,
        allowlist_tier=lambda _u: "general",
    )
    assert result["ok"] is False
    assert result["reason"] == "quote_not_in_page"
    assert result["expected_quote"] == "A hallucinated sentence that is not on the page at all"


def test_validate_candidate_prefers_anchor_when_both_signals_present(
    tmp_path: Path,
) -> None:
    """With both year anchor AND expected_quote present and matching,
    the happy path still returns ok, reporting verified_via=anchors
    (the cheaper, more trusted signal) when anchors pass."""
    finding = {
        "excerpt": "In 2018 Amazon scrapped its AI tool.",
        "signals": ["year_reference", "named_incident"],
    }
    candidate = {
        "url": "https://en.wikipedia.org/wiki/Real",
        "expected_quote": "Amazon scrapped its AI tool",
    }

    text_file = tmp_path / "body.txt"
    text_file.write_text(
        "In 2018 Amazon scrapped its AI tool after bias concerns.",
        encoding="utf-8",
    )

    result = citation_residuals.validate_candidate(
        candidate,
        finding,
        fetcher=lambda u: {"status": 200, "final_url": u, "allowlist_tier": "general"},
        cached_text_path=lambda _u: text_file,
        allowlist_tier=lambda _u: "general",
    )
    assert result["ok"] is True
    assert result["verified_via"] == "anchors"
    assert "2018" in result["anchors_matched"]
    assert result["quote_matched"] is True


def test_validate_candidate_rejects_anchor_mismatch_even_when_quote_matches(
    tmp_path: Path,
) -> None:
    """#360 Codex review, must-fix #1: when a finding has deterministic
    anchors, those anchors are authoritative. A matching
    expected_quote cannot override anchor mismatch — that's the exact
    failure mode Codex identified (claim says 2018, page says 2017,
    but generic quote 'Amazon scrapped its AI tool' is on the page
    anyway). Must reject, not accept."""
    finding = {
        "excerpt": "In 2018 Amazon scrapped its AI tool.",
        "signals": ["year_reference", "named_incident"],
    }
    candidate = {
        "url": "https://en.wikipedia.org/wiki/Wrong_year_page",
        "expected_quote": "Amazon scrapped its AI tool",
    }

    text_file = tmp_path / "body.txt"
    # Page supports the quote but uses 2017 — the claim-specific year
    # mismatches. Must reject.
    text_file.write_text(
        "In 2017 Amazon scrapped its AI tool after bias concerns.",
        encoding="utf-8",
    )

    result = citation_residuals.validate_candidate(
        candidate,
        finding,
        fetcher=lambda u: {"status": 200, "final_url": u, "allowlist_tier": "general"},
        cached_text_path=lambda _u: text_file,
        allowlist_tier=lambda _u: "general",
    )
    assert result["ok"] is False
    assert result["reason"] == "no_anchor_match"
    assert result["anchors_expected"] == ["2018"]
    assert result["anchors_matched"] == []
    # Quote DID match on the page — but anchors are authoritative.
    assert result["quote_matched"] is True


def test_request_candidates_passes_expected_quote_through() -> None:
    """Ensure the LLM's expected_quote survives JSON parsing and reaches
    validate_candidate."""
    finding = {"excerpt": "claim", "signals": [], "search_hint": []}

    def fake_dispatcher(_prompt: str) -> tuple[bool, str]:
        return True, json.dumps(
            {
                "candidates": [
                    {
                        "url": "https://en.wikipedia.org/wiki/X",
                        "tier": "general",
                        "expected_quote": "A sentence from the page.",
                    }
                ]
            }
        )

    out = citation_residuals.request_candidates(
        finding,
        dispatcher=fake_dispatcher,
        allowlist_tier=lambda _u: "general",
        head_checker=lambda _u: True,
    )
    assert len(out) == 1
    assert out[0]["expected_quote"] == "A sentence from the page."


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


def test_inject_source_preserves_content_after_sources_section() -> None:
    """Regression for Codex review of #355 (nit): inject_source must
    insert INSIDE the Sources section, not at EOF — otherwise any
    following prose gets stranded after the new bullet."""
    module = (
        "# Title\n\nBody.\n\n"
        "## Sources\n\n"
        "- [a](https://a.example) — first\n\n"
        "## Further Reading\n\n"
        "Some trailing prose.\n"
    )
    out, changed = citation_residuals.inject_source(
        module, "- [b](https://b.example) — second"
    )
    assert changed is True
    # New bullet appears BEFORE the Further Reading header.
    assert out.index("- [b](https://b.example)") < out.index("## Further Reading")
    # Trailing content preserved.
    assert out.endswith("Some trailing prose.\n")
    # Only one Further Reading header (no duplication).
    assert out.count("## Further Reading") == 1


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
        allowlist_tier=lambda _u: "official",
        head_checker=lambda _u: True,
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
