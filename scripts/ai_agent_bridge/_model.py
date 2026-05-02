"""Model availability checking."""

import os
import subprocess
from pathlib import Path

from ._config import _MODEL_CACHE, _MODEL_CACHE_TTL, GEMINI_CLI, agent_child_env


def _force_gemini_subscription() -> bool:
    return os.environ.get("KUBEDOJO_GEMINI_SUBSCRIPTION") == "1"


def _subscription_env() -> dict[str, str]:
    return agent_child_env(
        "gemini",
        {"GEMINI_API_KEY": None, "GOOGLE_API_KEY": None},
    )


def _has_gemini_api_key(env: dict[str, str]) -> bool:
    return bool(env.get("GEMINI_API_KEY") or env.get("GOOGLE_API_KEY"))


def _model_check_quota_exhausted(text: str) -> bool:
    lowered = text.lower()
    return (
        "exhausted" in lowered
        or "429" in text
        or "quota" in lowered
        or "resource_exhausted" in lowered
        or "usage limit reached" in lowered
    )


def check_model(model: str, timeout: int = 15, force: bool = False) -> bool:
    """Check if a Gemini model is available by sending a trivial prompt.

    Results are cached for 1 hour to avoid burning API quota.
    Returns True if the model responds, False if unavailable or errors.
    """
    import time as _time

    # Check cache first (saves an API call)
    if not force and model in _MODEL_CACHE:
        available, cached_at = _MODEL_CACHE[model]
        age = _time.time() - cached_at
        if age < _MODEL_CACHE_TTL:
            status = "available" if available else "NOT available"
            print(f"🔍 Model '{model}': {status} (cached {int(age)}s ago)")
            return available

    env = _subscription_env() if _force_gemini_subscription() else agent_child_env("gemini")
    try:
        result = subprocess.run(
            [GEMINI_CLI, "-m", model, "-p", "Reply with exactly: MODEL_OK"],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(Path(__file__).parent.parent.parent),
            env=env,
        )
        if result.returncode == 0 and "MODEL_OK" in result.stdout:
            _MODEL_CACHE[model] = (True, _time.time())
            return True
        combined = f"{result.stdout}\n{result.stderr}"
        if (
            not _force_gemini_subscription()
            and _has_gemini_api_key(env)
            and _model_check_quota_exhausted(combined)
        ):
            print(
                f"⚠️  Model '{model}' API-key quota exhausted; "
                "checking OAuth/subscription path."
            )
            oauth_result = subprocess.run(
                [GEMINI_CLI, "-m", model, "-p", "Reply with exactly: MODEL_OK"],
                capture_output=True, text=True, timeout=timeout,
                cwd=str(Path(__file__).parent.parent.parent),
                env=_subscription_env(),
            )
            if oauth_result.returncode == 0 and "MODEL_OK" in oauth_result.stdout:
                _MODEL_CACHE[model] = (True, _time.time())
                return True
            result = oauth_result
        _handle_model_check_failure(result, model, _time)
        _MODEL_CACHE[model] = (False, _time.time())
        return False
    except subprocess.TimeoutExpired:
        print(f"⚠️  Model '{model}' check timed out after {timeout}s.")
        _MODEL_CACHE[model] = (False, _time.time())
        return False
    except FileNotFoundError:
        print(f"❌ Gemini CLI not found at: {GEMINI_CLI}")
        return False


def _handle_model_check_failure(result, model: str, _time):
    """Print appropriate error message for model check failure."""
    stderr = result.stderr or ""
    if "not found" in stderr.lower() or "not available" in stderr.lower() or "invalid model" in stderr.lower():
        print(f"❌ Model '{model}' is not available on this account.")
    elif "exhausted" in stderr.lower() or "429" in stderr or "quota" in stderr.lower():
        print(f"⚠️  Model '{model}' exists but quota is exhausted.")
    else:
        print(f"⚠️  Model '{model}' check failed (exit {result.returncode}): {stderr[:200]}")


def _detect_model_error(stderr: str, model: str) -> str | None:
    """Detect model-specific errors from Gemini CLI stderr.

    Returns a user-friendly error message, or None if not a model error.
    """
    s = stderr.lower()
    if "not found" in s or "not available" in s or "invalid model" in s:
        _MODEL_CACHE[model] = (False, __import__("time").time())
        return f"Model '{model}' is not available on this account. Switch accounts or use a different model."
    return None
