"""Tests for ``scripts.quality.extractors``.

Covers the Codex must-fixes this module closes:

* **#7** — tolerate code fences, prose prefixes; fail loud on truncation
* **#8** — pick the LAST schema-matching JSON (verdict), not the first
  (reasoning)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.quality import extractors  # noqa: E402
from scripts.quality.extractors import (  # noqa: E402
    JsonExtractError,
    ModuleExtractError,
    extract_last_json,
    extract_module_markdown,
)


# ---------- module extractor ---------------------------------------------


_CLEAN_MODULE = """---
title: Test Module
sidebar:
  order: 1
---

# Test Module

Body content here.

```bash
echo hello
```

More content.
"""


def test_clean_module_extracts_unchanged() -> None:
    result = extract_module_markdown(_CLEAN_MODULE)
    assert result.text.strip().startswith("---")
    assert result.title == "Test Module"
    assert result.unwrapped_code_fence is False


def test_prose_prefixed_module_skips_preamble() -> None:
    raw = f"Here is the rewritten module:\n\nNote: I improved the quiz.\n\n{_CLEAN_MODULE}"
    result = extract_module_markdown(raw)
    assert result.text.lstrip().startswith("---")
    assert result.title == "Test Module"
    assert "Here is the rewritten" not in result.text


def test_code_fenced_markdown_module_unwraps() -> None:
    raw = f"```markdown\n{_CLEAN_MODULE}```\n"
    result = extract_module_markdown(raw)
    assert result.unwrapped_code_fence is True
    assert result.title == "Test Module"
    # Body should still contain the inner bash code fence.
    assert "```bash" in result.text


def test_code_fenced_no_lang_module_unwraps() -> None:
    raw = f"```\n{_CLEAN_MODULE}```"
    result = extract_module_markdown(raw)
    assert result.unwrapped_code_fence is True


def test_quoted_title_strips_surrounding_quotes() -> None:
    raw = """---
title: "Quoted Module Title"
sidebar:
  order: 2
---

Body.
"""
    result = extract_module_markdown(raw)
    assert result.title == "Quoted Module Title"


def test_single_quoted_title_strips_quotes() -> None:
    raw = """---
title: 'Single-Quoted'
sidebar:
  order: 2
---

Body.
"""
    result = extract_module_markdown(raw)
    assert result.title == "Single-Quoted"


def test_empty_input_raises() -> None:
    with pytest.raises(ModuleExtractError):
        extract_module_markdown("")


def test_whitespace_only_input_raises() -> None:
    with pytest.raises(ModuleExtractError):
        extract_module_markdown("   \n\n\t  \n")


def test_no_frontmatter_raises() -> None:
    raw = "Just a body.\n\nNo frontmatter anywhere.\n"
    with pytest.raises(ModuleExtractError):
        extract_module_markdown(raw)


def test_frontmatter_opened_but_not_closed_raises() -> None:
    raw = """---
title: Unclosed

The LLM got cut off before writing the closing ---.
"""
    with pytest.raises(ModuleExtractError, match="truncated"):
        extract_module_markdown(raw)


def test_truncated_mid_code_block_raises() -> None:
    """Body with odd number of ``` lines — LLM was cut off inside a code fence.

    Without this check, v1 silently accepted truncated modules and
    reviewers got garbage. The ``---`` frontmatter closes, so the
    structural check must look at ``` fences too.
    """
    raw = """---
title: Truncated Body
---

Content before the code block.

