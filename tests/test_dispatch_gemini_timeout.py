from __future__ import annotations

import io
import signal
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import dispatch


def test_dispatch_gemini_starts_new_session():
    proc = MagicMock()
    proc.stdin = io.StringIO()
    proc.stdout = io.StringIO()
    proc.stderr = io.StringIO()
    proc.wait.return_value = 0
    proc.returncode = 0

    with patch("dispatch.subprocess.Popen", return_value=proc) as popen_mock, patch(
        "dispatch._stream_with_timeout", return_value=(["ok"], False)
    ), patch("dispatch._log"):
        ok, output = dispatch.dispatch_gemini("prompt", model="gemini-3-flash-preview")

    assert ok is True
    assert output == "ok"
    assert popen_mock.call_args.kwargs["start_new_session"] is True


def test_stream_timeout_kills_process_group_first():
    proc = MagicMock()
    proc.pid = 12345
    parent = MagicMock()
    child = MagicMock()
    parent.children.return_value = [child]

    with patch("dispatch.psutil.Process", return_value=parent), patch(
        "dispatch.os.killpg"
    ) as killpg:
        dispatch._kill_process_tree(proc)

    child.kill.assert_called_once()
    parent.kill.assert_called_once()
    killpg.assert_called_once_with(12345, signal.SIGKILL)
    proc.kill.assert_not_called()


def test_stream_timeout_falls_back_to_proc_kill():
    proc = MagicMock()
    proc.pid = None

    dispatch._kill_process_tree(proc)

    proc.kill.assert_called_once()


def test_stream_timeout_uses_process_group_when_psutil_cannot_inspect():
    proc = MagicMock()
    proc.pid = 12345

    with patch("dispatch.psutil.Process", side_effect=dispatch.psutil.AccessDenied), patch(
        "dispatch.os.killpg"
    ) as killpg:
        dispatch._kill_process_tree(proc)

    killpg.assert_called_once_with(12345, signal.SIGKILL)
    proc.kill.assert_not_called()


def test_stream_timeout_falls_back_to_proc_kill_when_group_kill_fails():
    proc = MagicMock()
    proc.pid = 12345

    with patch("dispatch.psutil.Process", side_effect=dispatch.psutil.AccessDenied), patch(
        "dispatch.os.killpg", side_effect=OSError
    ):
        dispatch._kill_process_tree(proc)

    proc.kill.assert_called_once()


def test_stream_timeout_kills_all_descendants_before_parent():
    proc = MagicMock()
    proc.pid = 12345
    parent = MagicMock()
    child = MagicMock()
    grandchild = MagicMock()
    kill_order: list[str] = []
    parent.children.return_value = [child, grandchild]
    child.kill.side_effect = lambda: kill_order.append("child")
    grandchild.kill.side_effect = lambda: kill_order.append("grandchild")
    parent.kill.side_effect = lambda: kill_order.append("parent")

    with patch("dispatch.psutil.Process", return_value=parent), patch(
        "dispatch.os.killpg"
    ):
        dispatch._kill_process_tree(proc)

    assert kill_order == ["child", "grandchild", "parent"]


def test_gemini_quiet_mode_defaults_on_in_pipeline_mode(monkeypatch):
    monkeypatch.delenv("KUBEDOJO_QUIET", raising=False)
    monkeypatch.setenv("KUBEDOJO_PIPELINE", "1")

    assert dispatch._gemini_quiet_mode_enabled() is True


def test_gemini_quiet_mode_defaults_off_outside_pipeline(monkeypatch):
    monkeypatch.delenv("KUBEDOJO_QUIET", raising=False)
    monkeypatch.delenv("KUBEDOJO_PIPELINE", raising=False)

    assert dispatch._gemini_quiet_mode_enabled() is False


def test_gemini_env_strips_api_keys_on_subscription(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "sk-test")
    monkeypatch.setenv("GOOGLE_API_KEY", "gg-test")

    api_env = dispatch._gemini_env(use_subscription=False)
    sub_env = dispatch._gemini_env(use_subscription=True)

    assert api_env["GEMINI_API_KEY"] == "sk-test"
    assert api_env["GOOGLE_API_KEY"] == "gg-test"
    assert "GEMINI_API_KEY" not in sub_env
    assert "GOOGLE_API_KEY" not in sub_env
    assert sub_env is not api_env  # independent dict, no mutation


