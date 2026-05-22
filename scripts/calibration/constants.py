"""Shared constants for calibration analysis and reporting."""
from __future__ import annotations

DETERMINISTIC_SCORERS = ("deterministic", "respected_inline_return")

PROSE_LANES = frozenset(
    (
        "orchestrating",
        "refactoring",
        "summarization",
        "content-writing-long",
        "architecting",
        "content-review",
        "fact-check",
        "mcp-use",
        "harness-following",
    )
)
MECHANICAL_LANES = frozenset(
    (
        "code-writing",
        "code-review",
        "debugging",
    )
)

COMPOSITE_GATE_WEIGHT = 0.4
COMPOSITE_JUDGE_WEIGHT = 0.6

# Letter grade bands are lower-inclusive and upper-exclusive except A, whose
# 10.01 upper bound admits a clamped 10.0 score.
LETTER_GRADE_BANDS = [
    ("A", 8.5, 10.01, "#1f8a3f"),
    ("B", 7.0, 8.5, "#4caf50"),
    ("C", 5.5, 7.0, "#ffb300"),
    ("D", 4.0, 5.5, "#fb8c00"),
    ("F", 0.0, 4.0, "#e53935"),
]

JUDGE_DISSENT_THRESHOLD = 2.0
