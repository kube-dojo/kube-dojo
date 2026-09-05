"""Adversarial cache-boundary tests for the semantic citation verifier."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import verify_citations as verifier

URL = "https://source.example/page"
PAGE_BYTES = ("A supported passage with enough text for the verifier. " * 8).encode()
RAW_VERDICT = '{"verdict":"SUPPORTED","evidence":"passage","reason":"supported"}'
CLAIM = {"claim_id": "C1", "claim_text": "The source supports this claim.", "claim_class": "standard", "proposed_url": URL}


@pytest.fixture
def cache(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setattr(verifier, "cached_text_path", lambda _url: tmp_path / "source.txt")
    return tmp_path


def _write_cache(cache: Path, body: bytes | None = PAGE_BYTES, *, raw: bytes | None = None,
                 tamper: bytes | None = None, omit: tuple[str, ...] = (), **changes: object) -> None:
    if body is None:
        return
    metadata: dict[str, object] = {
        "url": URL, "final_url": "https://source.example/redirected", "status": 200,
        "issues": [], "truncated": False, "text_sha256": hashlib.sha256(body).hexdigest(),
        "text_bytes": len(body), "fetch_attempt_completed_at": "2026-09-05T12:00:00+00:00",
    }
    metadata.update(changes)
    for key in omit:
        metadata.pop(key, None)
    (cache / "source.txt").write_bytes(tamper if tamper is not None else body)
    (cache / "source.json").write_bytes(raw if raw is not None else json.dumps(metadata).encode("utf-8"))


BAD_CASES = [
    (None, {}, None, None, (), "cache_text_missing"), (PAGE_BYTES, {}, None, None, ("truncated",), "cache_metadata_missing_truncated"),
    (PAGE_BYTES, {}, b"{", None, (), "cache_metadata_malformed"), (PAGE_BYTES, {}, b"\xff", None, (), "cache_metadata_malformed"), (PAGE_BYTES, {}, b"[]", None, (), "cache_metadata_not_object"),
    (PAGE_BYTES, {"url": URL + "/wrong"}, None, None, (), "cache_source_url_mismatch"), (PAGE_BYTES, {"text_sha256": "0" * 64}, None, None, (), "cache_text_sha256_mismatch"),
    (PAGE_BYTES, {"text_bytes": 1}, None, None, (), "cache_text_bytes_mismatch"),
    (PAGE_BYTES, {}, None, None, ("fetch_attempt_completed_at",), "cache_metadata_missing_fetch_attempt_completed_at"),
    (PAGE_BYTES, {"issues": ["pdf_needs_adapter"]}, None, None, (), "cache_issues:"), (PAGE_BYTES, {"truncated": True}, None, None, (), "cache_text_truncated"),
    (PAGE_BYTES, {"status": 500, "issues": ["http_500"]}, None, None, (), "cache_http_status_500"),
    (b"\xff" * 240, {}, None, None, (), "cache_text_invalid_utf8"), (PAGE_BYTES, {}, None, b"tampered", (), "cache_text_sha256_mismatch"),
    (b"too short", {}, None, None, (), "cached_text_missing_or_too_short"),
]


def test_valid_cache_binds_prompt_source_and_clip(cache, monkeypatch):
    body = ("long source text " * 30).encode()
    _write_cache(cache, body=body)
    monkeypatch.setattr(verifier, "MAX_PAGE_CHARS", 200)
    dispatch = Mock(return_value=(True, RAW_VERDICT))
    monkeypatch.setattr(verifier, "dispatch_agy", dispatch)
    result = verifier.verify_claim(CLAIM, agent="agy", module_key="ai/test")
    prompt = dispatch.call_args.args[0]
    assert result["verdict"] == "SUPPORTED"
    assert result["source_url"] == URL and result["final_url"] == "https://source.example/redirected"
    assert result["text_sha256"] == hashlib.sha256(body).hexdigest() and result["text_bytes"] == len(body)
    assert result["fetch_attempt_completed_at"] == "2026-09-05T12:00:00+00:00" and result["prompt_sha256"] == hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    assert result["source_text_clipped"] is True and result["source_text_chars"] == len(body.decode())
    assert result["source_text_chars_used"] == 200
    assert result["source_text_chars_clipped"] == len(body.decode()) - 200


@pytest.mark.parametrize(("body", "changes", "raw", "tamper", "omit", "reason"), BAD_CASES)
def test_untrusted_cache_never_dispatches(cache, monkeypatch, body, changes, raw, tamper, omit, reason):
    _write_cache(cache, body=body, raw=raw, tamper=tamper, omit=omit, **changes)
    dispatch = Mock(side_effect=AssertionError("provider must not run"))
    monkeypatch.setattr(verifier, "dispatch_agy", dispatch)
    result = verifier.verify_claim(CLAIM, agent="agy", module_key="ai/test")
    assert result["verdict"] == "UNREADABLE"
    assert reason in result["reason"]
    dispatch.assert_not_called()


FAILURES = [((False, "provider unavailable"), None, "dispatch_failed"), ((True, RAW_VERDICT), ValueError("bad JSON"), "parse_failed")]


@pytest.mark.parametrize(("dispatch_result", "parser_error", "reason"), FAILURES)
def test_dispatch_failures_keep_validated_provenance(cache, monkeypatch, dispatch_result,
                                                      parser_error, reason):
    _write_cache(cache)
    dispatch = Mock(return_value=dispatch_result)
    monkeypatch.setattr(verifier, "dispatch_agy", dispatch)
    if parser_error is not None:
        monkeypatch.setattr(verifier, "parse_agent_response", Mock(side_effect=parser_error))
    result = verifier.verify_claim(CLAIM, agent="agy", module_key="ai/test")
    assert result["verdict"] == "UNREADABLE"
    assert reason in result["reason"]
    assert result["source_url"] == URL and result["text_sha256"] == hashlib.sha256(PAGE_BYTES).hexdigest() and result["prompt_sha256"]
