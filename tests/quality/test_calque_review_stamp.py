from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "quality" / "calque_review_stamp.py"


def _load_calque_review_stamp():
    spec = importlib.util.spec_from_file_location("calque_review_stamp_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


stamp_mod = _load_calque_review_stamp()


SAMPLE_FRONTMATTER = """---
title: "Тестовий модуль"
sidebar:
  order: 42
en_file: "prerequisites/module-1.1-test.md"
---

# Заголовок

Тіло модуля без кальків.
"""


def _write_sample(path: Path, body_suffix: str = "") -> None:
    path.write_text(SAMPLE_FRONTMATTER + body_suffix, encoding="utf-8")


def test_stamp_then_read_status_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "module.md"
    _write_sample(path)

    stamp_mod.stamp(path, detector_version="v1", flags_resolved=3, status="reviewed")
    status = stamp_mod.read_status(path)

    assert status is not None
    assert status["status"] == "reviewed"
    assert status["detector_version"] == "v1"
    assert status["flags_resolved"] == 3
    assert status["stale"] is False
    assert status["reviewed_at"]


def test_body_edit_after_stamping_marks_stale(tmp_path: Path) -> None:
    path = tmp_path / "module.md"
    _write_sample(path)
    stamp_mod.stamp(path, detector_version="v1", flags_resolved=1, status="clean")

    text = path.read_text(encoding="utf-8")
    path.write_text(text + "\nНовий абзац.\n", encoding="utf-8")

    status = stamp_mod.read_status(path)
    assert status is not None
    assert status["stale"] is True


def test_editing_calque_block_does_not_mark_stale(tmp_path: Path) -> None:
    path = tmp_path / "module.md"
    _write_sample(path)
    stamp_mod.stamp(path, detector_version="v1", flags_resolved=2, status="reviewed")

    text = path.read_text(encoding="utf-8")
    updated = text.replace('flags_resolved: 2', "flags_resolved: 99")
    path.write_text(updated, encoding="utf-8")

    status = stamp_mod.read_status(path)
    assert status is not None
    assert status["flags_resolved"] == 99
    assert status["stale"] is False


def test_other_frontmatter_keys_are_byte_preserved(tmp_path: Path) -> None:
    path = tmp_path / "module.md"
    _write_sample(path)
    before = path.read_text(encoding="utf-8")

    stamp_mod.stamp(path, detector_version="v1", flags_resolved=0, status="clean")
    after = path.read_text(encoding="utf-8")

    for line in before.splitlines():
        if line.startswith("calque_review:"):
            continue
        if line.startswith("  reviewed_at:") or line.startswith("  detector_version:"):
            continue
        if line.startswith("  status:") or line.startswith("  flags_resolved:"):
            continue
        if line.startswith("  content_sha:"):
            continue
        assert line in after


def test_restamping_replaces_block_without_duplicating(tmp_path: Path) -> None:
    path = tmp_path / "module.md"
    _write_sample(path)

    stamp_mod.stamp(path, detector_version="v1", flags_resolved=1, status="reviewed")
    stamp_mod.stamp(path, detector_version="v2", flags_resolved=4, status="clean")

    text = path.read_text(encoding="utf-8")
    assert text.count("calque_review:") == 1

    status = stamp_mod.read_status(path)
    assert status is not None
    assert status["detector_version"] == "v2"
    assert status["flags_resolved"] == 4
    assert status["status"] == "clean"
    assert status["stale"] is False
