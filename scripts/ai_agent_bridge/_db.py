"""Database initialization and session management."""

import sqlite3
from datetime import UTC, datetime

from ._config import DB_PATH


def init_db():
    """Initialize database if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    # Ensure messages table exists with all columns
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT,
            from_llm TEXT NOT NULL,
            to_llm TEXT NOT NULL,
            message_type TEXT DEFAULT 'message',
            content TEXT NOT NULL,
            data TEXT,
            timestamp TEXT NOT NULL,
            acknowledged INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending'
        )
    """)
    # Sessions table - track CLI session IDs for resuming conversations
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            task_id TEXT PRIMARY KEY,
            claude_session_id TEXT,
            gemini_session_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def get_db():
    """Get database connection with auto-migration (#604)."""
    if not DB_PATH.exists():
        return init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA busy_timeout=5000")

    try:
        # Check for missing columns (migration for existing DBs)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(messages)")
        columns = [row[1] for row in cursor.fetchall()]

        if "status" not in columns:
            print("🔧 Migrating database: adding 'status' column to 'messages' table")
            conn.execute("ALTER TABLE messages ADD COLUMN status TEXT DEFAULT 'pending'")

        # Ensure sessions table exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                task_id TEXT PRIMARY KEY,
                claude_session_id TEXT,
                gemini_session_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return conn


def get_session(task_id: str) -> dict:
    """Get session IDs for a task."""
    if not task_id:
        return {"claude": None, "gemini": None}

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT claude_session_id, gemini_session_id FROM sessions WHERE task_id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {"claude": row[0], "gemini": row[1]}
    return {"claude": None, "gemini": None}


def set_session(task_id: str, agent: str, session_id: str):
    """Set session ID for an agent on a task."""
    if not task_id:
        return

    conn = get_db()
    cursor = conn.cursor()
    timestamp = datetime.now(UTC).isoformat()

    # Upsert session
    cursor.execute("SELECT task_id FROM sessions WHERE task_id = ?", (task_id,))
    if cursor.fetchone():
        if agent == "claude":
            cursor.execute("UPDATE sessions SET claude_session_id = ?, updated_at = ? WHERE task_id = ?",
                          (session_id, timestamp, task_id))
        else:
            cursor.execute("UPDATE sessions SET gemini_session_id = ?, updated_at = ? WHERE task_id = ?",
                          (session_id, timestamp, task_id))
    else:
        if agent == "claude":
            cursor.execute("INSERT INTO sessions (task_id, claude_session_id, created_at, updated_at) VALUES (?, ?, ?, ?)",
                          (task_id, session_id, timestamp, timestamp))
        else:
            cursor.execute("INSERT INTO sessions (task_id, gemini_session_id, created_at, updated_at) VALUES (?, ?, ?, ?)",
                          (task_id, session_id, timestamp, timestamp))

    conn.commit()
    conn.close()
    print(f"📌 Stored {agent} session: {session_id[:8]}... for task {task_id}")
