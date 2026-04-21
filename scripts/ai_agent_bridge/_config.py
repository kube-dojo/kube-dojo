"""Shared constants and environment configuration for the AI Agent Bridge."""

import os
import shutil
from pathlib import Path

# Repo root for path resolution
REPO_ROOT = Path(
    os.environ.get("AB_REPO_ROOT", str(Path(__file__).parent.parent.parent))
)

# Database path (same as MCP server uses)
DB_PATH = Path(
    os.environ.get(
        "AB_DB_PATH",
        str(REPO_ROOT / ".mcp" / "servers" / "message-broker" / "messages.db"),
    )
)
PID_DIR = Path(
    os.environ.get(
        "AB_PID_DIR",
        str(REPO_ROOT / ".mcp" / "servers" / "message-broker" / "pids"),
    )
)

# Resolve CLI paths at import time (before detached children lose PATH)
# Use npx to run Claude Code — avoids bugs in the globally installed version.
# Returns a list: ["npx", "@anthropic-ai/claude-code"] to use as cmd prefix.
CLAUDE_CMD = ["npx", "@anthropic-ai/claude-code@latest"]
GEMINI_CLI = shutil.which("gemini") or "gemini"
CODEX_CLI = shutil.which("codex") or "codex"
CLAUDE_DEFAULT_MODEL = os.environ.get("AB_CLAUDE_MODEL", "claude-opus-4-7")
GEMINI_DEFAULT_MODEL = os.environ.get("AB_GEMINI_MODEL", "")
if not GEMINI_DEFAULT_MODEL:
    try:
        from batch_gemini_config import FLASH_MODEL

        GEMINI_DEFAULT_MODEL = FLASH_MODEL
    except ImportError:
        GEMINI_DEFAULT_MODEL = "gemini-2.0-flash"

# Snapshot environment for passing to detached children
# Set GEMINI_SESSION so .bashrc disables hostile aliases (eza, bat, zoxide)
_PARENT_ENV = os.environ.copy()
_PARENT_ENV["GEMINI_SESSION"] = "1"
_PIPELINE_ENV_KEY = os.environ.get(
    "AB_PIPELINE_ENV_KEY", "KUBEDOJO_PIPELINE"
)
_PARENT_ENV[_PIPELINE_ENV_KEY] = "1"  # Suppress inbox hooks during pipeline runs
# Gemini auth: CLI prefers GEMINI_API_KEY when set; otherwise falls
# through to OAuth/subscription creds in ~/.gemini/oauth_creds.json.
# When the API-key tier is rate-limited, set
# KUBEDOJO_GEMINI_SUBSCRIPTION=1 to strip the key from child env so
# dispatches use the subscription path instead.
if os.environ.get("KUBEDOJO_GEMINI_SUBSCRIPTION") == "1":
    _PARENT_ENV.pop("GEMINI_API_KEY", None)
    _PARENT_ENV.pop("GOOGLE_API_KEY", None)

# Model availability cache: {model: (available: bool, timestamp: float)}
# Avoids burning API quota on repeated checks within the same session.
_MODEL_CACHE: dict[str, tuple[bool, float]] = {}
_MODEL_CACHE_TTL = 3600  # 1 hour — re-check after this

# GitHub comment/body limit is 65,536 chars. Use 64K with 1.5K safety margin for headers.
GH_CHAR_LIMIT = 64000
