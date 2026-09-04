"""Deterministic cache-provenance tests for the citation fetcher."""
from __future__ import annotations

import hashlib
import json
import sys
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Self
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import fetch_citation


class _Response:
    def __init__(self, body: bytes, *, final_url: str, content_type: str = "text/plain") -> None:
        self._body = body
        self._final_url = final_url
        self.headers = {"Content-Type": content_type}

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, _limit: int = -1) -> bytes:
        return self._body

    def geturl(self) -> str:
        return self._final_url

    def getcode(self) -> int:
        return 200


@pytest.fixture
def cache_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setattr(fetch_citation, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(fetch_citation, "allowlist_tier", lambda _url: "standards")
    return tmp_path


def test_new_fetch_hashes_exact_utf8_bytes_and_records_completion(cache_dir):
    url = "https://source.example/article"
    body = "<p>Café</p><p>Line\nTwo</p>".encode()
    expected = "Café\nLine\nTwo".encode()
    with patch.object(
        fetch_citation.urllib.request,
        "urlopen",
        return_value=_Response(
            body,
            final_url="https://source.example/article",
            content_type="text/html; charset=utf-8",
        ),
    ):
        result = fetch_citation.fetch(url)

    text_path = fetch_citation.cached_text_path(url)
    assert text_path.read_bytes() == expected
    assert result["text_sha256"] == hashlib.sha256(expected).hexdigest()
    assert result["text_bytes"] == len(expected)
    assert result["truncated"] is False
    datetime.fromisoformat(result["fetch_attempt_completed_at"])
    assert result["from_cache"] is False
    assert result["allowlist_tier"] == "standards"
    assert cache_dir.joinpath(text_path.name).read_bytes() == expected


def test_redirect_and_truncation_are_recorded(cache_dir, monkeypatch):
    monkeypatch.setattr(fetch_citation, "MAX_BYTES", 5)
    allowlist = MagicMock(return_value="standards")
    monkeypatch.setattr(fetch_citation, "allowlist_tier", allowlist)
    url = "https://source.example/start"
    final_url = "https://source.example/final"
    with patch.object(
        fetch_citation.urllib.request,
        "urlopen",
        return_value=_Response(b"abcdef", final_url=final_url),
    ):
        result = fetch_citation.fetch(url)

    assert result["final_url"] == final_url
    assert result["bytes"] == 6
    assert result["truncated"] is True
    assert "truncated_body" in result["issues"]
    allowlist.assert_called_once_with(final_url)
    assert result["text_bytes"] == 5
    assert result["text_sha256"] == hashlib.sha256(b"abcde").hexdigest()
    assert fetch_citation.cached_text_path(url).read_bytes() == b"abcde"


def test_failed_and_pdf_fetches_keep_issues_without_acceptance(cache_dir):
    failed_url = "https://source.example/fails"
    with patch.object(
        fetch_citation.urllib.request,
        "urlopen",
        side_effect=urllib.error.URLError("offline"),
    ):
        failed = fetch_citation.fetch(failed_url)

    assert failed["status"] == 0
    assert failed["truncated"] is None
    assert "network_failure" in failed["issues"]
    assert failed["text_bytes"] == 0
    assert "source_acceptance" not in failed

    pdf_url = "https://source.example/report.pdf"
    with patch.object(
        fetch_citation.urllib.request,
        "urlopen",
        return_value=_Response(b"%PDF-1.7", final_url=pdf_url, content_type="application/pdf"),
    ):
        pdf = fetch_citation.fetch(pdf_url)

    assert "pdf_needs_adapter" in pdf["issues"]
    assert pdf["text_sha256"] == hashlib.sha256(b"").hexdigest()
    assert "source_acceptance" not in pdf
    assert fetch_citation.cached_text_path(pdf_url).read_bytes() == b""


def test_legacy_cache_hit_does_not_gain_provenance(cache_dir):
    url = "https://source.example/legacy"
    meta_path, text_path = fetch_citation._cache_paths(url)
    legacy = {
        "url": url,
        "final_url": url,
        "status": 200,
        "content_type": "text/plain",
        "bytes": 6,
        "text_length": 6,
        "cached_at": "2024-01-01T00:00:00+00:00",
        "issues": [],
    }
    meta_path.write_text(json.dumps(legacy), encoding="utf-8")
    text_path.write_bytes(b"legacy")

    with patch.object(fetch_citation.urllib.request, "urlopen") as urlopen:
        result = fetch_citation.fetch(url)

    urlopen.assert_not_called()
    assert result["from_cache"] is True
    assert result["cached_at"] == legacy["cached_at"]
    assert all(
        key not in result
        for key in ("text_sha256", "text_bytes", "fetch_attempt_completed_at", "truncated")
    )
