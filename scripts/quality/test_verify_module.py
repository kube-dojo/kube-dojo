from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.quality import verify_module


def _base_gates() -> dict[str, bool | None]:
    return {
        "density_mean_wpp_30": True,
        "density_median_wpp_28": True,
        "density_short_rate_20pct": True,
        "density_max_consecutive_short_2": True,
        "body_words_5000": True,
        "sentence_length_12_28": True,
        "structure_sections_present": True,
        "structure_order_correct": True,
        "structure_did_you_know_4": True,
        "structure_common_mistakes_6_8": True,
        "structure_quiz_6_8_with_details": True,
        "structure_hands_on_checkboxes": True,
        "sources_min_10": True,
        "sources_all_reachable": None,
        "anti_leak": True,
        "runnable_no_kubectl_alias": True,
        "anti_fabrication_no_unsourced_anecdote": True,
        "practice_mcq_four_options_with_distractors": True,
        "outcomes_aligned": True,
    }


def _gate_results(
    *,
    runnable_shell: dict[str, object] | None = None,
    anti_fabrication: dict[str, object] | None = None,
    practice_mcq: dict[str, object] | None = None,
) -> dict[str, bool | None]:
    return verify_module.gate_results(
        {
            "mean_wpp": 35,
            "median_wpp": 35,
            "short_paragraph_rate": 0.0,
            "max_consecutive_short_run": 0,
            "body_words": 6000,
            "mean_sentence_length": 18,
        },
        {
            "has_learning_outcomes": True,
            "learning_outcome_count": 3,
            "has_why_matters": True,
            "did_you_know_count": 4,
            "common_mistakes_rows": 6,
            "quiz_count": 6,
            "quiz_with_details": 6,
            "hands_on_checkboxes": 3,
            "section_order_correct": True,
            "next_module_link": True,
        },
        {"count": 10, "url_status": {"skipped": 10}, "urls": []},
        {"forbidden_tokens": [], "has_emoji": False, "has_47": False},
        runnable_shell or {"kubectl_alias_violations": []},
        anti_fabrication or {"unsourced_anecdotes": []},
        practice_mcq or {"applies": False, "question_count": 0, "violations": []},
        {"all_outcomes_covered": True},
        skip_source_check=True,
    )


def test_body_prose_extraction_skips_non_prose_blocks() -> None:
    text = """---
title: Demo
---
# Heading

This paragraph remains with enough words to count as real teaching prose.

```bash
echo TBD
```

| A | B |
| --- | --- |
| one | two |

- list item
  continuation

+--------+--------+
| box    | value  |
+--------+--------+

<details>
<summary>Answer</summary>
Hidden prose should not appear.
</details>

## Sources
- https://example.com/source
"""
    assert verify_module.extract_body_paragraphs(text) == [
        "This paragraph remains with enough words to count as real teaching prose."
    ]


def test_body_prose_extraction_skips_top_metadata_blockquote() -> None:
    text = """---
title: Demo
---
> **Complexity**: [MEDIUM]
>
> **Time to Complete**: 45-60 minutes
>
> **Prerequisites**: Prior module

---

## What You'll Be Able to Do

This teaching paragraph remains with enough words to count as prose after the metadata block.
"""
    assert verify_module.extract_body_paragraphs(text) == [
        "This teaching paragraph remains with enough words to count as prose after the metadata block."
    ]


def test_body_prose_extraction_skips_horizontal_rules() -> None:
    text = """---
title: Demo
---
## What You'll Be Able to Do

This first teaching paragraph has enough words to count as prose before the separator.

---

This second teaching paragraph also remains after the separator without counting the rule itself.
"""
    assert verify_module.extract_body_paragraphs(text) == [
        "This first teaching paragraph has enough words to count as prose before the separator.",
        "This second teaching paragraph also remains after the separator without counting the rule itself.",
    ]


def test_runnable_no_kubectl_alias_passes_on_clean_kubectl() -> None:
    text = """---
title: Demo
---
```bash
kubectl get pods
```
"""
    metrics = verify_module.runnable_shell_metrics(text)
    assert metrics["kubectl_alias_violations"] == []
    assert _gate_results(runnable_shell=metrics)["runnable_no_kubectl_alias"] is True


def test_runnable_no_kubectl_alias_fails_on_alias_definition() -> None:
    text = """---
title: Demo
---
```bash
alias k=kubectl
```
"""
    metrics = verify_module.runnable_shell_metrics(text)
    assert metrics["kubectl_alias_violations"] == ["alias k=kubectl"]
    assert _gate_results(runnable_shell=metrics)["runnable_no_kubectl_alias"] is False


