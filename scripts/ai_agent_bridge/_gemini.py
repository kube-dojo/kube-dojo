"""Gemini interaction: ask_gemini and process_and_respond (decomposed).

Phase 4 of #1184: the subprocess path in _run_gemini_attempt was migrated
onto scripts.agent_runtime.runner.invoke(). The legacy _stream_with_watchdog
helper is preserved (and still used by the fire-and-forget Popen path for
output-path callers) but the core subprocess block now routes through the
runtime. The runtime owns stall detection, rate-limit classification, and
usage logging uniformly across agents.
"""

import atexit
import subprocess
import sys
import time
from pathlib import Path

from agent_runtime.errors import (
    AgentStalledError,
    AgentTimeoutError,
    AgentUnavailableError,
    RateLimitedError,
)
from agent_runtime.runner import invoke as runtime_invoke

from ._broker import (
    _git_status_snapshot,
    _is_task_locked,
    _remove_pid_file,
    _validate_file_writes,
    _write_pid_file,
)
from ._config import (
    _MODEL_CACHE,
    _MODEL_CACHE_TTL,
    _PARENT_ENV,
    GEMINI_DEFAULT_MODEL,
    GEMINI_FALLBACK_MODEL,
    PYTHON_CMD,
    REPO_ROOT,
)
from ._github import _post_review_to_github
from ._messaging import (
    _extract_issue_number,
    acknowledge,
    get_conversation_context,
    read_message,
    send_message,
    send_to_gemini,
)
from ._model import _detect_model_error, check_model
from ._prompts import build_gemini_prompt

try:
    from dispatch import GEMINI_WRITER_MODEL
except ImportError:  # pragma: no cover - package import path variant
    GEMINI_WRITER_MODEL = _PARENT_ENV.get("KUBEDOJO_WRITER_MODEL", "gemini-3.1-pro-preview")


def converse_gemini(content: str, task_id: str, model: str = GEMINI_WRITER_MODEL,
                    skip_github: bool = False):
    """Multi-turn conversation with Gemini. Includes conversation history in prompt.

    Each call adds to the conversation thread (via task_id) and Gemini sees
    all previous messages for context.
    """
    history, msg_count = get_conversation_context(task_id)

    if history:
        full_content = (
            f"## Conversation History\n\n{history}\n\n"
            f"===\n\n## Current Message\n\n{content}"
        )
        print(f"📜 Conversation '{task_id}' — turn {msg_count + 1}")
    else:
        full_content = content
        print(f"📜 Starting conversation '{task_id}'")

    return ask_gemini(
        full_content, task_id=task_id, msg_type="query",
        model=model, skip_github=skip_github,
    )


def ask_gemini(content: str, task_id: str | None = None, msg_type: str = "query",
               data: str | None = None, model: str = GEMINI_DEFAULT_MODEL,
               from_model: str | None = None, async_mode: bool = False,
               stdout_only: bool = False, output_path: str | None = None,
               extract_tags: list | None = None, skip_model_check: bool = False,
               allow_write: bool = False, delimiters: str | None = None,
               skip_github: bool = False):
    """Send message to Gemini AND optionally invoke Gemini to process it."""
    # Model cache management
    if skip_model_check and model in _MODEL_CACHE:
        del _MODEL_CACHE[model]
    elif not async_mode and model in _MODEL_CACHE:
        available, cached_at = _MODEL_CACHE[model]
        if not available:
            age = time.time() - cached_at
            if age < _MODEL_CACHE_TTL:
                if model == GEMINI_FALLBACK_MODEL:
                    print(f"❌ Model '{model}' was unavailable {int(age)}s ago (cached). Skipping.")
                    print("💡 To switch accounts: run 'gemini auth login' or ask the user to switch.")
                    print("   To retry: --skip-model-check (clears cache)")
                    return None
                print(
                    f"⚠️  Model '{model}' was unavailable {int(age)}s ago "
                    f"(cached); falling back to '{GEMINI_FALLBACK_MODEL}'."
                )
                model = GEMINI_FALLBACK_MODEL

    # Auto-enable async for handoff type
    if msg_type == "handoff":
        async_mode = True
        print("ℹ️  Async mode auto-enabled for handoff (complex task)")

    # Warn if handoff message is too long
    _warn_long_handoff(content, msg_type, task_id)

    model = _resolve_gemini_model(model, async_mode, skip_model_check)

    # Send the message
    msg_id = _send_gemini_message(content, task_id, msg_type, data, from_model, model,
                                  stdout_only, output_path)

    # Invoke Gemini or queue
    if async_mode:
        print(f"\n📥 Message #{msg_id} queued for Gemini (async mode - no immediate invocation)")
        print("   Gemini will see this in his inbox when he starts a session.")
        print(f"   To trigger manually: .venv/bin/python scripts/ai_agent_bridge/__main__.py process {msg_id}")
    else:
        if not stdout_only:
            print(f"\n🚀 Invoking Gemini to process message #{msg_id}...")
        response = process_and_respond(msg_id, model, stdout_only=stdout_only,
                                       output_path=output_path, allow_write=allow_write,
                                       delimiters=delimiters, skip_github=skip_github)

        # Post-process: extract delimited content
        if extract_tags is not None and response:
            _extract_and_print(response, extract_tags)

    return msg_id


