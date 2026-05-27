"""Send a prompt to an Antigravity UI conversation via `agy --print`.

Lane 2 implementation for the agent bridge: drive a persisted Antigravity
(`agy`) conversation in the same orchestration shape as `send-codex-ui`.

## How it works

`agy --conversation <CONVERSATION_ID> --print "<message>"` resumes a
persisted Antigravity conversation non-interactively. Unlike Codex, agy does
not emit a JSON event stream on stdout in print mode. It prints plain text,
then writes richer turn events to its local transcript files.

The bridge runs agy in print mode, prefixes the prompt with a `Bridge-ID:`
line for correlation, and returns a structured result. When the transcript is
available, the final message is extracted from the latest
`MODEL_RESPONSE`/`PLANNER_RESPONSE` event. Otherwise stdout is treated as the
final message.

## Empirical findings (2026-05-27 bridge probe)

Commands run from this worktree:

1. `agy --print-timeout 60s --print 'Reply with exactly: hello-from-agy-probe'`
   returned plain stdout: `hello-from-agy-probe`.
2. The invocation created conversation
   `48fd721e-a259-438c-9eb9-53b0fd271c11` under
   `~/.gemini/antigravity-cli/conversations/48fd721e-a259-438c-9eb9-53b0fd271c11.pb`.
3. `~/.gemini/antigravity-cli/cache/last_conversations.json` maps the
   worktree path to that conversation id.
4. `agy --print-timeout 60s --conversation 48fd721e-a259-438c-9eb9-53b0fd271c11
   --print 'Reply with exactly: resumed-agy-probe'` succeeded. The log line
   said `Print mode: resuming conversation 48fd...`; stdout contained the
   prior and current short replies, while the transcript JSONL contained the
   latest `PLANNER_RESPONSE` content `resumed-agy-probe`.
5. Turn transcripts are written at
   `~/.gemini/antigravity-cli/brain/<conversation-id>/.system_generated/logs/transcript.jsonl`.

## Usage from CLI

    ab send-agy-ui --thread <CONVERSATION-ID> "your message"
    ab send-agy-ui --thread <CONVERSATION-ID> --from-file relay.md
    ab send-agy-ui --cwd ~/some/worktree --from-file relay.md --json

Omit `--thread`, or pass `--thread new`, to start a fresh conversation. The
result's `thread_id` is then parsed from the agy log file.

## Usage from Python

    from ai_agent_bridge._ui_agy import send
    result = send(thread_id="48fd721e-...", message="ping", cwd=Path("/tmp"))
    print(result["final_message"])
"""

from __future__ import annotations

import argparse
import contextlib
import json
import re
import subprocess
import sys
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path

AGY_APP_DATA_ROOT = Path.home() / ".gemini" / "antigravity-cli"
AGY_CONVERSATIONS_ROOT = AGY_APP_DATA_ROOT / "conversations"
DEFAULT_TIMEOUT_S = 1800  # 30 min - covers most multi-turn dispatches

_AGY_CONVERSATION_RE = re.compile(
    r"\b(?:conversation=|Created conversation\s+|resuming conversation\s+)"
    r"(?P<id>[0-9a-fA-F-]{36})\b",
    re.IGNORECASE,
)
_NEW_THREAD_SENTINELS = {"", "-", "new", "fresh", "none", "null"}


