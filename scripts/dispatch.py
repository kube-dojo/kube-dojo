#!/usr/bin/env python3
"""Direct CLI dispatch for Gemini and Claude — no broker, no database.

V2: Adds rate limit detection, inter-call pacing, MCP tool support for
Ukrainian translations (shared RAG server from learn-ukrainian), and
fallback model support. Based on learn-ukrainian V6 dispatch.

Usage:
    python scripts/dispatch.py gemini "Review this module" [--model MODEL] [--github ISSUE_NUM]
    python scripts/dispatch.py gemini "Translate this" --mcp --model gemini-3-flash-preview
    python scripts/dispatch.py claude "Expand this draft" [--model MODEL] [--mcp]
    python scripts/dispatch.py logs [-n 10] [--full]
"""

import argparse
import json
import os
import signal
import shutil
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

import psutil

from agent_runtime.env_sanitize import build_agent_env
from agent_runtime.redact import redact_text
from ai_agent_bridge._prompts import build_review_message

REPO_ROOT = Path(__file__).parent.parent
LOG_DIR = REPO_ROOT / ".dispatch-logs"
MCP_CONFIG = REPO_ROOT / ".mcp.json"

# Resolve CLI paths at import time
GEMINI_CLI = shutil.which("gemini") or "gemini"
CODEX_CLI = shutil.which("codex") or "codex"

# Environment for subprocesses. Agent CLIs get sanitized snapshots so broad
# shell credentials (GitHub/cloud/npm/etc.) are not inherited by model children.
_AGENT_ENV_OVERRIDES = {
    "GEMINI_SESSION": "1",        # Disable hostile aliases (eza, bat, zoxide).
    "KUBEDOJO_PIPELINE": "1",     # Suppress inbox hooks during pipeline runs.
}


def _agent_env(provider: str, overrides: dict[str, str | None] | None = None) -> dict:
    merged_overrides = {**_AGENT_ENV_OVERRIDES}
    if overrides:
        merged_overrides.update(overrides)
    return build_agent_env(provider=provider, overrides=merged_overrides)


_ENV = _agent_env("bridge")
# Gemini auth: CLI prefers GEMINI_API_KEY when set; otherwise falls
# through to OAuth/subscription creds in ~/.gemini/oauth_creds.json.
#
# Runtime behavior (see dispatch_gemini_with_retry):
#   - Default: start on API-key path. If a 429 / quota hit is detected,
#     automatically strip the key from the child env and retry on OAuth.
#   - Force subscription: set KUBEDOJO_GEMINI_SUBSCRIPTION=1 to skip the
#     API-key attempt entirely (e.g. on known-exhausted API quota).
#
# _ENV stays unmodified (API-key path). Subscription env is built on
# demand via _gemini_env(use_subscription=True).
_FORCE_GEMINI_SUBSCRIPTION = os.environ.get("KUBEDOJO_GEMINI_SUBSCRIPTION") == "1"


def _gemini_env(use_subscription: bool) -> dict:
    """Return the child env for a Gemini dispatch. When use_subscription=True,
    strip the API keys so the CLI falls back to OAuth creds."""
    if not use_subscription:
        return _agent_env("gemini")
    return _agent_env(
        "gemini",
        {"GEMINI_API_KEY": None, "GOOGLE_API_KEY": None},
    )

# GitHub comment char limit (65,536 minus safety margin)
GH_CHAR_LIMIT = 64000

# ---------------------------------------------------------------------------
# Model defaults
# ---------------------------------------------------------------------------

# 2026-04-18: Google still exposes Gemini 3 Pro as preview-only, so pin the
# currently tested writer alias here until a GA replacement is available.
GEMINI_WRITER_MODEL = "gemini-3.1-pro-preview"
GEMINI_DEFAULT_MODEL = "gemini-3-flash-preview"
GEMINI_REVIEW_MODEL = "gemini-3.1-pro-preview"  # Pro for reviews — hallucinations on Flash cost real iteration time
GEMINI_FALLBACK_MODEL = "auto"
# Last-ditch fallback when the review model is rate-limited on every tier.
# Pinned to gemini-3-flash-preview rather than "auto" because auto can pick
# gemini-2.5-flash which hallucinates on review tasks (per memory
# feedback_gemini_models.md). Flash-3 misses some Pro nuance but is the agreed
# "good enough to publish a verdict" floor when Pro is capacity-out.
GEMINI_REVIEW_FALLBACK_MODEL = "gemini-3-flash-preview"
CLAUDE_DEFAULT_MODEL = "claude-sonnet-4-6"
CODEX_DEFAULT_MODEL = "codex"  # lets codex CLI pick the default model
CODEX_REVIEW_DEFAULT_MODEL = "codex"
CODEX_PATCH_DEFAULT_MODEL = "gpt-5.4"

# ---------------------------------------------------------------------------
# Rate limit detection + pacing
# ---------------------------------------------------------------------------

_RATE_LIMIT_PATTERNS = (
    "429",
    "RESOURCE_EXHAUSTED",
    "rate limit",
    "rate_limit",
    "quota exceeded",
    "No capacity available",
    "capacity",
    "too many requests",
    "Too Many Requests",
)

_GEMINI_INTER_CALL_DELAY = 0.5  # Reduced from 3.0s per Gemini capacity consultation (2026-04-12)
_last_gemini_call_time: float = 0.0


def _is_rate_limited(text: str) -> bool:
    """Check if a failure was caused by rate limiting."""
    text_lower = text.lower()
    return any(pat.lower() in text_lower for pat in _RATE_LIMIT_PATTERNS)


