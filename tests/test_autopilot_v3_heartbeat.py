from __future__ import annotations

import json
import time

from scripts import autopilot_v3


def test_start_heartbeat_writes_heartbeat_file(monkeypatch, tmp_path) -> None:
    heartbeat_path = tmp_path / "heartbeat.json"
    monkeypatch.setattr(autopilot_v3, "HEARTBEAT_PATH", heartbeat_path)
    stop = autopilot_v3._start_heartbeat(pid=1234)
    try:
        time.sleep(1.5)
        assert heartbeat_path.exists()
        data = json.loads(heartbeat_path.read_text(encoding="utf-8"))
        assert data["pid"] == 1234
        assert isinstance(data["ts"], str)
        assert isinstance(data["uptime_s"], int)
    finally:
        stop.set()
