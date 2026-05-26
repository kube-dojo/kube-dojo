from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import dispatch_smart  # noqa: E402


@pytest.fixture()
def skill_dirs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path]:
    shared = tmp_path / "agents_extensions" / "shared" / "skills"
    claude = tmp_path / "agents_extensions" / "claude" / "skills"
    monkeypatch.setattr(dispatch_smart, "SHARED_SKILLS_DIR", shared)
    monkeypatch.setattr(dispatch_smart, "CLAUDE_SKILLS_DIR", claude)
    return shared, claude


def _write_skill(parent: Path, name: str, body: str) -> Path:
    path = parent / name / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _run_main(monkeypatch: pytest.MonkeyPatch, args: list[str]) -> int:
    monkeypatch.setattr(sys, "argv", ["dispatch_smart.py", *args])
    try:
        return int(dispatch_smart.main())
    except SystemExit as exc:
        return int(exc.code)


def test_draft_loads_curriculum_writer(skill_dirs: tuple[Path, Path]) -> None:
    shared, _claude = skill_dirs
    skill_path = _write_skill(shared, "curriculum-writer", "writer body")

    skill_name = dispatch_smart._skill_to_load_for_dispatch(
        task_class="draft",
        explicit_skill=None,
        no_skill=False,
    )
    loaded = dispatch_smart._load_skill_body(skill_name)

    assert skill_name == "curriculum-writer"
    assert loaded == ("writer body", skill_path)


def test_review_loads_cross_family_reviewer(skill_dirs: tuple[Path, Path]) -> None:
    shared, _claude = skill_dirs
    skill_path = _write_skill(shared, "cross-family-reviewer", "reviewer body")

    skill_name = dispatch_smart._skill_to_load_for_dispatch(
        task_class="review",
        explicit_skill=None,
        no_skill=False,
    )
    loaded = dispatch_smart._load_skill_body(skill_name)

    assert skill_name == "cross-family-reviewer"
    assert loaded == ("reviewer body", skill_path)


def test_architect_loads_no_skill() -> None:
    skill_name = dispatch_smart._skill_to_load_for_dispatch(
        task_class="architect",
        explicit_skill=None,
        no_skill=False,
    )

    assert skill_name is None


def test_explicit_skill_flag_overrides_mapping(
    skill_dirs: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    shared, _claude = skill_dirs
    _write_skill(shared, "cross-family-reviewer", "reviewer body")
    _write_skill(shared, "k8s-cert-expert", "k8s body")

    code = _run_main(
        monkeypatch,
        ["review", "--dry-run", "--skill", "k8s-cert-expert", "user prompt"],
    )
    captured = capsys.readouterr()

    assert code == 0
    assert "auto-loaded skill: k8s-cert-expert" in captured.err
    assert '<auto-loaded-skill name="k8s-cert-expert">' in captured.out
    assert "k8s body" in captured.out
    assert "reviewer body" not in captured.out


def test_explicit_unknown_skill_exits_2(
    skill_dirs: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = _run_main(
        monkeypatch,
        ["review", "--dry-run", "--skill", "nonexistent", "user prompt"],
    )
    captured = capsys.readouterr()

    assert code == 2
    assert "skill 'nonexistent' not found" in captured.err
    assert "agents_extensions/shared/skills/" in captured.err


def test_auto_mapped_unknown_skill_warns_and_proceeds(
    skill_dirs: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = _run_main(
        monkeypatch,
        ["review", "--dry-run", "user prompt"],
    )
    captured = capsys.readouterr()

    assert code == 0
    assert "auto-mapped skill 'cross-family-reviewer' not found" in captured.err
    assert "<auto-loaded-skill" not in captured.out
    assert "user prompt" in captured.out


def test_default_draft_dry_run_autoloads_curriculum_writer(
    skill_dirs: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    shared, _claude = skill_dirs
    _write_skill(shared, "curriculum-writer", "writer body")

    code = _run_main(
        monkeypatch,
        ["draft", "--dry-run", "user prompt"],
    )
    captured = capsys.readouterr()

    assert code == 0
    assert "auto-loaded skill: curriculum-writer" in captured.err
    assert '<auto-loaded-skill name="curriculum-writer">' in captured.out
    assert "writer body" in captured.out


def test_no_skill_flag_disables_loading(
    skill_dirs: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    shared, _claude = skill_dirs
    _write_skill(shared, "curriculum-writer", "writer body")

    code = _run_main(
        monkeypatch,
        ["draft", "--dry-run", "--no-skill", "user prompt"],
    )
    captured = capsys.readouterr()

    assert code == 0
    assert "auto-loaded skill" not in captured.err
    assert "<auto-loaded-skill" not in captured.out
    assert "writer body" not in captured.out


def test_wrap_format_matches_marker() -> None:
    wrapped = dispatch_smart._wrap_prompt_with_skill(
        "user prompt",
        "skill body",
        "name",
    )

    assert wrapped.startswith('<auto-loaded-skill name="name">\n')
    assert "skill body" in wrapped
    assert wrapped.endswith("user prompt")


def test_shared_overrides_claude_for_same_name(
    skill_dirs: tuple[Path, Path],
) -> None:
    shared, claude = skill_dirs
    shared_path = _write_skill(shared, "foo", "shared body")
    _write_skill(claude, "foo", "claude body")

    assert dispatch_smart._resolve_skill_path("foo") == shared_path
