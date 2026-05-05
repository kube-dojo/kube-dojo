from scripts.audit_review_coverage import _expected_lane_fields, _lane_satisfied


def test_part6_claude_research_requires_codex_and_gemini_reviews():
    assert _expected_lane_fields(32, "research") == {"codex_anchor", "gemini_gap"}
    assert _expected_lane_fields(37, "research") == {"codex_anchor", "gemini_gap"}


def test_part6_exception_does_not_apply_after_ch37():
    assert _expected_lane_fields(38, "research") == {"claude_anchor", "gemini_gap"}


def test_part6_codex_gemini_research_markers_satisfy_cross_family_rule():
    values = {
        "claude_anchor": "n/a",
        "gemini_gap": "done",
        "codex_anchor": "done",
    }

    assert _lane_satisfied(values, 32, "research") is True

