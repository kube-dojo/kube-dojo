"""Environment sanitizing for child LLM/agent processes.

Agent CLIs should not inherit the full login shell environment. The parent
process can keep GitHub, cloud, npm, and other credentials for orchestration,
but child model processes only need normal shell settings plus the credential
for the provider being invoked.
"""
from __future__ import annotations

import os
import re
from collections.abc import Mapping

_SENSITIVE_NAME_RE = re.compile(
    r"(TOKEN|SECRET|PASSWORD|PASSWD|PRIVATE|CREDENTIAL|API[_-]?KEY|"
    r"ACCESS[_-]?KEY|AUTH|COOKIE)",
    re.IGNORECASE,
)

_SECRET_VALUE_RES = (
    re.compile(r"^github_pat_[A-Za-z0-9_]{20,}$"),
    re.compile(r"^gh[pousr]_[A-Za-z0-9_]{20,}$"),
    re.compile(r"^sk-[A-Za-z0-9_-]{20,}$"),
    re.compile(r"^xox[baprs]-[A-Za-z0-9-]{20,}$"),
    re.compile(r"^hf_[A-Za-z0-9]{20,}$"),
    re.compile(r"^npm_[A-Za-z0-9]{20,}$"),
    re.compile(r"^AKIA[0-9A-Z]{16}$"),
    re.compile(r"^AIza[0-9A-Za-z_-]{20,}$"),
)

_SAFE_NAME_ALLOWLIST = {
    "AB_CLAUDE_MODEL",
    "AB_DB_PATH",
    "AB_GEMINI_FALLBACK_MODEL",
    "AB_GEMINI_MODEL",
    "AB_GEMINI_REVIEW_MODEL",
    "AB_PID_DIR",
    "AB_PIPELINE_ENV_KEY",
    "AB_PYTHON",
    "AB_REPO_ROOT",
    "CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS",
    "CLAUDE_PROJECT_DIR",
    "CODEX_BRIDGE_MODE",
    "GEMINI_SESSION",
    "HOME",
    "KUBEDOJO_GEMINI_SUBSCRIPTION",
    "KUBEDOJO_IGNORE_PEAK_HOURS",
    "KUBEDOJO_MAX_CLAUDE_CALLS",
    "KUBEDOJO_PIPELINE",
    "KUBEDOJO_QUIET",
    "KUBEDOJO_WRITER_MODEL",
    "LANG",
    "LC_ALL",
    "LOGNAME",
    "PATH",
    "PWD",
    "SHELL",
    "SSH_AUTH_SOCK",
    "TERM",
    "TMP",
    "TMPDIR",
    "USER",
    "VIRTUAL_ENV",
    "XDG_CACHE_HOME",
    "XDG_CONFIG_HOME",
    "XDG_DATA_HOME",
    "XDG_STATE_HOME",
}

_PROVIDER_SECRET_ALLOWLIST = {
    "codex": {"OPENAI_API_KEY", "CODEX_API_KEY"},
    "claude": {"ANTHROPIC_API_KEY", "CLAUDE_API_KEY"},
    "gemini": {"GEMINI_API_KEY", "GOOGLE_API_KEY"},
}
_PROVIDER_SECRET_ALLOWLIST["bridge"] = set().union(
    *_PROVIDER_SECRET_ALLOWLIST.values()
)


def _value_looks_secret(value: str) -> bool:
    stripped = value.strip()
    return any(pattern.match(stripped) for pattern in _SECRET_VALUE_RES)


def _provider_allowed_secrets(provider: str | None) -> set[str]:
    if provider is None:
        return set()
    return set(_PROVIDER_SECRET_ALLOWLIST.get(provider, set()))


def build_agent_env(
    *,
    provider: str | None = None,
    base: Mapping[str, str] | None = None,
    overrides: Mapping[str, str | None] | None = None,
    extra_allow: set[str] | frozenset[str] | None = None,
) -> dict[str, str]:
    """Return a child-process environment with unrelated secrets removed.

    ``provider`` controls which provider credential may pass through. For
    example, ``provider="gemini"`` may keep ``GEMINI_API_KEY`` while still
    dropping ``GITHUB_TOKEN`` and cloud/npm/HF credentials. ``overrides`` are
    applied before filtering; a value of ``None`` removes a name.
    """
    source: dict[str, str] = dict(os.environ if base is None else base)
    for key, value in (overrides or {}).items():
        if value is None:
            source.pop(key, None)
        else:
            source[key] = value

    safe_names = _SAFE_NAME_ALLOWLIST | set(extra_allow or ())
    allowed_secrets = _provider_allowed_secrets(provider)
    sanitized: dict[str, str] = {}

    for key, value in source.items():
        if key in allowed_secrets:
            sanitized[key] = value
            continue
        if key in safe_names or key.startswith("LC_"):
            if not _value_looks_secret(value):
                sanitized[key] = value
            continue
        if _SENSITIVE_NAME_RE.search(key):
            continue
        if _value_looks_secret(value):
            continue
        sanitized[key] = value

    return sanitized
