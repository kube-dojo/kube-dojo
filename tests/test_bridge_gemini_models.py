from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.adapters.gemini import GeminiAdapter
from agent_runtime.errors import RateLimitedError
from agent_runtime.result import Result
from ai_agent_bridge import _cli, _gemini


def _ask_args(*, model: str | None = None, review: bool = False) -> SimpleNamespace:
    return SimpleNamespace(
        content="please review",
        task_id="task-1",
        type="query",
        data=None,
        model=model,
        review=review,
        from_model=None,
        async_mode=False,
        stdout_only=False,
        output_path=None,
        extract=None,
        skip_model_check=False,
        allow_write=False,
        delimiters=None,
        no_github=True,
    )


def test_ask_gemini_review_defaults_to_review_model(monkeypatch):
    calls: list[tuple] = []
    monkeypatch.setattr(_cli, "ask_gemini", lambda *args: calls.append(args))

    _cli._handle_ask_gemini(_ask_args(review=True))

    assert calls
    assert calls[0][4] == _cli.GEMINI_REVIEW_MODEL


def test_ask_gemini_non_review_defaults_to_default_model(monkeypatch):
    calls: list[tuple] = []
    monkeypatch.setattr(_cli, "ask_gemini", lambda *args: calls.append(args))

    _cli._handle_ask_gemini(_ask_args())

    assert calls
    assert calls[0][4] == _cli.GEMINI_DEFAULT_MODEL


def test_resolve_gemini_model_uses_requested_model_when_available(monkeypatch):
    monkeypatch.setattr(_gemini, "check_model", lambda model: True)

    resolved = _gemini._resolve_gemini_model(
        _gemini.GEMINI_DEFAULT_MODEL,
        async_mode=False,
        skip_model_check=False,
    )

    assert resolved == _gemini.GEMINI_DEFAULT_MODEL


def test_resolve_gemini_model_falls_back_when_requested_model_unavailable(
    monkeypatch,
):
    monkeypatch.setattr(_gemini, "check_model", lambda model: False)

    resolved = _gemini._resolve_gemini_model(
        _cli.GEMINI_REVIEW_MODEL,
        async_mode=False,
        skip_model_check=False,
    )

    assert resolved == _gemini.GEMINI_FALLBACK_MODEL


def test_resolve_gemini_model_does_not_check_async_or_fallback(monkeypatch):
    def fail_check(_model: str) -> bool:
        raise AssertionError("check_model should not be called")

    monkeypatch.setattr(_gemini, "check_model", fail_check)

    assert (
        _gemini._resolve_gemini_model(
            _cli.GEMINI_REVIEW_MODEL,
            async_mode=True,
            skip_model_check=False,
        )
        == _cli.GEMINI_REVIEW_MODEL
    )
    assert (
        _gemini._resolve_gemini_model(
            _gemini.GEMINI_FALLBACK_MODEL,
            async_mode=False,
            skip_model_check=False,
        )
        == _gemini.GEMINI_FALLBACK_MODEL
    )


def test_ask_gemini_cached_unavailable_model_uses_fallback(monkeypatch):
    seen_models: list[str] = []
    _gemini._MODEL_CACHE.clear()
    _gemini._MODEL_CACHE[_cli.GEMINI_REVIEW_MODEL] = (False, _gemini.time.time())

    def send_message(*args):
        seen_models.append(args[5])
        return 123

    monkeypatch.setattr(_gemini, "_send_gemini_message", send_message)
    monkeypatch.setattr(_gemini, "process_and_respond", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        _gemini,
        "check_model",
        lambda _model: (_ for _ in ()).throw(
            AssertionError("cached unavailable model should not be rechecked")
        ),
    )

    try:
        _gemini.ask_gemini(
            "please review",
            task_id="task-1",
            model=_cli.GEMINI_REVIEW_MODEL,
        )
    finally:
        _gemini._MODEL_CACHE.clear()

    assert seen_models == [_gemini.GEMINI_FALLBACK_MODEL]


