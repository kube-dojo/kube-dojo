from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import citation_residuals  # noqa: E402


def _point_at_tmp_repo(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(citation_residuals, "REPO_ROOT", tmp_path)

    def fake_module_path_from_key(module_key: str) -> Path:
        return tmp_path / "src" / "content" / "docs" / f"{module_key}.md"

    monkeypatch.setattr(citation_residuals, "module_path_from_key", fake_module_path_from_key)


def _write_module(tmp_path: Path, module_key: str, text: str) -> Path:
    module_path = tmp_path / "src" / "content" / "docs" / f"{module_key}.md"
    module_path.parent.mkdir(parents=True, exist_ok=True)
    module_path.write_text(text, encoding="utf-8")
    return module_path


def _write_queue(tmp_path: Path, module_key: str, queued: dict[str, list[dict[str, Any]]]) -> Path:
    queue_dir = tmp_path / ".pipeline" / "v3" / "human-review"
    queue_dir.mkdir(parents=True, exist_ok=True)
    queue_path = queue_dir / f"{module_key.replace('/', '-')}.json"
    queue_path.write_text(
        json.dumps(
            {
                "module_key": module_key,
                "queued_findings": {
                    "needs_citation": [],
                    "overstated_unfixed": queued.get("overstated_unfixed", []),
                    "off_topic_unfixed": queued.get("off_topic_unfixed", []),
                    "overstatement_queued": queued.get("overstatement_queued", []),
                    "off_topic_delete_queued": queued.get("off_topic_delete_queued", []),
                },
                "resolved_findings": [],
                "unresolvable_findings": [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return queue_path


def test_apply_queued_applies_overstatement_swap_and_offtopic_delete(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _point_at_tmp_repo(tmp_path, monkeypatch)
    module_key = "ai/demo/module-1"
    module_path = _write_module(
        tmp_path,
        module_key,
        "# Demo\n\nThis setup always prevents outages.\n\n"
        "This paragraph wanders into unrelated travel planning and should go away.\n\n"
        "The module continues here.\n",
    )
    queue_path = _write_queue(
        tmp_path,
        module_key,
        {
            "overstatement_queued": [
                {
                    "line": 3,
                    "trigger": "always",
                    "sentence": "This setup always prevents outages.",
                    "suggested_rewrite": "This setup can reduce outage risk.",
                }
            ],
            "off_topic_delete_queued": [
                {
                    "section": "Demo",
                    "excerpt": "This paragraph wanders into unrelated travel planning",
                    "suggested_action": "delete paragraph",
                }
            ],
        },
    )

    stats = citation_residuals.resolve_phase2_module(queue_path, apply_queued=True)

    assert stats["considered"] == 2
    assert stats["resolved"] == 2
    updated = module_path.read_text(encoding="utf-8")
    assert "This setup can reduce outage risk." in updated
    assert "always prevents outages" not in updated
    assert "travel planning" not in updated
    data = json.loads(queue_path.read_text(encoding="utf-8"))
    assert data["queued_findings"]["overstatement_queued"] == []
    assert data["queued_findings"]["off_topic_delete_queued"] == []
    assert {item["action"] for item in data["resolved_findings"]} == {
        "softened",
        "deleted",
    }


def test_fix_overstatements_calls_codex_prompt_and_applies_rewrite(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _point_at_tmp_repo(tmp_path, monkeypatch)
    module_key = "ai/demo/module-2"
    module_path = _write_module(
        tmp_path,
        module_key,
        "# Demo\n\nThe controller never misses a failed pod.\n",
    )
    queue_path = _write_queue(
        tmp_path,
        module_key,
        {
            "overstated_unfixed": [
                {
                    "line": 3,
                    "trigger": "never",
                    "sentence": "The controller never misses a failed pod.",
                }
            ]
        },
    )
    prompts: list[str] = []

    def fake_dispatch(prompt: str) -> tuple[bool, str]:
        prompts.append(prompt)
        return True, json.dumps(
            {"suggested_rewrite": "The controller is designed to detect failed pods."}
        )

    stats = citation_residuals.resolve_phase2_module(
        queue_path,
        fix_overstatements=True,
        dispatcher=fake_dispatch,
    )

    assert stats["resolved"] == 1
    assert "overstated" in prompts[0]
    assert "never misses" in prompts[0]
    assert "designed to detect failed pods" in module_path.read_text(encoding="utf-8")
    data = json.loads(queue_path.read_text(encoding="utf-8"))
    assert data["queued_findings"]["overstated_unfixed"] == []


def test_fix_offtopic_calls_codex_prompt_and_deletes_paragraph(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _point_at_tmp_repo(tmp_path, monkeypatch)
    module_key = "ai/demo/module-3"
    module_path = _write_module(
        tmp_path,
        module_key,
        "# Demo\n\nKeep this platform engineering paragraph.\n\n"
        "This paragraph discusses weekend meal planning instead of Kubernetes.\n\n"
        "Keep this closing paragraph.\n",
    )
    queue_path = _write_queue(
        tmp_path,
        module_key,
        {
            "off_topic_unfixed": [
                {
                    "section": "Demo",
                    "excerpt": "This paragraph discusses weekend meal planning",
                    "reason": "unrelated filler",
                    "suggested_action": "delete",
                }
            ]
        },
    )
    prompts: list[str] = []

    def fake_dispatch(prompt: str) -> tuple[bool, str]:
        prompts.append(prompt)
        return True, json.dumps({"action": "delete", "reason": "unrelated"})

    stats = citation_residuals.resolve_phase2_module(
        queue_path,
        fix_offtopic=True,
        dispatcher=fake_dispatch,
    )

    assert stats["resolved"] == 1
    assert "off-topic" in prompts[0]
    assert "meal planning" in prompts[0]
    updated = module_path.read_text(encoding="utf-8")
    assert "meal planning" not in updated
    assert "Keep this closing paragraph." in updated


def test_sample_prints_diff_without_modifying_source_or_queue(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    _point_at_tmp_repo(tmp_path, monkeypatch)
    module_key = "ai/demo/module-4"
    module_path = _write_module(
        tmp_path,
        module_key,
        "# Demo\n\nThis deployment always heals itself.\n",
    )
    queue_path = _write_queue(
        tmp_path,
        module_key,
        {
            "overstatement_queued": [
                {
                    "line": 3,
                    "trigger": "always",
                    "sentence": "This deployment always heals itself.",
                    "suggested_rewrite": "This deployment can often heal itself.",
                }
            ]
        },
    )
    before_source = module_path.read_text(encoding="utf-8")
    before_queue = queue_path.read_text(encoding="utf-8")

    rc = citation_residuals.run_sample(
        [queue_path],
        [citation_residuals.BUCKET_OVERSTATEMENT_QUEUED],
        1,
    )

    assert rc == 0
    out = capsys.readouterr().out
    assert "--- ai/demo/module-4.before" in out
    assert "+++ ai/demo/module-4.after" in out
    assert "-This deployment always heals itself." in out
    assert "+This deployment can often heal itself." in out
    assert module_path.read_text(encoding="utf-8") == before_source
    assert queue_path.read_text(encoding="utf-8") == before_queue
