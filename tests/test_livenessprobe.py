"""Unit tests for scripts.dispatch_livenessprobe primitives."""
from __future__ import annotations

import os
import subprocess
from unittest.mock import patch

import pytest

from scripts.dispatch_livenessprobe import (
    CompositeProbe,
    FileMTimeSignal,
    FileSizeGrowthSignal,
    ProcCpuSignal,
    StdoutStreamedSignal,
)


class StaticSignal:
    def __init__(self, value: bool) -> None:
        self.value = value

    def evaluate(self) -> bool:
        return self.value


def _stop_process(proc: subprocess.Popen[str]) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=3)


def test_file_mtime_signal_returns_true_for_recent_file(tmp_path):
    target = tmp_path / "rollout.jsonl"
    target.write_text("event\n", encoding="utf-8")
    os.utime(target, (100.0, 100.0))

    signal = FileMTimeSignal(str(target), max_age_s=10, now_provider=lambda: 105.0)

    assert signal.evaluate() is True


def test_file_mtime_signal_returns_false_for_stale_file(tmp_path):
    target = tmp_path / "rollout.jsonl"
    target.write_text("event\n", encoding="utf-8")
    os.utime(target, (100.0, 100.0))

    signal = FileMTimeSignal(str(target), max_age_s=10, now_provider=lambda: 111.0)

    assert signal.evaluate() is False


def test_file_mtime_signal_returns_false_for_absent_file(tmp_path):
    signal = FileMTimeSignal(str(tmp_path / "missing.jsonl"), max_age_s=10, now_provider=lambda: 100.0)

    assert signal.evaluate() is False


def test_file_mtime_signal_respects_glob_and_picks_newest_match(tmp_path):
    old = tmp_path / "rollout-old.jsonl"
    new = tmp_path / "rollout-new.jsonl"
    old.write_text("old\n", encoding="utf-8")
    new.write_text("new\n", encoding="utf-8")
    os.utime(old, (100.0, 100.0))
    os.utime(new, (200.0, 200.0))

    signal = FileMTimeSignal(str(tmp_path / "rollout-*.jsonl"), max_age_s=10, now_provider=lambda: 205.0)

    assert signal.evaluate() is True


def test_file_size_growth_signal_first_call_returns_true_and_baselines(tmp_path):
    target = tmp_path / "rollout.jsonl"
    target.write_text("abc", encoding="utf-8")
    signal = FileSizeGrowthSignal(str(target), min_bytes=2)

    assert signal.evaluate() is True


def test_file_size_growth_signal_returns_true_when_growth_reaches_min_bytes(tmp_path):
    target = tmp_path / "rollout.jsonl"
    target.write_text("abc", encoding="utf-8")
    signal = FileSizeGrowthSignal(str(target), min_bytes=2)

    assert signal.evaluate() is True
    target.write_text("abcde", encoding="utf-8")

    assert signal.evaluate() is True


def test_file_size_growth_signal_returns_false_when_growth_is_too_small(tmp_path):
    target = tmp_path / "rollout.jsonl"
    target.write_text("abc", encoding="utf-8")
    signal = FileSizeGrowthSignal(str(target), min_bytes=3)

    assert signal.evaluate() is True
    target.write_text("abcd", encoding="utf-8")

    assert signal.evaluate() is False


def test_file_size_growth_signal_returns_false_for_absent_file(tmp_path):
    signal = FileSizeGrowthSignal(str(tmp_path / "missing.jsonl"), min_bytes=1)

    assert signal.evaluate() is False


def test_file_size_growth_signal_resets_after_absent_file(tmp_path):
    target = tmp_path / "rollout.jsonl"
    signal = FileSizeGrowthSignal(str(target), min_bytes=1)

    assert signal.evaluate() is False
    target.write_text("abc", encoding="utf-8")

    assert signal.evaluate() is True


