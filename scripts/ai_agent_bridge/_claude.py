"""Claude interaction: ask_claude and process_for_claude (decomposed).

Phase 5 of #1184: the sync subprocess path in _run_claude_sync was
migrated onto scripts.agent_runtime.runner.invoke(). The fire-and-forget
background daemon path (_launch_claude_background) stays as-is — it
spawns the bridge itself in the background, and that background instance
then calls process_for_claude which goes through the runtime. The daemon
wrapper is NOT a Claude subprocess call; it's a process-level pattern.

The legacy _build_claude_command and _stream_claude_with_watchdog
helpers are preserved for test-mock backward compat and for the
fire-and-forget path's logging. They will be deleted in Phase 6 cleanup.
"""

import atexit
import subprocess
import sys
import uuid
from pathlib import Path

from agent_runtime.errors import (
    AgentStalledError,
    AgentTimeoutError,
    AgentUnavailableError,
    RateLimitedError,
)
from agent_runtime.runner import invoke as runtime_invoke

from ._broker import _is_task_locked, _remove_pid_file, _write_pid_file
from ._config import CLAUDE_CMD, CLAUDE_DEFAULT_MODEL, REPO_ROOT, agent_child_env
from ._db import get_db, get_session, set_session
from ._messaging import acknowledge, send_message
from ._prompts import build_claude_prompt

VENV_PYTHON = str((REPO_ROOT / ".venv" / "bin" / "python").resolve())


def ask_claude(content: str, task_id: str | None = None, msg_type: str = "query",
               data: str | None = None, new_session: bool = False,
               from_llm: str = "gemini", from_model: str | None = None,
               to_model: str | None = None):
    """Send message to Claude AND invoke Claude to process it."""
    msg_id = send_message(content, task_id, msg_type, data, from_llm=from_llm,
                          to_llm="claude", from_model=from_model, to_model=to_model)
    print(f"\n🚀 Invoking Claude to process message #{msg_id}...")
    process_for_claude(msg_id, new_session)
    return msg_id


def process_for_claude(message_id: int, new_session: bool = False,
                       fire_and_forget: bool = False, no_timeout: bool = False):
    """Read message addressed to Claude, invoke via agent_runtime, send response.

    Fire-and-forget path still spawns the bridge in background (a
    process-level pattern that the runtime doesn't cover). The
    background instance re-enters this function with fire_and_forget=False
    and routes through the runtime for the actual Claude call.
    """
    msg = _fetch_claude_message(message_id)
    if not msg:
        return

    session = get_session(msg['task_id']) if msg['task_id'] else {"claude": None, "gemini": None}
    claude_session_id = session["claude"] if not new_session else None

    _print_claude_message_info(msg, fire_and_forget, no_timeout, claude_session_id)

    if fire_and_forget:
        _launch_claude_background(msg, message_id, new_session)
    else:
        _run_claude_sync_via_runtime(msg, message_id, claude_session_id, no_timeout)