# ---------------------------------------------------------------------------
# Claude peak-hours pricing guard + per-run budget
# ---------------------------------------------------------------------------
#
# Anthropic charges 2x for Claude API calls during weekday peak hours
# (14:00-20:00 local). To avoid accidental spend, the pipeline refuses to
# invoke Claude during those hours. Weekends are exempt — no peak pricing
# applies Sat/Sun regardless of clock time.
#
# Separately, we cap the number of Claude calls per process to prevent a
# stuck module or runaway retry loop from draining the user's Max-plan quota.
# Default is 30, override via KUBEDOJO_MAX_CLAUDE_CALLS.
#
# Overrides:
#   KUBEDOJO_IGNORE_PEAK_HOURS=1  → bypass peak-hours refusal
#   KUBEDOJO_MAX_CLAUDE_CALLS=N   → change per-process call budget

_CLAUDE_PEAK_START_HOUR = 14  # 14:00 local time
_CLAUDE_PEAK_END_HOUR = 20    # 20:00 local time
_CLAUDE_CALL_BUDGET_DEFAULT = 30
_claude_call_count = 0


class ClaudeUnavailableError(Exception):
    """Raised when a Claude call is blocked (peak hours / budget) or fails
    terminally (rate limit / quota). The pipeline catches this and pauses the
    affected module so it can resume on the next run without losing state."""


def _is_claude_peak_hours() -> bool:
    """Return True if current local time is inside weekday peak hours
    (14:00-20:00 Mon-Fri). Weekends are always off-peak.
    KUBEDOJO_IGNORE_PEAK_HOURS=1 disables the check entirely."""
    if os.environ.get("KUBEDOJO_IGNORE_PEAK_HOURS", "") == "1":
        return False
    now = datetime.now()
    if now.weekday() >= 5:  # Sat=5, Sun=6
        return False
    return _CLAUDE_PEAK_START_HOUR <= now.hour < _CLAUDE_PEAK_END_HOUR


def _claude_call_budget() -> int:
    """Max Claude calls allowed per process. Read from env var on each call
    so the user can tune mid-session without restarting."""
    raw = os.environ.get("KUBEDOJO_MAX_CLAUDE_CALLS", "")
    if raw.isdigit():
        return int(raw)
    return _CLAUDE_CALL_BUDGET_DEFAULT


def _check_claude_budget() -> None:
    """Raise ClaudeUnavailableError if we've already hit the per-process
    Claude call budget. Counter is incremented on each successful dispatch."""
    budget = _claude_call_budget()
    if _claude_call_count >= budget:
        raise ClaudeUnavailableError(
            f"Claude call budget exhausted: {_claude_call_count}/{budget} "
            f"calls this run. Override: KUBEDOJO_MAX_CLAUDE_CALLS=<N>."
        )


def _pace_gemini_calls() -> None:
    """Enforce minimum delay between Gemini CLI calls to avoid bursts."""
    global _last_gemini_call_time
    if _last_gemini_call_time > 0:
        elapsed = time.monotonic() - _last_gemini_call_time
        if elapsed < _GEMINI_INTER_CALL_DELAY:
            wait = _GEMINI_INTER_CALL_DELAY - elapsed
            time.sleep(wait)
    _last_gemini_call_time = time.monotonic()


# ---------------------------------------------------------------------------
# MCP tools for Ukrainian translations (shared RAG server)
# ---------------------------------------------------------------------------

# Claude with MCP: Ukrainian verification + quality tools
CLAUDE_TRANSLATION_TOOLS = (
    "mcp__rag__verify_word,"
    "mcp__rag__verify_words,"
    "mcp__rag__verify_lemma,"
    "mcp__rag__search_text,"
    "mcp__rag__search_literary,"
    "mcp__rag__query_pravopys,"
    "mcp__rag__search_style_guide,"
    "mcp__rag__query_cefr_level,"
    "mcp__rag__search_definitions,"
    "mcp__rag__search_etymology,"
    "mcp__rag__search_idioms,"
    "mcp__rag__search_synonyms,"
    "mcp__rag__translate_en_uk,"
    "mcp__rag__query_grac,"
    "mcp__rag__query_ulif,"
    "mcp__rag__query_r2u,"
    "Read"
)

# ---------------------------------------------------------------------------
# Core dispatch functions
# ---------------------------------------------------------------------------
# Review context now lives in docs/review-protocol.md and is loaded via
# ai_agent_bridge._prompts.build_review_message() on the dispatch path.


