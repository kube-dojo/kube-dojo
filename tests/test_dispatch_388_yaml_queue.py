"""Tests for per-module budget support in dispatch_388_pilot queue parsing."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.quality import dispatch_388_pilot as pilot


def test_yaml_queue_dispatch_writes_budget_sidecar_and_defaults_to_5000(tmp_path, monkeypatch) -> None:
    queue = tmp_path / "pilot.yaml"
    queue.write_text(
        """queue:
  - path: src/content/docs/ai/module-a.md
    budget: 3000
  - path: src/content/docs/cloud/module-b.md
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(pilot, "REPO", tmp_path)
    monkeypatch.setattr(pilot, "PRIMARY_REPO", tmp_path)
    monkeypatch.setattr(pilot, "PILOT_FILE", tmp_path / "scripts/quality/pilot-2026-05-02.txt")
    log = tmp_path / "dispatch.log"
    monkeypatch.setattr(pilot, "LOG", log)

    codex_result = MagicMock(ok=True, response="Opened PR: https://github.com/org/repo/pull/1")
    with patch.object(pilot, "dispatch_codex", return_value=codex_result) as mock_codex, \
         patch.object(pilot, "dispatch_agy_review", return_value=("VERDICT: APPROVE", "APPROVE")), \
         patch.object(pilot, "merge_pr", return_value="abc123"), \
         patch.object(pilot, "dispatch_backfill", return_value=True), \
         patch.object(pilot, "make_worktree", return_value=tmp_path), \
         patch.object(pilot, "post_review_comment"), \
         patch.object(pilot.time, "sleep"), \
         patch.object(pilot, "log") as mock_log:
        rc = pilot.main(["--input", str(queue), "--log", str(log)])

    assert rc == 0
    budget_path = tmp_path / ".pipeline" / "budgets" / "ai__module-a.md.json"
    sidecars = list((tmp_path / ".pipeline" / "budgets").glob("*.json"))
    assert rc == 0
    assert len(sidecars) == 1
    data = json.loads(budget_path.read_text(encoding="utf-8"))
    assert data["body_words_min"] == 3000
    assert data["source_module"] == "src/content/docs/ai/module-a.md"
    assert any(
        call.args[0]["event"] == "budget_sidecar_written"
        for call in mock_log.call_args_list
    )
    assert mock_codex.call_args_list[0].args[3] == 3000
    assert mock_codex.call_args_list[1].args[3] == 5000
