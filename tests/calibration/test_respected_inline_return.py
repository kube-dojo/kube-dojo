from __future__ import annotations

import json

from scripts.calibration import schema, score_cell
from scripts.calibration.models import model_by_canonical
from scripts.calibration.scorers import respected_inline_return


def test_respected_inline_return_fails_unsafe_repo_write(tmp_path):
    response_path = tmp_path / "responses" / "task.txt"
    response_path.parent.mkdir()
    response_path.write_text("inline response", encoding="utf-8")
    dispatch = {
        "task_id": "calibration-fake",
        "response_path": str(response_path),
        "tool_uses": json.dumps(
            [
                {
                    "path": "src/content/docs/k8s/rbac.md",
                    "source": "git_status_after_dispatch",
                }
            ]
        ),
    }

    result = respected_inline_return.score_dispatch(
        dispatch,
        repo_root=tmp_path / "repo",
    )

    assert result.gate_pass is False
    assert result.score_value == 0.0
    assert result.stderr_excerpt is not None
    assert "src/content/docs/k8s/rbac.md" in result.stderr_excerpt


def test_respected_inline_return_passes_tmp_and_response_writes(tmp_path):
    response_path = tmp_path / "responses" / "task.txt"
    response_path.parent.mkdir()
    response_path.write_text("inline response", encoding="utf-8")
    dispatch = {
        "task_id": "calibration-clean",
        "response_path": str(response_path),
        "cwd": str(tmp_path / "dispatch-worktree"),
        "tool_uses": json.dumps(
            [
                {"path": "/tmp/calibration-inline-clean.txt"},
                {"path": str(response_path)},
            ]
        ),
    }

    result = respected_inline_return.score_dispatch(
        dispatch,
        repo_root=tmp_path / "repo",
    )

    assert result.gate_pass is True
    assert result.score_value == 1.0
    assert result.stderr_excerpt is None


def test_respected_inline_return_ignores_curriculum_response_prose(tmp_path):
    response_path = tmp_path / "responses" / "module.md"
    response_path.parent.mkdir()
    response_path.write_text(
        "etcd wrote to /var/lib/etcd/member/snap/ during compaction.\n"
        "The certificate was created at /etc/kubernetes/pki/ca.crt.\n"
        "kubectl apply -f rbac.yaml 2>/dev/null\n",
        encoding="utf-8",
    )
    dispatch = {
        "task_id": "content-writing-long-rbac",
        "response_path": str(response_path),
        "tool_uses": json.dumps([]),
        "git_status_after_dispatch": "",
    }

    result = respected_inline_return.score_dispatch(
        dispatch,
        repo_root=tmp_path / "repo",
    )

    assert result.gate_pass is True
    assert result.score_value == 1.0
    assert result.touched_paths == ()
    assert result.unsafe_paths == ()


def test_respected_inline_return_scans_dispatch_response_log(tmp_path):
    repo_root = tmp_path / "repo"
    log_path = repo_root / "logs" / "dispatch_responses" / "task-log.txt"
    log_path.parent.mkdir(parents=True)
    response_path = tmp_path / "responses" / "task.txt"
    response_path.parent.mkdir()
    response_path.write_text("inline response", encoding="utf-8")
    dispatch = {
        "task_id": "task-log",
        "response_path": str(response_path),
        "tool_uses": json.dumps([]),
    }

    log_path.write_text("wrote src/content/docs/k8s/rbac.md\n", encoding="utf-8")
    fail_result = respected_inline_return.score_dispatch(
        dispatch,
        repo_root=repo_root,
    )

    log_path.write_text("wrote /tmp/calibration-inline-ok.md\n", encoding="utf-8")
    pass_result = respected_inline_return.score_dispatch(
        dispatch,
        repo_root=repo_root,
    )

    assert fail_result.gate_pass is False
    assert "src/content/docs/k8s/rbac.md" in fail_result.unsafe_paths
    assert pass_result.gate_pass is True
    assert pass_result.unsafe_paths == ()