def test_gemini_with_retry_flips_to_subscription_on_rate_limit():
    """On 429 from API-key path, next retry must use the subscription path
    immediately (no backoff — independent quotas)."""
    calls: list[dict] = []

    def fake_dispatch(*args, use_subscription=None, **kwargs):
        calls.append({"args": args, "kwargs": kwargs,
                      "use_subscription": use_subscription})
        if len(calls) == 1:
            return False, "429 Too Many Requests — quota exceeded"
        return True, "real output"

    with patch("dispatch.dispatch_gemini", side_effect=fake_dispatch), \
         patch("dispatch.time.sleep") as sleep_mock, \
         patch.object(dispatch, "_FORCE_GEMINI_SUBSCRIPTION", False):
        ok, output = dispatch.dispatch_gemini_with_retry("hello", max_retries=3)

    assert ok is True
    assert output == "real output"
    assert len(calls) == 2
    assert calls[0]["use_subscription"] is False  # first try: API key
    assert calls[1]["use_subscription"] is True   # retry: subscription
    sleep_mock.assert_not_called()  # no backoff between auth-path flip


def test_gemini_with_retry_force_subscription_skips_api_key():
    """When KUBEDOJO_GEMINI_SUBSCRIPTION=1, first call must use subscription."""
    calls: list[dict] = []

    def fake_dispatch(*args, use_subscription=None, **kwargs):
        calls.append({"args": args, "kwargs": kwargs,
                      "use_subscription": use_subscription})
        return True, "out"

    with patch("dispatch.dispatch_gemini", side_effect=fake_dispatch), \
         patch.object(dispatch, "_FORCE_GEMINI_SUBSCRIPTION", True):
        ok, _ = dispatch.dispatch_gemini_with_retry("hello")

    assert ok is True
    assert calls[0]["use_subscription"] is True


def test_gemini_with_retry_flip_works_with_max_retries_one():
    """Regression: with max_retries=1 the API-key 429 flip must still produce
    an attempt on the subscription path. Previously the `continue` consumed
    the only loop iteration and the subscription path was never tried."""
    calls: list[dict] = []

    def fake_dispatch(*args, use_subscription=None, **kwargs):
        calls.append({"args": args, "kwargs": kwargs,
                      "use_subscription": use_subscription})
        if len(calls) == 1:
            return False, "429 Too Many Requests — quota exceeded"
        return True, "real output"

    with patch("dispatch.dispatch_gemini", side_effect=fake_dispatch), \
         patch("dispatch.time.sleep") as sleep_mock, \
         patch.object(dispatch, "_FORCE_GEMINI_SUBSCRIPTION", False):
        ok, output = dispatch.dispatch_gemini_with_retry("hello", max_retries=1)

    assert ok is True
    assert output == "real output"
    assert len(calls) == 2
    assert calls[0]["use_subscription"] is False  # first try: API key
    assert calls[1]["use_subscription"] is True   # flip retry: subscription
    sleep_mock.assert_not_called()


def test_gemini_with_retry_double_429_falls_back_to_subscription_backoff():
    """When both API-key AND subscription return 429, the flip produces one
    subscription attempt, then on the next loop iteration we apply subscription
    backoff — not another flip."""
    calls: list[dict] = []

    def fake_dispatch(*args, use_subscription=None, **kwargs):
        calls.append({"args": args, "kwargs": kwargs,
                      "use_subscription": use_subscription})
        if len(calls) <= 2:
            return False, "429 rate limit"
        return True, "finally ok"

    with patch("dispatch.dispatch_gemini", side_effect=fake_dispatch), \
         patch("dispatch.time.sleep") as sleep_mock, \
         patch.object(dispatch, "_FORCE_GEMINI_SUBSCRIPTION", False):
        ok, output = dispatch.dispatch_gemini_with_retry("hello", max_retries=3)

    assert ok is True
    assert output == "finally ok"
    # Expected sequence: API-key (429) → flip, subscription (429) →
    # backoff sleep → subscription (success)
    assert [c["use_subscription"] for c in calls] == [False, True, True]
    sleep_mock.assert_called_once()  # exactly one backoff between the two subscription attempts