def _run_claude_sync_via_runtime(
    msg: dict,
    message_id: int,
    claude_session_id: str | None,
    no_timeout: bool,
):
    """Run Claude CLI synchronously via agent_runtime.runner.invoke().

    Phase 5: replaces the Popen + _stream_claude_with_watchdog path.
    Session handling:
    - If claude_session_id is set (prior session in SQLite), pass it
      with is_new_session=False → runtime uses --resume for cache warmth.
    - Otherwise if task_id is set, mint a new UUID, pass with
      is_new_session=True → runtime uses --session-id, and persist
      the new ID in SQLite for future turns.
    """
    task_key = msg.get('task_id') or str(message_id)
    timeout_val = 1800 if no_timeout else 900
    mode_label = "no-timeout" if no_timeout else "sync, 15 min timeout"

    if _is_task_locked("claude", task_key):
        print(f"⏸️  Task '{task_key}' is already being processed by another Claude bridge. Skipping.")
        return

    print(f"\n🤖 Processing with Claude CLI via runtime [{mode_label}]...")
    sys.stdout.flush()

    _write_pid_file("claude", task_key, {
        "message_id": message_id,
        "task_id": msg.get('task_id'),
        "mode": mode_label,
    })
    atexit.register(_remove_pid_file, "claude", task_key)

    # Decide session handling
    session_id_to_pass: str | None = None
    is_new_session_flag = False
    if claude_session_id:
        session_id_to_pass = claude_session_id
        is_new_session_flag = False
        print(f"   Resuming session: {claude_session_id[:8]}...")
    elif msg['task_id']:
        new_id = str(uuid.uuid4())
        session_id_to_pass = new_id
        is_new_session_flag = True
        set_session(msg['task_id'], "claude", new_id)
        print(f"   New session: {new_id[:8]}...")

    tool_config: dict = {
        "cmd_prefix": CLAUDE_CMD,
        "is_new_session": is_new_session_flag,
    }

    _response_sent = False
    try:
        result = runtime_invoke(
            "claude",
            build_claude_prompt(msg),
            mode="read-only",
            cwd=REPO_ROOT,
            model=msg.get("to_model") or CLAUDE_DEFAULT_MODEL,
            task_id=msg.get('task_id'),
            session_id=session_id_to_pass,
            tool_config=tool_config,
            entrypoint="bridge",
            hard_timeout=timeout_val,
            # 600s matches dispatch.py. Claude CLI can go quiet for
            # several minutes during long reasoning; the project-scoped
            # session JSONL dir under ~/.claude/projects/<slug>/ gives
            # the mtime poller a reliable liveness signal. Raised from
            # 300s on 2026-04-10 for consistency across the codebase
            # after the dispatch.py bump. (#1184)
            stall_timeout=min(600, timeout_val),
        )

        if not result.ok:
            _response_sent = _handle_claude_error(
                msg, message_id,
                result.stderr_excerpt or "Claude returned no content",
            )
            return

        response = result.response.strip()
        print(f"\n\n{'─' * 40}")
        print(f"✅ Claude finished ({len(response)} chars)")
        sys.stdout.flush()

        reply_id = send_message(
            content=response, task_id=msg['task_id'], msg_type="response",
            from_llm="claude", to_llm=msg['from'], from_model=None, to_model=None,
        )
        _response_sent = True

        acknowledge(message_id)
        acknowledge(reply_id)

    except RateLimitedError as exc:
        print(f"\n⏳ Claude rate limited: {exc}")
        err_id = send_message(
            content=f"[Bridge Error] Claude rate limited: {exc}",
            task_id=msg['task_id'], msg_type="error",
            from_llm="claude", to_llm=msg['from'],
            from_model="claude-bridge-rate-limited",
        )
        _response_sent = True
        acknowledge(message_id)
        acknowledge(err_id)
    except (AgentStalledError, AgentTimeoutError) as exc:
        timeout_mins = timeout_val // 60
        print(f"\n❌ Claude CLI timed out ({timeout_mins} min sync limit): {exc}")
        err_id = send_message(
            content=(
                f"[Bridge Error] Claude CLI timed out after {timeout_mins} minutes. "
                f"({type(exc).__name__}: {exc}). Consider using --async for long tasks."
            ),
            task_id=msg['task_id'], msg_type="error",
            from_llm="claude", to_llm=msg['from'],
            from_model="claude-bridge-timeout",
        )
        _response_sent = True
        acknowledge(message_id)
        acknowledge(err_id)
    except AgentUnavailableError:
        print("❌ claude CLI not found. Is it installed?")
        err_id = send_message(
            content="[Bridge Error] Claude CLI not found on system",
            task_id=msg['task_id'], msg_type="error",
            from_llm="claude", to_llm=msg['from'],
            from_model="claude-bridge-not-found",
        )
        _response_sent = True
        acknowledge(err_id)
    finally:
        if not _response_sent:
            _send_claude_fallback_error(msg, message_id)
        _remove_pid_file("claude", task_key)


