from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import psutil

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import dispatch


def _pid_exited(pid: int, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not psutil.pid_exists(pid):
            return True
        try:
            if psutil.Process(pid).status() == psutil.STATUS_ZOMBIE:
                return True
        except psutil.NoSuchProcess:
            return True
        time.sleep(0.05)
    return False


def _cleanup_pid(pid: int | None) -> None:
    if pid is None:
        return
    try:
        process = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return
    for child in process.children(recursive=True):
        try:
            child.kill()
        except psutil.NoSuchProcess:
            pass
    try:
        process.kill()
    except psutil.NoSuchProcess:
        pass


def test_kill_process_tree_reaps_child_in_different_process_group():
    python_bin = Path(".venv/bin/python")
    assert python_bin.exists()

    parent_code = """
import subprocess
import time

child = subprocess.Popen(["sleep", "300"], start_new_session=True)
print(child.pid, flush=True)
time.sleep(300)
"""
    parent = subprocess.Popen(
        [str(python_bin), "-c", parent_code],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    child_pid = None

    try:
        assert parent.stdout is not None
        child_pid = int(parent.stdout.readline().strip())
        assert psutil.pid_exists(child_pid)

        dispatch._kill_process_tree(parent)

        parent.wait(timeout=5)
        assert _pid_exited(parent.pid)
        assert _pid_exited(child_pid)
    finally:
        _cleanup_pid(child_pid)
        _cleanup_pid(parent.pid)