def dispatch_gemini_rest(prompt: str, model: str | None = None,
                         review: bool = False,
                         timeout: int = 900) -> tuple[bool, str]:
    """Call Gemini via the public generativelanguage.googleapis.com REST API
    using the GEMINI_API_KEY env var. Returns (success, output).

    Bypasses the gemini CLI subprocess (which is hardwired to OAuth via
    ~/.gemini/settings.json `selectedType`). Use this for the API-key path
    so dispatch_gemini_with_retry can use API as primary and OAuth as
    fallback per the user's quota constraint (1000 API calls/day, then
    spill to OAuth Ultra).
    """
    import json as _json
    import urllib.error as _urlerr
    import urllib.request as _urlreq

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return False, "GEMINI_API_KEY not set"

    if model is None:
        model = GEMINI_REVIEW_MODEL if review else GEMINI_DEFAULT_MODEL
    full_prompt = build_review_message(prompt) if review else prompt

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    body = _json.dumps({
        "contents": [{"parts": [{"text": full_prompt}]}],
    }).encode("utf-8")
    req = _urlreq.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    t0 = time.time()
    try:
        with _urlreq.urlopen(req, timeout=timeout) as resp:
            payload = _json.loads(resp.read().decode("utf-8"))
    except _urlerr.HTTPError as e:
        elapsed = time.time() - t0
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            err_body = ""
        msg = f"HTTP {e.code}: {err_body[:500]}"
        _log("gemini-rest", model, full_prompt, "", False, elapsed, msg)
        return False, msg
    except (TimeoutError, _urlerr.URLError, OSError) as e:
        elapsed = time.time() - t0
        msg = f"network error: {e!s}"
        _log("gemini-rest", model, full_prompt, "", False, elapsed, msg)
        return False, msg

    elapsed = time.time() - t0
    candidates = payload.get("candidates") or []
    if not candidates:
        msg = f"no candidates in response: {_json.dumps(payload)[:500]}"
        _log("gemini-rest", model, full_prompt, "", False, elapsed, msg)
        return False, msg
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        finish = candidates[0].get("finishReason", "")
        msg = f"empty text (finishReason={finish}): {_json.dumps(payload)[:500]}"
        _log("gemini-rest", model, full_prompt, "", False, elapsed, msg)
        return False, msg
    _log("gemini-rest", model, full_prompt, text, True, elapsed)
    return True, text


def dispatch_gemini(prompt: str, model: str | None = None,
                    review: bool = False, timeout: int = 900,
                    mcp: bool = False,
                    use_subscription: bool | None = None) -> tuple[bool, str]:
    """Call Gemini CLI directly. Returns (success, output).

    When ``review=True`` and no ``model`` is specified, uses Pro
    (``GEMINI_REVIEW_MODEL``) — Flash hallucinations on code reviews cost more
    iteration time than the extra Pro latency.

    ``use_subscription`` selects the auth path: ``False`` → API key (default),
    ``True`` → strip keys and use OAuth. ``None`` defers to
    ``KUBEDOJO_GEMINI_SUBSCRIPTION`` (True if set, else False).

    NOTE 2026-05-04: when ``GEMINI_API_KEY`` is set, ``dispatch_gemini_with_retry``
    now intercepts before this function and routes via ``dispatch_gemini_rest``.
    The ``use_subscription=False`` (API-key) branch here is therefore largely
    dead code under the with-retry orchestrator — kept for direct-callers and
    as a fallback when no API key is present. TODO: prune in a follow-up PR
    once all programmatic callers are confirmed to go through ``with_retry``.
    """
    if model is None:
        model = GEMINI_REVIEW_MODEL if review else GEMINI_DEFAULT_MODEL
    if use_subscription is None:
        use_subscription = _FORCE_GEMINI_SUBSCRIPTION
    full_prompt = build_review_message(prompt) if review else prompt
    cmd = [GEMINI_CLI, "-m", model, "-y"]
    if mcp:
        cmd.extend(["--allowed-mcp-server-names", "rag"])
    t0 = time.time()

    _pace_gemini_calls()

    try:
        proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, cwd=str(REPO_ROOT),
            env=_gemini_env(use_subscription),
            start_new_session=True,
        )

        # Write stdin in a background thread to avoid deadlock on large prompts
        stderr_lines: list[str] = []

        def _write_stdin():
            try:
                if proc.stdin:
                    proc.stdin.write(full_prompt)
                    proc.stdin.close()
            except OSError:
                pass

        def _read_stderr():
            try:
                if proc.stderr:
                    for line in proc.stderr:
                        stderr_lines.append(line)
            except (OSError, ValueError):
                pass

        stdin_thread = threading.Thread(target=_write_stdin, daemon=True)
        stderr_thread = threading.Thread(target=_read_stderr, daemon=True)
        stdin_thread.start()
        stderr_thread.start()

        quiet = _gemini_quiet_mode_enabled()
        output_lines, timed_out = _stream_with_timeout(proc, timeout, quiet=quiet)
        proc.wait()
        stdin_thread.join(timeout=5)
        stderr_thread.join(timeout=5)
        stderr = "".join(stderr_lines)
        elapsed = time.time() - t0

        if timed_out:
            print(f"Gemini timed out after {timeout}s", file=sys.stderr)
            _log("gemini", model, full_prompt, "", False, elapsed, "TIMEOUT")
            return False, "TIMEOUT"

        if proc.returncode != 0:
            output = "".join(output_lines).strip()
            if output and len(output) > 50:
                # Non-zero exit but got output — likely usable
                _log("gemini", model, full_prompt, output, True, elapsed, stderr)
                return True, output
            print(f"Gemini error (exit {proc.returncode}): {redact_text(stderr)[:500]}", file=sys.stderr)
            _log("gemini", model, full_prompt, output, False, elapsed, stderr)
            return False, redact_text(stderr)

        output = "".join(output_lines).strip()
        _log("gemini", model, full_prompt, output, True, elapsed)
        return True, output

    except FileNotFoundError:
        _log("gemini", model, full_prompt, "", False, time.time() - t0, "CLI not found")
        print("gemini CLI not found. Install: https://github.com/google-gemini/gemini-cli", file=sys.stderr)
        return False, ""


