"""LLM dispatch — thin wrapper over ``scripts/dispatch.py`` with round-robin.

Contract:

* :func:`dispatch` is a single call site for Codex / Claude / Gemini.
* :func:`writer_for_index` assigns writer + reviewer by **permanent**
  module index so the assignment is stable across re-bootstraps and
  SIGKILL-recovery. Even indexes → Codex writes + Claude reviews; odd
  → Claude writes + Codex reviews.
* :class:`DispatcherUnavailable` is raised when Claude's peak-hours
  guard / budget / rate-limit refuses the call. Callers keep the
  module in a retryable stage (not ``FAILED``) because the LLM is
  temporarily off, not the module.

Delegates to ``scripts/dispatch.py`` as a subprocess so each call gets
process isolation and inherits the existing budget / peak-hours guards
without reimplementing them.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .worktree import primary_checkout_root

_REPO_ROOT = primary_checkout_root(Path(__file__).resolve().parents[2])
_VENV_PYTHON = str(_REPO_ROOT / ".venv" / "bin" / "python")
_DISPATCH_CLI = str(_REPO_ROOT / "scripts" / "dispatch.py")

Agent = Literal["codex", "claude", "gemini"]

VALID_AGENTS: frozenset[str] = frozenset({"codex", "claude", "gemini"})

# Timeouts by role, not agent. The citation-verify path is per-URL so
# it gets a short timeout; writer/reviewer dispatches are per-module so
# they get a long one. Callers that need different values pass explicit
# ``timeout=`` kwargs.
DEFAULT_TIMEOUTS: dict[str, int] = {
    "write": 900,
    "review": 900,
    "citation_verify": 60,
}


class DispatcherUnavailable(RuntimeError):
    """Dispatcher refused a call due to peak-hours / budget / rate-limit.

    Callers must distinguish this from a real failure: the module should
    stay in a retryable stage rather than advancing to ``FAILED``. A
    bulk run that crossed Claude peak hours (14:00–20:00 weekdays)
    without this signal would silently drain modules from the queue.
    """


@dataclass(frozen=True)
class DispatchResult:
    """Structured dispatch return — replaces the older ``tuple[bool, str]`` shape."""

    ok: bool
    stdout: str
    stderr: str
    returncode: int
    duration_sec: float
    agent: str
    model: str | None


# Stderr fragments that indicate a temporary "dispatcher off" condition
# rather than a real failure. Kept in sync with ``citation_backfill``'s
# list. Substring-and-case-insensitive match so small wording changes in
# ``dispatch.py`` don't silently reclassify unavailability as failure.
_UNAVAILABLE_MARKERS = (
    "peak hours in effect",
    "claude peak hours",
    "call budget",
    "claude budget",
    "claude unavailable",
    "claudeunavailableerror",
    "rate_limit",
    "rate limited",
)


def _looks_unavailable(text: str) -> bool:
    s = (text or "").lower()
    return any(m in s for m in _UNAVAILABLE_MARKERS)


def dispatch(
    agent: Agent,
    prompt: str,
    *,
    timeout: int,
    model: str | None = None,
    cwd: Path | None = None,
    tools_disabled: bool = False,
) -> DispatchResult:
    """Call ``scripts/dispatch.py <agent>`` with the prompt on stdin.

    ``cwd`` defaults to the primary checkout. Pass the worktree path when
    dispatching a writer — Codex's file operations anchor to cwd.

    ``tools_disabled=True`` forces text-only output (no Edit/Write/Bash
    tool use). Required for v2 writer/reviewer dispatches: Claude
    in print mode is agentic by default and will modify files in
    ``cwd``, returning only a summary on stdout. Currently honored for
    Claude only; Codex relies on its ``--sandbox read-only`` setting
    in :mod:`scripts.dispatch` and Gemini has no built-in tools.

    Raises :class:`DispatcherUnavailable` when the stderr signals a
    temporary refusal. Returns :class:`DispatchResult` with ``ok=False``
    for genuine failures (crashes, timeouts, non-zero exits without
    availability markers) — caller decides retry vs FAILED.
    """
    if agent not in VALID_AGENTS:
        raise ValueError(f"unknown agent {agent!r}; expected one of {sorted(VALID_AGENTS)}")

    cmd: list[str] = [_VENV_PYTHON, _DISPATCH_CLI, agent, "-", "--timeout", str(timeout)]
    if model:
        cmd.extend(["--model", model])
    if tools_disabled and agent == "claude":
        cmd.append("--no-tools")

    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            input=prompt,
            cwd=str(cwd or _REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout + 30,  # headroom so dispatch.py's own timeout fires first
            check=False,
        )
    except subprocess.TimeoutExpired:
        return DispatchResult(
            ok=False,
            stdout="",
            stderr=f"dispatch_wrapper_timeout_after_{timeout + 30}s",
            returncode=-1,
            duration_sec=time.monotonic() - t0,
            agent=agent,
            model=model,
        )

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    duration = time.monotonic() - t0

    if proc.returncode != 0 and _looks_unavailable(stderr + "\n" + stdout):
        raise DispatcherUnavailable(
            f"{agent} refused the call: {(stderr or stdout).strip()[:400]}"
        )

    return DispatchResult(
        ok=proc.returncode == 0,
        stdout=stdout,
        stderr=stderr,
        returncode=proc.returncode,
        duration_sec=duration,
        agent=agent,
        model=model,
    )


def writer_for_index(module_index: int) -> tuple[Agent, Agent]:
    """Return ``(writer, reviewer)`` — codex writes, claude reviews.

    The earlier even/odd alternation was abandoned 2026-04-25 after
    empirical evidence that claude-as-writer lands ~440-line modules
    (below the 600-line minimum in ``module-quality.md``) while codex
    consistently lands 1500–2000+ lines at rubric ≥4.0. Claude is
    redirected to coding/review tasks where it's strong. Cross-family
    review per ``docs/review-protocol.md`` is still satisfied because
    claude reviews codex (different model families).

    The ``module_index`` parameter is kept in the signature so callers
    don't break; it's no longer used to choose roles.

    Gemini is never a writer or reviewer here — it's reserved for the
    teaching audit (pre-pipeline) and citation verification (per-URL)
    and as tiebreaker after 2 retries (via :func:`tiebreaker_agent`).
    """
    del module_index
    return ("codex", "claude")


def tiebreaker_agent() -> Agent:
    """Agent invoked when Codex↔Claude retry loop hits the cap.

    Gemini is the third party because it's cheap, fast, and outside
    the writer/reviewer rotation so its verdict is structurally
    independent.
    """
    return "gemini"