def _fetch_claude_message(message_id: int) -> dict | None:
    """Fetch a message addressed to Claude from the database."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, task_id, from_llm, to_llm, message_type, content, data, timestamp
        FROM messages
        WHERE id = ? AND to_llm = 'claude'
    """, (message_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        print(f"❌ Message {message_id} not found or not addressed to Claude")
        return None

    return {
        "id": row[0],
        "task_id": row[1],
        "from": row[2],
        "to": row[3],
        "type": row[4],
        "content": row[5],
        "data": row[6],
        "timestamp": row[7]
    }


def _print_claude_message_info(msg, fire_and_forget, no_timeout, claude_session_id):
    """Print message info header."""
    print(f"📨 Message #{msg['id']}")
    print(f"   From: {msg['from']} → To: {msg['to']}")
    print(f"   Type: {msg['type']}")
    print(f"   Task: {msg['task_id'] or 'N/A'}")
    print(f"   Mode: {'🚀 async (bridge bg)' if fire_and_forget else '⏳ sync' + (' (no timeout)' if no_timeout else '')}")
    print(f"   Session: {claude_session_id[:8] + '...' if claude_session_id else 'NEW'}")


# _build_claude_command was removed in Phase 6 — ClaudeAdapter in
# scripts.agent_runtime.adapters.claude now owns Claude CLI flag
# construction including --bare, --resume, --session-id, --model,
# --output-format, --mcp-config, --allowedTools, and
# --exclude-dynamic-system-prompt-sections (version-gated).


def _launch_claude_background(msg, message_id, new_session):
    """Launch the bridge itself as a background process for Claude."""
    task_key = msg['task_id'] or str(message_id)

    if _is_task_locked("claude", task_key):
        print(f"⏸️  Task '{task_key}' is already being processed by another Claude bridge. Skipping.")
        return

    log_dir = REPO_ROOT / ".mcp/servers/message-broker/logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"claude-{task_key}.log"

    print("\n🚀 Launching bridge in background (no timeout)...")
    print(f"   Log: {log_file}")
    print("   Bridge will capture Claude's response and route it when done.")

    try:
        bridge_cmd = [
            VENV_PYTHON, str(Path(__file__).parent / "__main__.py"),
            "process-claude", str(message_id),
            "--no-timeout"
        ]
        if new_session:
            bridge_cmd.append("--new-session")
        lf = open(log_file, "w")  # noqa: SIM115 — fd passed to Popen, closed after
        proc = subprocess.Popen(
            bridge_cmd,
            stdout=lf,
            stderr=subprocess.STDOUT,
            cwd=str(REPO_ROOT),
            env=agent_child_env("claude"),
            start_new_session=True
        )
        lf.close()
        print(f"   PID: {proc.pid}")

        _write_pid_file("claude", task_key, {
            "message_id": message_id,
            "task_id": msg.get('task_id'),
            "mode": "fire-and-forget",
        }, pid=proc.pid)

    except FileNotFoundError:
        print("❌ Python or bridge script not found")


# _run_claude_sync and _stream_claude_with_watchdog were removed in
# Phase 6 — process_for_claude() now calls _run_claude_sync_via_runtime()
# which delegates to scripts.agent_runtime.runner.invoke(). Stall
# detection, hard timeout, and streaming are all handled uniformly by
# the runtime's watchdog.py.


def _handle_claude_error(msg, message_id, stderr):
    """Handle Claude CLI non-zero exit. Returns True (response_sent)."""
    error_msg = stderr.strip() or "Unknown error"
    print(f"\n❌ Claude CLI error: {error_msg[:500]}")
    sys.stdout.flush()

    err_id = send_message(
        content=f"[Bridge Error] Claude CLI failed:\n{error_msg[:500]}",
        task_id=msg['task_id'], msg_type="error",
        from_llm="claude", to_llm=msg['from'], from_model="claude-bridge-error"
    )
    acknowledge(message_id)
    acknowledge(err_id)
    return True


def _send_claude_fallback_error(msg, message_id):
    """Send fallback error when Claude process fails without sending a response."""
    try:
        err_id = send_message(
            content=f"[Bridge Error] Claude process failed unexpectedly for message #{message_id}. Check logs.",
            task_id=msg['task_id'], msg_type="error",
            from_llm="claude", to_llm=msg['from'], from_model="claude-bridge-error"
        )
        acknowledge(message_id)
        acknowledge(err_id)
    except Exception:
        pass
