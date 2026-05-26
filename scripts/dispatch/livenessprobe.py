"""Pure liveness probe primitives copied from learn-ukrainian phase-1 design.

This module is currently Phase 1 of kube-dojo/kube-dojo.github.io #373:
only the standalone signal primitives and composite probe are implemented.

Phase 2 (out of scope for this PR) will wire these primitives into
`scripts/dispatch.py` subprocess monitoring so dispatch paths can act on
composite liveness.

Phase 3 (out of scope for this PR) will integrate optional
`citation_backfill` usage, including per-CLI probe descriptors.

Design reference:
https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1520
"""
from __future__ import annotations

import glob
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import psutil


class Signal(Protocol):
    """A probe signal returns True if liveness is observed in this cycle."""

    def evaluate(self) -> bool: ...


def _newest_path(pattern: str) -> Path | None:
    """Return the newest matching path, or None when no file exists."""
    matches = [Path(match) for match in glob.glob(pattern)]
    if not matches:
        return None
    return max(
        (path for path in matches if path.exists()),
        key=lambda path: path.stat().st_mtime,
        default=None,
    )


@dataclass
class FileMTimeSignal:
    """Positive if the target file mtime is within ``max_age_s`` of now.

    For glob patterns (for example, ``rollout-*.jsonl``), evaluate against the
    most recently modified match.
    """

    path: str
    max_age_s: int
    now_provider: Callable[[], float] = field(default=time.time, repr=False, compare=False)

    def evaluate(self) -> bool:
        target = _newest_path(self.path)
        if target is None:
            return False
        return (self.now_provider() - target.stat().st_mtime) <= self.max_age_s


@dataclass
class FileSizeGrowthSignal:
    """Positive if the target file has grown by at least ``min_bytes``.

    The first call baselines the file size and returns True if the file exists.
    If the file disappears, the signal clears state and returns False.
    """

    path: str
    min_bytes: int
    _last_size: int | None = field(default=None, init=False, repr=False)

    def evaluate(self) -> bool:
        target = Path(self.path)
        if not target.exists():
            self._last_size = None
            return False

        current_size = target.stat().st_size
        if self._last_size is None:
            self._last_size = current_size
            return True

        grew_by = current_size - self._last_size
        self._last_size = current_size
        return grew_by >= self.min_bytes


@dataclass
class ProcCpuSignal:
    """Positive if PID CPU usage exceeds threshold during the sample window."""

    pid: int
    min_percent: float
    sample_window_s: float = 1.0

    def evaluate(self) -> bool:
        try:
            process = psutil.Process(self.pid)
            return process.cpu_percent(interval=self.sample_window_s) >= self.min_percent
        except psutil.Error:
            return False


@dataclass
class StdoutStreamedSignal:
    """Positive when stdout has received a byte within ``max_age_s`` seconds."""

    last_write_time_provider: Callable[[], float | None]
    max_age_s: int
    now_provider: Callable[[], float] = field(default=time.time, repr=False, compare=False)

    def evaluate(self) -> bool:
        last_write_time = self.last_write_time_provider()
        if last_write_time is None:
            return False
        return (self.now_provider() - last_write_time) <= self.max_age_s


@dataclass
class CompositeProbe:
    """ANY-mode composition over independent liveness signals."""

    signals: list[Signal]
    mode: str = "ANY"
    periodSeconds: int = 30
    failureThreshold: int = 3
    initialDelaySeconds: int = 90
    _failure_count: int = 0
    _started_at: float | None = None

    def __post_init__(self) -> None:
        if self.mode != "ANY":
            raise ValueError("CompositeProbe currently supports mode='ANY' only")

    @property
    def period_s(self) -> int:
        return self.periodSeconds

    @property
    def failure_threshold(self) -> int:
        return self.failureThreshold

    @property
    def initial_delay_seconds(self) -> int:
        return self.initialDelaySeconds

    def evaluate_once(self) -> bool:
        """Return True if any signal reports liveness."""
        return any(signal.evaluate() for signal in self.signals)

    def report(self, alive_this_cycle: bool) -> None:
        """Update the internal consecutive-failure counter."""
        if alive_this_cycle:
            self._failure_count = 0
            return
        self._failure_count += 1

    def should_kill(self) -> bool:
        """True once consecutive failures reaches ``failureThreshold``."""
        return self._failure_count >= self.failureThreshold

    def in_initial_grace(self, now: float) -> bool:
        """Return True while still within startup grace."""
        if self._started_at is None:
            return False
        return (now - self._started_at) < self.initialDelaySeconds
