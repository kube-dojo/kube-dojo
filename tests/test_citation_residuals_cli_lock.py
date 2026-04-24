"""CLI-level tests for citation_residuals resolve + per-module lock.

These tests shim `resolve_module` so the test does not need network,
LLMs, or real module files. Focus is on the lock orchestration layer in
`main()`: acquire before each module, complete on success, release on
crash, and the --no-lock / --dry-run escape hatches.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import citation_residuals  # noqa: E402
from pipeline_common import module_lock  # noqa: E402


@pytest.fixture
def tmp_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    p = tmp_path / ".pipeline" / "v2.db"
    monkeypatch.setattr(module_lock, "DEFAULT_DB_PATH", p)
    monkeypatch.setattr(module_lock, "_INITIALIZED_DBS", set())
    return p


@pytest.fixture
def tmp_queue(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Two fake queue files with one needs_citation each, pointed at by
    HUMAN_REVIEW_DIR so main() discovers them naturally."""
    review_dir = tmp_path / "human-review"
    review_dir.mkdir(parents=True)
    for key in ("mod-alpha", "mod-beta"):
        (review_dir / f"{key}.json").write_text(
            json.dumps(
                {
                    "module_key": key,
                    "queued_findings": {
                        "needs_citation": [{"line": 1, "signals": ["year_reference"]}]
                    },
                    "resolved_findings": [],
                    "unresolvable_findings": [],
                },
                indent=2,
            )
            + "\n"
        )
    monkeypatch.setattr(citation_residuals, "HUMAN_REVIEW_DIR", review_dir)
    return review_dir


def _fake_resolve(qp: Path, *, dry_run: bool = False, **_: object) -> dict:
    """A no-op resolver that only reports considered=1 resolved=1."""
    return {
        "module_key": qp.stem,
        "considered": 1,
        "resolved": 1,
        "unresolvable": 0,
        "skipped_already_resolved": 0,
        "module_edited": True,
    }


