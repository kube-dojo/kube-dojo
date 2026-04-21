from __future__ import annotations

import io
import json
from typing import Any

from scripts import rubric_gaps


class _FakeResponse(io.BytesIO):
    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def _stub_scores_fetch(monkeypatch, payload: dict[str, Any]) -> None:
    monkeypatch.setattr(
        rubric_gaps,
        "urlopen",
        lambda url, timeout=5.0: _FakeResponse(json.dumps(payload).encode("utf-8")),
    )


def _quality_payload(*entries: dict[str, Any]) -> dict[str, Any]:
    return {
        "critical": [entry for entry in entries if float(entry.get("score", 0.0)) < 2.0],
        "modules": list(entries),
    }


def test_parse_primary_issue_multiple_known_gaps() -> None:
    assert rubric_gaps.parse_primary_issue("thin, no quiz") == ["thin", "no_quiz"]


def test_parse_primary_issue_known_single_gap() -> None:
    assert rubric_gaps.parse_primary_issue("no citations") == ["no_citations"]


def test_parse_primary_issue_empty_returns_no_gaps() -> None:
    assert rubric_gaps.parse_primary_issue("") == []


def test_parse_primary_issue_unknown_kept_as_normalized_gap() -> None:
    assert rubric_gaps.parse_primary_issue("Needs diagrams badly") == ["needs_diagrams_badly"]


def test_target_loc_for_kcna_path() -> None:
    assert rubric_gaps.target_loc_for_path("k8s/kcna/part1/module-1.1-topic.md") == 250


def test_target_loc_for_non_kcna_path() -> None:
    assert rubric_gaps.target_loc_for_path("k8s/cka/part1/module-1.1-topic.md") == 600


def test_fetch_gap_list_parses_output_shape(monkeypatch) -> None:
    payload = _quality_payload(
        {
            "module": "AI Ai For Kubernetes Platform Work: AI for Kubernetes Troubleshooting and Triage",
            "path": "ai/ai-for-kubernetes-platform-work/module-1.2-ai-for-kubernetes-troubleshooting-and-triage.md",
            "score": 2.0,
            "severity": "poor",
            "primary_issue": "thin, no quiz",
        }
    )
    _stub_scores_fetch(monkeypatch, payload)

    result = rubric_gaps.fetch_gap_list()

    assert result == [
        {
            "module_key": "ai/ai-for-kubernetes-platform-work/module-1.2-ai-for-kubernetes-troubleshooting-and-triage",
            "path": "ai/ai-for-kubernetes-platform-work/module-1.2-ai-for-kubernetes-troubleshooting-and-triage.md",
            "module": "AI Ai For Kubernetes Platform Work: AI for Kubernetes Troubleshooting and Triage",
            "score": 2.0,
            "severity": "poor",
            "primary_issue": "thin, no quiz",
            "gaps": ["thin", "no_quiz"],
            "target_loc": 600,
        }
    ]


def test_fetch_gap_list_min_score_filter(monkeypatch) -> None:
    payload = _quality_payload(
        {
            "module": "High Score",
            "path": "platform/foo/module-1.1-high-score.md",
            "score": 4.5,
            "severity": "excellent",
            "primary_issue": "balanced",
        },
        {
            "module": "Low Score",
            "path": "platform/foo/module-1.2-low-score.md",
            "score": 2.0,
            "severity": "poor",
            "primary_issue": "thin, no quiz",
        },
    )
    _stub_scores_fetch(monkeypatch, payload)

    result = rubric_gaps.fetch_gap_list(min_score=4.0)

    assert [item["module_key"] for item in result] == ["platform/foo/module-1.1-high-score"]


def test_gaps_for_module_returns_known_and_none_for_unknown(monkeypatch) -> None:
    payload = _quality_payload(
        {
            "module": "Known Module",
            "path": "platform/foo/module-1.1-known.md",
            "score": 1.5,
            "severity": "critical",
            "primary_issue": "no citations",
        }
    )
    _stub_scores_fetch(monkeypatch, payload)

    found = rubric_gaps.gaps_for_module("platform/foo/module-1.1-known")
    missing = rubric_gaps.gaps_for_module("platform/foo/module-1.2-missing")

    assert found is not None
    assert found["gaps"] == ["no_citations"]
    assert missing is None
