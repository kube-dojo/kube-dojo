"""Regression tests for scripts/quality/filter_content_changed.py.

Guards the UK-quality-gate collision surfaced by the #2237 en_commit provenance
backfill: a metadata-only frontmatter touch must not re-scan an untouched
translation (fixed in PR #2238), while real content changes must still be gated.

Drives a throwaway git repo so the git-diff plumbing is exercised end-to-end.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest


def _load():
    p = Path(__file__).resolve().parent / "filter_content_changed.py"
    spec = importlib.util.spec_from_file_location("filter_content_changed", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


fc = _load()

BASE = """---
title: "Модуль 7.1: Архітектура AKS"
slug: uk/cloud/aks-deep-dive/module-7.1
sidebar:
  order: 2
---
**Складність**: [MEDIUM]

Це тіло містить пре-існуючий русизм самий тут, який гейт має ігнорувати
доки його рядок не змінюється у цьому PR.
"""


def _git(args: list[str], cwd: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


@pytest.fixture
def repo(tmp_path: Path, monkeypatch):
    """A repo with one committed UK file. Yields (base_sha, file_path)."""
    _git(["init", "-q", "-b", "main"], tmp_path)
    _git(["config", "user.email", "t@example.com"], tmp_path)
    _git(["config", "user.name", "Test"], tmp_path)
    d = tmp_path / "src" / "content" / "docs" / "uk" / "cloud" / "aks-deep-dive"
    d.mkdir(parents=True)
    f = d / "module-7.1.md"
    f.write_text(BASE, encoding="utf-8")
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-qm", "base"], tmp_path)
    base_sha = _git(["rev-parse", "HEAD"], tmp_path).strip()
    monkeypatch.chdir(tmp_path)
    return base_sha, f


def _commit(tmp_path: Path, msg: str) -> None:
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-qm", msg], tmp_path)


# --- pure-function: frontmatter boundary -------------------------------------


def test_frontmatter_end_line():
    # closing `---` is the 6th line of BASE
    assert fc.frontmatter_end_line(BASE) == 6


def test_frontmatter_end_line_no_frontmatter():
    assert fc.frontmatter_end_line("no frontmatter here\njust body\n") == 0


# --- metadata-only additions are dropped -------------------------------------


def test_ascii_frontmatter_addition_is_metadata_only(repo, tmp_path):
    base_sha, f = repo
    text = f.read_text(encoding="utf-8")
    # insert an en_commit provenance line just before the closing fence
    text = text.replace(
        "  order: 2\n---",
        "  order: 2\nen_commit: a4a4935b266ce46eefb0682ff97beb7279f2f869\n---",
    )
    f.write_text(text, encoding="utf-8")
    _commit(tmp_path, "backfill en_commit")
    assert fc.is_metadata_only(base_sha, f) is True


def test_main_drops_metadata_only(repo, tmp_path, capsys):
    base_sha, f = repo
    text = f.read_text(encoding="utf-8").replace(
        "  order: 2\n---", "  order: 2\nen_commit: deadbeef\n---"
    )
    f.write_text(text, encoding="utf-8")
    _commit(tmp_path, "backfill")
    rc = fc.main(["--base-ref", base_sha, str(f)])
    assert rc == 0
    assert capsys.readouterr().out.strip() == ""  # dropped → nothing to scan


# --- real content changes are kept -------------------------------------------


def test_body_change_is_kept(repo, tmp_path, capsys):
    base_sha, f = repo
    f.write_text(f.read_text(encoding="utf-8") + "\nНовий рядок тіла.\n", encoding="utf-8")
    _commit(tmp_path, "body edit")
    assert fc.is_metadata_only(base_sha, f) is False
    rc = fc.main(["--base-ref", base_sha, str(f)])
    assert rc == 0
    assert capsys.readouterr().out.strip() == str(f)  # kept


def test_cyrillic_frontmatter_edit_is_kept(repo, tmp_path):
    """Editing translated frontmatter prose (title) must NOT be skipped."""
    base_sha, f = repo
    text = f.read_text(encoding="utf-8").replace(
        'title: "Модуль 7.1: Архітектура AKS"',
        'title: "Модуль 7.1: Архітектура та мережі AKS"',
    )
    f.write_text(text, encoding="utf-8")
    _commit(tmp_path, "retitle")
    assert fc.is_metadata_only(base_sha, f) is False


def test_new_file_is_kept(repo, tmp_path, capsys):
    base_sha, _ = repo
    new = tmp_path / "src" / "content" / "docs" / "uk" / "cloud" / "new.md"
    new.write_text(BASE, encoding="utf-8")
    _commit(tmp_path, "new translation")
    assert fc.is_metadata_only(base_sha, new) is False
    rc = fc.main(["--base-ref", base_sha, str(new)])
    assert rc == 0
    assert capsys.readouterr().out.strip() == str(new)


# --- bypass regressions (codex R1 findings) ----------------------------------


def test_plus_prefixed_body_line_is_kept(repo, tmp_path):
    """A body addition whose content starts with `++` shows as `+++…` in the
    diff and must NOT be mistaken for a file header and skipped (bypass)."""
    base_sha, f = repo
    f.write_text(
        f.read_text(encoding="utf-8") + "\n++ самий ы тест\n", encoding="utf-8"
    )
    _commit(tmp_path, "body line starting with ++")
    added = fc.added_new_side_lines(base_sha, f)
    assert any("++ самий" in text for _, text in (added or [])), added
    assert fc.is_metadata_only(base_sha, f) is False


def test_pure_deletion_is_kept(repo, tmp_path):
    """A body-only deletion (no added lines) can create a structural FAIL
    (e.g. adjacent `##` headings); fail toward scan, not skip."""
    base_sha, f = repo
    lines = f.read_text(encoding="utf-8").splitlines(keepends=True)
    # drop the last body line (a deletion, zero additions)
    f.write_text("".join(lines[:-1]), encoding="utf-8")
    _commit(tmp_path, "delete a body line")
    assert fc.added_new_side_lines(base_sha, f) == []
    assert fc.is_metadata_only(base_sha, f) is False


# --- fail-safe: no base ref → emit everything unchanged ----------------------


def test_no_base_ref_emits_all(repo, capsys):
    _, f = repo
    rc = fc.main([str(f)])
    assert rc == 0
    assert capsys.readouterr().out.strip() == str(f)
