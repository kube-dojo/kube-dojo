"""QwenAdapter — wraps ``hermes -z`` (openrouter provider) for the agent runtime.

Fifth production adapter. Brings qwen3.6 plus/flash online as a
peer to codex / claude / gemini / deepseek for code review, deliberation,
and write lanes.

Key design points:

- **Transport:** ``hermes`` CLI in oneshot mode (``--oneshot=<prompt>``
  argv binding). Hermes proxies to Qwen via the ``openrouter`` provider.
- **Modes:** All three (read-only / workspace-write / danger) supported.
  Mode → hermes toolset mapping is conservative for read-only (no
  terminal/file tools), permissive for workspace-write and danger.
- **Project context:** hermes injects KubeDojo project state via its
  ``memory`` + ``skills`` toolsets unless suppressed. We keep this on for
  review/code work (gives Qwen situational awareness) but disable via
  ``--ignore-user-config --ignore-rules`` when the caller passes
  ``tool_config={"isolated": True}`` (used for calibration / benchmark).
- **No session resume.** ``resume_policy=never`` in the registry — hermes
  has session semantics but cross-worktree contamination would mirror the
  Codex footgun. Defensively ignored even if passed.
- **Liveness:** hermes streams output to stdout, so the runner's stdout
  watchdog handles liveness. ``liveness_signal_paths()`` returns ``()``.

Status: qwen replaces the legacy lane as the calibrated external reviewer per
  2026-05-19 user direction.

In read-only mode, Qwen runs with a restricted Hermes toolset (web-only). If
the model emits unfulfilled tool-use intent (e.g. ``<bash>`` blocks), the returned
text is a non-executable stub and not a useful review. See
``feedback_qwen_tool_use_stub_detection.md`` if present.

Rate limit follows hermes transport patterns (mostly provider-side HTTP
429-style failures).
"""
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Any

from ..result import ParseResult
from .base import InvocationPlan


# Rate-limit patterns. Qwen follows Hermes transport patterns, including
# standard 429 signaling.
_RATE_LIMIT_PATTERNS = (
    r"rate limit",
    r"rate_limit",
    r"usage limit",
    r"quota exceeded",
    r"too many requests",
    r"\bHTTP 429\b",
    r"\bstatus 429\b",
    r"\b429\b",
)
_RATE_LIMIT_RE = re.compile("|".join(_RATE_LIMIT_PATTERNS), re.IGNORECASE)
_TOOL_USE_INTENT_RE = re.compile(
    r"<\s*(bash|tool_use|tool|terminal|shell)\b[^>]*>",
    re.IGNORECASE,
)

# Hermes startup warnings we strip before declaring success.
_HERMES_BANNER_RE = re.compile(
    r"^(💡 Python project detected\..*|hermes -z:.*)$",
    re.MULTILINE,
)

# Toolsets per mode. Hermes built-in toolsets are documented under
# `hermes tools list`. We deliberately exclude memory / skills from
# read-only to keep calibration runs reproducible; they're great for
# real review/code work though.
_TOOLSETS_READ_ONLY = "web"
_TOOLSETS_WORKSPACE = "web,file,terminal,code_execution,todo"
_TOOLSETS_DANGER = "web,file,terminal,code_execution,todo,memory,skills"