def test_runnable_no_kubectl_alias_fails_on_kubectl_shorthand() -> None:
    text = """---
title: Demo
---
```bash
k get pods
```
"""
    metrics = verify_module.runnable_shell_metrics(text)
    assert metrics["kubectl_alias_violations"] == ["k get"]
    assert _gate_results(runnable_shell=metrics)["runnable_no_kubectl_alias"] is False


def test_runnable_no_kubectl_alias_allows_text_blocks() -> None:
    text = """---
title: Demo
---
```text
k get pods
```
"""
    metrics = verify_module.runnable_shell_metrics(text)
    assert metrics["kubectl_alias_violations"] == []
    assert _gate_results(runnable_shell=metrics)["runnable_no_kubectl_alias"] is True


def test_density_metrics_on_synthetic_short_module_fail() -> None:
    metrics = verify_module.density_metrics("Tiny.\n\nShort too.\n")
    gates = verify_module.gate_results(
        metrics,
        {
            "has_learning_outcomes": True,
            "learning_outcome_count": 3,
            "has_why_matters": True,
            "did_you_know_count": 4,
            "common_mistakes_rows": 6,
            "quiz_count": 6,
            "quiz_with_details": 6,
            "hands_on_checkboxes": 3,
            "section_order_correct": True,
            "next_module_link": True,
        },
        {"count": 10, "url_status": {"skipped": 10}, "urls": []},
        {"forbidden_tokens": [], "has_emoji": False, "has_47": False},
        {"kubectl_alias_violations": []},
        {"unsourced_anecdotes": []},
        {"applies": False, "question_count": 0, "violations": []},
        {"all_outcomes_covered": True},
        skip_source_check=True,
    )
    assert metrics["body_words"] < 5000
    assert gates["density_mean_wpp_30"] is False
    assert gates["body_words_5000"] is False


def test_max_consecutive_short_run_edge_case() -> None:
    two_short = verify_module.density_metrics(
        "one two three.\n\nfour five six.\n\n"
        "This paragraph has enough words to break the short paragraph run before another short one appears "
        "inside the fixture with room to spare."
    )
    three_short = verify_module.density_metrics("one two three.\n\nfour five six.\n\nseven eight nine.\n")
    assert two_short["max_consecutive_short_run"] == 2
    assert three_short["max_consecutive_short_run"] == 3
    assert two_short["max_consecutive_short_run"] <= 2
    assert three_short["max_consecutive_short_run"] > 2


def test_tier_classification_variants() -> None:
    metrics = {"body_words": 6000}
    gates = _base_gates()
    assert verify_module.classify_tier(metrics, gates) == ("T0", [])

    structure_only = _base_gates()
    structure_only["structure_order_correct"] = False
    assert verify_module.classify_tier(metrics, structure_only)[0] == "T1"

    density_only = _base_gates()
    density_only["density_max_consecutive_short_2"] = False
    assert verify_module.classify_tier(metrics, density_only)[0] == "T2"

    both = _base_gates()
    both["density_max_consecutive_short_2"] = False
    both["structure_order_correct"] = False
    assert verify_module.classify_tier(metrics, both)[0] == "T3"

    assert verify_module.classify_tier({"body_words": 2999}, _base_gates())[0] == "T3"


def test_sources_url_extraction_handles_markdown_and_bare_urls() -> None:
    section = """
- [Kubernetes](https://kubernetes.io/docs/)
- Bare: https://example.com/path?x=1.
- Duplicate [again](https://kubernetes.io/docs/)
"""
    assert verify_module.extract_urls(section) == [
        "https://kubernetes.io/docs/",
        "https://example.com/path?x=1",
    ]


def test_anti_leak_catches_tbd_but_not_inside_code_fence() -> None:
    fenced = verify_module.anti_leak_metrics("```text\nTBD\n```\nClean body.")
    plain = verify_module.anti_leak_metrics("This module still has TBD in prose.")
    assert fenced["forbidden_tokens"] == []
    assert plain["forbidden_tokens"] == ["TBD"]


def test_anti_fabrication_no_unsourced_anecdote_passes_on_neutral_prose() -> None:
    metrics = verify_module.anti_fabrication_metrics("This section explains a generic rollout failure mode.")
    assert metrics["unsourced_anecdotes"] == []
    assert _gate_results(anti_fabrication=metrics)["anti_fabrication_no_unsourced_anecdote"] is True


