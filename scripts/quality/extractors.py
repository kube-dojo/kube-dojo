"""Robust extractors for LLM output — module markdown + JSON verdicts.

Two systematic v1 failure modes:

1. **Module extractor took the wrong thing.** ``codex exec`` prefixed
   reasoning prose before the ``---`` frontmatter, OR wrapped the whole
   module in a ``markdown`` code fence, OR got cut off mid-code-block
   and the v1 naive "first ``---``" scan quietly accepted the truncated
   output. Each of these shipped broken modules to review. (Codex #7)

2. **JSON extractor took the first balanced object.** Codex's verdict
   response often contains a reasoning object FIRST ("thinking") and
   the verdict JSON LAST. v1 grabbed the reasoning blob, mis-parsed it
   as the verdict, and auto-approved modules that weren't actually
   approved. (Codex #8)

Both extractors fail LOUD — they raise rather than return a "best effort"
guess — so the pipeline can mark the state ``FAILED`` with a traceable
reason instead of advancing with garbage.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Iterable


class ExtractorError(ValueError):
    """Base for extractor failures. Callers mark state FAILED with ``str(e)``."""


class ModuleExtractError(ExtractorError):
    """Could not recover a well-formed module from LLM output."""


class JsonExtractError(ExtractorError):
    """Could not find a schema-valid JSON object in LLM output."""


@dataclass(frozen=True)
class ModuleExtract:
    """Result of :func:`extract_module_markdown`.

    Carries enough metadata for the caller to log a useful failure if the
    module is structurally sound but semantically suspect (e.g., frontmatter
    was recovered but no ``title`` survived the code-fence unwrap).
    """

    text: str
    """The extracted module markdown, ending in a trailing newline."""

    unwrapped_code_fence: bool
    """True if the LLM wrapped the module in a ``markdown`` code fence."""

    title: str | None
    """Value of ``title:`` in frontmatter, or ``None`` if absent."""


_FRONTMATTER_DELIM = "---"


def extract_module_markdown(raw: str) -> ModuleExtract:
    """Extract a complete module (frontmatter + body) from messy LLM output.

    Tolerated input shapes (all tested in ``tests/test_quality_extractors.py``):

    * Clean: starts with ``---``, frontmatter, body.
    * Prose-prefixed: reasoning/preamble before the first ``---``.
    * Code-fenced: whole module inside ``` ```markdown ... ``` ``` or
      ``` ``` ... ``` ``` fences.
    * Body-only: no frontmatter at all — rejected (we need title/slug).

    Raises :class:`ModuleExtractError` when:

    * no opening ``---`` found after prose stripping
    * no closing ``---`` for the frontmatter
    * the body ends mid-code-block (odd number of triple backticks in the
      body, indicating LLM output was truncated before completion)
    """
    if not raw or not raw.strip():
        raise ModuleExtractError("extractor received empty input")

    # Step 1: unwrap a surrounding code fence if present. LLMs often do
    # ```markdown\n---\ntitle: ...\n...\n```. We look for a fence that
    # opens near the top and closes near the bottom and is the outermost
    # fence in the output.
    body, unwrapped = _unwrap_outer_fence(raw)

    # Step 2: find the opening ``---`` frontmatter delimiter. Skip any
    # prose or reasoning above it. The delimiter must be on its own line
    # and immediately followed by a line that looks like frontmatter
    # (contains ``:``) — this rejects decorative ``---`` separators that
    # sometimes appear in reasoning prose.
    lines = body.splitlines()
    start = _find_frontmatter_start(lines)
    if start < 0:
        raise ModuleExtractError(
            "no frontmatter delimiter found (expected a line `---` followed by `key: value`)"
        )

    # Step 3: find the CLOSING ``---`` for the frontmatter.
    end = _find_frontmatter_end(lines, start)
    if end < 0:
        raise ModuleExtractError(
            "frontmatter opened but never closed — LLM output likely truncated"
        )

    # Step 4: the body is from the opening ``---`` to the end of input.
    # Validate that the body doesn't end mid-code-block.
    recovered = "\n".join(lines[start:]).strip()
    _assert_code_fences_balanced(recovered)

    title = _extract_title(lines[start + 1 : end])

    if not recovered.endswith("\n"):
        recovered += "\n"

    return ModuleExtract(text=recovered, unwrapped_code_fence=unwrapped, title=title)


def _unwrap_outer_fence(raw: str) -> tuple[str, bool]:
    """Strip a surrounding ``` fence if the module is wholly inside one.

    Heuristic: the first non-empty line after an optional prose prefix is
    ``` or ```<lang>, and a matching ``` exists near the end of input.
    Anything between them is the module. If no such fence structure is
    present, returns the input unchanged.
    """
    lines = raw.splitlines()
    # Find first non-empty line — must be a fence to trigger unwrap.
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines):
        return raw, False
    first = lines[i].strip()
    if not first.startswith("```"):
        return raw, False

    # Find the last ``` in the input — paired with the opener if the
    # interior contains the rest of the module. Naive: last non-empty
    # line that is exactly ``` wins.
    for j in range(len(lines) - 1, i, -1):
        if lines[j].strip() == "```":
            inside = "\n".join(lines[i + 1 : j])
            return inside, True
    return raw, False


def _find_frontmatter_start(lines: list[str]) -> int:
    """Index of the opening ``---`` frontmatter line, or -1 if none."""
    for i, line in enumerate(lines):
        if line.strip() != _FRONTMATTER_DELIM:
            continue
        # Next non-empty line must look like ``key: value`` for this to
        # be real frontmatter, not a decorative separator.
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j < len(lines) and ":" in lines[j]:
            return i
    return -1


def _find_frontmatter_end(lines: list[str], start: int) -> int:
    for i in range(start + 1, len(lines)):
        if lines[i].strip() == _FRONTMATTER_DELIM:
            return i
    return -1


_CODE_FENCE = re.compile(r"^```", re.MULTILINE)


def _assert_code_fences_balanced(body: str) -> None:
    """Raise if the body has an odd number of ``` lines — likely truncated.

    The opening ``---`` frontmatter delimiter counts separately; we only
    scan for triple-backticks in the content body.
    """
    fence_count = len(_CODE_FENCE.findall(body))
    if fence_count % 2 != 0:
        raise ModuleExtractError(
            f"body has {fence_count} triple-backtick lines (odd count) — "
            "code block opened but not closed, LLM output likely truncated"
        )


_TITLE_RE = re.compile(r"^\s*title\s*:\s*(.+?)\s*$")


def _extract_title(frontmatter_lines: Iterable[str]) -> str | None:
    for line in frontmatter_lines:
        m = _TITLE_RE.match(line)
        if m:
            val = m.group(1).strip()
            # Strip surrounding quotes if the LLM quoted the title.
            if (val.startswith('"') and val.endswith('"')) or (
                val.startswith("'") and val.endswith("'")
            ):
                val = val[1:-1]
            return val
    return None


def extract_last_json(raw: str, required_keys: set[str]) -> dict[str, Any]:
    """Return the LAST balanced JSON object in ``raw`` that has every required key.

    This is the Codex-pattern fix: reasoning JSON appears first, verdict
    JSON appears last, and a schema-check on ``required_keys`` rejects
    objects that happen to be balanced but aren't the verdict we want.

    Tolerates:

    * leading prose / reasoning ("Here is my verdict: ...")
    * a fenced JSON block (``` ```json ... ``` ```) — fences are stripped
      before scanning
    * multiple JSON objects in the output — the last one matching the
      required keys wins
    * extra keys beyond ``required_keys`` — caller schema-validates later

    Raises :class:`JsonExtractError` if no matching object is found.
    """
    if not raw or not raw.strip():
        raise JsonExtractError("extractor received empty input")

    # Strip a fenced JSON block if it's the ONLY thing in the output —
    # this is the happy path when Codex follows instructions.
    stripped = raw.strip()
    fenced = _try_parse_single_fenced(stripped, required_keys)
    if fenced is not None:
        return fenced

    # General case: scan for all balanced JSON objects, then take the
    # last one that matches the schema.
    candidates = _iter_balanced_json(raw)
    last_match: dict[str, Any] | None = None
    for obj in candidates:
        if required_keys.issubset(obj.keys()):
            last_match = obj
    if last_match is None:
        raise JsonExtractError(
            f"no JSON object in output had all required keys {sorted(required_keys)!r}"
        )
    return last_match


def _try_parse_single_fenced(text: str, required_keys: set[str]) -> dict[str, Any] | None:
    if not text.startswith("```"):
        return None
    # Drop the opening fence line.
    parts = text.split("\n", 1)
    if len(parts) != 2:
        return None
    inner = parts[1]
    if inner.rstrip().endswith("```"):
        inner = inner.rstrip()[: -len("```")].rstrip()
    try:
        obj = json.loads(inner)
    except json.JSONDecodeError:
        return None
    if isinstance(obj, dict) and required_keys.issubset(obj.keys()):
        return obj
    return None