def _resolve_gemini_model(model: str, async_mode: bool, skip_model_check: bool) -> str:
    """Return an available Gemini model, falling back before sync invocation."""
    if async_mode or skip_model_check or model == GEMINI_FALLBACK_MODEL:
        return model
    if check_model(model):
        return model
    print(
        f"⚠️  Gemini model '{model}' is unavailable; "
        f"falling back to '{GEMINI_FALLBACK_MODEL}'."
    )
    return GEMINI_FALLBACK_MODEL


def _warn_long_handoff(content: str, msg_type: str, task_id: str | None):
    """Warn if handoff message is too long."""
    HANDOFF_WARNING_THRESHOLD = 500
    issue_num = _extract_issue_number(task_id) if task_id else None
    if msg_type == "handoff" and len(content) > HANDOFF_WARNING_THRESHOLD and issue_num:
        print(f"⚠️  WARNING: Handoff message is {len(content)} chars (>{HANDOFF_WARNING_THRESHOLD})")
        print("   For task handoffs, the GitHub issue should contain details.")
        print("   Consider sending a SHORT message with issue reference only:")
        print(f"   'Issue #{issue_num} is assigned to you. Read it for details.'")
        print()


def _send_gemini_message(content, task_id, msg_type, data, from_model, model,
                         stdout_only, output_path):
    """Send the message and handle pre-acknowledgement."""
    if output_path:
        msg_id = send_to_gemini(content, task_id, msg_type, data,
                                from_model=from_model, to_model=model, quiet=stdout_only)
        acknowledge(msg_id, quiet=stdout_only)
        if not stdout_only:
            print("   Pre-acknowledged (file output mode — no broker traffic)")
    else:
        msg_id = send_to_gemini(content, task_id, msg_type, data,
                                from_model=from_model, to_model=model, quiet=stdout_only)
        if stdout_only:
            acknowledge(msg_id, quiet=stdout_only)
    return msg_id


def _extract_and_print(response: str, extract_tags: list):
    """Extract delimited content from response and print it."""
    from gemini_output import ALL_TAGS, find_complete_pairs
    from gemini_output import extract_delimited as _extract
    tags = extract_tags if extract_tags else find_complete_pairs(response, ALL_TAGS)
    if tags:
        print(f"\n{'═' * 40}")
        print(f"EXTRACTED ({', '.join(tags)}):")
        print(f"{'═' * 40}")
        for tag in tags:
            extracted = _extract(response, tag)
            if extracted is not None:
                print(f"\n--- {tag} ---")
                print(extracted)
        print(f"\n{'═' * 40}")
    else:
        print("\n⚠️  No complete delimiter pairs found in output.")


def process_and_respond(message_id: int, model: str = GEMINI_DEFAULT_MODEL,
                        fire_and_forget: bool = False, no_timeout: bool = False,
                        stdout_only: bool = False, output_path: str | None = None,
                        allow_write: bool = False, delimiters: str | None = None,
                        skip_github: bool = False):
    """Read message, process with Gemini CLI, send response.

    Runs in sync mode by default (15 min timeout). On any failure, sends an
    error message back to the sender and always cleans up the PID file.
    """
    msg = read_message(message_id, quiet=stdout_only)
    if not msg:
        return

    prompt = build_gemini_prompt(msg, stdout_only, output_path, allow_write, delimiters)

    if fire_and_forget:
        _launch_gemini_background(msg, message_id, model, prompt)
    else:
        return _run_gemini_sync(msg, message_id, model, prompt, no_timeout, stdout_only,
                                output_path, allow_write, skip_github)