def dispatch_gemini_with_retry(prompt: str, model: str = GEMINI_DEFAULT_MODEL,
                               review: bool = False, max_retries: int = 3,
                               timeout: int = 900, mcp: bool = False) -> tuple[bool, str]:
    """Call Gemini with retry on rate limits + fallback model.

    Auth-path order: REST API (`GEMINI_API_KEY`, ~1000/day on free tier) is the
    primary path. On 429 / 5xx / network error, fall back to the gemini CLI
    subprocess (which uses OAuth Code Assist via ~/.gemini/settings.json,
    `selectedType=oauth-personal`). The CLI path also auto-flips to
    subscription mode when API-key inheritance is rate-limited there.

    REST does not support MCP tool injection — when ``mcp=True`` we skip
    REST and go straight to the CLI path.
    """
    base_delay = 30
    output = ""
    use_subscription = _FORCE_GEMINI_SUBSCRIPTION

    # When review=True and the caller did not pass an explicit non-default
    # model, promote to GEMINI_REVIEW_MODEL. dispatch_gemini_rest only does
    # this swap when model is None, but this function defaults model to
    # GEMINI_DEFAULT_MODEL — so without this branch, programmatic callers
    # using `review=True` would silently get Flash on the REST path.
    if review and model == GEMINI_DEFAULT_MODEL:
        model = GEMINI_REVIEW_MODEL

    # Primary: REST API key path. Skip if MCP tools requested or no key in env.
    if not mcp and (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
        ok, output = dispatch_gemini_rest(prompt, model, review, timeout)
        if ok:
            return True, output
        # On REST failure, log and fall through to CLI/OAuth path.
        if _is_rate_limited(output):
            print("Gemini REST rate-limited (free-tier 1000/day or quota) — falling back to OAuth via CLI",
                  file=sys.stderr)
        else:
            print(f"Gemini REST failed ({output[:120]}) — falling back to OAuth via CLI",
                  file=sys.stderr)

    for attempt in range(max_retries):
        ok, output = dispatch_gemini(prompt, model, review, timeout, mcp,
                                     use_subscription=use_subscription)
        if ok:
            return True, output

        # Check for rate limit
        if _is_rate_limited(output):
            # If we're still on the API-key path, flip to subscription and
            # retry immediately *without consuming the retry budget*. This
            # guarantees that even callers with max_retries=1 get one attempt
            # on the OAuth tier (independent quota).
            if not use_subscription:
                print("Gemini API-key rate-limited — switching to subscription (OAuth) path",
                      file=sys.stderr)
                use_subscription = True
                ok, output = dispatch_gemini(prompt, model, review, timeout, mcp,
                                             use_subscription=True)
                if ok:
                    return True, output
                # Subscription also failed. If it was a rate-limit, fall through
                # to the backoff branch below. Otherwise, fall through to the
                # timeout / fallback-model / failure branches.

        if _is_rate_limited(output):
            # At this point we're on subscription — either because the caller
            # forced it, or because we just flipped. Apply exponential backoff.
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"Rate limited on subscription (attempt {attempt + 1}/{max_retries}). Waiting {delay}s...",
                      file=sys.stderr)
                time.sleep(delay)
                continue
            # All retries exhausted on the primary model — last-ditch try the
            # fallback model on subscription. If gemini-3.1-pro-preview is
            # capacity-out, gemini-3-flash-preview often still answers.
            # Reviews use GEMINI_REVIEW_FALLBACK_MODEL (explicit, never "auto")
            # to avoid silently picking gemini-2.5-flash for verdicts.
            fallback = GEMINI_REVIEW_FALLBACK_MODEL if review else GEMINI_FALLBACK_MODEL
            if model != fallback:
                print(f"Rate-limit retries exhausted on {model} — last-ditch on fallback model {fallback} (subscription)",
                      file=sys.stderr)
                ok, output = dispatch_gemini(prompt, fallback, review, timeout, mcp,
                                             use_subscription=True)
                if ok:
                    return True, output
            return False, output

        # Timeout — don't retry, just fail (Gemini is slow, not broken)
        if output == "TIMEOUT":
            return False, output

        # Non-rate-limit, non-timeout failure — try fallback model once
        if model != GEMINI_FALLBACK_MODEL:
            print(f"Retrying with fallback model: {GEMINI_FALLBACK_MODEL}", file=sys.stderr)
            return dispatch_gemini(prompt, GEMINI_FALLBACK_MODEL, review, timeout, mcp,
                                   use_subscription=use_subscription)

        return False, output

    return False, output


_CLAUDE_TEXT_ONLY_DISALLOWED = (
    "Bash,Edit,Write,NotebookEdit,Skill,Agent,Task,ExitPlanMode"
)
"""Tool list passed to ``--disallowedTools`` when ``tools_disabled=True``.

Claude in print mode (``-p``) defaults to allowing the full built-in
tool set. Given an agentic prompt and a writable cwd it will use
Edit/Write to modify files in cwd and return only a summary on stdout —
which is fatal for the v2 quality pipeline writer/reviewer paths, where
the pipeline expects the rewritten module markdown on stdout (see the
k8s-capa-module-1.2-argo-events smoke autopsy).

``Task`` (sub-agent invocation) is also disallowed — without it Claude
delegated rewrites to a subagent that wrote to a separate context, then
summarized in stdout (observed twice on
ai-ai-building-module-1.2-models-apis-context-structured-output: 8 min
of internal work, ~1 KB summary out, classic "the module above" prose).

``WebFetch`` and ``WebSearch`` STAY ENABLED (removed from this list
2026-05-05). Original blanket ban was collateral damage — it stopped
agentic file mutation but also blinded the reviewer to fact errors
(hallucinated CIS recs, fake kube-bench flags, dead Sources URLs).
The v2 reviewer needs web access to do its job; without it, factual
hallucinations from the writer pass through every cross-family review.

Read-only tools (Read, Glob, Grep, TodoWrite) stay enabled —
empirically Claude needs them to plan output without hanging. With ALL
tools blocked (including Read/Glob/Grep) the writer prompt produced
zero stdout for 900s before timing out; with only mutating + external +
sub-agent tools blocked it returns the full ~80KB module markdown.
"""


