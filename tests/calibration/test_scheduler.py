from __future__ import annotations

from scripts.calibration.models import model_by_canonical
from scripts.calibration.scheduler import FamilyParallelScheduler


def test_scheduler_interleaves_families_until_only_one_family_remains():
    openai = model_by_canonical("gpt-5.5")
    anthropic = model_by_canonical("claude-opus-4-7")
    google = model_by_canonical("gemini-3.5-flash-high")
    cells = [
        ("code-writing", "f1", openai),
        ("code-review", "f2", openai),
        ("fact-check", "f3", openai),
        ("code-writing", "f1", anthropic),
        ("code-review", "f2", anthropic),
        ("code-writing", "f1", google),
    ]

    scheduled = list(FamilyParallelScheduler([openai, anthropic, google]).schedule(cells))
    families = [cell[2].family for cell in scheduled]

    for index, family in enumerate(families[:-1]):
        remaining_other_families = set(families[index + 1 :]) - {family}
        if remaining_other_families:
            assert families[index + 1] != family
    assert sorted(families) == sorted(["openai", "openai", "openai", "anthropic", "anthropic", "google"])