def _launch_gemini_background(msg: dict, message_id: int, model: str, prompt: str):
    """Launch the bridge itself as a background process (fire-and-forget mode)."""
    task_key = msg['task_id'] or str(message_id)

    if _is_task_locked("gemini", task_key):
        print(f"⏸️  Task '{task_key}' is already being processed by another Gemini bridge. Skipping.")
        return

    log_dir = REPO_ROOT / ".mcp/servers/message-broker/logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"gemini-{task_key}.log"

    print("\n🚀 Launching bridge in background (no timeout)...")
    print(f"   Log: {log_file}")
    print("   Bridge will capture Gemini's response and route it when done.")

    try:
        bridge_cmd = [
            PYTHON_CMD, str(Path(__file__).parent / "__main__.py"),
            "process", str(message_id),
            "--model", model,
            "--no-timeout"
        ]
        lf = open(log_file, "w")  # noqa: SIM115 — fd passed to Popen, closed after
        proc = subprocess.Popen(
            bridge_cmd,
            stdout=lf,
            stderr=subprocess.STDOUT,
            cwd=str(REPO_ROOT),
            env=_PARENT_ENV,
            start_new_session=True
        )
        lf.close()
        print(f"   PID: {proc.pid}")

        _write_pid_file("gemini", task_key, {
            "message_id": message_id,
            "task_id": msg.get('task_id'),
            "model": model,
            "mode": "fire-and-forget",
        }, pid=proc.pid)

    except FileNotFoundError:
        print("❌ Python or bridge script not found")


def _run_gemini_sync(msg: dict, message_id: int, model: str, prompt: str,
                     no_timeout: bool, stdout_only: bool, output_path: str | None,
                     allow_write: bool, skip_github: bool):
    """Run Gemini synchronously with streaming output and retry logic."""
    task_key = msg.get('task_id') or str(message_id)
    timeout_val = None if no_timeout else 1800
    mode_label = "no-timeout" if no_timeout else "sync, 30 min timeout"

    if _is_task_locked("gemini", task_key):
        print(f"⏸️  Task '{task_key}' is already being processed by another Gemini bridge. Skipping.")
        return

    if not stdout_only:
        print(f"\n🤖 Processing with Gemini ({model}) [{mode_label}]...")
        sys.stdout.flush()

    _write_pid_file("gemini", task_key, {
        "message_id": message_id,
        "task_id": msg.get('task_id'),
        "model": model,
        "mode": mode_label,
    })
    atexit.register(_remove_pid_file, "gemini", task_key)

    max_retries = 5
    base_delay = 30
    _response_sent = False

    try:
        for attempt in range(max_retries):
            result = _run_gemini_attempt(msg, message_id, model, prompt, timeout_val,
                                         stdout_only, output_path, skip_github, attempt,
                                         max_retries, base_delay)
            if result is None:
                continue  # Retry (rate limited)
            if result is False:
                return  # Fatal error, stop
            # result is (response, response_sent)
            response, sent = result
            _response_sent = sent
            return response
    finally:
        if not _response_sent:
            _send_gemini_error(msg, message_id)
        _remove_pid_file("gemini", task_key)


def _run_gemini_attempt(msg, message_id, model, prompt, timeout_val, stdout_only,
                        output_path, skip_github, attempt, max_retries, base_delay):
    """Run a single Gemini CLI attempt via agent_runtime.

    Returns None to retry, False to stop, or (response, sent).

    Phase 4: routes through runtime_invoke() instead of direct Popen.
    The runtime handles stall detection, hard timeout, and rate-limit
    classification. The retry loop stays here because it's higher-level
    policy (multiple attempts with backoff).
    """
    prompt_preview = prompt[:200].replace('\n', ' ')
    print(f"  [gemini] attempt {attempt+1}/{max_retries}, model={model}, "
          f"prompt={len(prompt)} chars: {prompt_preview}...", flush=True)

    pre_snapshot = None
    if output_path:
        pre_snapshot = _git_status_snapshot()

    # Gemini bridge is always write-enabled (--approval-mode=yolo) — preserving
    # legacy behavior. Tool config is None because the bridge doesn't restrict
    # MCP tools the way dispatch.py does.
    try:
        result = runtime_invoke(
            "gemini",
            prompt,
            mode="workspace-write",
            cwd=REPO_ROOT,
            model=model,
            task_id=msg.get("task_id"),
            session_id=None,  # Gemini CLI has no --resume; bridge multi-turn
                              # is handled via conversation context injection
                              # in the prompt builder, not CLI-level resume.
            tool_config=None,
            entrypoint="bridge",
            hard_timeout=max(timeout_val or 1800, 300),
            # 600s matches dispatch.py. Gemini block-buffers stdout when
            # not a TTY and can stay silent 5+ min during reasoning; the
            # mtime poller on ~/.gemini/tmp/<project>/{logs.json, chats/}
            # catches real activity, so this ceiling only fires on
            # genuinely dead processes. Raised from 180s on 2026-04-10
            # after a successful 319s skeleton was killed at 181s. (#1184)
            stall_timeout=min(600, timeout_val or 600),
        )
    except RateLimitedError as exc:
        # Rate-limited: treat as retryable per legacy behavior
        print(f"\n⏳ Gemini rate limited: {exc}")
        retry_result = _handle_gemini_error(str(exc), model, attempt, max_retries, base_delay)
        if retry_result == "retry":
            return None
        return False
    except AgentStalledError as exc:
        print(f"\n❌ Gemini stalled: {exc}")
        return False
    except AgentTimeoutError as exc:
        print(f"\n❌ Gemini CLI timed out ({timeout_val}s sync limit): {exc}")
        return False
    except AgentUnavailableError as exc:
        print(f"❌ gemini CLI not available: {exc}")
        return False

    if not result.ok:
        # Runtime returned a structured failure. Decide retry vs stop based
        # on stderr signal (legacy _handle_gemini_error).
        stderr_text = result.stderr_excerpt or ""
        retry_result = _handle_gemini_error(stderr_text, model, attempt, max_retries, base_delay)
        if retry_result == "retry":
            return None
        if retry_result == "stop":
            return False
        # "continue" — some non-zero-but-useful output case
        if not result.response or len(result.response.strip()) < 50:
            return False

    response = result.response.strip()

    # Post-validation for file writes (preserved from legacy path)
    if output_path and pre_snapshot is not None:
        violations = _validate_file_writes(pre_snapshot, output_path)
        if violations:
            print("\n⚠️  VIOLATION: Gemini wrote to unauthorized files:")
            for v in violations:
                print(f"   - {v}")
            sys.stdout.flush()

    # Print completion status
    if not stdout_only:
        _print_completion_status(output_path, response)

    # Route response
    _route_gemini_response(msg, message_id, model, response, stdout_only, output_path,
                           skip_github)

    acknowledge(message_id, quiet=stdout_only)
    return (response, True)


