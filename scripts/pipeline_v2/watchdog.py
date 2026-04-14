from __future__ import annotations

import threading
import time

from .control_plane import ControlPlane


def sweep_once(control_plane: ControlPlane) -> int:
    """Release expired leases once. Used directly by tests and CLI."""
    return control_plane.sweep_once()


def watch_forever(
    control_plane: ControlPlane,
    *,
    interval_seconds: int = 30,
    stop_event: threading.Event | None = None,
) -> None:
    """Optional loop wrapper. Callers opt in; CLI never starts a daemon."""
    stop = stop_event or threading.Event()
    while not stop.wait(interval_seconds):
        sweep_once(control_plane)
