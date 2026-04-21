from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import expand_module  # noqa: E402
import module_sections  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parent.parent
THIN_MODULE_KEY = "ai/ai-for-kubernetes-platform-work/module-1.2-ai-for-kubernetes-troubleshooting-and-triage"
THIN_MODULE_PATH = REPO_ROOT / "src" / "content" / "docs" / f"{THIN_MODULE_KEY}.md"


QUIZ_FIXTURE = """---
title: "Quiz Fixture"
slug: quiz-fixture
sidebar:
  order: 1
---

## Why This Module Matters

Operators need clear reasoning under pressure.

## Deep Dive

This section explains the key concept.

## Hands-On Exercise

Goal: validate the workflow.

## Next Module

Continue onward.
"""


THIN_FIXTURE = """---
title: "Thin Fixture"
slug: thin-fixture
sidebar:
  order: 1
---

## Why This Module Matters

Thin modules need enough depth to clear the rubric quickly.

## Deep Dive

This section introduces the main concept.
It needs more operational detail to become useful in practice.

## Another Core Section

This section gives a second place where the expander can append content.

## Sources

- [Docs](https://example.com/docs)
"""


def _write_module(root: Path, module_key: str, text: str) -> Path:
    path = root / "src" / "content" / "docs" / f"{module_key}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _thin_module_text() -> str:
    return THIN_MODULE_PATH.read_text(encoding="utf-8")


def _big_gemini_addition() -> str:
    lines = [
        "When teams triage Kubernetes failures, they need evidence they can compare across time, namespaces, and rollout boundaries.",
        "That means preserving event order, capturing pod status transitions, and identifying whether the blast radius points at scheduling, startup, or network behavior.",
        "A strong operator narrative connects each signal to an explicit question instead of treating every symptom as a likely root cause.",
        "This matters because most incident time is lost in ambiguity, not in typing commands.",
        "If your evidence only tells you that 'pods are unhappy,' AI will mirror that ambiguity back to you.",
        "If your evidence isolates one control plane event stream, one resource constraint, and one config change, the next step becomes much clearer.",
        "In practice, experienced responders keep a running split between what is observed, what is inferred, and what is still unknown.",
        "That structure makes it easier to challenge model output when it overreaches or starts collapsing possibilities too early.",
        "It also gives you a reusable artifact for handoff, postmortem work, and repeated failures that look similar at first glance but differ in one critical signal.",
        "Good triage notes are not paperwork; they are the mechanism that keeps the investigation falsifiable.",
    ]
    return "\n".join(lines * 8)


def _tiny_gemini_addition() -> str:
    return "Add one sentence.\n\nAdd one more sentence."


def _codex_output_for_gap(gap: str) -> str:
    if gap == "no_quiz":
        return "\n\n".join(
            (
                f"**Q{index}.** Your team is debugging a rollout in production. What evidence matters most first?\n\n"
                "<details>\n<summary>Answer</summary>\n"
                "Focus on concrete symptoms, current scope, and the evidence that separates the top hypotheses.\n"
                "</details>"
            )
            for index in range(1, 7)
        )
    if gap == "no_mistakes":
        rows = "\n".join(
            [
                "| Mistake | Why it's wrong | Fix |",
                "| --- | --- | --- |",
                "| Guessing the root cause early | It collapses the investigation too soon | Separate symptoms from hypotheses |",
                "| Skipping events | You lose the scheduling or admission context | Capture `kubectl describe` output first |",
                "| Treating AI output as fact | The model cannot see your cluster unless you show it | Require evidence-backed reasoning |",
                "| Running every command suggested | Noise hides signal | Rank checks by uncertainty reduction |",
                "| Ignoring recent changes | You miss the strongest candidate cause | Start with what changed |",
                "| Mixing verified and unverified notes | You blur confidence levels | Tag every conclusion by evidence level |",
            ]
        )
        return rows
    if gap == "no_exercise":
        return "\n".join(
            [
                "Goal: practice evidence-first Kubernetes triage.",
                "",
                "- [ ] Inspect the stuck workload and note the exact symptom.",
                "- [ ] Capture `kubectl describe pod <pod>` output.",
                "- [ ] Compare the latest deployment diff.",
                "- [ ] Run `kubectl get events -n <ns> --sort-by=.lastTimestamp` to rank likely causes.",
                "",
                "Verification commands:",
                "- `kubectl describe deploy <name>`",
                "- `kubectl get pods -o wide`",
                "",
                "Success criteria:",
                "- You can name the observed symptom.",
                "- You can rank the top hypotheses.",
                "- You can justify the next check.",
            ]
        )
    if gap == "no_outcomes":
        return "\n".join(
            [
                "- Distinguish symptoms, hypotheses, and confirmed causes in a Kubernetes triage flow.",
                "- Construct an evidence-first prompt that gives AI enough cluster context to be useful.",
                "- Evaluate AI troubleshooting output by ranking which checks reduce uncertainty fastest.",
            ]
        )
    raise AssertionError(f"unexpected gap: {gap}")