def test_file_size_growth_signal_resets_on_file_truncation(tmp_path):
    target = tmp_path / "rollout.jsonl"
    target.write_text("abcdef", encoding="utf-8")
    signal = FileSizeGrowthSignal(str(target), min_bytes=2)

    assert signal.evaluate() is True
    target.write_text("abc", encoding="utf-8")
    assert signal.evaluate() is False
    target.write_text("abcde", encoding="utf-8")

    assert signal.evaluate() is True


def test_proc_cpu_signal_returns_true_for_cpu_spinning_subprocess():
    proc = subprocess.Popen(
        ["/bin/sh", "-c", "while :; do :; done"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    try:
        signal = ProcCpuSignal(proc.pid, min_percent=1.0, sample_window_s=0.2)

        assert signal.evaluate() is True
    finally:
        _stop_process(proc)


def test_proc_cpu_signal_returns_false_for_sleeping_subprocess():
    proc = subprocess.Popen(
        ["/bin/sleep", "10"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    try:
        with patch("psutil.Process.cpu_percent", return_value=0.0):
            signal = ProcCpuSignal(proc.pid, min_percent=1.0, sample_window_s=0.2)

            assert signal.evaluate() is False
    finally:
        _stop_process(proc)


def test_proc_cpu_signal_returns_false_for_missing_pid():
    signal = ProcCpuSignal(999_999_999, min_percent=1.0, sample_window_s=0.01)

    assert signal.evaluate() is False


def test_stdout_streamed_signal_returns_true_when_last_write_is_recent():
    signal = StdoutStreamedSignal(lambda: 95.0, max_age_s=10, now_provider=lambda: 100.0)

    assert signal.evaluate() is True


def test_stdout_streamed_signal_returns_false_when_last_write_is_stale():
    signal = StdoutStreamedSignal(lambda: 80.0, max_age_s=10, now_provider=lambda: 100.0)

    assert signal.evaluate() is False


def test_stdout_streamed_signal_returns_false_when_last_write_is_none():
    signal = StdoutStreamedSignal(lambda: None, max_age_s=10, now_provider=lambda: 100.0)

    assert signal.evaluate() is False


def test_composite_probe_evaluate_once_returns_true_with_any_positive_signal():
    probe = CompositeProbe(signals=[StaticSignal(False), StaticSignal(True), StaticSignal(False)])

    assert probe.evaluate_once() is True


def test_composite_probe_evaluate_once_returns_false_with_all_negative_signals():
    probe = CompositeProbe(signals=[StaticSignal(False), StaticSignal(False)])

    assert probe.evaluate_once() is False


def test_composite_probe_report_true_resets_counter():
    probe = CompositeProbe(signals=[])
    probe.report(False)
    probe.report(False)

    probe.report(True)

    assert probe._failure_count == 0


def test_composite_probe_report_false_increments_counter():
    probe = CompositeProbe(signals=[])

    probe.report(False)
    probe.report(False)

    assert probe._failure_count == 2


def test_composite_probe_should_kill_fires_at_exactly_failure_threshold():
    probe = CompositeProbe(signals=[], failureThreshold=2)

    probe.report(False)
    assert probe.should_kill() is False
    probe.report(False)

    assert probe.should_kill() is True


@pytest.mark.parametrize(
    ("started_at", "now", "expected"),
    [
        (None, 100.0, False),
        (100.0, 189.9, True),
        (100.0, 190.0, False),
    ],
)
def test_composite_probe_in_initial_grace_correctly_gates_on_started_at(
    started_at: float | None,
    now: float,
    expected: bool,
):
    probe = CompositeProbe(signals=[], initial_delay_s=90)
    probe._started_at = started_at

    assert probe.in_initial_grace(now) is expected


def test_composite_probe_accepts_issue_shape_parameters():
    probe = CompositeProbe(
        mode="ANY",
        signals=[],
        periodSeconds=30,
        failureThreshold=3,
        initial_delay_s=90,
    )

    assert probe.periodSeconds == 30
    assert probe.failureThreshold == 3
    assert probe.initial_delay_s == 90
