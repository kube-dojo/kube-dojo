from __future__ import annotations

import importlib.util
import os
import re
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _load_module():
    module_path = Path(__file__).resolve().parent.parent / "scripts" / "local_api.py"
    spec = importlib.util.spec_from_file_location("local_api_state_session", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


local_api = _load_module()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _manifest_entries(body: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        entry
        for category in body["categories"]
        for entry in category["entries"]
    ]


def _seed_handoffs(repo_root: Path) -> None:
    _write(
        repo_root / "docs" / "session-state" / "2026-05-09-cka-part1-and-html-migration-pivot.html",
        """
        <!doctype html>
        <html>
        <body>
        <h1>CKA Part 1 and HTML Migration Pivot</h1>
        <p>Latest HTML handoff summary for cold-start routing.</p>
        </body>
        </html>
        """,
    )
    _write(
        repo_root / "docs" / "session-state" / "2026-05-08-4-content-green-canary.md",
        """
        # Content Green Canary

        TL;DR: Previous handoff summary.
        """,
    )
    _write(repo_root / "docs" / "session-state" / "archive-pre-2026-04-28.md", "# Archive")
    _write(repo_root / "docs" / "session-state" / "handoff-without-prefix.html", "<h1>Ignored</h1>")


def _seed_benchmark_reports(repo_root: Path) -> None:
    _write(
        repo_root / "calibration" / "v1" / "reports" / "2026-05-20" / "index.html",
        "<title>Previous</title>",
    )
    latest = repo_root / "calibration" / "v1" / "reports" / "2026-05-21"
    latest_index = latest / "index.html"
    _write(latest_index, "<title>Latest</title>")
    rendered_at = datetime(2026, 5, 21, 12, 0, tzinfo=UTC).timestamp()
    os.utime(latest_index, (rendered_at, rendered_at))
    _write(latest / "matrix.html", "<title>Matrix</title>")
    _write(latest / "wave-ab-report.html", "<title>Wave AB</title>")
    _write(latest / "stability.html", "<title>Stability</title>")
    _write(latest / "per-lane" / "architecting.html", "<title>Architecting</title>")
    _write(latest / "per-model" / "gpt-5.html", "<title>GPT-5</title>")

    ledger_path = repo_root / "calibration" / "v1" / "ledger.db"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(ledger_path)
    try:
        conn.execute("CREATE TABLE cells (cell_id TEXT, model_id TEXT, lane TEXT)")
        conn.execute("CREATE TABLE scores (cell_id TEXT, scored_at TEXT)")
        conn.executemany(
            "INSERT INTO cells (cell_id, model_id, lane) VALUES (?, ?, ?)",
            [
                ("cell-1", "model-a", "architecting"),
                ("cell-2", "model-a", "implementation"),
                ("cell-3", "model-b", "architecting"),
            ],
        )
        scored_at = datetime.fromtimestamp(rendered_at + 42, UTC).isoformat()
        conn.executemany(
            "INSERT INTO scores (cell_id, scored_at) VALUES (?, ?)",
            [("cell-1", scored_at), ("cell-2", scored_at), ("cell-2", scored_at)],
        )
        conn.commit()
    finally:
        conn.close()


def test_state_manifest_contains_cold_start_critical_paths(tmp_path: Path) -> None:
    status, body, content_type = local_api.route_request(tmp_path, "/api/state/manifest")

    assert status == 200
    assert content_type == "application/json; charset=utf-8"
    paths = {entry["path"] for entry in _manifest_entries(body)}
    assert "/api/briefing/session" in paths
    assert "/api/briefing/session?compact=1" in paths
    assert "/api/schema" in paths
    assert "/api/session/current" in paths
    assert "/api/benchmarks/latest" in paths


def test_state_manifest_contains_benchmarks_category(tmp_path: Path) -> None:
    status, body, _ = local_api.route_request(tmp_path, "/api/state/manifest")

    assert status == 200
    benchmarks = [category for category in body["categories"] if category["category"] == "benchmarks"]
    assert benchmarks
    assert benchmarks[0]["ui"] == "/benchmarks"
    assert benchmarks[0]["entries"][0]["path"] == "/api/benchmarks/latest"
    assert benchmarks[0]["entries"][1]["path"] == "/benchmarks"


def test_state_manifest_entries_are_well_formed(tmp_path: Path) -> None:
    status, body, _ = local_api.route_request(tmp_path, "/api/state/manifest")

    assert status == 200
    for entry in _manifest_entries(body):
        assert entry["name"]
        assert entry["path"]
        assert entry["purpose"]


def test_current_session_returns_latest_key(tmp_path: Path) -> None:
    _seed_handoffs(tmp_path)

    status, body, content_type = local_api.route_request(tmp_path, "/api/session/current")

    assert status == 200
    assert content_type == "application/json; charset=utf-8"
    assert "latest" in body
    assert body["latest"]["filename"] == "2026-05-09-cka-part1-and-html-migration-pivot.html"


def test_current_session_latest_date_matches_filename_prefix(tmp_path: Path) -> None:
    _seed_handoffs(tmp_path)

    _, body, _ = local_api.route_request(tmp_path, "/api/session/current")

    latest = body["latest"]
    assert latest["date"] == re.match(r"^\d{4}-\d{2}-\d{2}", latest["filename"]).group(0)


def test_current_session_predecessor_is_not_newer_than_latest(tmp_path: Path) -> None:
    _seed_handoffs(tmp_path)

    _, body, _ = local_api.route_request(tmp_path, "/api/session/current")

    assert body["predecessors"][0]["date"] <= body["latest"]["date"]


def test_current_session_excludes_archive_and_prefixless_files(tmp_path: Path) -> None:
    _seed_handoffs(tmp_path)

    _, body, _ = local_api.route_request(tmp_path, "/api/session/current")

    filenames = {body["latest"]["filename"], *(item["filename"] for item in body["predecessors"])}
    assert "archive-pre-2026-04-28.md" not in filenames
    assert "handoff-without-prefix.html" not in filenames
    assert body["total_handoffs"] == 2


def test_current_session_contains_at_least_one_html_handoff(tmp_path: Path) -> None:
    _seed_handoffs(tmp_path)

    _, body, _ = local_api.route_request(tmp_path, "/api/session/current")

    handoffs = [body["latest"], *body["predecessors"]]
    assert any(item["format"] == "html" for item in handoffs)


def test_latest_benchmarks_returns_report_tree_and_ledger_counts(tmp_path: Path) -> None:
    _seed_benchmark_reports(tmp_path)

    status, body, content_type = local_api.route_request(tmp_path, "/api/benchmarks/latest")

    assert status == 200
    assert content_type == "application/json; charset=utf-8"
    assert body["total_runs"] == 2
    assert body["latest"]["date"] == "2026-05-21"
    assert body["latest"]["directory"] == "calibration/v1/reports/2026-05-21"
    assert (
        body["latest"]["render_url"]
        == "http://127.0.0.1:8768/artifacts/calibration/v1/reports/2026-05-21/index.html"
    )
    assert body["latest"]["files"] == {
        "index": "/artifacts/calibration/v1/reports/2026-05-21/index.html",
        "matrix": "/artifacts/calibration/v1/reports/2026-05-21/matrix.html",
        "wave_ab": "/artifacts/calibration/v1/reports/2026-05-21/wave-ab-report.html",
        "stability": "/artifacts/calibration/v1/reports/2026-05-21/stability.html",
        "per_lane": ["/artifacts/calibration/v1/reports/2026-05-21/per-lane/architecting.html"],
        "per_model": ["/artifacts/calibration/v1/reports/2026-05-21/per-model/gpt-5.html"],
    }
    assert body["latest"]["ledger"] == {
        "path": "calibration/v1/ledger.db",
        "cells_total": 3,
        "cells_scored": 2,
        "models": 2,
        "lanes": 2,
    }
    assert body["latest"]["staleness_seconds"] == 42.0
    assert body["predecessors"] == [
        {
            "date": "2026-05-20",
            "directory": "calibration/v1/reports/2026-05-20",
            "render_url": "http://127.0.0.1:8768/artifacts/calibration/v1/reports/2026-05-20/index.html",
        }
    ]


def test_latest_benchmarks_empty_reports_tree_returns_empty_payload(tmp_path: Path) -> None:
    status, body, content_type = local_api.route_request(tmp_path, "/api/benchmarks/latest")

    assert status == 200
    assert content_type == "application/json; charset=utf-8"
    assert body == {"latest": None, "predecessors": [], "total_runs": 0}