class QwenAdapter:
    """Adapter for ``hermes -z`` with the openrouter provider."""

    name: str = "qwen"
    # qwen3.6-plus is the canonical model identifier for hermes via
    # openrouter.
    # User may override via env (e.g. when qwen3.6-flash is needed
    # for a cheap search lane).
    default_model: str = os.environ.get("AB_QWEN_MODEL", "qwen/qwen3.6-plus")
    supported_modes: frozenset[str] = frozenset({"read-only", "workspace-write", "danger"})

    def build_invocation(
        self,
        *,
        prompt: str,
        mode: str,
        cwd: Path,
        model: str | None,
        task_id: str | None,
        session_id: str | None,
        tool_config: dict | None,
    ) -> InvocationPlan:
        """Build the hermes oneshot invocation.

        ``tool_config`` keys honored:
            - ``isolated: bool`` — if True, pass ``--ignore-user-config
              --ignore-rules`` to bypass hermes's project-context
              injection. Default False (project context is feature, not
              bug, for review/code work).
            - ``toolsets: str`` — comma-separated override for ``-t``.
              Wins over the mode-default mapping.
            - ``provider: str`` — override hermes provider. Default
              ``openrouter``.
            - ``effort: str`` — reasoning effort label. Hermes does not
              expose this as a flag today; we forward it via prompt
              prefix when ``"xhigh"`` is requested. Tracking issue: see
              ``project_hermes_model_inventory.md``.
            - ``yolo: bool`` — pass ``--yolo`` (auto-accept tool calls).
              Default True for write modes, False for read-only.
            - ``accept_hooks: bool`` — pass ``--accept-hooks``. Default
              False; opt-in for callers that want project hooks to fire.
        """
        if mode not in self.supported_modes:
            raise ValueError(f"QwenAdapter: unsupported mode {mode!r}")

        tc: dict[str, Any] = tool_config or {}

        binary = shutil.which("hermes") or "hermes"
        cmd: list[str] = [binary]

        # Reasoning effort hint applied first so the final prompt string is
        # bound via --oneshot= below.
        effort = tc.get("effort")
        final_prompt = prompt
        if effort and effort != "default":
            final_prompt = f"[Reasoning effort hint: {effort}]\n\n{prompt}"

        # Model
        cmd.extend(["-m", model or self.default_model])

        # Provider — openrouter is the canonical qwen runtime path.
        provider = tc.get("provider", "openrouter")
        cmd.extend(["--provider", provider])

        # Toolset selection — caller override wins, else mode default.
        toolsets = tc.get("toolsets")
        if not toolsets:
            if mode == "read-only":
                toolsets = _TOOLSETS_READ_ONLY
            elif mode == "workspace-write":
                toolsets = _TOOLSETS_WORKSPACE
            else:  # danger
                toolsets = _TOOLSETS_DANGER
        cmd.extend(["-t", toolsets])

        # Auto-accept tool calls. Required for non-interactive runs that
        # do file edits or shell ops. Read-only stays prompt-only by
        # default so we don't accidentally grant network egress through
        # the web tool's confirm step.
        yolo_default = mode in ("workspace-write", "danger")
        if bool(tc.get("yolo", yolo_default)):
            cmd.append("--yolo")

        if bool(tc.get("accept_hooks", False)):
            cmd.append("--accept-hooks")

        # Isolation: bypass user config + project rules. Used for
        # calibration / benchmark runs where deterministic output is
        # more important than context awareness.
        if bool(tc.get("isolated", False)):
            cmd.extend(["--ignore-user-config", "--ignore-rules"])

        # --oneshot (-z): one-shot mode; PROMPT must be a single argv token.
        # Use ``--oneshot=<prompt>`` so flag-like prompts (e.g. ``--provider``)
        # are bound as the flag value, not parsed as a separate CLI flag.
        # Do NOT use stdin (``hermes -z -``) — that is interpreted as
        # "no prompt, project-introspection mode".
        cmd.append(f"--oneshot={final_prompt}")

        # Defensively drop session_id — resume_policy=never.
        _ = session_id
        _ = task_id

        return InvocationPlan(
            cmd=cmd,
            cwd=cwd,
            stdin_payload="",  # prompt is in argv; stdin must be empty
            output_file=None,
            env_overrides={},
            liveness_paths=(),
        )

    def parse_response(
        self,
        *,
        stdout: str,
        stderr: str,
        returncode: int,
        output_file: Path | None,
        plan: InvocationPlan | None = None,
        call_start_time: float | None = None,
    ) -> ParseResult:
        """Parse hermes -z output.

        Hermes prints the final assistant message to stdout. Diagnostic
        warnings ("💡 Python project detected.", argument errors) appear
        in stdout/stderr depending on how hermes was invoked.
        """
        _ = output_file
        _ = plan
        _ = call_start_time

        # Strip hermes banners that aren't part of the response.
        clean_stdout = _HERMES_BANNER_RE.sub("", stdout or "").strip()
        tool_use_unfulfilled = bool(_TOOL_USE_INTENT_RE.search(clean_stdout))

        if tool_use_unfulfilled and len(clean_stdout) < 1000:
            return ParseResult(
                ok=False,
                response="",
                stderr_excerpt=(
                    "Qwen returned tool-use intent without execution "
                    f"({len(clean_stdout)} chars). The hermes toolset for this mode "
                    "doesn't include the requested tool. For Qwen reviews, re-dispatch "
                    "with --mode workspace-write (grants terminal/file tools), "
                    "or fall back to claude. Raw stub: " + clean_stdout[:200]
                ),
                rate_limited=False,
                session_id=None,
                tokens=None,
            )

        combined = f"{clean_stdout}\n{stderr or ''}"
        pattern_hit = bool(_RATE_LIMIT_RE.search(combined))
        call_failed = returncode != 0 or not bool(clean_stdout)
        rate_limited = pattern_hit and call_failed

        ok = returncode == 0 and bool(clean_stdout) and not rate_limited
        response = clean_stdout if ok else ""

        stderr_excerpt: str | None = None
        if not ok:
            excerpt_source = (stderr or "").strip() or (stdout or "").strip()
            stderr_excerpt = excerpt_source[:500] or None

        return ParseResult(
            ok=ok,
            response=response,
            stderr_excerpt=stderr_excerpt,
            rate_limited=rate_limited,
            session_id=None,
            tokens=None,
        )

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        """Hermes streams to stdout; the runner's stdout watchdog covers liveness."""
        _ = plan
        return ()
