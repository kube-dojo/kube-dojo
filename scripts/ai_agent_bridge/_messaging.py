"""Message CRUD operations: send, read, check inbox, acknowledge, conversations."""

import json
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from agent_runtime.redact import redact_jsonable, redact_json_string, redact_text

from ._db import get_db


def check_inbox(for_llm: str = "gemini"):
    """Check inbox for messages addressed to an agent."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, from_llm, message_type, substr(content, 1, 100), timestamp
        FROM messages
        WHERE to_llm = ? AND acknowledged = 0
        ORDER BY id ASC
    """, (for_llm,))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print(f"📭 No unread messages for {for_llm}")
        return

    print(f"📬 {len(rows)} unread message(s) for {for_llm}:\n")
    for row in rows:
        msg_id, from_llm, msg_type, preview, timestamp = row
        preview = redact_text(preview).replace('\n', ' ')
        if len(preview) >= 100:
            preview += "..."
        print(f"  [{msg_id}] From: {from_llm} | Type: {msg_type} | {timestamp}")
        print(f"      {preview}\n")


def read_message(message_id: int, quiet: bool = False):
    """Read a specific message."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, task_id, from_llm, to_llm, message_type, content, data, timestamp
        FROM messages
        WHERE id = ?
    """, (message_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        if not quiet:
            print(f"❌ Message {message_id} not found")
        return None

    msg = {
        "id": row[0],
        "task_id": row[1],
        "from": row[2],
        "to": row[3],
        "type": row[4],
        "content": row[5],
        "data": row[6],
        "timestamp": row[7]
    }

    if not quiet:
        print(f"📨 Message #{msg['id']}")
        print(f"   From: {msg['from']} → To: {msg['to']}")
        print(f"   Type: {msg['type']}")
        print(f"   Task: {msg['task_id'] or 'N/A'}")
        print(f"   Time: {msg['timestamp']}")
        print(f"\n{'='*60}\n")
        print(redact_text(msg['content']))

        if msg['data']:
            print(f"\n{'='*60}")
            print("📎 Attached Data:")
            print(redact_json_string(msg['data']))

    return msg


def send_message(content: str, task_id: str | None = None, msg_type: str = "response",
                 data: str | None = None, from_llm: str = "gemini", to_llm: str = "claude",
                 from_model: str | None = None, to_model: str | None = None,
                 quiet: bool = False):
    """Send a message between agents."""
    content = redact_text(content)
    data = redact_text(data) if data is not None else None

    conn = get_db()
    cursor = conn.cursor()

    timestamp = datetime.now(UTC).isoformat()

    # Store model info in data as JSON if provided
    metadata = {}
    if data:
        try:
            metadata = json.loads(data) if isinstance(data, str) and data.startswith('{') else {"raw": data}
        except (json.JSONDecodeError, ValueError):
            metadata = {"raw": data}
    if from_model:
        metadata["from_model"] = from_model
    if to_model:
        metadata["to_model"] = to_model

    data_json = json.dumps(redact_jsonable(metadata)) if metadata else None

    cursor.execute("""
        INSERT INTO messages (task_id, from_llm, to_llm, message_type, content, data, timestamp, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
    """, (task_id, from_llm, to_llm, msg_type, content, data_json, timestamp))

    msg_id = cursor.lastrowid

    # Auto-ack self-addressed messages (agent dispatching to itself via CLI, not broker)
    if from_llm == to_llm:
        cursor.execute("UPDATE messages SET acknowledged = 1 WHERE id = ?", (msg_id,))

    conn.commit()
    conn.close()

    if not quiet:
        print(f"✅ Message sent to {to_llm.title()} (ID: {msg_id}){' [auto-acked: self-addressed]' if from_llm == to_llm else ''}")

    # Trigger macOS notification to alert human
    try:
        preview = redact_text(content[:80]).replace('"', '\\"').replace('\n', ' ')
        notification = f'display notification "{preview}..." with title "{from_llm.title()} → {to_llm.title()}" subtitle "Check inbox"'
        subprocess.run(["osascript", "-e", notification], check=False, capture_output=True)
    except Exception:
        pass  # Notification is nice-to-have, don't fail if it doesn't work

    return msg_id


def detect_sender() -> str:
    """Detect if the current process is running as Gemini or Claude."""
    if (os.environ.get("GEMINI_SESSION") or
        os.environ.get("GOOGLE_API_KEY")):
        return "gemini"
    if (os.environ.get("CLAUDE_PROJECT_DIR") or
        os.environ.get("CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS")):
        return "claude"
    if os.environ.get("CODEX_SESSION"):
        return "codex"
    if Path(".gemini").exists():
        return "gemini"
    return "claude"


def send_to_gemini(content: str, task_id: str | None = None, msg_type: str = "query",
                   data: str | None = None, from_model: str | None = None,
                   to_model: str | None = None, quiet: bool = False):
    """Send a message to Gemini with auto-detected sender."""
    return send_message(content, task_id, msg_type, data, from_llm=detect_sender(),
                       to_llm="gemini", from_model=from_model, to_model=to_model, quiet=quiet)


def send_to_codex(content: str, task_id: str | None = None, msg_type: str = "query",
                  data: str | None = None, from_model: str | None = None,
                  to_model: str | None = None, quiet: bool = False):
    """Send a message to Codex with auto-detected sender."""
    return send_message(content, task_id, msg_type, data, from_llm=detect_sender(),
                        to_llm="codex", from_model=from_model, to_model=to_model, quiet=quiet)


def acknowledge(message_ids: list[int] | int, quiet: bool = False):
    """Mark message(s) as acknowledged."""
    if isinstance(message_ids, int):
        message_ids = [message_ids]

    conn = get_db()
    cursor = conn.cursor()

    for msg_id in message_ids:
        cursor.execute("UPDATE messages SET acknowledged = 1 WHERE id = ?", (msg_id,))

    conn.commit()
    conn.close()

    if not quiet:
        if len(message_ids) == 1:
            print(f"✓ Message {message_ids[0]} acknowledged")
        else:
            print(f"✓ {len(message_ids)} messages acknowledged: {', '.join(map(str, message_ids))}")


def acknowledge_all(for_llm: str):
    """Acknowledge ALL unread messages for a given agent."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM messages
        WHERE to_llm = ? AND acknowledged = 0
        ORDER BY id ASC
    """, (for_llm,))

    rows = cursor.fetchall()

    if not rows:
        print(f"📭 No unread messages to acknowledge for {for_llm}")
        conn.close()
        return

    msg_ids = [row[0] for row in rows]

    cursor.execute("""
        UPDATE messages SET acknowledged = 1
        WHERE to_llm = ? AND acknowledged = 0
    """, (for_llm,))

    conn.commit()
    conn.close()

    print(f"✓ Acknowledged {len(msg_ids)} messages for {for_llm}: {', '.join(map(str, msg_ids))}")


