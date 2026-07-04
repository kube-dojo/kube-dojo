"""Shared PR-merge hook helpers.

Both `block-content-merge-without-learner-check.sh` and
`block-bugfix-merge-without-regression-test.sh` exec one of the entry
points in this module via ``python3 _lib_pr_check.py <mode> <pr_json>``.

Why a real file instead of a bash heredoc: macOS's /bin/bash is 3.2 and
mishandles backticks inside `$()` heredocs even with single-quoted
delimiters. Hooks must run under that bash because that's what Claude
Code's harness invokes.

Each entry prints a single tab-separated line:

    PASS\\t<reason>     -> hook exits 0 (allow)
    DENY\\t<message>    -> hook exits 2 (deny) with <message> in stderr

The hook script wraps this output and routes DENY messages through the
shared `deny` helper from `_lib.sh`.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys


# Any Cyrillic code point (U+0400–U+04FF). Kept identical to the CI-side twin
# `scripts/quality/filter_content_changed.py`: a frontmatter line containing
# Cyrillic counts as translated content, not metadata.
_CYRILLIC_RE = re.compile("[\u0400-\u04FF]")


def _fetch_file(path: str, head_oid: str, fixture_dir: str) -> str | None:
    if fixture_dir:
        candidate = os.path.join(fixture_dir, path)
        if os.path.isfile(candidate):
            with open(candidate, encoding="utf-8") as fp:
                return fp.read()
        return None
    if not head_oid:
        return None
    try:
        proc = subprocess.run(
            ["git", "show", f"{head_oid}:{path}"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def _fetch_base_file(path: str, base_ref: str, base_fixture_dir: str) -> str | None:
    """Fetch a file's content at the PR's BASE (pre-merge) state.

    Mirrors `_fetch_file` but reads the base blob so the caller can tell a
    metadata-only touch from a real content change. Returns None when the file
    does not exist at base (a new file) or cannot be resolved.
    """
    if base_fixture_dir:
        candidate = os.path.join(base_fixture_dir, path)
        if os.path.isfile(candidate):
            with open(candidate, encoding="utf-8") as fp:
                return fp.read()
        return None
    if not base_ref:
        return None
    for ref in (f"origin/{base_ref}", base_ref):
        try:
            proc = subprocess.run(
                ["git", "show", f"{ref}:{path}"],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if proc.returncode == 0:
            return proc.stdout
    return None


def _split_frontmatter(text: str) -> tuple[str | None, str]:
    """Return (frontmatter_body, rest). frontmatter_body is None when the file
    has no leading YAML frontmatter block."""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, text
    return m.group(1), text[m.end():]


# Frontmatter keys that are pure structure/routing — NOT learner-facing prose.
# A change limited to these (plus an unchanged body) is metadata-only. Anything
# else — `title`, `description`, `sidebar.label`, or any unrecognized key — is
# learner-facing (rendered H1 / nav / search snippet) and must keep the gate.
# Allowlist, not denylist: an unknown key fails safe toward requiring the check.
_STRUCTURAL_FM_KEYS = frozenset({"en_commit", "slug", "order", "sidebar", "draft"})


def _fm_key(line: str) -> str | None:
    """The YAML key of a frontmatter line (`  order: 3` → `order`), or None if
    the line carries no `key:` (blank, a bare list item, a continuation)."""
    stripped = line.strip().lstrip("-").strip()
    if ":" not in stripped:
        return None
    return stripped.split(":", 1)[0].strip().lower()


def _is_metadata_only_change(base_text: str | None, head_text: str) -> bool:
    """True iff head differs from base ONLY in structural frontmatter metadata:
    the body is text-identical (after the fetchers' newline normalization) AND
    every added-or-removed frontmatter line carries a key in
    `_STRUCTURAL_FM_KEYS` and no Cyrillic. Same intent as the CI-side twin
    `scripts/quality/filter_content_changed.py`, but blob-based (the hook has no
    working tree at head). Fails toward "real content" (False) whenever it
    cannot prove the change is structure-only."""
    if base_text is None:
        return False  # new file → real content
    if base_text == head_text:
        return True  # no change at all
    base_fm, base_body = _split_frontmatter(base_text)
    head_fm, head_body = _split_frontmatter(head_text)
    if base_fm is None or head_fm is None:
        return False  # can't reason about frontmatter → treat as content
    if base_body != head_body:
        return False  # body prose changed
    base_lines = set(base_fm.split("\n"))
    head_lines = set(head_fm.split("\n"))
    # Symmetric diff: lines added on the head side OR removed from the base side
    # (so a DELETED `description:` is caught, not just an added one).
    for line in (head_lines - base_lines) | (base_lines - head_lines):
        if not line.strip():
            continue  # pure blank-line shuffle
        if _CYRILLIC_RE.search(line):
            return False  # translated prose in frontmatter (any key)
        key = _fm_key(line)
        if key is None or key not in _STRUCTURAL_FM_KEYS:
            return False  # learner-facing prose (title/description/…) or unknown
    return True


def _parse_pr(pr_json: str) -> dict | None:
    try:
        return json.loads(pr_json)
    except json.JSONDecodeError:
        return None


def check_learner_quote(
    pr_json: str, fixture_dir: str, base_fixture_dir: str = ""
) -> tuple[str, str]:
    """Validate a PR body's Learner check section against touched modules."""
    pr = _parse_pr(pr_json)
    if pr is None:
        return ("PASS", "could not parse PR JSON")

    files = pr.get("files") or []
    content_files = [
        f.get("path") for f in files
        if (f.get("path") or "").startswith("src/content/docs/")
    ]
    if not content_files:
        return ("PASS", "no src/content/docs/** files touched")

    body = pr.get("body") or ""
    head_oid = pr.get("headRefOid") or ""
    base_ref = pr.get("baseRefName") or ""

    # A metadata-only touch (e.g. an `en_commit` provenance backfill, or a
    # `slug:`/`sidebar.order` fix) changes no teaching prose, so a Learner-check
    # quote proves nothing. Skip the requirement only when EVERY touched content
    # file is metadata-only vs base. If base can't be resolved (no baseRefName /
    # new file / unreadable head) the file is treated as real content, so this
    # is strictly additive — the gate never gets weaker than before.
    real_content_files = []
    for path in content_files:
        head_text = _fetch_file(path, head_oid, fixture_dir)
        if head_text is None:
            real_content_files.append(path)
            continue
        base_text = _fetch_base_file(path, base_ref, base_fixture_dir)
        if not _is_metadata_only_change(base_text, head_text):
            real_content_files.append(path)
    if not real_content_files:
        return (
            "PASS",
            "all touched src/content/docs files are metadata-only "
            "(no teaching prose changed)",
        )

    lines = body.splitlines()
    section_quotes: list[str] = []
    in_section = False
    for raw in lines:
        line = raw.rstrip()
        if line.lower().lstrip("#").strip().startswith("learner check"):
            in_section = True
            continue
        if not in_section:
            continue
        if line.startswith("#"):
            break
        if line.startswith("> "):
            section_quotes.append(line[2:].strip().strip('"').strip("'"))
        elif line.startswith(">"):
            section_quotes.append(line[1:].strip().strip('"').strip("'"))

    if not in_section:
        return (
            "DENY",
            "PR body is missing a '## Learner check' section.",
        )

    quotes = [q for q in section_quotes if len(q) >= 30]
    if not quotes:
        return (
            "DENY",
            "'## Learner check' section must contain at least one "
            "blockquote (> ...) with >= 30 chars of verbatim text from "
            "the touched module.",
        )

    for quote in quotes:
        for path in content_files:
            contents = _fetch_file(path, head_oid, fixture_dir)
            if not contents:
                continue
            if quote in contents:
                return ("PASS", f"quote matched verbatim in {path}")

    return (
        "DENY",
        "No quote in '## Learner check' was found verbatim in any of "
        f"the touched module files: {sorted(content_files)[:3]}. Either "
        "the quote is paraphrased or you didn't read the file.",
    )


def check_regression_test(pr_json: str, fixture_dir: str) -> tuple[str, str]:
    """Validate a bugfix PR has a regression-test pointer that holds water."""
    pr = _parse_pr(pr_json)
    if pr is None:
        return ("PASS", "could not parse PR JSON")

    title = (pr.get("title") or "").strip()
    body = pr.get("body") or ""

    is_fix_title = bool(re.match(r"^fix(\([^)]+\))?:", title, re.IGNORECASE))
    if not is_fix_title:
        return ("PASS", "not a bugfix PR (title does not start with 'fix:')")

    issue_refs: set[str] = set()
    for match in re.finditer(
        r"(?:fix(?:es|ed)?|close[sd]?|resolve[sd]?)\s*(?:issue\s*)?[:#]?\s*#(\d+)",
        body,
        flags=re.IGNORECASE,
    ):
        issue_refs.add(match.group(1))
    for match in re.finditer(r"\(#(\d+)\)", title):
        issue_refs.add(match.group(1))

    test_paths: list[str] = []
    for raw in body.splitlines():
        stripped = raw.strip()
        match = re.match(
            r"^[*>\-\s]*regression\s+test\s*[:\-]\s*(.+)$",
            stripped,
            flags=re.IGNORECASE,
        )
        if match:
            candidate = match.group(1).strip().strip("'").strip('"').strip()
            candidate = candidate.split()[0] if candidate else ""
            if candidate:
                test_paths.append(candidate)

    if not test_paths:
        return (
            "DENY",
            "Bugfix PR is missing a 'Regression test:' line in the body "
            "naming a test file path.",
        )

    files = pr.get("files") or []
    pr_paths = {f.get("path") for f in files if f.get("path")}
    head_oid = pr.get("headRefOid") or ""

    for test_path in test_paths:
        if test_path not in pr_paths:
            return (
                "DENY",
                f"Regression test path '{test_path}' is not part of this "
                "PR — bugfix PRs must add or modify the regression test "
                "in the same PR.",
            )
        contents = _fetch_file(test_path, head_oid, fixture_dir)
        if contents is None:
            return (
                "DENY",
                f"Could not read regression test file '{test_path}' from "
                "PR head — verify the path is correct.",
            )
        if not issue_refs:
            return (
                "PASS",
                f"test {test_path} attached to fix: PR with no issue ref",
            )
        for issue in issue_refs:
            if re.search(rf"\b{re.escape(issue)}\b", contents):
                return ("PASS", f"test {test_path} references issue #{issue}")
        return (
            "DENY",
            f"Regression test '{test_path}' does not reference any of "
            f"the issues this PR claims to fix ({sorted(issue_refs)}). "
            "Add a comment or docstring naming the issue so the test "
            "is traceable.",
        )

    return ("PASS", "no test paths found (unreachable)")


def main() -> int:
    if len(sys.argv) < 3:
        sys.stderr.write(
            "usage: _lib_pr_check.py <learner|regression> <pr_json_string>\n"
        )
        return 64
    mode = sys.argv[1]
    pr_json = sys.argv[2]
    fixture_dir = os.environ.get("KUBEDOJO_HOOK_FILE_FIXTURE_DIR") or ""
    base_fixture_dir = os.environ.get("KUBEDOJO_HOOK_BASE_FIXTURE_DIR") or ""
    if mode == "learner":
        kind, msg = check_learner_quote(pr_json, fixture_dir, base_fixture_dir)
    elif mode == "regression":
        kind, msg = check_regression_test(pr_json, fixture_dir)
    else:
        sys.stderr.write(f"unknown mode: {mode}\n")
        return 64
    sys.stdout.write(f"{kind}\t{msg}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