def test_anti_fabrication_no_unsourced_anecdote_fails_on_war_story() -> None:
    metrics = verify_module.anti_fabrication_metrics("War story: a rollout went sideways during an upgrade.")
    assert metrics["unsourced_anecdotes"] == ["War story:"]
    assert _gate_results(anti_fabrication=metrics)["anti_fabrication_no_unsourced_anecdote"] is False


def test_anti_fabrication_no_unsourced_anecdote_fails_on_industry_once_frame() -> None:
    metrics = verify_module.anti_fabrication_metrics("A payments company once routed traffic to the wrong cluster.")
    assert metrics["unsourced_anecdotes"] == ["A payments company once"]
    assert _gate_results(anti_fabrication=metrics)["anti_fabrication_no_unsourced_anecdote"] is False


def test_anti_fabrication_no_unsourced_anecdote_allows_hypothetical_prefix() -> None:
    metrics = verify_module.anti_fabrication_metrics(
        "Hypothetical scenario: a payments company once would have routed traffic to the wrong cluster."
    )
    assert metrics["unsourced_anecdotes"] == []
    assert _gate_results(anti_fabrication=metrics)["anti_fabrication_no_unsourced_anecdote"] is True


def test_anti_fabrication_no_unsourced_anecdote_allows_bold_hypothetical_prefix() -> None:
    metrics = verify_module.anti_fabrication_metrics(
        "**Hypothetical scenario:** A payments company once would have routed traffic to the wrong cluster."
    )
    assert metrics["unsourced_anecdotes"] == []
    assert _gate_results(anti_fabrication=metrics)["anti_fabrication_no_unsourced_anecdote"] is True


def test_learning_outcomes_synonym_is_detected() -> None:
    metrics = verify_module.structure_metrics(
        """
## What You'll Be Able to Do
- Explain one outcome.
- Configure another outcome.
- Troubleshoot a third outcome.
"""
    )
    assert metrics["has_learning_outcomes"] is True
    assert metrics["learning_outcome_count"] == 3


def test_quiz_topic_heading_is_detected() -> None:
    metrics = verify_module.structure_metrics(
        """
## Quiz: Operational Scenarios
<details>
<summary>How should you respond?</summary>
Answer.
</details>
"""
    )
    assert metrics["quiz_count"] == 1
    assert metrics["quiz_with_details"] == 1


def test_practice_mcq_four_options_with_distractors_passes() -> None:
    path = verify_module.REPO_ROOT / "src/content/docs/k8s/cgoa/module-1.4-practice-questions-set-1.md"
    text = """
## Quiz

### Question 1

What should the operator do first?

1. Inspect the failing Pod events.
2. Delete every workload in the namespace.
3. Restart the control plane.
4. Ignore the alert until the next sync.

<details>
<summary>Answer</summary>

Option 1 is correct because events show scheduler and admission failures. Option 2 is wrong because it
destroys unrelated state. Option 3 is incorrect because the symptom is workload-scoped. Option 4 is not
correct because the alert needs immediate triage.
</details>
"""
    metrics = verify_module.practice_mcq_metrics(path, text)
    assert metrics["violations"] == []
    assert _gate_results(practice_mcq=metrics)["practice_mcq_four_options_with_distractors"] is True


def test_practice_mcq_four_options_with_plural_distractor_references_passes() -> None:
    path = verify_module.REPO_ROOT / "src/content/docs/k8s/cgoa/module-1.4-practice-questions-set-1.md"
    text = """
## Quiz

### Question 1

What should the operator do first?

1. Inspect the failing Pod events.
2. Delete every workload in the namespace.
3. Restart the control plane.
4. Ignore the alert until the next sync.

<details>
<summary>Answer</summary>

Option 1 is correct because events show scheduler and admission failures. Options 2 and 3 are incorrect
because they destroy unrelated state or restart healthy components. Option 4 is wrong because the alert
needs immediate triage.
</details>
"""
    metrics = verify_module.practice_mcq_metrics(path, text)
    assert metrics["violations"] == []
    assert _gate_results(practice_mcq=metrics)["practice_mcq_four_options_with_distractors"] is True


def test_practice_mcq_four_options_ignores_embedded_numbered_list() -> None:
    path = verify_module.REPO_ROOT / "src/content/docs/k8s/cgoa/module-1.4-practice-questions-set-1.md"
    text = """
## Quiz

### Question 1

The operator did: 1. Restarted pod 2. Checked logs. What should happen next?

1. Inspect the failing Pod events.
2. Delete every workload in the namespace.
3. Restart the control plane.
4. Ignore the alert until the next sync.

<details>
<summary>Answer</summary>

Option 1 is correct because events show scheduler and admission failures. Option 2 is wrong because it
destroys unrelated state. Option 3 is incorrect because the symptom is workload-scoped. Option 4 is not
correct because the alert needs immediate triage.
</details>
"""
    metrics = verify_module.practice_mcq_metrics(path, text)
    assert metrics["violations"] == []
    assert _gate_results(practice_mcq=metrics)["practice_mcq_four_options_with_distractors"] is True