def get_conversation(task_id: str):
    """Get full conversation for a task."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, from_llm, to_llm, message_type, content, timestamp
        FROM messages
        WHERE task_id = ?
        ORDER BY id ASC
    """, (task_id,))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print(f"❌ No messages found for task: {task_id}")
        return

    print(f"📜 Conversation: {task_id} ({len(rows)} messages)\n")
    print("="*70)

    for row in rows:
        msg_id, from_llm, to_llm, msg_type, content, timestamp = row
        print(f"\n[{msg_id}] {from_llm.upper()} → {to_llm.upper()} | {msg_type} | {timestamp}")
        print("-"*70)
        print(content[:500])
        if len(content) > 500:
            print(f"\n... [{len(content) - 500} more characters]")
        print()


def get_conversation_context(task_id: str, max_chars: int = 30000) -> tuple[str, int]:
    """Get conversation history as formatted context for prompt injection.

    Returns (formatted_text, message_count). Keeps the most recent messages
    when truncation is needed (oldest messages dropped first).
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT from_llm, content, timestamp
        FROM messages
        WHERE task_id = ?
        ORDER BY id ASC
    """, (task_id,))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "", 0

    # Build entries newest-first so truncation drops oldest
    entries = []
    for from_llm, content, timestamp in rows:
        entries.append(f"**{from_llm.upper()}** ({timestamp}):\n{content}\n")

    # Keep newest messages within budget
    kept = []
    total = 0
    for entry in reversed(entries):
        if total + len(entry) > max_chars:
            dropped = len(entries) - len(kept)
            kept.append(f"... [{dropped} older messages omitted] ...")
            break
        kept.append(entry)
        total += len(entry)

    kept.reverse()
    return "\n\n".join(kept), len(rows)


def _extract_issue_number(task_id: str) -> int | None:
    """Extract GH issue number from task_id. Returns None if no issue pattern."""
    if not task_id:
        return None
    match = re.match(r'^(?:issue|gh)-(\d+)$', task_id)
    return int(match.group(1)) if match else None
