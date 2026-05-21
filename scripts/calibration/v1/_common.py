"""Shared helpers for calibration v1 command scripts."""
from __future__ import annotations


def unit_score(gate_name: str, score_value: float) -> float:
    """Map mixed ledger scores onto a pass/fail-like 0..1 scale."""
    if gate_name == "llm_judge_score":
        return max(0.0, min(1.0, score_value / 10.0))
    return max(0.0, min(1.0, score_value))