def test_launch_gemini_background_uses_configured_python(monkeypatch, tmp_path):
    captured: dict[str, list[str]] = {}

    class FakeProcess:
        pid = 321

    def fake_popen(cmd, **_kwargs):
        captured["cmd"] = cmd
        return FakeProcess()

    monkeypatch.setattr(_gemini, "PYTHON_CMD", "custom-python")
    monkeypatch.setattr(_gemini, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(_gemini, "_is_task_locked", lambda *_args: False)
    monkeypatch.setattr(_gemini, "_write_pid_file", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(_gemini.subprocess, "Popen", fake_popen)

    _gemini._launch_gemini_background(
        {"task_id": "task-1"},
        123,
        "gemini-test",
        "prompt",
    )

    assert captured["cmd"][0] == "custom-python"


def test_gemini_adapter_strips_api_keys_for_subscription_auth(tmp_path):
    plan = GeminiAdapter().build_invocation(
        prompt="hello",
        mode="workspace-write",
        cwd=tmp_path,
        model="gemini-test",
        task_id="task-1",
        session_id=None,
        tool_config={"use_subscription_auth": True},
    )

    assert plan.env_overrides["GEMINI_API_KEY"] is None
    assert plan.env_overrides["GOOGLE_API_KEY"] is None


def test_bridge_switches_from_api_key_to_oauth_on_quota(monkeypatch, tmp_path):
    calls: list[bool] = []

    def fake_runtime_invoke(*_args, **kwargs):
        calls.append(kwargs["tool_config"] == {"use_subscription_auth": True})
        if len(calls) == 1:
            raise RateLimitedError("gemini", "gemini-test", "quota exceeded")
        return Result(
            ok=True,
            agent="gemini",
            model="gemini-test",
            mode="workspace-write",
            response="OAuth response",
            stderr_excerpt=None,
            duration_s=0.1,
            session_id=None,
            rate_limited=False,
            stalled=False,
            returncode=0,
            usage_record={},
        )

    monkeypatch.setenv("GEMINI_API_KEY", "api-key")
    monkeypatch.delenv("KUBEDOJO_GEMINI_SUBSCRIPTION", raising=False)
    monkeypatch.setattr(_gemini, "runtime_invoke", fake_runtime_invoke)
    monkeypatch.setattr(_gemini, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(_gemini, "_is_task_locked", lambda *_args: False)
    monkeypatch.setattr(_gemini, "_write_pid_file", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(_gemini, "_remove_pid_file", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(_gemini, "_route_gemini_response", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(_gemini, "acknowledge", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(_gemini, "_send_gemini_error", lambda *_args, **_kwargs: None)

    response = _gemini._run_gemini_sync(
        {"task_id": "task-1"},
        123,
        "gemini-test",
        "prompt",
        no_timeout=False,
        stdout_only=True,
        output_path=None,
        allow_write=False,
        skip_github=True,
    )

    assert response == "OAuth response"
    assert calls == [False, True]


def test_bridge_switches_to_oauth_when_rate_limit_reason_is_noisy(monkeypatch, tmp_path):
    calls: list[bool] = []

    def fake_runtime_invoke(*_args, **kwargs):
        calls.append(kwargs["tool_config"] == {"use_subscription_auth": True})
        if len(calls) == 1:
            raise RateLimitedError(
                "gemini",
                "gemini-test",
                "Warning: Basic terminal detected. Visual rendering limited.",
            )
        return Result(
            ok=True,
            agent="gemini",
            model="gemini-test",
            mode="workspace-write",
            response="OAuth response after noisy rate limit",
            stderr_excerpt=None,
            duration_s=0.1,
            session_id=None,
            rate_limited=False,
            stalled=False,
            returncode=0,
            usage_record={},
        )

    monkeypatch.setenv("GEMINI_API_KEY", "api-key")
    monkeypatch.delenv("KUBEDOJO_GEMINI_SUBSCRIPTION", raising=False)
    monkeypatch.setattr(_gemini, "runtime_invoke", fake_runtime_invoke)
    monkeypatch.setattr(_gemini, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(_gemini, "_is_task_locked", lambda *_args: False)
    monkeypatch.setattr(_gemini, "_write_pid_file", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(_gemini, "_remove_pid_file", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(_gemini, "_route_gemini_response", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(_gemini, "acknowledge", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(_gemini, "_send_gemini_error", lambda *_args, **_kwargs: None)

    response = _gemini._run_gemini_sync(
        {"task_id": "task-1"},
        123,
        "gemini-test",
        "prompt",
        no_timeout=False,
        stdout_only=True,
        output_path=None,
        allow_write=False,
        skip_github=True,
    )

    assert response == "OAuth response after noisy rate limit"
    assert calls == [False, True]


def test_bridge_force_subscription_skips_api_key(monkeypatch, tmp_path):
    calls: list[dict | None] = []

    def fake_runtime_invoke(*_args, **kwargs):
        calls.append(kwargs["tool_config"])
        return Result(
            ok=True,
            agent="gemini",
            model="gemini-test",
            mode="workspace-write",
            response="forced OAuth response",
            stderr_excerpt=None,
            duration_s=0.1,
            session_id=None,
            rate_limited=False,
            stalled=False,
            returncode=0,
            usage_record={},
        )

    monkeypatch.setenv("GEMINI_API_KEY", "api-key")
    monkeypatch.setenv("KUBEDOJO_GEMINI_SUBSCRIPTION", "1")
    monkeypatch.setattr(_gemini, "runtime_invoke", fake_runtime_invoke)
    monkeypatch.setattr(_gemini, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(_gemini, "_is_task_locked", lambda *_args: False)
    monkeypatch.setattr(_gemini, "_write_pid_file", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(_gemini, "_remove_pid_file", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(_gemini, "_route_gemini_response", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(_gemini, "acknowledge", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(_gemini, "_send_gemini_error", lambda *_args, **_kwargs: None)

    response = _gemini._run_gemini_sync(
        {"task_id": "task-1"},
        123,
        "gemini-test",
        "prompt",
        no_timeout=False,
        stdout_only=True,
        output_path=None,
        allow_write=False,
        skip_github=True,
    )

    assert response == "forced OAuth response"
    assert calls == [{"use_subscription_auth": True}]


def test_model_check_falls_back_to_oauth_on_api_quota(monkeypatch):
    from ai_agent_bridge import _model

    envs: list[dict[str, str]] = []

    def fake_run(*_args, **kwargs):
        envs.append(kwargs["env"])
        if len(envs) == 1:
            return SimpleNamespace(
                returncode=1,
                stdout="",
                stderr="RESOURCE_EXHAUSTED quota exceeded",
            )
        return SimpleNamespace(returncode=0, stdout="MODEL_OK", stderr="")

    monkeypatch.setattr(_model, "_PARENT_ENV", {"GEMINI_API_KEY": "api-key"})
    monkeypatch.setattr(_model.subprocess, "run", fake_run)
    monkeypatch.delenv("KUBEDOJO_GEMINI_SUBSCRIPTION", raising=False)
    _model._MODEL_CACHE.clear()

    try:
        assert _model.check_model("gemini-test")
    finally:
        _model._MODEL_CACHE.clear()

    assert envs[0]["GEMINI_API_KEY"] == "api-key"
    assert "GEMINI_API_KEY" not in envs[1]