def test_main_acquires_and_completes_per_module(
    tmp_db: Path,
    tmp_queue: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    monkeypatch.setattr(citation_residuals, "resolve_module", _fake_resolve)
    rc = citation_residuals.main(["resolve", "--all"])
    assert rc == 0
    # Both modules processed successfully.
    out = capsys.readouterr().out
    assert "mod-alpha" in out
    assert "mod-beta" in out
    assert "skipped_locked=0" in out
    # Heartbeat: start → resolving → summary, in that order. Order is the
    # contract, not string presence — a refactor that prints heartbeats
    # after resolve_module() returns would still leak silent stdout.
    assert (
        out.index("[1/2] mod-alpha: start")
        < out.index("[1/2] mod-alpha: resolving")
        < out.index("mod-alpha: considered=1")
    )
    assert (
        out.index("[2/2] mod-beta: start")
        < out.index("[2/2] mod-beta: resolving")
        < out.index("mod-beta: considered=1")
    )
    # Lock table has both rows completed.
    import sqlite3

    conn = sqlite3.connect(tmp_db)
    rows = conn.execute(
        "SELECT module_key, outcome, completed_at FROM module_write_locks "
        "ORDER BY module_key"
    ).fetchall()
    conn.close()
    assert len(rows) == 2
    for key, outcome, completed_at in rows:
        assert outcome == "ok"
        assert completed_at is not None


def test_main_skips_module_held_by_other_worker(
    tmp_db: Path,
    tmp_queue: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    monkeypatch.setattr(citation_residuals, "resolve_module", _fake_resolve)
    # Pre-hold mod-alpha under a different holder. mod-beta is free.
    conflict = module_lock.acquire_module_lock("mod-alpha", holder="other-worker")
    assert conflict is None  # acquire succeeded

    rc = citation_residuals.main(
        ["resolve", "--all", "--worker-id", "resolver-01"]
    )
    assert rc == 0
    out = capsys.readouterr().out
    # alpha was skipped with a clear reason; beta ran through.
    assert "mod-alpha: SKIPPED" in out
    assert "locked by 'other-worker'" in out
    assert "mod-beta" in out
    assert "considered=1" in out  # only beta counted toward totals
    assert "skipped_locked=1" in out


def test_main_no_lock_flag_bypasses_locking(
    tmp_db: Path,
    tmp_queue: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    monkeypatch.setattr(citation_residuals, "resolve_module", _fake_resolve)
    # Pre-hold mod-alpha. Without --no-lock this would be skipped.
    module_lock.acquire_module_lock("mod-alpha", holder="other")

    rc = citation_residuals.main(["resolve", "--all", "--no-lock"])
    assert rc == 0
    out = capsys.readouterr().out
    # Both ran — lock was bypassed.
    assert "SKIPPED" not in out
    assert "considered=2" in out


def test_main_dry_run_bypasses_locking(
    tmp_db: Path,
    tmp_queue: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    monkeypatch.setattr(citation_residuals, "resolve_module", _fake_resolve)
    # Pre-hold both. --dry-run doesn't write, so no lock contention.
    module_lock.acquire_module_lock("mod-alpha", holder="other1")
    module_lock.acquire_module_lock("mod-beta", holder="other2")

    rc = citation_residuals.main(["resolve", "--all", "--dry-run"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "SKIPPED" not in out
    assert "considered=2" in out


def test_main_releases_lock_on_resolver_exception(
    tmp_db: Path,
    tmp_queue: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(qp: Path, **_: object) -> dict:
        raise RuntimeError("synthetic resolver failure")

    monkeypatch.setattr(citation_residuals, "resolve_module", boom)
    with pytest.raises(RuntimeError, match="synthetic"):
        citation_residuals.main(
            ["resolve", "mod-alpha", "--worker-id", "resolver-01"]
        )
    # Crash released the lock so the next run can retry the same module.
    assert (
        module_lock.acquire_module_lock("mod-alpha", holder="next-worker")
        is None
    )


def test_main_uses_worker_id_when_provided(
    tmp_db: Path,
    tmp_queue: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(citation_residuals, "resolve_module", _fake_resolve)
    rc = citation_residuals.main(
        ["resolve", "mod-alpha", "--worker-id", "named-worker-42"]
    )
    assert rc == 0
    import sqlite3

    conn = sqlite3.connect(tmp_db)
    row = conn.execute(
        "SELECT holder FROM module_write_locks WHERE module_key = ?",
        ("mod-alpha",),
    ).fetchone()
    conn.close()
    assert row is not None
    # Lock still present (completed, not evicted). Holder was the named id.
    assert row[0] == "named-worker-42"


def test_main_locks_on_canonical_module_key_not_filename_stem(
    tmp_db: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression for Codex PR #363 review finding.

    Queue filenames are slash-flattened (e.g.
    `ai-ml-engineering-advanced-genai-module-1.1-fine-tuning-llms.json`)
    but the canonical module_key inside the JSON keeps slashes
    (`ai-ml-engineering/advanced-genai/module-1.1-fine-tuning-llms`).
    The lock must be keyed on the canonical value so other writers
    using the canonical key coordinate properly. Locking on the stem
    would cause false non-coordination.
    """
    review_dir = tmp_path / "human-review"
    review_dir.mkdir(parents=True)
    flattened_filename = "track-topic-module-1"
    canonical_key = "track/topic/module-1"
    (review_dir / f"{flattened_filename}.json").write_text(
        json.dumps(
            {
                "module_key": canonical_key,
                "queued_findings": {
                    "needs_citation": [{"line": 1, "signals": ["year_reference"]}]
                },
                "resolved_findings": [],
                "unresolvable_findings": [],
            },
            indent=2,
        )
        + "\n"
    )
    monkeypatch.setattr(citation_residuals, "HUMAN_REVIEW_DIR", review_dir)
    monkeypatch.setattr(citation_residuals, "resolve_module", _fake_resolve)

    rc = citation_residuals.main(
        ["resolve", "--all", "--worker-id", "resolver-01"]
    )
    assert rc == 0
    import sqlite3

    conn = sqlite3.connect(tmp_db)
    # Lock row uses the canonical (slashed) key, NOT the stem.
    row_canonical = conn.execute(
        "SELECT holder, outcome FROM module_write_locks WHERE module_key = ?",
        (canonical_key,),
    ).fetchone()
    row_stem = conn.execute(
        "SELECT holder FROM module_write_locks WHERE module_key = ?",
        (flattened_filename,),
    ).fetchone()
    conn.close()
    assert row_canonical is not None, (
        "lock was not recorded under the canonical module_key — "
        "concurrent writers using the canonical key would not "
        "coordinate with this resolver"
    )
    assert row_canonical[0] == "resolver-01"
    assert row_canonical[1] == "ok"
    assert row_stem is None, (
        "lock was incorrectly recorded under the flattened stem"
    )


def test_main_falls_back_to_stem_when_module_key_missing(
    tmp_db: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Legacy queue files without a `module_key` field fall back to
    using the filename stem. Preserves behavior for pre-canonical-key
    files that might still exist in an operator's local pipeline state.
    """
    review_dir = tmp_path / "human-review"
    review_dir.mkdir(parents=True)
    (review_dir / "legacy-mod.json").write_text(
        json.dumps(
            {
                # No "module_key" field.
                "queued_findings": {
                    "needs_citation": [{"line": 1, "signals": ["year_reference"]}]
                },
                "resolved_findings": [],
                "unresolvable_findings": [],
            },
            indent=2,
        )
        + "\n"
    )
    monkeypatch.setattr(citation_residuals, "HUMAN_REVIEW_DIR", review_dir)
    monkeypatch.setattr(citation_residuals, "resolve_module", _fake_resolve)

    rc = citation_residuals.main(["resolve", "--all"])
    assert rc == 0
    import sqlite3

    conn = sqlite3.connect(tmp_db)
    row = conn.execute(
        "SELECT module_key FROM module_write_locks"
    ).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == "legacy-mod"