```bash
kubectl get pods
"""
    with pytest.raises(ModuleExtractError, match="truncated"):
        extract_module_markdown(raw)


def test_decorative_dashes_in_prose_do_not_match_as_frontmatter() -> None:
    """A ``---`` separator in reasoning prose followed by more prose must
    NOT be mistaken for the frontmatter opening."""
    raw = f"""Here's my thinking:

---

I decided to rewrite section 3 because the quiz was weak.

{_CLEAN_MODULE}"""
    result = extract_module_markdown(raw)
    # The real frontmatter (with title:) wins — not the decorative ---.
    assert result.title == "Test Module"


def test_frontmatter_without_title_returns_none_for_title_field() -> None:
    raw = """---
sidebar:
  order: 3
---

Body without a title field.
"""
    result = extract_module_markdown(raw)
    assert result.title is None


def test_result_ends_with_trailing_newline() -> None:
    raw = _CLEAN_MODULE.rstrip()
    result = extract_module_markdown(raw)
    assert result.text.endswith("\n")


# ---------- JSON extractor ----------------------------------------------


def test_fenced_single_json_extracts() -> None:
    raw = """```json
{"verdict": "approve", "rubric_score": 4.5, "teaching_score": 4.2}
```"""
    result = extract_last_json(raw, {"verdict", "rubric_score"})
    assert result["verdict"] == "approve"
    assert result["rubric_score"] == 4.5


def test_bare_single_json_extracts() -> None:
    raw = '{"verdict": "changes_requested", "rubric_score": 3.0, "must_fix": ["X"]}'
    result = extract_last_json(raw, {"verdict", "must_fix"})
    assert result["verdict"] == "changes_requested"
    assert result["must_fix"] == ["X"]


def test_prose_preamble_before_json_handled() -> None:
    raw = """Here is my verdict:

{"verdict": "approve", "rubric_score": 4.0, "teaching_score": 4.1}

Thanks for the module."""
    result = extract_last_json(raw, {"verdict", "rubric_score"})
    assert result["verdict"] == "approve"


def test_last_matching_json_wins_over_reasoning_json() -> None:
    """Codex-pattern regression — must-fix #8.

    v1's first-balanced-object scan would grab the ``reasoning`` blob
    and auto-approve modules that weren't actually approved.
    """
    raw = """First, let me think:

{"reasoning": "The module has weak quiz questions but strong exercise", "draft_score": 3.0}

After consideration, my verdict is:

{"verdict": "changes_requested", "rubric_score": 3.5, "must_fix": ["fix quiz"], "nits": []}
"""
    result = extract_last_json(raw, {"verdict", "rubric_score"})
    assert result["verdict"] == "changes_requested"
    assert result["rubric_score"] == 3.5
    assert "reasoning" not in result  # the reasoning object didn't match


def test_schema_mismatch_first_is_skipped() -> None:
    """Even if the reasoning object is balanced JSON, missing required keys
    means it's NOT chosen — only the object with all required keys wins."""
    raw = """{"draft": "some thought"}

{"verdict": "approve", "rubric_score": 4.2, "teaching_score": 4.0}"""
    result = extract_last_json(raw, {"verdict", "rubric_score", "teaching_score"})
    assert result["verdict"] == "approve"


def test_nested_json_objects_handled() -> None:
    raw = """{"verdict": "approve", "rubric_score": 4.5, "scores": {"teaching": 4.0, "structure": 4.5}}"""
    result = extract_last_json(raw, {"verdict", "scores"})
    assert result["scores"]["teaching"] == 4.0


def test_braces_inside_strings_dont_confuse_parser() -> None:
    raw = '{"verdict": "approve", "rubric_score": 4.0, "reasoning": "author used {tera} template syntax"}'
    result = extract_last_json(raw, {"verdict", "reasoning"})
    assert result["reasoning"] == "author used {tera} template syntax"


def test_escaped_quote_inside_string_handled() -> None:
    raw = r'{"verdict": "approve", "rubric_score": 4.0, "quote": "He said \"hi\""}'
    result = extract_last_json(raw, {"verdict", "quote"})
    assert result["quote"] == 'He said "hi"'


def test_no_matching_object_raises() -> None:
    raw = '{"draft": "x"}\n{"thought": "y"}'
    with pytest.raises(JsonExtractError):
        extract_last_json(raw, {"verdict", "rubric_score"})


def test_empty_input_raises_json() -> None:
    with pytest.raises(JsonExtractError):
        extract_last_json("", {"verdict"})


def test_truncated_unbalanced_json_raises_not_parse_partial() -> None:
    """An unclosed ``{`` shouldn't be returned as partial data — we
    want a fail-loud so the pipeline marks FAILED rather than acting
    on a verdict that might flip sign when the truncation cut."""
    raw = '{"verdict": "approve", "rubric_score": 4.0, "must_fix":'
    with pytest.raises(JsonExtractError):
        extract_last_json(raw, {"verdict", "rubric_score"})


def test_array_only_json_skipped_as_not_a_dict() -> None:
    """We only want dict verdicts. Arrays near the top are skipped."""
    raw = """[1, 2, 3]

{"verdict": "approve", "rubric_score": 4.0}"""
    result = extract_last_json(raw, {"verdict"})
    assert result["verdict"] == "approve"


def test_internal_api_balanced_close_on_unbalanced_returns_negative() -> None:
    # Direct unit test of the internal helper — confidence for the
    # public extract_last_json paths.
    assert extractors._find_balanced_close('{"a": 1', 0) == -1