def _iter_balanced_json(text: str) -> list[dict[str, Any]]:
    """Yield every top-level balanced JSON object in ``text``.

    Scans character-by-character, tracking brace depth but treating
    braces inside JSON strings as literal. This handles nested objects
    (the outer balanced object contains them) and does NOT mistake a
    brace inside a string key/value for a structural brace.

    Non-dict JSON values (arrays, scalars) are skipped — we only care
    about objects because verdicts are always objects.
    """
    results: list[dict[str, Any]] = []
    n = len(text)
    i = 0
    while i < n:
        if text[i] != "{":
            i += 1
            continue
        end = _find_balanced_close(text, i)
        if end < 0:
            break
        try:
            obj = json.loads(text[i : end + 1])
        except json.JSONDecodeError:
            # Not valid JSON starting here — advance past the ``{`` and
            # keep searching; another balanced start may follow.
            i += 1
            continue
        if isinstance(obj, dict):
            results.append(obj)
        i = end + 1
    return results


def _find_balanced_close(text: str, start: int) -> int:
    """Return the index of the ``}`` that closes the ``{`` at ``start``.

    Tracks string literals so a ``}`` inside ``"key": "value}"`` doesn't
    prematurely close the object. Returns -1 if unbalanced (likely
    truncated input).
    """
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if in_string:
            if ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1