def dispatch_claude(prompt: str, model: str = CLAUDE_DEFAULT_MODEL,
                    timeout: int = 600, mcp: bool = False,
                    tools_disabled: bool = False) -> tuple[bool, str]:
    """Call Claude CLI directly. Returns (success, output).

    ``tools_disabled=True`` forces Claude to return all output via stdout
    (no Edit/Write/Bash/etc.) by passing a comprehensive
    ``--disallowedTools`` list. Required for the v2 writer/reviewer
    paths — without it Claude treats the prompt agentically and modifies
    files in cwd, returning only a summary on stdout.

    Raises:
        ClaudeUnavailableError: during weekday 14:00-20:00 local peak-hours
            (2x pricing), when the per-process call budget is exhausted, or
            on terminal rate-limit / quota errors. The pipeline catches this
            and pauses the affected module so it can resume on the next run.
    """
    global _claude_call_count

    if _is_claude_peak_hours():
        hour = datetime.now().hour
        msg = (
            f"Claude peak hours in effect ({_CLAUDE_PEAK_START_HOUR}:00-"
            f"{_CLAUDE_PEAK_END_HOUR}:00 local Mon-Fri, currently {hour:02d}:xx). "
            f"Refusing to dispatch to avoid 2x pricing. "
            f"Set KUBEDOJO_IGNORE_PEAK_HOURS=1 to override."
        )
        print(f"⏸ {msg}", file=sys.stderr)
        raise ClaudeUnavailableError(msg)

    _check_claude_budget()

    cmd = [
        "npx", "@anthropic-ai/claude-code@latest", "-p",
        "--model", model,
        "--output-format", "text",
    ]
    if mcp and MCP_CONFIG.exists():
        cmd.extend([
            "--mcp-config", str(MCP_CONFIG),
            "--allowedTools", CLAUDE_TRANSLATION_TOOLS,
        ])
    elif tools_disabled:
        cmd.extend(["--disallowedTools", _CLAUDE_TEXT_ONLY_DISALLOWED])

    t0 = time.time()

    try:
        result = _run_with_process_group(
            cmd, prompt, timeout, str(REPO_ROOT), _agent_env("claude")
        )
        elapsed = time.time() - t0
        if result.returncode != 0:
            print(f"Claude error (exit {result.returncode}): {redact_text(result.stderr)[:500]}", file=sys.stderr)
            _log("claude", model, prompt, "", False, elapsed, result.stderr)
            # Escalate rate-limit / quota failures so the pipeline can pause
            # the module instead of treating it as a generic write failure.
            if _is_rate_limited(result.stderr) or _is_rate_limited(result.stdout):
                raise ClaudeUnavailableError(
                    f"Claude rate-limited or quota exhausted: {redact_text(result.stderr)[:200]}"
                )
            return False, redact_text(result.stderr)
        output = result.stdout.strip()
        _claude_call_count += 1
        _log("claude", model, prompt, output, True, elapsed)
        budget = _claude_call_budget()
        print(f"  Claude call {_claude_call_count}/{budget} used", file=sys.stderr)
        return True, output

    except FileNotFoundError:
        _log("claude", model, prompt, "", False, time.time() - t0, "CLI not found")
        print("claude CLI not found.", file=sys.stderr)
        return False, ""
    except subprocess.TimeoutExpired:
        _log("claude", model, prompt, "", False, time.time() - t0, "TIMEOUT")
        print(f"Claude timed out after {timeout}s", file=sys.stderr)
        return False, ""


def dispatch_codex(prompt: str, model: str = CODEX_DEFAULT_MODEL,
                   timeout: int = 900) -> tuple[bool, str]:
    """Call Codex CLI directly via `codex exec`. Returns (success, output).

    Reads prompt from stdin, skips git repo check.

    Environment overrides (default off — preserves prior read-only / no-search
    behavior for callers that only need text reasoning):

    - ``KUBEDOJO_CODEX_SEARCH=1`` enables ``--search`` (live web). Required for
      writer dispatches that produce factual content (#388 module rewrites,
      anything quoting CLI flags or version-specific behavior).
    - ``KUBEDOJO_CODEX_SANDBOX`` overrides the sandbox mode. Valid values:
      ``read-only`` (default), ``workspace-write``, ``danger-full-access``.
      Use ``danger-full-access`` for dispatches that commit + push inside the
      codex run (workspace-write blocks ``.git/worktrees/.../index.lock`` and
      ``api.github.com``; see ``feedback_codex_danger_for_git_gh.md``).

    On rate-limit or quota errors, returns (False, stderr) so the caller can
    react (see run_module review branch, which degrades gracefully).
    """
    sandbox = os.environ.get("KUBEDOJO_CODEX_SANDBOX", "read-only")
    use_search = os.environ.get("KUBEDOJO_CODEX_SEARCH", "0") == "1"

    cmd = [CODEX_CLI]
    if use_search:
        cmd.append("--search")
    cmd.extend(["exec", "--skip-git-repo-check", "--sandbox", sandbox])
    # Allow caller to pin a model (e.g. "codex-gpt-5"); "codex" alone means default.
    if model and model != "codex":
        cmd.extend(["-m", model])

    t0 = time.time()
    try:
        result = _run_with_process_group(
            cmd, prompt, timeout, str(REPO_ROOT), _agent_env("codex")
        )
        elapsed = time.time() - t0
        output = result.stdout.strip()
        stderr = result.stderr or ""

        if result.returncode != 0:
            # Check if it was a rate limit / quota issue so caller can degrade
            rate_limited = _is_rate_limited(output + "\n" + stderr)
            tag = "RATE_LIMIT" if rate_limited else redact_text(stderr)[:500]
            print(f"Codex error (exit {result.returncode}): {tag}", file=sys.stderr)
            _log("codex", model, prompt, output, False, elapsed, tag)
            return False, redact_text(output if output else stderr)

        _log("codex", model, prompt, output, True, elapsed)
        return True, output

    except FileNotFoundError:
        _log("codex", model, prompt, "", False, time.time() - t0, "CLI not found")
        print("codex CLI not found. Install: https://github.com/openai/codex", file=sys.stderr)
        return False, ""
    except subprocess.TimeoutExpired:
        _log("codex", model, prompt, "", False, time.time() - t0, "TIMEOUT")
        print(f"Codex timed out after {timeout}s", file=sys.stderr)
        return False, "TIMEOUT"


