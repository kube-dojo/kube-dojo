"""Claude interaction: ask_claude and process_for_claude (decomposed)."""

import atexit
import contextlib
import subprocess
import sys
import uuid
from pathlib import Path

from ._broker import _is_task_locked, _remove_pid_file, _write_pid_file
from ._config import _PARENT_ENV, CLAUDE_CLI, REPO_ROOT
from ._db import get_db, get_session, set_session
from ._messaging import acknowledge, send_message
from ._prompts import build_claude_prompt


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
    """Read message addressed to Claude, invoke Claude CLI headlessly, send response."""
    msg = _fetch_claude_message(message_id)
    if not msg:
        return

    session = get_session(msg['task_id']) if msg['task_id'] else {"claude": None, "gemini": None}
    claude_session_id = session["claude"] if not new_session else None

    _print_claude_message_info(msg, fire_and_forget, no_timeout, claude_session_id)

    prompt = build_claude_prompt(msg)
    cmd = _build_claude_command(prompt, claude_session_id, msg, new_session)

    if fire_and_forget:
        _launch_claude_background(msg, message_id, new_session)
    else:
        _run_claude_sync(msg, message_id, cmd, no_timeout)


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


def _build_claude_command(prompt, claude_session_id, msg, new_session):
    """Build the Claude CLI command."""
    cmd = [CLAUDE_CLI, "-p", prompt]
    if claude_session_id:
        cmd.extend(["--resume", claude_session_id])
        print(f"   Resuming session: {claude_session_id[:8]}...")
    elif msg['task_id']:
        new_id = str(uuid.uuid4())
        cmd.extend(["--session-id", new_id])
        set_session(msg['task_id'], "claude", new_id)
        print(f"   New session: {new_id[:8]}...")
    return cmd


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
            sys.executable, str(Path(__file__).parent / "__main__.py"),
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
            env=_PARENT_ENV,
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


def _run_claude_sync(msg, message_id, cmd, no_timeout):
    """Run Claude CLI synchronously with streaming output."""
    task_key = msg.get('task_id') or str(message_id)
    timeout_val = None if no_timeout else 900
    mode_label = "no-timeout" if no_timeout else "sync, 15 min timeout"

    if _is_task_locked("claude", task_key):
        print(f"⏸️  Task '{task_key}' is already being processed by another Claude bridge. Skipping.")
        return

    print(f"\n🤖 Processing with Claude CLI (headless) [{mode_label}]...")
    sys.stdout.flush()

    _write_pid_file("claude", task_key, {
        "message_id": message_id,
        "task_id": msg.get('task_id'),
        "mode": mode_label,
    })
    atexit.register(_remove_pid_file, "claude", task_key)

    _response_sent = False
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(REPO_ROOT),
            env=_PARENT_ENV
        )

        _timed_out, output_lines = _stream_claude_with_watchdog(proc, timeout_val)

        stderr = proc.stderr.read() if proc.stderr else ""

        if _timed_out:
            stderr += f"\n[bridge] Process killed after {timeout_val}s timeout"
            proc.returncode = -9

        if proc.returncode != 0:
            _response_sent = _handle_claude_error(msg, message_id, stderr)
            return

        response = ''.join(output_lines).strip()

        print(f"\n\n{'─' * 40}")
        print(f"✅ Claude finished ({len(response)} chars)")
        sys.stdout.flush()

        reply_id = send_message(
            content=response, task_id=msg['task_id'], msg_type="response",
            from_llm="claude", to_llm=msg['from'], from_model=None, to_model=None
        )
        _response_sent = True

        acknowledge(message_id)
        acknowledge(reply_id)

    except subprocess.TimeoutExpired:
        proc.kill()
        timeout_mins = timeout_val // 60 if timeout_val else "?"
        print(f"\n❌ Claude CLI timed out ({timeout_mins} min sync limit)")
        err_id = send_message(
            content=f"[Bridge Error] Claude CLI timed out after {timeout_mins} minutes. Consider using --async flag for long tasks.",
            task_id=msg['task_id'], msg_type="error",
            from_llm="claude", to_llm=msg['from'], from_model="claude-bridge-timeout"
        )
        _response_sent = True
        acknowledge(message_id)
        acknowledge(err_id)
    except FileNotFoundError:
        print("❌ claude CLI not found. Is it installed?")
        err_id = send_message(
            content="[Bridge Error] Claude CLI not found on system",
            task_id=msg['task_id'], msg_type="error",
            from_llm="claude", to_llm=msg['from'], from_model="claude-bridge-not-found"
        )
        _response_sent = True
        acknowledge(err_id)
    finally:
        if not _response_sent:
            _send_claude_fallback_error(msg, message_id)
        _remove_pid_file("claude", task_key)


def _stream_claude_with_watchdog(proc, timeout_val):
    """Stream Claude output with optional watchdog timer."""
    _timed_out = False

    _watchdog_timer = None
    if timeout_val:
        def _kill_on_timeout():
            nonlocal _timed_out
            _timed_out = True
            print(f"\n⏰ Claude CLI timed out after {timeout_val}s — killing process")
            sys.stdout.flush()
            with contextlib.suppress(OSError):
                proc.kill()
        import threading
        _watchdog_timer = threading.Timer(timeout_val, _kill_on_timeout)
        _watchdog_timer.daemon = True
        _watchdog_timer.start()

    output_lines = []
    try:
        for line in proc.stdout:
            print(line, end='')
            sys.stdout.flush()
            output_lines.append(line)
    except (OSError, ValueError):
        pass

    proc.wait()
    if _watchdog_timer:
        _watchdog_timer.cancel()

    return _timed_out, output_lines


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