# _stream_with_watchdog was removed in Phase 6 — the runtime's watchdog.py
# now provides streaming stdout + mtime liveness polling for all agents.


def _handle_gemini_error(stderr, model, attempt, max_retries, base_delay):
    """Handle Gemini CLI error. Returns 'retry', 'stop', or 'continue'."""
    model_err = _detect_model_error(stderr, model)
    if model_err:
        print(f"\n❌ {model_err}")
        print("💡 To switch accounts: run 'gemini auth login'")
        return "stop"

    if "exhausted your capacity" in stderr or "429" in stderr or "quota" in stderr.lower():
        delay = base_delay * (2 ** attempt)
        if attempt < max_retries - 1:
            print(f"\n⏳ Rate limited (attempt {attempt + 1}/{max_retries}). Waiting {delay}s...")
            sys.stdout.flush()
            time.sleep(delay)
            return "retry"
        else:
            print(f"\n❌ Rate limited after {max_retries} attempts. Giving up.")
            return "stop"

    print(f"\n❌ Gemini CLI error (exit code): {stderr[:500]}")
    sys.stdout.flush()
    return "continue"


def _print_completion_status(output_path, response):
    """Print completion status line."""
    print(f"\n\n{'─' * 40}")
    if output_path:
        output_exists = Path(output_path).exists()
        output_size = Path(output_path).stat().st_size if output_exists else 0
        print(f"✅ Gemini finished → {output_path} ({output_size} bytes)")
    else:
        print(f"✅ Gemini finished ({len(response)} chars)")
    sys.stdout.flush()


def _route_gemini_response(msg, message_id, model, response, stdout_only, output_path,
                           skip_github):
    """Route Gemini's response to the appropriate destination."""
    if output_path:
        if not stdout_only:
            print("   (no broker message — file output mode)")
    elif stdout_only:
        summary = f"[stdout-only] Gemini finished. {len(response)} chars output to stdout."
        reply_id = send_message(
            content=summary, task_id=msg['task_id'], msg_type="response",
            from_llm="gemini", to_llm="claude", from_model=model, to_model=None,
            quiet=stdout_only
        )
        acknowledge(reply_id, quiet=stdout_only)
        if not stdout_only:
            print(f"   Auto-acknowledged reply #{reply_id} (stdout delivery — no inbox accumulation)")
    else:
        reply_id = send_message(
            content=response, task_id=msg['task_id'], msg_type="response",
            from_llm="gemini", to_llm="claude", from_model=model, to_model=None
        )
        acknowledge(reply_id)
        print(f"   Auto-acknowledged reply #{reply_id} (stdout delivery — no inbox accumulation)")
        if not skip_github:
            _post_review_to_github(msg['task_id'], response, model)


def _send_gemini_error(msg, message_id):
    """Send error message when Gemini process fails without sending a response."""
    try:
        err_id = send_message(
            content=f"[Bridge Error] Gemini process failed for message #{message_id}. Check logs.",
            task_id=msg['task_id'], msg_type="error",
            from_llm="gemini", to_llm="claude", from_model="gemini-bridge-error"
        )
        acknowledge(message_id)
        acknowledge(err_id)
    except Exception:
        pass