def dispatch_codex_review(prompt: str, model: str = CODEX_REVIEW_DEFAULT_MODEL,
                          timeout: int = 900, use_search: bool = False) -> tuple[bool, str]:
    """Call Codex review via `codex exec --sandbox read-only`.

    ``use_search`` enables `--search` only for checks that need live web
    verification (FACT_CHECK in the deep-review batch). Simple checks do
    not need search and paying for it on every call wastes latency/budget.
    """
    cmd = [CODEX_CLI]
    if use_search:
        cmd.append("--search")
    cmd.extend(["exec", "--skip-git-repo-check", "--sandbox", "read-only"])
    if model and model != "codex":
        cmd.extend(["-m", model])

    t0 = time.time()
    try:
        result = _run_with_process_group(
            cmd, prompt, timeout, str(REPO_ROOT), _agent_env("codex")
        )
        elapsed = time.time() - t0
        output = result.stdout.strip()
        stderr = result.stderr or ""

        if result.returncode != 0:
            rate_limited = _is_rate_limited(output + "\n" + stderr)
            tag = "RATE_LIMIT" if rate_limited else redact_text(stderr)[:500]
            print(f"Codex review error (exit {result.returncode}): {tag}", file=sys.stderr)
            _log("codex-review", model, prompt, output, False, elapsed, tag)
            return False, redact_text(output if output else stderr)

        _log("codex-review", model, prompt, output, True, elapsed)
        return True, output

    except FileNotFoundError:
        _log("codex-review", model, prompt, "", False, time.time() - t0, "CLI not found")
        print("codex CLI not found. Install: https://github.com/openai/codex", file=sys.stderr)
        return False, ""
    except subprocess.TimeoutExpired:
        _log("codex-review", model, prompt, "", False, time.time() - t0, "TIMEOUT")
        print(f"Codex review timed out after {timeout}s", file=sys.stderr)
        return False, "TIMEOUT"


def dispatch_codex_patch(prompt: str, model: str = CODEX_PATCH_DEFAULT_MODEL,
                         timeout: int = 1200) -> tuple[bool, str]:
    """Call Codex patch via `codex exec`.

    Codex returns a JSON edit list. `patch_worker.py` applies the edits in
    Python (`apply_review_edits` → `_atomic_write_text`), so Codex itself
    needs no write capability — read-only sandbox is the right default.

    Environment overrides (default off — preserves prior read-only / no-search
    behavior for callers that don't need to verify cited URLs or version-gated
    behavior while applying review edits):

    - ``KUBEDOJO_CODEX_SEARCH=1`` enables ``--search`` (live web). Useful when
      the review verdict cites URLs or version-specific facts the patcher
      needs to confirm before rewriting prose around them.
    - ``KUBEDOJO_CODEX_SANDBOX`` overrides the sandbox mode. Same valid values
      and rationale as ``dispatch_codex``; default ``read-only`` is correct
      for the patcher because edits are applied in Python downstream.
    """
    sandbox = os.environ.get("KUBEDOJO_CODEX_SANDBOX", "read-only")
    use_search = os.environ.get("KUBEDOJO_CODEX_SEARCH", "0") == "1"

    cmd = [CODEX_CLI]
    if use_search:
        cmd.append("--search")
    cmd.extend(["exec", "--skip-git-repo-check", "--sandbox", sandbox])
    if model:
        cmd.extend(["-m", model])

    t0 = time.time()
    try:
        result = _run_with_process_group(
            cmd, prompt, timeout, str(REPO_ROOT), _agent_env("codex")
        )
        elapsed = time.time() - t0
        output = result.stdout.strip()
        stderr = result.stderr or ""

        if result.returncode != 0:
            rate_limited = _is_rate_limited(output + "\n" + stderr)
            tag = "RATE_LIMIT" if rate_limited else redact_text(stderr)[:500]
            print(f"Codex patch error (exit {result.returncode}): {tag}", file=sys.stderr)
            _log("codex-patch", model, prompt, output, False, elapsed, tag)
            return False, redact_text(output if output else stderr)

        _log("codex-patch", model, prompt, output, True, elapsed)
        return True, output

    except FileNotFoundError:
        _log("codex-patch", model, prompt, "", False, time.time() - t0, "CLI not found")
        print("codex CLI not found. Install: https://github.com/openai/codex", file=sys.stderr)
        return False, ""
    except subprocess.TimeoutExpired:
        _log("codex-patch", model, prompt, "", False, time.time() - t0, "TIMEOUT")
        print(f"Codex patch timed out after {timeout}s", file=sys.stderr)
        return False, "TIMEOUT"