def test_practice_mcq_requires_details_answer_block() -> None:
    path = verify_module.REPO_ROOT / "src/content/docs/k8s/cgoa/module-1.4-practice-questions-set-1.md"
    text = """
## Quiz

### Question 1

What should the operator do first?

1. Inspect the failing Pod events.
2. Delete every workload in the namespace.
3. Restart the control plane.
4. Ignore the alert until the next sync.

Answer: Option 1 is correct because events show scheduler and admission failures. Option 2 is wrong
because it destroys unrelated state. Option 3 is incorrect because the symptom is workload-scoped.
Option 4 is not correct because the alert needs immediate triage.
"""
    metrics = verify_module.practice_mcq_metrics(path, text)
    assert metrics["violations"][0]["message"] == "MCQ at line 4 missing `<details>` answer block"
    assert _gate_results(practice_mcq=metrics)["practice_mcq_four_options_with_distractors"] is False


def test_practice_mcq_four_options_with_distractors_fails_on_stripped_options() -> None:
    path = verify_module.REPO_ROOT / "src/content/docs/k8s/cgoa/module-1.4-practice-questions-set-1.md"
    text = """
## Quiz

<details>
<summary>Question 1: What should the operator do first?</summary>

Option 1 is correct because events show the root cause. Option 2 is wrong because it destroys unrelated
state. Option 3 is incorrect because the symptom is workload-scoped.
</details>
"""
    metrics = verify_module.practice_mcq_metrics(path, text)
    assert metrics["violations"][0]["visible_options"] == 0
    assert _gate_results(practice_mcq=metrics)["practice_mcq_four_options_with_distractors"] is False


def test_practice_mcq_four_options_with_distractors_skips_non_practice_modules() -> None:
    path = verify_module.REPO_ROOT / "src/content/docs/k8s/cgoa/module-1.1-exam-strategy.md"
    metrics = verify_module.practice_mcq_metrics(path, "## Quiz\nNo MCQs here.")
    assert metrics["applies"] is False
    assert _gate_results(practice_mcq=metrics)["practice_mcq_four_options_with_distractors"] is None


def test_hands_on_topic_heading_is_detected() -> None:
    metrics = verify_module.structure_metrics(
        """
## Hands-On: Build a RAG vs Fine-tuning Decision Engine CLI
- [ ] Create the CLI scaffold.
- [ ] Add the decision rules.
- [ ] Test two scenarios.
"""
    )
    assert metrics["hands_on_checkboxes"] == 3


def test_common_mistakes_prefix_heading_is_detected() -> None:
    metrics = verify_module.structure_metrics(
        """
## Common Mistakes and How to Avoid Them
| Mistake | Fix |
| --- | --- |
| one | fix |
| two | fix |
| three | fix |
| four | fix |
| five | fix |
| six | fix |
"""
    )
    assert metrics["common_mistakes_rows"] == 6


def test_further_reading_heading_is_detected_as_sources() -> None:
    metrics = verify_module.sources_metrics(
        """
## Further Reading
- https://example.com/source
""",
        skip_source_check=True,
        max_workers=1,
    )
    assert metrics["count"] == 1


def test_did_you_know_question_mark_heading_is_detected() -> None:
    metrics = verify_module.structure_metrics(
        """
## Did You Know?
- One fact.
- Two facts.
- Three facts.
- Four facts.
"""
    )
    assert metrics["did_you_know_count"] == 4


def test_cli_all_revision_pending_writes_jsonl(tmp_path: Path, monkeypatch) -> None:
    docs = tmp_path / "src/content/docs"
    docs.mkdir(parents=True)
    module = docs / "module.md"
    module.write_text("---\ntitle: Pending\nrevision_pending: true\n---\nBody\n", encoding="utf-8")
    out = tmp_path / "records.jsonl"

    def fake_verify(path: Path, skip_source_check: bool = False, max_workers: int = 8) -> dict[str, object]:
        return {"path": str(path), "tier": "T3", "tier_reasons": ["body_words_5000"]}

    monkeypatch.setattr(verify_module, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(verify_module, "verify", fake_verify)

    assert verify_module.main(["--all-revision-pending", "--out", str(out), "--skip-source-check", "--quiet"]) == 0
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["tier"] == "T3"
