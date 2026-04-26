from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path


def _load_module():
    module_path = Path(__file__).resolve().parent.parent / "scripts" / "local_api.py"
    spec = importlib.util.spec_from_file_location("local_api_quality_board", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


local_api = _load_module()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _module_text(title: str, *, pending: bool = False, strong: bool = True) -> str:
    lines = ["---", f'title: "{title}"']
    if pending:
        lines.append("revision_pending: true")
    lines.extend(["---", "", "## Overview", ""])
    filler = 320 if strong else 40
    lines.extend(f"Line {i}" for i in range(filler))
    if strong:
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
                "- Question",
                "",
                "## Hands-On",
                "",
                "1. Do thing",
            ]
        )
    lines.extend(["", "## Sources", "", "- [Docs](https://example.com/docs)"])
    return "\n".join(lines) + "\n"


def _seed_module(repo: Path, rel: str, *, title: str, pending: bool = False, strong: bool = True) -> str:
    _write(repo / "src" / "content" / "docs" / f"{rel}.md", _module_text(title, pending=pending, strong=strong))
    return rel.replace("/", "-")


def _write_state(repo: Path, slug: str, *, stage: str, auto_approved: bool = False, verdict: str | None = None) -> None:
    review = {"auto_approved": auto_approved}
    if verdict:
        review["verdict"] = verdict
    _write(
        repo / ".pipeline" / "quality-pipeline" / f"{slug}.json",
        json.dumps({"slug": slug, "stage": stage, "review": review}),
    )


def _clear_caches() -> None:
    with local_api._CACHE_LOCK:
        local_api._CACHE.clear()
    with local_api._QUALITY_AUDIT_CACHE_LOCK:
        local_api._QUALITY_AUDIT_CACHE.clear()


def test_quality_board_precedence_both_beats_rewrite(tmp_path: Path) -> None:
    slug = _seed_module(
        tmp_path,
        "platform/core/module-1.1-backlog",
        title="Backlog",
        pending=True,
        strong=True,
    )
    _write_state(tmp_path, slug, stage="COMMITTED", auto_approved=True)
    _write(tmp_path / ".pipeline" / "quality-pipeline" / "post-review-queue.txt", f"{slug}\n")
    _clear_caches()

    board = local_api.build_quality_board(tmp_path)

    assert board["totals"]["both"] == 1
    assert board["totals"]["needs_rewrite"] == 0
    module = board["modules"][0]
    assert module["status"] == "both"
    assert module["revision_pending"] is True
    assert module["in_post_review_queue"] is True


def test_quality_board_track_totals_sum_to_modules(tmp_path: Path) -> None:
    done = _seed_module(tmp_path, "cloud/aws/module-1.1-done", title="Done")
    rewrite = _seed_module(tmp_path, "cloud/aws/module-1.2-rewrite", title="Rewrite", strong=False)
    review = _seed_module(tmp_path, "k8s/cka/module-1.1-review", title="Review")
    flight = _seed_module(tmp_path, "k8s/cka/module-1.2-flight", title="Flight")
    _write_state(tmp_path, done, stage="COMMITTED", verdict="APPROVE")
    _write_state(tmp_path, rewrite, stage="FAILED")
    _write_state(tmp_path, review, stage="COMMITTED", auto_approved=True)
    _write_state(tmp_path, flight, stage="WRITE_IN_PROGRESS")
    _write(tmp_path / ".pipeline" / "quality-pipeline" / "post-review-queue.txt", f"{review}\n")
    _clear_caches()

    board = local_api.build_quality_board(tmp_path)

    assert board["totals"] == {
        "done": 1,
        "needs_rewrite": 1,
        "needs_review": 1,
        "both": 0,
        "in_flight": 1,
        "total": 4,
    }
    assert sum(t["totals"]["total"] for t in board["tracks"]) == 4
    assert sum(len(t["modules"]) for t in board["tracks"]) == 4


def test_quality_board_source_counts_reconcile_with_388_script_inputs(tmp_path: Path) -> None:
    full = _seed_module(tmp_path, "cloud/aws/module-1.1-full", title="Full")
    auto = _seed_module(tmp_path, "cloud/aws/module-1.2-auto", title="Auto")
    pending = _seed_module(tmp_path, "cloud/aws/module-1.3-pending", title="Pending", pending=True)
    _write_state(tmp_path, full, stage="COMMITTED", auto_approved=False)
    _write_state(tmp_path, auto, stage="COMMITTED", auto_approved=True)
    _write_state(tmp_path, pending, stage="UNAUDITED")
    _write(tmp_path / ".pipeline" / "quality-pipeline" / "post-review-queue.txt", f"{auto}\n")
    _clear_caches()

    counts = local_api.build_quality_board(tmp_path)["source_counts"]

    assert counts["committed_full_review"] == 1
    assert counts["committed_auto_approved"] == 1
    assert counts["revision_pending"] == 1
    assert counts["post_review_queue"] == 1


def test_quality_board_cache_invalidates_on_input_mtime(tmp_path: Path) -> None:
    rel = "cloud/aws/module-1.1-cache"
    _seed_module(tmp_path, rel, title="Cache")
    _clear_caches()

    code_a, body_a, _ct_a, etag_a = local_api.serve_request(tmp_path, "/api/quality/board")
    assert code_a == 200
    assert json.loads(body_a)["totals"]["done"] == 1

    time.sleep(0.01)
    _write(tmp_path / "src" / "content" / "docs" / f"{rel}.md", _module_text("Cache", pending=True, strong=True))
    code_b, body_b, _ct_b, etag_b = local_api.serve_request(tmp_path, "/api/quality/board")

    assert code_b == 200
    assert etag_b != etag_a
    assert json.loads(body_b)["totals"]["needs_rewrite"] == 1
