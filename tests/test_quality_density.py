"""Density triple-gate + 3-way classifier tests (#388)."""
from __future__ import annotations

from scripts.quality.density import (
    DensityMetrics,
    DensityVerdict,
    W_PER_LINE_FLOOR,
    W_PER_LINE_FLOOR_REWRITE,
    W_PER_PARA_FLOOR,
    W_PER_PARA_FLOOR_REWRITE,
    WORDS_FLOOR,
    WORDS_FLOOR_REWRITE,
    evaluate_text,
)


def _m(*, words: int = 2000, wpl: float = 22.0, wpp: float = 30.0) -> DensityMetrics:
    """Build a DensityMetrics with the given signal triple."""
    return DensityMetrics(
        prose_words=words,
        textual_words=words,
        nonblank_lines=max(int(words / wpl), 1) if wpl else 1,
        total_paragraphs=max(int(words / wpp), 1) if wpp else 1,
        prose_paragraphs=max(int(words / wpp), 1) if wpp else 1,
        w_per_line=wpl,
        w_per_para=wpp,
    )


def test_classify_pass_at_pass_floors():
    assert _m(words=WORDS_FLOOR, wpl=W_PER_LINE_FLOOR, wpp=W_PER_PARA_FLOOR).classify() == DensityVerdict.PASS


def test_classify_pass_above_pass_floors():
    assert _m(words=3000, wpl=25.0, wpp=50.0).classify() == DensityVerdict.PASS


def test_classify_review_when_wpp_between_floors():
    """wpp ∈ [REWRITE_FLOOR, PASS_FLOOR) with other signals OK → REVIEW."""
    assert _m(wpp=W_PER_PARA_FLOOR_REWRITE).classify() == DensityVerdict.REVIEW
    assert _m(wpp=W_PER_PARA_FLOOR - 0.1).classify() == DensityVerdict.REVIEW


def test_classify_review_when_wpl_between_floors():
    assert _m(wpl=W_PER_LINE_FLOOR_REWRITE).classify() == DensityVerdict.REVIEW
    assert _m(wpl=W_PER_LINE_FLOOR - 0.1).classify() == DensityVerdict.REVIEW


def test_classify_rewrite_when_wpp_below_rewrite_floor():
    assert _m(wpp=W_PER_PARA_FLOOR_REWRITE - 0.1).classify() == DensityVerdict.REWRITE


def test_classify_rewrite_when_wpl_below_rewrite_floor():
    assert _m(wpl=W_PER_LINE_FLOOR_REWRITE - 0.1).classify() == DensityVerdict.REWRITE


def test_classify_rewrite_when_words_below_rewrite_floor():
    """Even with great wpp/wpl, sub-1000 prose words → REWRITE (too thin)."""
    assert _m(words=WORDS_FLOOR_REWRITE - 1, wpl=25.0, wpp=50.0).classify() == DensityVerdict.REWRITE


def test_classify_rewrite_dominates_when_multiple_signals_fail():
    """REWRITE-tier on any one signal wins regardless of the others."""
    assert _m(words=500, wpl=10.0, wpp=12.0).classify() == DensityVerdict.REWRITE


def test_evaluate_text_strips_code_blocks_from_prose():
    """Code blocks must NOT count toward prose_words — they are scaffolding."""
    text = """\
A short opening paragraph that should count as prose.

```bash
this is a code block with many words none of which should be in prose_words
this is a code block with many words none of which should be in prose_words
```

A second prose paragraph that also counts.
"""
    m = evaluate_text(text)
    # Two paragraphs, each ~10 words → ~20 prose words; code block excluded.
    assert m.prose_paragraphs == 2
    assert m.prose_words < 30  # well below the code block's word count