def post_to_github(issue_num: int, content: str, model: str) -> bool:
    """Post review content to a GitHub issue as comment(s)."""
    if not content:
        return False

    chunks = _split_content(redact_text(content))
    total = len(chunks)

    for i, chunk in enumerate(chunks, start=1):
        if total > 1:
            body = f"**[Part {i}/{total}]** Review ({model})\n\n{chunk}"
        else:
            body = f"**Review** ({model})\n\n{chunk}"

        try:
            result = subprocess.run(
                ["gh", "issue", "comment", str(issue_num), "-F", "-"],
                input=redact_text(body), text=True, capture_output=True, timeout=15,
            )
            if result.returncode != 0:
                print(f"GitHub comment failed: {redact_text(result.stderr)[:200]}", file=sys.stderr)
                return False
        except FileNotFoundError:
            print("gh CLI not found — skipping GitHub posting", file=sys.stderr)
            return False
        except subprocess.TimeoutExpired:
            print("GitHub posting timed out", file=sys.stderr)
            return False

    print(f"Review posted to #{issue_num} ({total} part{'s' if total > 1 else ''})")
    return True


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def _log(agent: str, model: str, prompt: str, output: str, ok: bool,
         duration_s: float, stderr: str = "") -> Path:
    """Write a JSON log entry. Returns the log file path."""
    LOG_DIR.mkdir(exist_ok=True)
    ts = datetime.now(UTC)
    slug = ts.strftime("%Y%m%d-%H%M%S")
    log_file = LOG_DIR / f"{slug}-{agent}.json"

    entry = {
        "timestamp": ts.isoformat(),
        "agent": agent,
        "model": model,
        "success": ok,
        "duration_s": round(duration_s, 1),
        "prompt_chars": len(prompt),
        "output_chars": len(output),
        "prompt": redact_text(prompt)[:5000] + ("..." if len(prompt) > 5000 else ""),
        "output": redact_text(output)[:10000] + ("..." if len(output) > 10000 else ""),
    }
    if stderr:
        entry["stderr"] = redact_text(stderr)[:2000]

    log_file.write_text(json.dumps(entry, indent=2, ensure_ascii=False))
    return log_file


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _stream_with_timeout(proc, timeout: int, quiet: bool = False) -> tuple[list[str], bool]:
    """Stream stdout lines, kill if timeout exceeded. Returns (lines, timed_out)."""
    output_lines: list[str] = []
    timed_out = False

    if timeout:
        def _kill():
            nonlocal timed_out
            timed_out = True
            _kill_process_tree(proc)

        timer = threading.Timer(timeout, _kill)
        timer.daemon = True
        timer.start()
    else:
        timer = None

    try:
        for line in proc.stdout:
            if not quiet:
                print(line, end="")
                sys.stdout.flush()
            output_lines.append(line)
    except (OSError, ValueError):
        pass

    if timer:
        timer.cancel()

    return output_lines, timed_out


def _gemini_quiet_mode_enabled() -> bool:
    """Suppress Gemini stdout streaming during pipeline runs by default."""
    return (
        os.environ.get("KUBEDOJO_QUIET", "") == "1"
        or os.environ.get("KUBEDOJO_PIPELINE", "") == "1"
    )


def _kill_process_tree(proc) -> None:
    """Terminate a subprocess and any children left behind by CLI wrappers."""
    pid = getattr(proc, "pid", None)
    try:
        if pid:
            killed_processes = []
            killed_parent = False
            try:
                parent = psutil.Process(pid)
                descendants = parent.children(recursive=True)
                for child in descendants:
                    try:
                        child.kill()
                        killed_processes.append(child)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                try:
                    parent.kill()
                    killed_processes.append(parent)
                    killed_parent = True
                except psutil.NoSuchProcess:
                    pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

            if killed_processes:
                psutil.wait_procs(killed_processes, timeout=1)

            try:
                os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except OSError:
                if not killed_parent:
                    proc.kill()
            return

        proc.kill()
    except OSError:
        pass


def _run_with_process_group(cmd, prompt: str, timeout: int,
                            cwd: str, env: dict) -> subprocess.CompletedProcess:
    """Run ``cmd`` in its own session/process group so timeout cleanup reaches
    any grandchildren spawned by CLI wrappers (e.g. codex → node subprocesses).

    Raises ``subprocess.TimeoutExpired`` on timeout, after killing the whole
    process group.
    """
    with subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=cwd,
        env=env,
        start_new_session=True,
    ) as proc:
        try:
            stdout, stderr = proc.communicate(input=prompt, timeout=timeout)
        except subprocess.TimeoutExpired:
            _kill_process_tree(proc)
            try:
                proc.communicate()
            except (OSError, ValueError):
                pass
            raise
        return subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)