def _patch_roots(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(expand_module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(expand_module, "DOCS_ROOT", tmp_path / "src" / "content" / "docs")


def test_handler_quiz_injection(monkeypatch) -> None:
    monkeypatch.setattr(expand_module, "dispatch_codex_patch", lambda prompt, timeout=1200, model="gpt-5.4": (True, _codex_output_for_gap("no_quiz")))
    doc = module_sections.parse_module(QUIZ_FIXTURE)

    result = expand_module.handler_quiz(doc, "platform/foo/module-1.1-quiz-fixture")

    assert result.ok is True
    updated = module_sections.parse_module(result.text)
    slots = [section.slot for section in updated.sections]
    assert "quiz" in slots
    assert slots.index("quiz") < slots.index("hands_on")
    assert "<!-- v4:generated type=no_quiz model=codex turn=1 -->" in result.text
    assert expand_module.PROVENANCE_SUFFIX in result.text
    old_text = module_sections.assemble_module(doc)
    assert expand_module._diff_lint_additive_only(old_text, result.text) == (True, "additive-only")


def test_handler_thin_multi_pass_crosses_target(monkeypatch) -> None:
    monkeypatch.setattr(expand_module, "dispatch_gemini_with_retry", lambda prompt, timeout=900: (True, _big_gemini_addition()))
    doc = module_sections.parse_module(THIN_FIXTURE)

    result = expand_module.handler_thin(doc, THIN_MODULE_KEY, target_loc=600, max_thin_passes=5)

    assert result.ok is True
    assert expand_module._count_loc(result.text) >= 220
    assert result.provenance_blocks_added >= 1
    assert result.llm_calls >= 1


def test_handler_thin_max_passes_cap(monkeypatch) -> None:
    monkeypatch.setattr(expand_module, "dispatch_gemini_with_retry", lambda prompt, timeout=900: (True, _tiny_gemini_addition()))
    doc = module_sections.parse_module(THIN_FIXTURE)

    result = expand_module.handler_thin(doc, THIN_MODULE_KEY, target_loc=600, max_thin_passes=2)

    assert result.ok is False
    assert result.reason is not None
    assert result.reason.startswith("thin: max_passes reached")
    assert result.llm_calls == 2


def test_diff_lint_rejects_rewrite_and_expand_rolls_back(monkeypatch, tmp_path: Path) -> None:
    _patch_roots(monkeypatch, tmp_path)
    original = QUIZ_FIXTURE
    _write_module(tmp_path, "platform/foo/module-1.1-quiz-fixture", original)
    mutated_output = _codex_output_for_gap("no_quiz")
    monkeypatch.setattr(expand_module, "dispatch_codex_patch", lambda prompt, timeout=1200, model="gpt-5.4": (True, mutated_output))

    original_diff_lint = expand_module._diff_lint_additive_only

    def _reject_rewrite(old_text: str, new_text: str):
        rewritten = original.replace("Operators need clear reasoning under pressure.", "Operators need faster reasoning under pressure.")
        if new_text != rewritten:
            parsed = module_sections.parse_module(new_text)
            quiz = module_sections.find_section(parsed, "quiz")
            assert quiz is not None
            rewritten_doc = module_sections.parse_module(rewritten)
            rewritten_doc = module_sections.insert_section(
                rewritten_doc,
                "quiz",
                "Quiz",
                quiz.body,
            )
            new_text = module_sections.assemble_module(rewritten_doc)
        return original_diff_lint(old_text, new_text)

    monkeypatch.setattr(expand_module, "_diff_lint_additive_only", _reject_rewrite)

    is_safe, reason = original_diff_lint(
        original,
        original.replace("Operators need clear reasoning under pressure.", "Operators need faster reasoning under pressure."),
    )
    assert is_safe is False
    assert "original line missing after expansion" in reason

    result = expand_module.expand_module(
        "platform/foo/module-1.1-quiz-fixture",
        ["no_quiz"],
    )

    assert result.gaps_failed and result.gaps_failed[0][0] == "no_quiz"
    assert result.gaps_filled == []
    path = expand_module._module_path("platform/foo/module-1.1-quiz-fixture")
    assert path.read_text(encoding="utf-8") == original


def test_provenance_markers_preserved_roundtrip(monkeypatch) -> None:
    monkeypatch.setattr(expand_module, "dispatch_codex_patch", lambda prompt, timeout=1200, model="gpt-5.4": (True, _codex_output_for_gap("no_quiz")))
    doc = module_sections.parse_module(QUIZ_FIXTURE)

    result = expand_module.handler_quiz(doc, "platform/foo/module-1.1-quiz-fixture")

    assert result.ok is True
    reparsed = module_sections.parse_module(result.text)
    assert module_sections.assemble_module(reparsed) == result.text


def test_gap_skip_reasons_do_not_dispatch(monkeypatch, tmp_path: Path) -> None:
    _patch_roots(monkeypatch, tmp_path)
    _write_module(tmp_path, "platform/foo/module-1.1-skip-fixture", QUIZ_FIXTURE)

    def _fail_dispatch(*args, **kwargs):
        raise AssertionError("dispatch should not run for skipped gaps")

    monkeypatch.setattr(expand_module, "dispatch_codex_patch", _fail_dispatch)
    monkeypatch.setattr(expand_module, "dispatch_gemini_with_retry", _fail_dispatch)

    result = expand_module.expand_module(
        "platform/foo/module-1.1-skip-fixture",
        ["no_diagram", "no_citations"],
        dry_run=True,
    )

    assert result.gaps_filled == []
    assert result.gaps_failed == [
        ("no_diagram", "skipped: diagram gap requires human judgment"),
        ("no_citations", "handled by Stage 4 (citation_v3), not expand stage"),
    ]


def test_expand_module_integration_shape_and_file_content(monkeypatch, tmp_path: Path) -> None:
    _patch_roots(monkeypatch, tmp_path)
    original = THIN_FIXTURE
    _write_module(tmp_path, THIN_MODULE_KEY, original)

    def _fake_codex(prompt: str, timeout: int = 1200, model: str = "gpt-5.4"):
        lowered = prompt.lower()
        if "scenario-based quiz questions" in lowered:
            return True, _codex_output_for_gap("no_quiz")
        if "common mistakes" in lowered:
            return True, _codex_output_for_gap("no_mistakes")
        if "hands-on exercise" in lowered:
            return True, _codex_output_for_gap("no_exercise")
        if "learning outcomes" in lowered:
            return True, _codex_output_for_gap("no_outcomes")
        raise AssertionError(prompt)

    monkeypatch.setattr(expand_module, "dispatch_codex_patch", _fake_codex)
    monkeypatch.setattr(expand_module, "dispatch_gemini_with_retry", lambda prompt, timeout=900: (True, _big_gemini_addition()))

    result = expand_module.expand_module(
        THIN_MODULE_KEY,
        ["no_mistakes", "no_quiz", "no_exercise", "thin"],
        target_loc=600,
        max_thin_passes=5,
    )

    assert result.module_key == THIN_MODULE_KEY
    assert result.gaps_processed == ["no_mistakes", "no_quiz", "no_exercise", "thin"]
    assert result.gaps_failed == []
    assert set(result.gaps_filled) == {"no_mistakes", "no_quiz", "no_exercise", "thin"}
    assert result.provenance_blocks_added >= 4
    assert result.loc_after >= 220
    final_text = expand_module._module_path(THIN_MODULE_KEY).read_text(encoding="utf-8")
    assert "<!-- v4:generated type=no_quiz model=codex turn=1 -->" in final_text
    assert "<!-- v4:generated type=thin model=gemini turn=1 -->" in final_text
    assert "## Quiz" in final_text
    assert "## Common Mistakes" in final_text
    assert "## Hands-On Exercise" in final_text
    assert result.diff.startswith("--- ")


def test_main_uses_rubric_gaps_when_gap_not_provided(monkeypatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _patch_roots(monkeypatch, tmp_path)
    _write_module(tmp_path, "platform/foo/module-1.1-cli-fixture", QUIZ_FIXTURE)
    monkeypatch.setattr(
        expand_module.rubric_gaps,
        "gaps_for_module",
        lambda module_key: {"module_key": module_key, "gaps": ["no_quiz"]},
    )
    monkeypatch.setattr(expand_module, "dispatch_codex_patch", lambda prompt, timeout=1200, model="gpt-5.4": (True, _codex_output_for_gap("no_quiz")))

    exit_code = expand_module.main(["platform/foo/module-1.1-cli-fixture", "--dry-run"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"module_key": "platform/foo/module-1.1-cli-fixture"' in captured.out


def test_handler_quiz_treats_existing_quiz_alias_as_already_satisfied() -> None:
    doc = module_sections.parse_module(
        """---
title: "Alias Fixture"
slug: alias-fixture
---

## Why This Module Matters

Operators need clear reasoning under pressure.

## Quick Quiz

- Existing question

## Hands-On Exercise

Goal: validate the workflow.
"""
    )

    result = expand_module.handler_quiz(doc, "platform/foo/module-1.2-alias-fixture")

    assert result.ok is True
    assert result.llm_calls == 0
    assert result.text == module_sections.assemble_module(doc)
