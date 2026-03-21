"""AI Agent Bridge - Multi-agent communication bridge via MCP Message Broker.

This package provides bidirectional communication between AI agents (Gemini, Claude)
using a shared SQLite database.

All public functions are re-exported here for backward compatibility.
"""

# Re-export everything that was previously importable from ai_agent_bridge
from ._broker import (
    _git_status_snapshot,
    _is_task_locked,
    _remove_pid_file,
    _validate_file_writes,
    _write_pid_file,
    bridge_status,
    broker_cleanup,
)
from ._claude import ask_claude, process_for_claude
from ._cli import interactive_mode, main, process_all_claude, process_all_gemini
from ._config import (
    _MODEL_CACHE,
    _MODEL_CACHE_TTL,
    _PARENT_ENV,
    CLAUDE_CLI,
    DB_PATH,
    GEMINI_CLI,
    GH_CHAR_LIMIT,
    PID_DIR,
)
from ._db import get_db, get_session, init_db, set_session
from ._gemini import ask_gemini, process_and_respond
from ._github import (
    _format_review_chunk,
    _gh_comment,
    _post_review_to_github,
    _split_content,
)
from ._messaging import (
    _extract_issue_number,
    acknowledge,
    acknowledge_all,
    check_inbox,
    detect_sender,
    get_conversation,
    read_message,
    send_message,
    send_to_gemini,
)
from ._model import _detect_model_error, check_model
from ._prompts import build_claude_prompt, build_gemini_prompt

__all__ = [
    # Config
    "DB_PATH", "PID_DIR", "CLAUDE_CLI", "GEMINI_CLI", "_PARENT_ENV",
    "_MODEL_CACHE", "_MODEL_CACHE_TTL", "GH_CHAR_LIMIT",
    # DB
    "init_db", "get_db", "get_session", "set_session",
    # Broker
    "_git_status_snapshot", "_validate_file_writes", "_write_pid_file",
    "_is_task_locked", "_remove_pid_file", "broker_cleanup", "bridge_status",
    # Messaging
    "check_inbox", "read_message", "send_message", "detect_sender",
    "send_to_gemini", "acknowledge", "acknowledge_all", "get_conversation",
    "_extract_issue_number",
    # GitHub
    "_format_review_chunk", "_split_content", "_gh_comment", "_post_review_to_github",
    # Model
    "check_model", "_detect_model_error",
    # Prompts
    "build_gemini_prompt", "build_claude_prompt",
    # Gemini
    "ask_gemini", "process_and_respond",
    # Claude
    "ask_claude", "process_for_claude",
    # CLI
    "interactive_mode", "process_all_gemini", "process_all_claude", "main",
]
