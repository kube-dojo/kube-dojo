"""Send a prompt to a running Codex Desktop UI session via `codex exec resume`.

Lane 1 implementation from issue #2285 (agent bridge — send + receive to
running Codex UI / Cursor / Claude Code Desktop sessions).

## How it works

`codex exec resume <THREAD_UUID> --json -` (Codex CLI 0.133.0+) resumes a
persisted thread non-interactively. The subprocess emits a JSON event stream
on stdout containing turn events, item executions, and the agent's final
message. We feed the prompt via stdin (prefixed with a `Bridge-ID:` line for
correlation), then parse the stream.

## Empirical findings (2026-05-25 bridge probe)

The probe ran `codex exec resume 019e6063-... --json -` with a small prompt,
targeting a thread that the Codex Desktop process held open for write.
Observed behavior:

1. The original session JSONL grew (codex APPENDED events). The live UI
   process (PID 83697) and the resume subprocess BOTH wrote to the same
   rollout file. The thread state is consistent on disk regardless of
   which subprocess produced an event.
2. A NEW parallel rollout JSONL was ALSO created (new UUID, sharing thread
   history). This is harmless overhead — both files reflect the same turn.
3. The resume subprocess inherits the caller's CWD. Codex executed
   `git rev-parse --short HEAD` and saw the caller's commit SHA, NOT the
   UI session's worktree HEAD. Callers wanting the work to happen in a
   specific worktree must `cd` there before invoking (or use `cwd=` here).
4. Whether the visible Codex Desktop window displays the new turn live is
   not verified here. The thread state is consistent on disk — re-opening
   the same thread in the UI shows the appended events regardless.

## Usage from CLI

    ab send-codex-ui --thread <UUID> "your message"
    ab send-codex-ui --thread <UUID> --from-file relay.md
    ab send-codex-ui --thread <UUID> --cwd ~/some/worktree "message"

## Usage from Python

    from ai_agent_bridge._ui_codex import send
    result = send(thread_id="019e6063-...", message="ping", cwd=Path("/tmp"))
    print(result["final_message"])
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

CODEX_SESSIONS_ROOT = Path.home() / ".codex" / "sessions"
DEFAULT_TIMEOUT_S = 1800  # 30 min — covers most multi-turn dispatches


def find_session_file(thread_id: str) -> Path | None:
    """Locate the most recent rollout JSONL for a given thread UUID.

    Codex stores session JSONLs as
    `~/.codex/sessions/YYYY/MM/DD/rollout-<timestamp>-<UUID>.jsonl`. The
    `<UUID>` segment matches the thread id. There may be multiple files
    per thread when `codex exec resume` has been invoked previously; we
    return the most recently modified.
    """
    matches = sorted(
        CODEX_SESSIONS_ROOT.glob(f"**/rollout-*{thread_id}.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return matches[0] if matches else None


def _extract_final_message(events: list[dict]) -> str | None:
    """Pick the last informative message from a stream of resume events.

    Prefer the last `agent_message` content. Fall back to the last
    completed `command_execution`'s aggregated_output if no agent_message
    fired (e.g. when the prompt asked codex to print a shell line directly).
    """
    final_agent_msg: str | None = None
    final_cmd_output: str | None = None
    for evt in events:
        if evt.get("type") != "item.completed":
            continue
        item = evt.get("item", {})
        item_type = item.get("type")
        if item_type == "agent_message":
            final_agent_msg = item.get("text") or item.get("content")
        elif item_type == "command_execution":
            final_cmd_output = item.get("aggregated_output")
    return final_agent_msg or final_cmd_output


def send(
    thread_id: str,
    message: str,
    *,
    bridge_id: str | None = None,
    cwd: Path | None = None,
    timeout_s: int = DEFAULT_TIMEOUT_S,
) -> dict:
    """Send a prompt to a running Codex Desktop UI session via `codex exec resume`.

    Args:
        thread_id: UUID of the persisted codex thread (find via
            `codex sessions list` or by inspecting `~/.codex/sessions/`
            for a rollout JSONL whose codex process holds it open for write).
        message: prompt body. A `Bridge-ID: <id>` line is prepended for
            correlation; the receiving agent should echo the Bridge-ID
            in its reply if asked.
        bridge_id: correlation id (auto-generated if None).
        cwd: working directory for the codex subprocess. If None, inherits
            the caller's cwd. Codex will run shell commands against this
            directory's git state — important when targeting a worktree.
        timeout_s: max wall-clock for the codex subprocess (default 30 min).

    Returns:
        dict with:
            bridge_id (str), thread_id (str), exit_code (int),
            events (list[dict] of parsed JSON event lines from stdout),
            final_message (str | None) — best-effort extraction,
            duration_s (float), session_file (str | None) — path to the
            original UI session JSONL if locatable, stderr (str).
    """
    bridge_id = bridge_id or f"bridge-{uuid.uuid4().hex[:8]}"
    framed_message = f"Bridge-ID: {bridge_id}\n\n{message}"
    session_file = find_session_file(thread_id)

    start = datetime.now(UTC)
    try:
        proc = subprocess.run(
            ["codex", "exec", "resume", "--json", thread_id, "-"],
            input=framed_message,
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

    return {
        "bridge_id": bridge_id,
        "thread_id": thread_id,
        "exit_code": exit_code,
        "events": events,
        "final_message": _extract_final_message(events),
        "duration_s": duration_s,
        "session_file": str(session_file) if session_file else None,
        "stderr": stderr,
    }


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ab send-codex-ui",
        description=(
            "Send a prompt to a running Codex Desktop UI session via "
            "`codex exec resume`. Lane 1 from issue #2285. "
            "Returns the codex subprocess exit code."
        ),
    )
    parser.add_argument(
        "--thread",
        required=True,
        help=(
            "Codex thread UUID. Find via `codex sessions list --last` or "
            "by inspecting `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`"
            " (the file whose codex process holds it open for write)."
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
            "Working directory for the codex subprocess. Codex will run "
            "shell commands against this directory's git state — point it "
            "at the target worktree when relevant."
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
    elif args.message:
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