def find_session_file(thread_id: str) -> Path | None:
    """Locate Antigravity's persisted conversation protobuf for *thread_id*."""
    if not thread_id:
        return None
    exact = AGY_CONVERSATIONS_ROOT / f"{thread_id}.pb"
    if exact.exists():
        return exact
    matches = sorted(
        AGY_CONVERSATIONS_ROOT.glob(f"*{thread_id}*.pb"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return matches[0] if matches else None


def _transcript_file(thread_id: str | None) -> Path | None:
    if not thread_id:
        return None
    path = (
        AGY_APP_DATA_ROOT
        / "brain"
        / thread_id
        / ".system_generated"
        / "logs"
        / "transcript.jsonl"
    )
    return path if path.exists() else None


def _read_transcript_events(thread_id: str | None) -> list[dict]:
    transcript = _transcript_file(thread_id)
    if transcript is None:
        return []

    events: list[dict] = []
    try:
        lines = transcript.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    for line in lines:
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def _parse_stdout_events(stdout: str) -> list[dict]:
    """Parse stdout JSON lines, or wrap plain print-mode stdout as one event."""
    events: list[dict] = []
    saw_json = False
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
            saw_json = True

    if saw_json:
        return events

    text = stdout.strip()
    if not text:
        return []
    return [{"type": "stdout_text", "content": text}]


def _extract_final_message(events: list[dict]) -> str | None:
    """Pick the last informative model message from agy or fallback events."""
    final_content: str | None = None

    for evt in events:
        event_type = evt.get("type")
        content = evt.get("content")
        if event_type in {"MODEL_RESPONSE", "PLANNER_RESPONSE", "stdout_text"}:
            if isinstance(content, str) and content.strip():
                final_content = content.strip()
            continue

        # Keep this fallback compatible with Codex-style synthetic tests and
        # future agy JSON stream shapes.
        if event_type == "item.completed":
            item = evt.get("item", {})
            item_type = item.get("type")
            if item_type == "agent_message":
                text = item.get("text") or item.get("content")
                if isinstance(text, str) and text.strip():
                    final_content = text.strip()
            elif item_type == "command_execution":
                output = item.get("aggregated_output")
                if isinstance(output, str) and output.strip():
                    final_content = output.strip()

    return final_content


def _thread_arg_is_new(thread_id: str | None) -> bool:
    return thread_id is None or thread_id.strip().lower() in _NEW_THREAD_SENTINELS


def _conversation_id_from_log(log_file: Path) -> str | None:
    latest: str | None = None
    try:
        with log_file.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                match = _AGY_CONVERSATION_RE.search(line)
                if match:
                    latest = match.group("id")
    except OSError:
        return None
    return latest


def _decode_timeout_text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def send(
    thread_id: str | None,
    message: str,
    *,
    bridge_id: str | None = None,
    cwd: Path | None = None,
    timeout_s: int = DEFAULT_TIMEOUT_S,
) -> dict:
    """Send a prompt to an Antigravity UI conversation via `agy --print`.

    Args:
        thread_id: Antigravity conversation id. Pass None, "", "-", or
            "new" to start a fresh conversation.
        message: prompt body. A `Bridge-ID: <id>` line is prepended for
            correlation; the receiving agent should echo the Bridge-ID in
            its reply if asked.
        bridge_id: correlation id (auto-generated if None).
        cwd: working directory for the agy subprocess. If None, inherits
            the caller's cwd. Agy chooses workspace context from this cwd.
        timeout_s: max wall-clock for the agy subprocess (default 30 min).

    Returns:
        dict with:
            bridge_id (str), thread_id (str | None), exit_code (int),
            events (list[dict] parsed from agy transcript/stdout),
            final_message (str | None), duration_s (float),
            session_file (str | None) for the conversation protobuf,
            stderr (str).
    """
    bridge_id = bridge_id or f"bridge-{uuid.uuid4().hex[:8]}"
    framed_message = f"Bridge-ID: {bridge_id}\n\n{message}"
    requested_thread_id = None if _thread_arg_is_new(thread_id) else thread_id
    session_file = find_session_file(requested_thread_id or "")
    preexisting_transcript_count = (
        len(_read_transcript_events(requested_thread_id)) if requested_thread_id else 0
    )

    log_path = Path(tempfile.gettempdir()) / f"agy-ui-bridge-{bridge_id}.log"
    cmd = [
        "agy",
        "--print-timeout",
        f"{timeout_s}s",
        "--dangerously-skip-permissions",
        "--log-file",
        str(log_path),
    ]
    if requested_thread_id:
        cmd += ["--conversation", requested_thread_id]
    cmd += ["--print", framed_message]

    start = datetime.now(UTC)
    try:
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
            stdout = _decode_timeout_text(e.stdout)
            stderr = f"[timeout after {timeout_s}s]\n{_decode_timeout_text(e.stderr)}"
            exit_code = -1
        duration_s = (datetime.now(UTC) - start).total_seconds()

        resolved_thread_id = requested_thread_id or _conversation_id_from_log(log_path)
        if resolved_thread_id and session_file is None:
            session_file = find_session_file(resolved_thread_id)

        stdout_events = _parse_stdout_events(stdout)
        all_transcript_events = _read_transcript_events(resolved_thread_id)
        if requested_thread_id and resolved_thread_id == requested_thread_id:
            transcript_events = all_transcript_events[preexisting_transcript_count:]
        else:
            transcript_events = all_transcript_events
        events = transcript_events or stdout_events
        final_message = _extract_final_message(events) or _extract_final_message(stdout_events)

        return {
            "bridge_id": bridge_id,
            "thread_id": resolved_thread_id,
            "exit_code": exit_code,
            "events": events,
            "final_message": final_message,
            "duration_s": duration_s,
            "session_file": str(session_file) if session_file else None,
            "stderr": stderr,
        }
    finally:
        with contextlib.suppress(OSError):
            log_path.unlink()


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ab send-agy-ui",
        description=(
            "Send a prompt to an Antigravity UI conversation via "
            "`agy --conversation ... --print`. Returns the agy subprocess "
            "exit code."
        ),
    )
    parser.add_argument(
        "--thread",
        default=None,
        help=(
            "Antigravity conversation id. Omit or pass 'new' to start a "
            "fresh conversation."
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
            "Working directory for the agy subprocess. Agy will choose "
            "workspace context from this cwd."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_S,
        help=f"Max wall-clock seconds (default {DEFAULT_TIMEOUT_S}).",
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
