"""Shared constants and environment configuration for the AI Agent Bridge."""

import os
import shutil
from pathlib import Path

# Database path (same as MCP server uses)
DB_PATH = Path(__file__).parent.parent.parent / ".mcp/servers/message-broker/messages.db"
PID_DIR = Path(__file__).parent.parent.parent / ".mcp/servers/message-broker/pids"

# Resolve CLI paths at import time (before detached children lose PATH)
CLAUDE_CLI = shutil.which("claude") or "claude"
GEMINI_CLI = shutil.which("gemini") or "gemini"

# Snapshot environment for passing to detached children
# Set GEMINI_SESSION so .bashrc disables hostile aliases (eza, bat, zoxide)
_PARENT_ENV = os.environ.copy()
_PARENT_ENV["GEMINI_SESSION"] = "1"
_PARENT_ENV["KUBEDOJO_PIPELINE"] = "1"  # Suppress inbox hooks during pipeline runs

# Model availability cache: {model: (available: bool, timestamp: float)}
# Avoids burning API quota on repeated checks within the same session.
_MODEL_CACHE: dict[str, tuple[bool, float]] = {}
_MODEL_CACHE_TTL = 3600  # 1 hour — re-check after this

# GitHub comment/body limit is 65,536 chars. Use 64K with 1.5K safety margin for headers.
GH_CHAR_LIMIT = 64000

# Repo root for path resolution
REPO_ROOT = Path(__file__).parent.parent.parent
