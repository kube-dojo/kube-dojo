"""Regression tests for scripts/quality/check_route_coherence.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


def _load():
    p = Path(__file__).resolve().parent / "check_route_coherence.py"
    spec = importlib.util.spec_from_file_location("check_route_coherence", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # required so @dataclass can resolve the module
    spec.loader.exec_module(mod)
    return mod


rc = _load()


@pytest.mark.parametrize(
    "name,expected",
    [
        ("module-1.2-foo.md", (1, 2)),
        ("module-0.10-bar.md", (0, 10)),
        ("module-2-advanced-merging.md", (2,)),
        ("module-1.1.7-tiny-nn.md", (1, 1, 7)),
        ("index.md", ()),
    ],
)
def test_module_number(name, expected):
    assert rc._module_number(name) == expected


def test_number_ordering_is_numeric_not_lexical():
    # 0.10 must sort AFTER 0.2 (numeric), not before (lexical)
    assert rc._module_number("module-0.10-x.md") > rc._module_number("module-0.2-y.md")


@pytest.mark.parametrize(
    "href,source_slug,expected_first_valid",
    [
        # sibling forward link via Starlight directory model
        ("../module-0.5-editing/", "prerequisites/zero-to-terminal/module-0.4-files",
         "prerequisites/zero-to-terminal/module-0.5-editing"),
        # './' targets the section index (parent dir), NOT the module itself
        ("./", "platform/toolkits/security-quality/security-tools/module-4.7-kyverno",
         "platform/toolkits/security-quality/security-tools"),
        ("../", "a/b/module-1.1", "a/b"),
        # absolute link
        ("/k8s/kcna/part1/module-1.2-foo/", "anywhere/module-9.9-x",
         "k8s/kcna/part1/module-1.2-foo"),
    ],
)
def test_resolve_candidates(href, source_slug, expected_first_valid):
    cands = rc._resolve_candidates(href, source_slug)
    assert expected_first_valid in cands


def test_resolve_dot_prefers_parent_over_self():
    # file-relative (parent) candidate must come before the self candidate
    cands = rc._resolve_candidates("./", "a/b/module-x")
    assert cands.index("a/b") < cands.index("a/b/module-x")


def _next(text: str):
    return rc._extract_next_href(text.splitlines())


def test_extract_next_basic():
    href, _ln = _next("body\n\n## Next Module\n\n**Next Module**: [Module 0.5](../module-0.5-editing/) — go\n")
    assert href == "../module-0.5-editing/"


def test_extract_skips_next_steps_content_section():
    # "## Next Steps" is a further-reading section, not module nav -> no nav link
    href, _ln = _next("## Next Steps\n\n- [Some tool](../module-1.4-devpod/) is worth a look\n")
    assert href is None


def test_extract_skips_related_links():
    text = ("## Next Module\n\n"
            "- **Related**: [Module 12.4: Snyk](/x/module-12.4-snyk/) — alt\n")
    href, _ln = _next(text)
    assert href is None  # only a Related link -> not a forward nav


def test_extract_skips_previous_keeps_next():
    text = ("## Next Module\n\n"
            "[Previous](../module-1.1-a/) | Next: [Module 1.3](../module-1.3-c/)\n")
    href, _ln = _next(text)
    assert href == "../module-1.3-c/"


def test_integration_backward_link_flagged(tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    sec = docs / "trk" / "sec"
    sec.mkdir(parents=True)
    (sec / "index.md").write_text("---\ntitle: Sec\n---\n", encoding="utf-8")
    (sec / "module-1.1-a.md").write_text(
        "---\ntitle: A\n---\n\n## Next Module\n\n**Next**: [B](../module-1.2-b/)\n", encoding="utf-8")
    (sec / "module-1.2-b.md").write_text(
        "---\ntitle: B\n---\n\n## Next Module\n\n**Next**: [A](../module-1.1-a/)\n", encoding="utf-8")  # backward!
    monkeypatch.setattr(rc, "DOCS_DIR", docs)
    findings = rc.run_all()
    rules = {(f.rule, f.path) for f in findings}
    assert ("next-backward", "trk/sec/module-1.2-b.md") in rules
    assert not any(f.rule == "next-backward" and f.path == "trk/sec/module-1.1-a.md" for f in findings)


def test_integration_broken_link_flagged(tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    sec = docs / "trk" / "sec"
    sec.mkdir(parents=True)
    (sec / "index.md").write_text("---\ntitle: Sec\n---\n", encoding="utf-8")
    (sec / "module-1.1-a.md").write_text(
        "---\ntitle: A\n---\n\n## Next Module\n\n**Next**: [Ghost](../module-9.9-ghost/)\n", encoding="utf-8")
    monkeypatch.setattr(rc, "DOCS_DIR", docs)
    findings = rc.run_all()
    assert any(f.rule == "next-broken" and f.path == "trk/sec/module-1.1-a.md" for f in findings)
