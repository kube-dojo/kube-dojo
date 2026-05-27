"""Send a prompt to a running Cursor Desktop chat session via `cursor-agent --resume`.

Sibling of `_ui_codex.py` / `_ui_agy.py`: mirrors the design from issue #2285
(agent bridge — send + receive to running Desktop sessions) but targets the
Cursor Desktop family of "agentic" sessions (Composer, Auto mode, etc.).

## How it works

`cursor-agent --resume <CHAT_ID> --print --output-format stream-json --trust
--force "<message>"` resumes a persisted Cursor chat non-interactively. The
subprocess emits a JSON event stream on stdout containing init, user/assistant
turn events, optional `thinking/delta` chunks, and a terminal `result` event.

When `--thread new` (or omitted) is passed, we first call `cursor-agent
create-chat`, capture the new chat id from stdout, and resume into it. This
keeps the orchestration shape identical to Codex/Agy.

## Storage — two locations, both real (verified 2026-05-27)

Every chat is persisted in two places, and the bridge surfaces both:

- `~/.cursor/chats/<workspace_hash>/<CHAT_ID>/store.db` — cursor-agent's
  CLI session state (binary SQLite). Surfaced as `session_file`.
- `~/.cursor/projects/<workspace_slug>/agent-transcripts/<CHAT_ID>/<CHAT_ID>.jsonl`
  — the human-readable JSONL transcript that Cursor Desktop indexes for
  its agent-transcripts surface. Surfaced as `transcript_file`. This is
  what other in-Cursor agents (Composer chat, the in-IDE assistant) can
  grep to find bridge-delivered work.

The `workspace_hash` / `workspace_slug` is derived from the cwd that
cursor-agent saw at create-chat time. Pass `--cwd <repo-root>` to keep all
bridge chats in the same workspace; otherwise a chat may end up bifurcated
across multiple workspace_hash directories.

## Event shape (empirical, cursor-agent 2026.05.x)

    {"type":"system","subtype":"init","session_id":"...","model":"Composer 2.5", ...}
    {"type":"user","message":{"role":"user","content":[{"type":"text","text":"..."}]}, ...}
    {"type":"thinking","subtype":"delta","text":"...","session_id":"...","timestamp_ms":...}
    {"type":"thinking","subtype":"completed", ...}
    {"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"..."}]}, ...}
    {"type":"result","subtype":"success","duration_ms":...,"result":"<final text>",
     "session_id":"...","usage":{...}}

The terminal event is `result` with `subtype` in {success, error}. The
`result` field carries the final assistant text directly — preferred over
concatenating `assistant` message chunks.

## Usage from CLI

    ab send-cursor-ui --thread <CHAT_ID> "your message"
    ab send-cursor-ui --thread new --from-file relay.md       # creates a fresh chat
    ab send-cursor-ui --thread <CHAT_ID> --cwd ~/some/worktree "message"
    ab send-cursor-ui --thread <CHAT_ID> --model gpt-5 "..."  # override model

## Usage from Python

    from ai_agent_bridge._ui_cursor import send
    result = send(thread_id="705e5125-...", message="ping", cwd=Path("/tmp"))
    print(result["final_message"])
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

CURSOR_CHATS_ROOT = Path.home() / ".cursor" / "chats"
CURSOR_PROJECTS_ROOT = Path.home() / ".cursor" / "projects"
DEFAULT_TIMEOUT_S = 1800  # 30 min — covers most multi-turn dispatches
DEFAULT_MODEL = os.environ.get("AB_CURSOR_UI_MODEL", "composer-2.5")
_NEW_THREAD_SENTINELS = {"", "-", "new", "fresh", "none", "null"}


def _cursor_binary() -> str:
    """Resolve the cursor-agent executable (or the legacy `agent` alias)."""
    return (
        os.environ.get("KUBEDOJO_CURSOR_CMD")
        or shutil.which("cursor-agent")
        or shutil.which("agent")
        or "cursor-agent"
    )


def find_session_file(thread_id: str) -> Path | None:
    """Locate the cursor chat store.db for a given chat id.

    Cursor stores per-chat CLI state at
    `~/.cursor/chats/<workspace_hash>/<CHAT_ID>/store.db`. The same chat
    may have store.db copies under multiple workspace_hash directories
    (one per cwd cursor-agent has seen the chat from); we return the
    most recently modified.
    """
    if not thread_id:
        return None
    matches = sorted(
        CURSOR_CHATS_ROOT.glob(f"*/{thread_id}/store.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return matches[0] if matches else None


def find_transcript_file(thread_id: str) -> Path | None:
    """Locate the Cursor Desktop agent-transcripts jsonl for a given chat id.

    cursor-agent mirrors each chat to
    `~/.cursor/projects/<workspace_slug>/agent-transcripts/<CHAT_ID>/<CHAT_ID>.jsonl`.
    This is the surface Cursor Desktop indexes for its agent-transcripts /
    "Background Agents" view — the user-facing artifact, distinct from the
    raw CLI store.db. Empirically verified 2026-05-27 (kubedojo PR #1613).
    """
    if not thread_id:
        return None
    matches = sorted(
        CURSOR_PROJECTS_ROOT.glob(
            f"*/agent-transcripts/{thread_id}/{thread_id}.jsonl"
        ),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return matches[0] if matches else None


def _thread_arg_is_new(thread_id: str | None) -> bool:
    return thread_id is None or thread_id.strip().lower() in _NEW_THREAD_SENTINELS


def _create_chat(cwd: Path | None) -> str:
    """Spawn `cursor-agent create-chat` and return the new chat UUID."""
    proc = subprocess.run(
        [_cursor_binary(), "create-chat"],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"cursor-agent create-chat exited {proc.returncode}: "
            f"{proc.stderr.strip()[-500:]}"
        )
    chat_id = proc.stdout.strip().splitlines()[-1].strip() if proc.stdout else ""
    if not chat_id:
        raise RuntimeError("cursor-agent create-chat returned empty chat id")
    return chat_id


def _extract_final_message(events: list[dict]) -> str | None:
    """Pick the final assistant message from a stream-json event list.

    Prefer the terminal `result/success` event's `result` field. Fall back to
    concatenating the last `assistant` message's text content blocks.
    """
    final_result: str | None = None
    final_assistant: str | None = None
    for evt in events:
        if not isinstance(evt, dict):
            continue
        etype = evt.get("type")
        if etype == "result":
            val = evt.get("result")
            if isinstance(val, str) and val.strip():
                final_result = val
        elif etype == "assistant":
            msg = evt.get("message") or {}
            content = msg.get("content") if isinstance(msg, dict) else None
            if isinstance(content, list):
                parts = [
                    blk.get("text", "")
                    for blk in content
                    if isinstance(blk, dict) and blk.get("type") == "text"
                ]
                text = "".join(parts).strip()
                if text:
                    final_assistant = text
    return final_result or final_assistant


def send(
    thread_id: str | None,
    message: str,
    *,
    bridge_id: str | None = None,
    cwd: Path | None = None,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    model: str | None = None,
) -> dict:
    """Send a prompt to a running Cursor Desktop chat via `cursor-agent --resume`.

    Args:
        thread_id: Cursor chat id (UUID). Pass None, "", "-", or "new" to
            spawn a fresh chat first via `cursor-agent create-chat`.
        message: prompt body. A `Bridge-ID: <id>` line is prepended for
            correlation; the receiving agent should echo the Bridge-ID in
            its reply if asked.
        bridge_id: correlation id (auto-generated if None).
        cwd: working directory for the cursor-agent subprocess. cursor-agent
            chooses workspace context from this cwd — point it at the target
            worktree when relevant.
        timeout_s: max wall-clock for the cursor-agent subprocess.
        model: override the model (default `composer-2.5`, or
            `$AB_CURSOR_UI_MODEL`).

    Returns:
        dict with:
            bridge_id (str), thread_id (str | None), exit_code (int),
            events (list[dict] parsed from stream-json stdout),
            final_message (str | None), duration_s (float),
            session_file (str | None) for `store.db`, stderr (str).
    """
    bridge_id = bridge_id or f"bridge-{uuid.uuid4().hex[:8]}"
    framed_message = f"Bridge-ID: {bridge_id}\n\n{message}"
    effective_model = model or DEFAULT_MODEL

    resolved_thread_id: str | None = thread_id
    if _thread_arg_is_new(thread_id):
        try:
            resolved_thread_id = _create_chat(cwd)
        except (RuntimeError, subprocess.TimeoutExpired, OSError) as exc:
            return {
                "bridge_id": bridge_id,
                "thread_id": None,
                "exit_code": -1,
                "events": [],
                "final_message": None,
                "duration_s": 0.0,
                "session_file": None,
                "stderr": f"create-chat failed: {exc}",
            }

    session_file = find_session_file(resolved_thread_id or "")

    cmd = [
        _cursor_binary(),
        "--resume",
        resolved_thread_id or "",
        "--print",
        "--output-format",
        "stream-json",
        "--trust",
        "--force",
        "--model",
        effective_model,
        framed_message,
    ]

    start = datetime.now(UTC)
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
        stdout = proc.stdout
        stderr = proc.stderr
        exit_code = proc.returncode
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout.decode("utf-8", errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = e.stderr.decode("utf-8", errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        stderr = f"[timeout after {timeout_s}s]\n{stderr}"
        exit_code = -1
    duration_s = (datetime.now(UTC) - start).total_seconds()

    events: list[dict] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    # If we created the chat ourselves, re-resolve session_file now that the
    # store.db should exist.
    if session_file is None and resolved_thread_id:
        session_file = find_session_file(resolved_thread_id)
    transcript_file = find_transcript_file(resolved_thread_id or "")

    return {
        "bridge_id": bridge_id,
        "thread_id": resolved_thread_id,
        "exit_code": exit_code,
        "events": events,
        "final_message": _extract_final_message(events),
        "duration_s": duration_s,
        "session_file": str(session_file) if session_file else None,
        "transcript_file": str(transcript_file) if transcript_file else None,
        "stderr": stderr,
    }


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ab send-cursor-ui",
        description=(
            "Send a prompt to a running Cursor Desktop chat via "
            "`cursor-agent --resume`. Sibling of send-codex-ui / send-agy-ui. "
            "Returns the cursor-agent subprocess exit code."
        ),
    )
    parser.add_argument(
        "--thread",
        default=None,
        help=(
            "Cursor chat id (UUID). Omit or pass 'new' to spawn a fresh "
            "chat via `cursor-agent create-chat`."
        ),
    )
    parser.add_argument(
        "--bridge-id",
        default=None,
        help="Correlation id (auto-generated if not given).",
    )
    parser.add_argument(
        "--cwd",
        type=Path,
        default=None,
        help=(
            "Working directory for the cursor-agent subprocess. cursor-agent "
            "chooses workspace context from this cwd."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_S,
        help=f"Max wall-clock seconds (default {DEFAULT_TIMEOUT_S}).",
    )
    parser.add_argument(
        "--model",
        default=None,
        help=(
            f"Model override (default {DEFAULT_MODEL!r}; honors "
            "$AB_CURSOR_UI_MODEL)."
        ),
    )
    parser.add_argument(
        "--from-file",
        type=Path,
        default=None,
        help="Read message body from a file (use '-' for stdin).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print result as compact JSON (excludes the verbose events list).",
    )
    parser.add_argument(
        "message",
        nargs="?",
        help="Inline message text. Mutually exclusive with --from-file.",
    )
    args = parser.parse_args(argv)

    if args.from_file and args.message:
        parser.error("provide either --from-file or a positional message, not both")
    if args.from_file:
        message = (
            sys.stdin.read()
            if str(args.from_file) == "-"
            else args.from_file.read_text(encoding="utf-8")
        )
    elif args.message is not None:
        message = args.message
    else:
        parser.error("must provide a message via positional arg or --from-file")

    result = send(
        thread_id=args.thread,
        message=message,
        bridge_id=args.bridge_id,
        cwd=args.cwd,
        timeout_s=args.timeout,
        model=args.model,
    )

    if args.json:
        compact = {k: v for k, v in result.items() if k != "events"}
        compact["event_count"] = len(result["events"])
        print(json.dumps(compact, indent=2, default=str))
    else:
        print(f"thread:       {result['thread_id']}")
        print(f"bridge_id:    {result['bridge_id']}")
        print(f"exit_code:    {result['exit_code']}")
        print(f"duration_s:   {result['duration_s']:.2f}")
        print(f"events:       {len(result['events'])}")
        print(f"session_file: {result['session_file']}")
        print(f"transcript:   {result['transcript_file']}")
        if result["final_message"]:
            print()
            print("=== final message ===")
            print(result["final_message"])
        if result["stderr"]:
            print()
            print("=== stderr (truncated) ===")
            print(result["stderr"][:2000])

    return 0 if result["exit_code"] == 0 else 1


if __name__ == "__main__":
    sys.exit(cli_main())
