from __future__ import annotations

from scripts.calibration.models import ANCHORS, LANES, model_by_canonical, models_by_family


def test_anchor_registry_has_locked_models_and_lanes():
    assert len(ANCHORS) == 14
    assert len({model.canonical_string for model in ANCHORS}) == 14
    assert len(LANES) == 10
    assert model_by_canonical("claude-opus-4-7").effort_mechanism == "native_flag"
    assert model_by_canonical("gpt-5.5").effort_requested == "xhigh"
    assert model_by_canonical("grok-4.3").effort_confidence == "unknown"


def test_models_by_family_groups_codex_under_openai():
    grouped = models_by_family()
    assert [model.canonical_string for model in grouped["openai"]] == [
        "gpt-5.5",
        "gpt-5.3-codex-spark",
        "gpt-5.4-mini",
    ]
    assert set(grouped) == {"anthropic", "openai", "google", "deepseek", "alibaba", "xai"}