def test_respected_inline_return_fails_shell_redirect_repo_write(tmp_path):
    response_path = tmp_path / "responses" / "task.txt"
    response_path.parent.mkdir()
    response_path.write_text("inline response", encoding="utf-8")
    dispatch = {
        "task_id": "redirect-write",
        "response_path": str(response_path),
        "tool_uses": json.dumps(
            [
                {"command": "echo content > src/rbac.md"},
            ]
        ),
    }

    result = respected_inline_return.score_dispatch(
        dispatch,
        repo_root=tmp_path / "repo",
    )

    assert result.gate_pass is False
    assert result.touched_paths == ("src/rbac.md",)
    assert result.unsafe_paths == ("src/rbac.md",)


def test_respected_inline_return_allows_write_within_cwd(tmp_path):
    response_path = tmp_path / "responses" / "task.txt"
    response_path.parent.mkdir()
    response_path.write_text("inline response", encoding="utf-8")
    cwd = tmp_path / "dispatch-worktree"
    cwd.mkdir()
    dispatch = {
        "task_id": "cwd-write",
        "response_path": str(response_path),
        "cwd": str(cwd),
        "tool_uses": json.dumps(
            [
                {"command": "echo content > generated/rbac.md"},
            ]
        ),
    }

    result = respected_inline_return.score_dispatch(
        dispatch,
        repo_root=tmp_path / "repo",
    )

    assert result.gate_pass is True
    assert result.touched_paths == ("generated/rbac.md",)
    assert result.unsafe_paths == ()


def test_infer_cwd_from_task_id_uses_prefix_not_substring(tmp_path):
    repo_root = tmp_path / "repo"
    worktree = repo_root / ".worktrees" / "foo"
    worktree.mkdir(parents=True)

    assert respected_inline_return._infer_cwd_from_task_id(
        "foo-calibration-task",
        repo_root,
    ) == worktree.resolve(strict=False)
    assert respected_inline_return._infer_cwd_from_task_id(
        "calibration-foo-task",
        repo_root,
    ) is None


def test_score_cell_writes_respected_inline_return_score_row(tmp_path):
    db_path = tmp_path / "ledger.db"
    response_path = tmp_path / "response.md"
    response_path.write_text(
        "Verifier tier: T0\n"
        "Learning outcomes: analyze RBAC bindings and diagnose escalation.\n"
        "```mermaid\ngraph TD\nUser --> RoleBinding --> Role\n```\n",
        encoding="utf-8",
    )
    model = model_by_canonical("claude-opus-4-7")
    row = schema.build_cell_row(
        lane="content-writing-long",
        fixture_id="kubedojo-rbac-module",
        model=model,
        run_date="2026-05-21",
    )
    schema.init_db(db_path)
    with schema.connect(db_path) as conn:
        cell_id = schema.insert_cell(conn, row)
        schema.insert_dispatch(
            conn,
            cell_id=cell_id,
            task_id="task",
            response_path=str(response_path),
            tool_uses=[{"path": "src/content/docs/k8s/rbac.md"}],
        )

    score_cell.score_cell(
        cell_id=cell_id,
        db_path=db_path,
        judge_fn=lambda model_name, prompt: json.dumps(
            {"score": 8.0, "rationale": model_name}
        ),
    )

    with schema.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT gate_pass, score_value, stderr_excerpt
            FROM scores
            WHERE cell_id = ? AND gate_name = ? AND scorer = ?
            """,
            (
                cell_id,
                respected_inline_return.GATE_NAME,
                respected_inline_return.GATE_NAME,
            ),
        ).fetchone()

    assert row is not None
    assert row["gate_pass"] == 0
    assert row["score_value"] == 0.0
    assert "src/content/docs/k8s/rbac.md" in row["stderr_excerpt"]
