from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


REPO_ROOT = Path(__file__).resolve().parents[2]
local_api = _load_module("local_api_quality_stub_regression", REPO_ROOT / "scripts" / "local_api.py")
sampler = _load_module(
    "sample_back_catalog_review_under_test",
    REPO_ROOT / "scripts" / "quality" / "sample_back_catalog_review.py",
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _strong_module(title: str) -> str:
    lines = [
        "---",
        f'title: "{title}"',
        "sidebar:",
        "  order: 1",
        "---",
        "",
        "## Overview",
        "",
    ]
    lines.extend(f"Detailed teaching line {index}." for index in range(500))
    lines.extend(
        [
            "",
            "```mermaid",
            "graph TD",
            "A-->B",
            "```",
            "",
            "## Quiz",
            "",
            "- What matters?",
            "",
            "## Hands-On",
            "",
            "1. Inspect the design.",
            "",
            "## Sources",
            "",
            "- [Docs](https://example.com/docs)",
        ]
    )
    return "\n".join(lines) + "\n"


def _redirect_stub(title: str) -> str:
    return "\n".join(
        [
            "---",
            f'title: "{title}"',
            "sidebar:",
            "  order: 1",
            "---",
            "",
            "This module has moved. See [the new module](/ai/new-home/module-2.1-harness-engineering/).",
            "",
        ]
    )


def _clear_caches() -> None:
    with local_api._QUALITY_AUDIT_CACHE_LOCK:
        local_api._QUALITY_AUDIT_CACHE.clear()


def _mock_gh_issue_list(monkeypatch: Any, issues: list[dict[str, Any]]) -> None:
    monkeypatch.setattr(sampler.shutil, "which", lambda command: "gh" if command == "gh" else None)

    def fake_run(command: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        assert command[:4] == ["gh", "issue", "list", "--state"]
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps(issues), stderr="")

    monkeypatch.setattr(sampler.subprocess, "run", fake_run)


def test_redirect_stub_excluded(tmp_path: Path) -> None:
    real_path = "cloud/aws/module-1.1-real-module.md"
    stub_path = "ai/ai-native-work/module-2.1-harness-engineering.md"
    _write(tmp_path / "src" / "content" / "docs" / real_path, _strong_module("Real Module"))
    _write(tmp_path / "src" / "content" / "docs" / stub_path, _redirect_stub("Harness Engineering"))
    _clear_caches()

    scores = local_api.build_quality_scores(tmp_path)
    scored_paths = {module["path"] for module in scores["modules"]}

    assert real_path in scored_paths
    assert stub_path not in scored_paths
    assert scores["count"] == 1

    board = local_api.build_quality_board(tmp_path)
    board_paths = {module["path"] for module in board["modules"]}
    assert real_path in board_paths
    assert stub_path not in board_paths
    assert board["totals"]["total"] == 1


def test_upgrade_plan_has_generated_at(tmp_path: Path) -> None:
    before = int(time.time()) - 5
    plan = local_api.build_quality_upgrade_plan(tmp_path)
    after = int(time.time()) + 5

    assert isinstance(plan["generated_at"], int)
    assert before <= plan["generated_at"] <= after


def test_sample_back_catalog_stratification() -> None:
    eligible = [
        {"track": track, "path": f"{track}/module-{index}.md"}
        for track, size in {
            "prerequisites": 10,
            "linux": 2,
            "cloud": 5,
            "k8s": 8,
            "platform": 20,
        }.items()
        for index in range(size)
    ]

    sampled = sampler.stratified_sample(eligible, sample_size=15, seed=2026)
    counts = {track: len(modules) for track, modules in sampled.items()}

    assert sum(counts.values()) == 15
    assert counts["linux"] == 2
    assert counts["prerequisites"] >= 3
    assert counts["cloud"] >= 3
    assert counts["k8s"] >= 3
    assert counts["platform"] >= 3
    assert counts == {track: len(modules) for track, modules in sampler.stratified_sample(eligible, sample_size=15, seed=2026).items()}


def test_gh_issue_check_ignores_meta_epic(monkeypatch: Any, tmp_path: Path) -> None:
    _mock_gh_issue_list(monkeypatch, [{"number": 1504, "title": "epic: review all starter modules"}])
    checker = sampler.GhIssueChecker(tmp_path, ignore_issue_numbers=frozenset({1504}))

    assert checker.open_issues_for_slug("prerequisites-cloud-native-101-module-1.1-what-are-containers") == []


def test_gh_issue_check_requires_slug_in_title(monkeypatch: Any, tmp_path: Path) -> None:
    _mock_gh_issue_list(
        monkeypatch,
        [{"number": 999, "title": "some unrelated issue mentioning prerequisites in body"}],
    )
    checker = sampler.GhIssueChecker(tmp_path)

    assert checker.open_issues_for_slug("prerequisites-cloud-native-101-module-1.1-what-are-containers") == []


def test_gh_issue_check_accepts_exact_title_match(monkeypatch: Any, tmp_path: Path) -> None:
    issue = {
        "number": 999,
        "title": "bug in prerequisites-cloud-native-101-module-1.1-what-are-containers",
    }
    _mock_gh_issue_list(monkeypatch, [issue])
    checker = sampler.GhIssueChecker(tmp_path)

    assert checker.open_issues_for_slug("prerequisites-cloud-native-101-module-1.1-what-are-containers") == [issue]


def test_eligible_pool_no_age_filter_by_default(monkeypatch: Any, tmp_path: Path) -> None:
    rel_path = "cloud/aws/module-1.1-new-module.md"
    _write(tmp_path / "src" / "content" / "docs" / rel_path, _strong_module("New Module"))

    monkeypatch.setattr(
        sampler.local_api,
        "build_quality_scores",
        lambda repo_root: {"modules": [{"path": rel_path, "score": 4.5, "lines": 520}]},
    )
    monkeypatch.setattr(
        sampler,
        "_git_first_commit_timestamp_on_main",
        lambda repo_root, module_path: int(time.time()) - (10 * 86400),
    )

    class FakeIssueChecker:
        def __init__(
            self,
            repo_root: Path,
            *,
            ignore_issue_numbers: frozenset[int] = frozenset(),
        ) -> None:
            self.repo_root = repo_root
            self.ignore_issue_numbers = ignore_issue_numbers

        def open_issues_for_slug(self, slug: str) -> list[dict[str, Any]]:
            return []

    monkeypatch.setattr(sampler, "GhIssueChecker", FakeIssueChecker)

    eligible = sampler.build_eligible_pool(tmp_path)

    assert [module["path"] for module in eligible] == [rel_path]
    assert eligible[0]["age_days"] == 10