def _split_content(content: str, limit: int = GH_CHAR_LIMIT) -> list[str]:
    """Split content into chunks at newline boundaries."""
    chunks = []
    pos = 0
    length = len(content)
    while pos < length:
        end = min(pos + limit, length)
        if end >= length:
            chunks.append(content[pos:])
            break
        split_at = content.rfind("\n", pos, end)
        if split_at <= pos:
            split_at = end
        chunks.append(content[pos:split_at])
        pos = split_at + (1 if split_at < length and content[split_at] == "\n" else 0)
    return chunks


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Direct CLI dispatch for Gemini/Claude — V2 with rate limiting + MCP",
    )
    subparsers = parser.add_subparsers(dest="agent", help="Target agent")

    # gemini
    gp = subparsers.add_parser("gemini", help="Dispatch prompt to Gemini CLI")
    gp.add_argument("prompt", help="Prompt text (use '-' to read from stdin)")
    gp.add_argument("--model", default=None, help=f"Gemini model (default: {GEMINI_REVIEW_MODEL} when --review else {GEMINI_DEFAULT_MODEL})")
    gp.add_argument("--review", action="store_true", help="Prepend KubeDojo review context")
    gp.add_argument("--mcp", action="store_true", help="Enable RAG MCP tools (for translations)")
    gp.add_argument("--github", type=int, metavar="ISSUE", help="Post output to GitHub issue")
    gp.add_argument("--retry", type=int, default=3, help="Max retries on rate limit (default: 3)")
    gp.add_argument("--timeout", type=int, default=900, help="Timeout in seconds (default: 900)")

    # claude
    cp = subparsers.add_parser("claude", help="Dispatch prompt to Claude CLI")
    cp.add_argument("prompt", help="Prompt text (use '-' to read from stdin)")
    cp.add_argument("--model", default=CLAUDE_DEFAULT_MODEL, help=f"Claude model (default: {CLAUDE_DEFAULT_MODEL})")
    cp.add_argument("--mcp", action="store_true", help="Enable RAG MCP tools (for translations)")
    cp.add_argument("--no-tools", dest="tools_disabled", action="store_true",
                    help="Force Claude to return text only (disables Edit/Write/Bash/etc.). "
                         "Use for v2 quality writer/reviewer dispatches where stdout = full module text.")
    cp.add_argument("--timeout", type=int, default=600, help="Timeout in seconds (default: 600)")

    # codex
    xp = subparsers.add_parser("codex", help="Dispatch prompt to Codex CLI (codex exec)")
    xp.add_argument("prompt", help="Prompt text (use '-' to read from stdin)")
    xp.add_argument("--model", default=CODEX_DEFAULT_MODEL,
                    help=f"Codex model (default: {CODEX_DEFAULT_MODEL!r}; pass 'codex' to use CLI default)")
    xp.add_argument("--no-tools", dest="tools_disabled", action="store_true",
                    help="Accepted for symmetry with --no-tools on claude. Codex already runs "
                         "with --sandbox read-only so the flag is a no-op (file writes are blocked "
                         "via the sandbox; pure-text output is the natural mode).")
    xp.add_argument("--timeout", type=int, default=900, help="Timeout in seconds (default: 900)")

    # logs
    lp = subparsers.add_parser("logs", help="Show recent dispatch logs")
    lp.add_argument("-n", type=int, default=10, help="Number of entries (default: 10)")
    lp.add_argument("--full", action="store_true", help="Show full prompt/output (not truncated)")
    lp.add_argument("--id", dest="log_id", help="Show a specific log file by timestamp prefix")

    args = parser.parse_args()

    if not args.agent:
        parser.print_help()
        sys.exit(1)

    if args.agent == "gemini":
        prompt = sys.stdin.read() if args.prompt == "-" else args.prompt
        chosen_model = args.model or (GEMINI_REVIEW_MODEL if args.review else GEMINI_DEFAULT_MODEL)
        ok, output = dispatch_gemini_with_retry(
            prompt, chosen_model, args.review, args.retry, args.timeout, args.mcp,
        )
        if ok and args.github:
            post_to_github(args.github, output, chosen_model)
        if ok:
            print(output)
        sys.exit(0 if ok else 1)

    elif args.agent == "claude":
        prompt = sys.stdin.read() if args.prompt == "-" else args.prompt
        ok, output = dispatch_claude(
            prompt, args.model, args.timeout, args.mcp,
            tools_disabled=getattr(args, "tools_disabled", False),
        )
        if ok:
            print(output)
        sys.exit(0 if ok else 1)

    elif args.agent == "codex":
        prompt = sys.stdin.read() if args.prompt == "-" else args.prompt
        ok, output = dispatch_codex(prompt, args.model, args.timeout)
        if ok:
            print(output)
        sys.exit(0 if ok else 1)

    elif args.agent == "logs":
        _show_logs(args.n, args.full, args.log_id)


def _show_logs(n: int, full: bool, log_id: str | None):
    """Show recent dispatch logs."""
    if not LOG_DIR.exists():
        print("No logs yet.")
        return

    if log_id:
        matches = sorted(LOG_DIR.glob(f"{log_id}*.json"))
        if not matches:
            print(f"No log matching '{log_id}'")
            return
        for m in matches:
            entry = json.loads(m.read_text())
            print(json.dumps(entry, indent=2, ensure_ascii=False))
        return

    logs = sorted(LOG_DIR.glob("*.json"), reverse=True)[:n]
    if not logs:
        print("No logs yet.")
        return

    for log_file in reversed(logs):
        entry = json.loads(log_file.read_text())
        status = "OK" if entry["success"] else "FAIL"
        prompt_preview = entry["prompt"][:80].replace("\n", " ")
        if not full:
            print(f"  {entry['timestamp'][:19]}  {entry['agent']:6s}  {status:4s}  "
                  f"{entry['duration_s']:6.1f}s  {entry['prompt_chars']:>6} -> {entry['output_chars']:>6} chars  "
                  f"{prompt_preview}...")
        else:
            print(f"\n{'='*60}")
            print(json.dumps(entry, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
