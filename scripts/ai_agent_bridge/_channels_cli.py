"""CLI subcommands for the channel bridge (#1190 Phase B.3).

This module is deliberately SEPARATE from ``_cli.py`` so that adding
channel commands doesn't touch the 600-line legacy CLI file more than
necessary. ``_cli.py`` imports ``register_channel_commands`` and
``dispatch_channel_command`` from this module — one line each — and
everything else lives here.

## CLI surface

```
ab channel new <name> [--description D] [--include C,...] [--agents A,...]
ab channel list
ab channel info <name>
ab channel context <name> [--edit] [--show]
ab channel tail <name> [--n N] [--thread TID]
ab channel watch <thread_id> [--follow] [--event-stream]

ab post <channel> <body> [--to A,...] [--parent ID] [--corr ID]
ab p <channel> <agent> <body>                    # shorthand

ab inbox run <agent> [--once] [--max-messages N] [--stop-after-seconds N]
ab inbox show <agent>
ab sync <agent> | ab sync --all

ab discuss <channel> <body> --with A,B [--max-rounds N]   # B.4, stub for now
```

All commands use the storage primitives in ``_channels``. They do NOT
invoke agents — that's B.4 (``ab discuss``) and the legacy ``ask-*``
commands handle the agent-calling side.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from typing import Any

from . import _channels
from ._channels_watch import watch_channel_events

# ── argparse registration ────────────────────────────────────────────


def register_channel_commands(subparsers: Any) -> None:
    """Register all channel-related CLI subcommands on a subparsers object.

    Called from ``_cli._build_parser()`` so that ``ai_agent_bridge -h``
    shows the channel commands alongside the legacy ``ask-*`` commands.
    """
    # ── top-level: channel group ──────────────────────────────────
    channel_parser = subparsers.add_parser(
        "channel",
        help="Channel management (new/list/info/context/tail)",
    )
    channel_sub = channel_parser.add_subparsers(
        dest="channel_command",
        required=True,
    )

    # ab channel new
    new_parser = channel_sub.add_parser("new", help="Create a new channel")
    new_parser.add_argument("name", help="Channel name (lowercase-kebab-case)")
    new_parser.add_argument(
        "--description", "-d", default="",
        help="One-line description of the channel's topic",
    )
    new_parser.add_argument(
        "--include", default="",
        help="Comma-separated list of channels to auto-include (e.g. 'shared')",
    )
    new_parser.add_argument(
        "--agents", default="",
        help="Comma-separated list of default subscriber agents",
    )

    # ab channel list
    channel_sub.add_parser(
        "list",
        help="List all channels with row counts and last activity",
    )

    # ab channel info
    info_parser = channel_sub.add_parser(
        "info",
        help="Show channel metadata + context preview + pending counts",
    )
    info_parser.add_argument("name", help="Channel name")

    # ab channel context
    ctx_parser = channel_sub.add_parser(
        "context",
        help="Edit or show a channel's pinned context.md",
    )
    ctx_parser.add_argument("name", help="Channel name")
    ctx_parser.add_argument(
        "--edit", action="store_true",
        help="Open context.md in $EDITOR (creates it if missing)",
    )
    ctx_parser.add_argument(
        "--show", action="store_true",
        help="Print context.md to stdout (default if no flags)",
    )

    # ab channel tail
    tail_parser = channel_sub.add_parser(
        "tail",
        help="Read the most recent messages from a channel",
    )
    tail_parser.add_argument("name", help="Channel name")
    tail_parser.add_argument(
        "-n", "--limit", type=int, default=20,
        help="How many recent messages to show (default: 20)",
    )
    tail_parser.add_argument(
        "--thread", default=None,
        help="Show all messages in a specific thread_id instead of channel tail",
    )
    tail_parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON instead of human-readable",
    )

    # ab channel watch
    watch_parser = channel_sub.add_parser(
        "watch",
        help="Replay and optionally follow progress events for one thread",
    )
    watch_parser.add_argument("thread_id", help="Thread ID to watch")
    watch_parser.add_argument(
        "--follow",
        action="store_true",
        help="Keep polling for newly appended events",
    )
    watch_parser.add_argument(
        "--event-stream",
        action="store_true",
        help="Emit JSONL rows for machine readers",
    )

    # ── top-level: post ───────────────────────────────────────────
    post_parser = subparsers.add_parser(
        "post",
        help="Post a message to a channel (full form)",
    )
    post_parser.add_argument("channel", help="Channel name")
    post_parser.add_argument("body", help="Message body (use '-' for stdin)")
    post_parser.add_argument(
        "--to", default="",
        help="Comma-separated list of recipient agents (default: channel subscribers)",
    )
    post_parser.add_argument(
        "--parent", default=None,
        help="parent message_id — marks this as a reply",
    )
    post_parser.add_argument(
        "--corr", default=None,
        help="correlation_id — shared across a fanout event",
    )
    post_parser.add_argument(
        "--from-agent", default="user",
        choices=list(_channels.VALID_AGENTS),
        help="Sender agent (default: user)",
    )
    post_parser.add_argument(
        "--no-snapshot", action="store_true",
        help="Skip context/monitor snapshot (tests and system posts)",
    )

    # ── top-level: p (shortcut) ───────────────────────────────────
    p_parser = subparsers.add_parser(
        "p",
        help="Quick post: ab p <channel> <agent> <body>",
    )
    p_parser.add_argument("channel", help="Channel name")
    p_parser.add_argument(
        "agent",
        choices=list(_channels.VALID_AGENTS),
        help="Single recipient agent",
    )
    p_parser.add_argument("body", help="Message body (use '-' for stdin)")

    # ── top-level: inbox extensions on the legacy parser ──────────
    inbox_parser = subparsers.choices.get("inbox")
    if inbox_parser is not None:
        inbox_sub = inbox_parser.add_subparsers(
            dest="inbox_command",
            required=False,
        )

        inbox_run = inbox_sub.add_parser(
            "run",
            help="Drain one channel inbox via the thread-coalesced worker",
        )
        inbox_run.add_argument(
            "agent",
            choices=list(_channels.VALID_AGENTS),
            help="Agent inbox to drain",
        )
        inbox_mode = inbox_run.add_mutually_exclusive_group()
        inbox_mode.add_argument(
            "--until-idle",
            action="store_true",
            help="Drain until no more eligible deliveries remain (default)",
        )
        inbox_mode.add_argument(
            "--once",
            action="store_true",
            help="Process one claimed thread and exit",
        )
        inbox_run.add_argument(
            "--max-messages",
            type=int,
            default=None,
            help="Soft cap on claimed deliveries for this run",
        )
        inbox_run.add_argument(
            "--stop-after-seconds",
            type=int,
            default=None,
            help="Stop after this many seconds between thread claims",
        )

        inbox_show = inbox_sub.add_parser(
            "show",
            help="Show pending/processing/failed channel deliveries for one agent",
        )
        inbox_show.add_argument(
            "agent",
            choices=list(_channels.VALID_AGENTS),
            help="Agent inbox to inspect",
        )

    # ── top-level: sync ───────────────────────────────────────────
    sync_parser = subparsers.add_parser(
        "sync",
        help="Manual inbox-drain fallback for one agent or all agents",
    )
    sync_parser.add_argument(
        "agent",
        nargs="?",
        choices=list(_channels.VALID_AGENTS),
        help="Single agent inbox to drain",
    )
    sync_parser.add_argument(
        "--all",
        action="store_true",
        help="Drain every agent inbox in sequence",
    )

    # ── top-level: discuss (B.4 stub) ─────────────────────────────
    discuss_parser = subparsers.add_parser(
        "discuss",
        help="Multi-agent discussion with round limit (B.4)",
    )
    discuss_parser.add_argument("channel", help="Channel name")
    discuss_parser.add_argument("body", help="Discussion topic (use '-' for stdin)")
    discuss_parser.add_argument(
        "--with", dest="with_agents", required=True,
        help="Comma-separated list of participating agents",
    )
    discuss_parser.add_argument(
        "--max-rounds", type=int, default=2,
        help="Maximum discussion rounds (default: 2, cap: 4)",
    )


# ── dispatch ──────────────────────────────────────────────────────────


def dispatch_channel_command(args) -> int:
    """Route an argparse ``Namespace`` to the right handler.

    Returns the process exit code (0 on success, non-zero on failure).
    Called from ``_cli._dispatch_command()`` when ``args.command`` is
    one of the channel commands.
    """
    command = args.command
    if command == "channel":
        return _dispatch_channel_group(args)
    if command == "inbox":
        return _dispatch_inbox_command(args)
    if command == "post":
        return _handle_post(args)
    if command == "p":
        return _handle_p(args)
    if command == "sync":
        return _handle_sync(args)
    if command == "discuss":
        return _handle_discuss(args)
    print(f"unknown channel command: {command}", file=sys.stderr)
    return 2


def _dispatch_channel_group(args) -> int:
    sub = args.channel_command
    if sub == "new":
        return _handle_channel_new(args)
    if sub == "list":
        return _handle_channel_list(args)
    if sub == "info":
        return _handle_channel_info(args)
    if sub == "context":
        return _handle_channel_context(args)
    if sub == "tail":
        return _handle_channel_tail(args)
    if sub == "watch":
        return _handle_channel_watch(args)
    print(f"unknown subcommand: channel {sub}", file=sys.stderr)
    return 2


def _dispatch_inbox_command(args) -> int:
    """Route `ab inbox ...` channel-worker subcommands."""
    sub = getattr(args, "inbox_command", None)
    if sub == "run":
        return _handle_inbox_run(args)
    if sub == "show":
        return _handle_inbox_show(args)
    print("unknown subcommand: inbox", file=sys.stderr)
    return 2


# ── handlers ──────────────────────────────────────────────────────────


def _resolve_body(body_arg: str) -> str:
    """Accept '-' to mean 'read from stdin'."""
    if body_arg == "-":
        return sys.stdin.read()
    return body_arg


def _parse_csv(s: str) -> list[str]:
    return [item.strip() for item in s.split(",") if item.strip()]


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _format_age(from_iso: str, *, now: datetime | None = None) -> str:
    """Render a compact human duration such as `12m` or `6h12m`."""
    current = now or _now_utc()
    delta = max(current - _parse_iso(from_iso), timedelta())
    total_minutes = int(delta.total_seconds() // 60)
    days, rem_minutes = divmod(total_minutes, 24 * 60)
    hours, minutes = divmod(rem_minutes, 60)
    if days > 0:
        return f"{days}d{hours}h"
    if hours > 0:
        return f"{hours}h{minutes}m"
    return f"{minutes}m"


def _parse_backlog_warn_hours() -> float:
    """Return the backlog warning threshold in hours."""
    raw_value = os.environ.get("AB_BACKLOG_WARN_HOURS", "2").strip()
    try:
        hours = float(raw_value)
    except ValueError:
        return 2.0
    return hours if hours > 0 else 2.0


def _run_exit_code(deliveries_failed: int, aborted: bool) -> int:
    """Map inbox-worker outcomes to the CLI exit codes from #1192."""
    if aborted:
        return 2
    if deliveries_failed > 0:
        return 1
    return 0


def _print_inbox_run_summary(summary: Any, *, duration_s: float) -> None:
    """Render the one-line inbox worker summary expected by #1192."""
    print(
        "processed: "
        f"{summary.deliveries_claimed} deliveries | "
        f"{summary.threads_processed} threads | "
        f"{summary.deliveries_failed} failed | "
        f"duration: {duration_s:.1f}s"
    )


def _query_inbox_show(agent: str) -> dict[str, Any]:
    """Return read-only inbox status details for one agent."""
    from ._db import get_db

    now = _now_utc()
    failed_cutoff = (now - timedelta(hours=24)).isoformat()

    conn = get_db()
    try:
        pending = conn.execute(
            """
            SELECT COUNT(*) AS count, MIN(cm.created_at) AS oldest_created_at
            FROM deliveries d
            JOIN channel_messages cm ON cm.message_id = d.message_id
            WHERE d.to_agent = ? AND d.status = 'pending'
            """,
            (agent,),
        ).fetchone()
        processing = conn.execute(
            """
            SELECT COUNT(*) AS count, MIN(d.lease_until) AS lease_until
            FROM deliveries d
            WHERE d.to_agent = ? AND d.status = 'processing'
            """,
            (agent,),
        ).fetchone()
        failed = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM deliveries d
            JOIN channel_messages cm ON cm.message_id = d.message_id
            WHERE d.to_agent = ?
              AND d.status = 'failed'
              AND cm.created_at >= ?
            """,
            (agent, failed_cutoff),
        ).fetchone()
        oldest = conn.execute(
            """
            SELECT cm.channel, cm.thread_id, cm.from_agent, cm.body
            FROM deliveries d
            JOIN channel_messages cm ON cm.message_id = d.message_id
            WHERE d.to_agent = ? AND d.status = 'pending'
            ORDER BY cm.created_at ASC, d.delivery_id ASC
            LIMIT 1
            """,
            (agent,),
        ).fetchone()
    finally:
        conn.close()

    preview = None
    if oldest is not None:
        body = str(oldest["body"]).replace("\n", " ").strip()
        preview = {
            "channel": str(oldest["channel"]),
            "thread_id": str(oldest["thread_id"]),
            "from_agent": str(oldest["from_agent"]),
            "body": body[:60] + ("..." if len(body) > 60 else ""),
        }

    return {
        "pending_count": int(pending["count"]) if pending else 0,
        "oldest_created_at": (
            str(pending["oldest_created_at"])
            if pending and pending["oldest_created_at"]
            else None
        ),
        "processing_count": int(processing["count"]) if processing else 0,
        "processing_lease_until": (
            str(processing["lease_until"])
            if processing and processing["lease_until"]
            else None
        ),
        "failed_count": int(failed["count"]) if failed else 0,
        "preview": preview,
    }


def _pending_backlog_rows() -> list[dict[str, Any]]:
    """Return pending-delivery backlog rows used for the warning banner."""
    from ._db import get_db

    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT d.to_agent, COUNT(*) AS count, MIN(cm.created_at) AS oldest_created_at
            FROM deliveries d
            JOIN channel_messages cm ON cm.message_id = d.message_id
            WHERE d.status = 'pending'
            GROUP BY d.to_agent
            ORDER BY d.to_agent ASC
            """
        ).fetchall()
    finally:
        conn.close()

    return [
        {
            "agent": str(row["to_agent"]),
            "count": int(row["count"]),
            "oldest_created_at": str(row["oldest_created_at"]),
        }
        for row in rows
        if row["oldest_created_at"]
    ]


def _maybe_print_backlog_warnings() -> None:
    """Emit one stderr warning per agent with stale pending deliveries."""
    threshold = timedelta(hours=_parse_backlog_warn_hours())
    now = _now_utc()
    for row in _pending_backlog_rows():
        if now - _parse_iso(row["oldest_created_at"]) < threshold:
            continue
        age = _format_age(row["oldest_created_at"], now=now)
        print(
            f"⚠️  {row['agent']} has {row['count']} pending deliveries "
            f"(oldest {age}). Run 'ab inbox run {row['agent']}' to drain.",
            file=sys.stderr,
        )


def _handle_channel_new(args) -> int:
    include = _parse_csv(args.include) if args.include else []
    agents = _parse_csv(args.agents) if args.agents else []
    try:
        ch = _channels.create_channel(
            args.name,
            description=args.description,
            include=include,
            subscribers=agents,
            exist_ok=True,
        )
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1
    print(f"✅ channel '{ch['name']}' ready")
    if ch["include"]:
        print(f"   includes: {', '.join(ch['include'])}")
    if ch["subscribers"]:
        print(f"   subscribers: {', '.join(ch['subscribers'])}")
    return 0


def _handle_channel_list(args) -> int:
    channels = _channels.list_channels()
    if not channels:
        print("(no channels yet — try 'ab channel new shared')")
        return 0
    # Resolve row counts + latest message timestamps per channel
    from ._db import get_db
    conn = get_db()
    try:
        counts: dict[str, int] = {}
        latest: dict[str, str] = {}
        rows = conn.execute(
            """
            SELECT channel, COUNT(*) AS n, MAX(created_at) AS latest
            FROM channel_messages GROUP BY channel
            """
        ).fetchall()
        for r in rows:
            counts[r["channel"]] = r["n"]
            latest[r["channel"]] = r["latest"] or ""
    finally:
        conn.close()

    print(f"{'NAME':<20} {'MSGS':>6}  {'INCLUDES':<20}  {'SUBSCRIBERS':<30}  LATEST")
    print("-" * 100)
    for ch in channels:
        inc = ",".join(ch["include"]) or "-"
        sub = ",".join(ch["subscribers"]) or "-"
        n = counts.get(ch["name"], 0)
        ts = latest.get(ch["name"], "")[:19]
        print(f"{ch['name']:<20} {n:>6}  {inc:<20}  {sub:<30}  {ts}")
    return 0


def _handle_channel_info(args) -> int:
    ch = _channels.get_channel(args.name)
    if ch is None:
        print(f"❌ channel '{args.name}' does not exist", file=sys.stderr)
        return 1
    print(f"channel:     {ch['name']}")
    print(f"description: {ch['description'] or '(none)'}")
    print(f"created:     {ch['created_at']}")
    print(f"includes:    {', '.join(ch['include']) or '(none)'}")
    print(f"subscribers: {', '.join(ch['subscribers']) or '(none)'}")

    # Context preview
    ctx = _channels.load_channel_context(args.name)
    ctx_path = _channels.channel_context_path(args.name)
    if ctx_path.exists():
        size = ctx_path.stat().st_size
        print(f"\ncontext.md:  {ctx_path} ({size} bytes)")
        preview = ctx["body"].strip().split("\n")[:5]
        for line in preview:
            print(f"  | {line}")
    else:
        print(f"\ncontext.md:  {ctx_path} (missing)")
    if ctx["missing"]:
        print(f"⚠️  missing context for: {', '.join(ctx['missing'])}")
    return 0


def _handle_channel_context(args) -> int:
    path = _channels.channel_context_path(args.name)

    if args.edit:
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        # Create the file with a helpful template if it doesn't exist
        if not path.exists():
            template = (
                f"# {args.name} — pinned context\n\n"
                f"This file holds project-wide rules and conventions that "
                f"agents should see on every post to the '{args.name}' channel. "
                f"Keep it STABLE — volatile state (current sprint, commits) "
                f"comes from the Monitor API snapshot per-post.\n\n"
                f"## Rules\n\n- (add rules here)\n"
            )
            path.write_text(template, encoding="utf-8")
        editor = os.environ.get("EDITOR", "vi")
        # Support EDITOR="code --wait" style values where the env var
        # contains the launcher plus flags. shlex splits the string
        # respecting POSIX quoting so "nvim -R" and similar work.
        editor_argv = shlex.split(editor) if editor else ["vi"]
        try:
            result = subprocess.run([*editor_argv, str(path)])
        except FileNotFoundError:
            print(
                f"❌ editor '{editor_argv[0]}' not found on PATH "
                f"(set $EDITOR to a valid command)",
                file=sys.stderr,
            )
            return 1
        except PermissionError:
            print(
                f"❌ editor '{editor_argv[0]}' is not executable "
                f"(check file permissions)",
                file=sys.stderr,
            )
            return 1
        return result.returncode

    # Default = show
    if not path.exists():
        print(f"(no context.md at {path})")
        print(f"create one with: ab channel context {args.name} --edit")
        return 0
    print(path.read_text("utf-8"))
    return 0


def _handle_channel_tail(args) -> int:
    # Verify the channel exists before hitting the storage layer so
    # the user gets a clean error instead of a raw traceback.
    if _channels.get_channel(args.name) is None:
        print(f"❌ channel '{args.name}' does not exist", file=sys.stderr)
        return 1

    try:
        if args.thread:
            msgs = _channels.read(args.name, thread_id=args.thread)
            header = f"thread {args.thread[:12]} in {args.name}"
        else:
            msgs = _channels.read(args.name, tail=args.limit)
            header = f"{args.name} tail {len(msgs)} / {args.limit}"
    except (ValueError, KeyError) as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(msgs, indent=2, ensure_ascii=False))
        return 0

    print(f"=== {header} ===")
    if not msgs:
        print("(no messages)")
        return 0
    for m in msgs:
        ts = m["created_at"][:19]
        parent_str = f" ← {m['parent_id'][:8]}" if m["parent_id"] else ""
        print(
            f"[{ts}] {m['from_agent']}"
            f" (r{m['round_index']}{parent_str}): {m['body'][:200]}"
        )
        if len(m["body"]) > 200:
            print(f"   ... [{len(m['body']) - 200} more chars]")
    return 0


def _handle_channel_watch(args) -> int:
    try:
        return watch_channel_events(
            args.thread_id,
            follow=args.follow,
            event_stream=args.event_stream,
        )
    except ValueError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 1


def _handle_post(args) -> int:
    body = _resolve_body(args.body)
    if not body.strip():
        print("❌ empty body", file=sys.stderr)
        return 1

    ch = _channels.get_channel(args.channel)
    if ch is None:
        print(f"❌ channel '{args.channel}' does not exist", file=sys.stderr)
        return 1

    # Default recipients = channel subscribers
    to_agents = _parse_csv(args.to) if args.to else ch["subscribers"]

    try:
        result = _channels.post(
            args.channel,
            args.from_agent,
            body,
            to_agents=to_agents,
            parent_id=args.parent,
            correlation_id=args.corr,
            auto_snapshot=not args.no_snapshot,
        )
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1

    print(f"✅ posted to #{args.channel}")
    print(f"   message_id: {result['message_id']}")
    print(f"   thread_id:  {result['thread_id']}")
    if to_agents:
        print(f"   → {', '.join(to_agents)}  ({len(result['delivery_ids'])} deliveries)")
    return 0


def _handle_p(args) -> int:
    """Shortcut: ab p <channel> <agent> <body>."""
    # Rewrite to _handle_post's args shape
    class _Args:
        channel = args.channel
        body = args.body
        to = args.agent
        parent = None
        corr = None
        from_agent = "user"
        no_snapshot = False

    return _handle_post(_Args())


def _handle_inbox_run(args) -> int:
    """Handle `ab inbox run <agent>`."""
    from ._inbox import run_inbox

    until_idle = not args.once
    if args.until_idle:
        until_idle = True

    started_at = time.monotonic()
    try:
        summary = run_inbox(
            args.agent,
            max_messages=args.max_messages,
            until_idle=until_idle,
            stop_after_seconds=args.stop_after_seconds,
        )
    except ValueError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 1

    _print_inbox_run_summary(summary, duration_s=time.monotonic() - started_at)
    return _run_exit_code(summary.deliveries_failed, summary.aborted)


def _handle_inbox_show(args) -> int:
    """Handle `ab inbox show <agent>` with pure read-only queries."""
    status = _query_inbox_show(args.agent)

    print(f"{args.agent} inbox:")
    pending_line = f"  pending:    {status['pending_count']}"
    if status["oldest_created_at"]:
        pending_line += f" (oldest {_format_age(status['oldest_created_at'])} ago)"
    print(pending_line)

    processing_line = f"  processing: {status['processing_count']}"
    if status["processing_lease_until"]:
        processing_line += f" (lease until {status['processing_lease_until']})"
    print(processing_line)
    print(f"  failed (last 24h): {status['failed_count']}")
    print("  oldest preview:")
    preview = status["preview"]
    if preview is None:
        print("    (none)")
        return 0
    print(
        f"    [{preview['channel']}/{preview['thread_id'][:5]}] "
        f"{preview['from_agent']} → \"{preview['body']}\""
    )
    return 0


def _handle_sync(args) -> int:
    """Handle `ab sync` as a manual fallback inbox drain."""
    if args.all and args.agent is not None:
        print("❌ choose either an agent or --all, not both", file=sys.stderr)
        return 2
    if not args.all and args.agent is None:
        print("❌ sync requires an agent or --all", file=sys.stderr)
        return 2

    agents = list(_channels.VALID_AGENTS) if args.all else [args.agent]
    worst_exit_code = 0
    for agent in agents:
        class _Args:
            once = False
            until_idle = True
            max_messages = None
            stop_after_seconds = None

            def __init__(self, agent_name: str) -> None:
                self.agent = agent_name

        exit_code = _handle_inbox_run(_Args(agent))
        worst_exit_code = max(worst_exit_code, exit_code)
    return worst_exit_code


def _handle_discuss(args) -> int:
    """Multi-agent fan-out discussion with bounded rounds.

    Workflow:
      1. Post the user's question to the channel as a normal message
         with ``to_agents=with_list``. This creates the root message
         that everything else threads off of.
      2. For each round, build a per-agent prompt via
         ``_channels.build_agent_prompt`` — the pinned context + the
         channel history + a "please respond" instruction — and hand
         it off to every agent in parallel through
         ``agent_runtime.runner.invoke``. Each response lands back in
         the channel as a reply with ``parent_id`` set to the root.
      3. From round 2 onward, if all agents end their response with
         ``[AGREE]``, treat the round as converged and stop early.
         Round 1 is parallel fan-out — agents have not seen each
         other's replies — so round-1 ``[AGREE]`` cannot mean cross-
         agent assent and is explicitly ignored for convergence (the
         protocol always runs at least 2 rounds; ``--max-rounds`` is
         clamped to a minimum of 2 for the same reason). Otherwise
         continue until ``max_rounds`` is hit (capped at 4 regardless
         of caller).
      4. Print a one-line transcript summary at the end so the user
         can tail the thread for the full conversation.

    The implementation is deliberately lightweight — no new schema,
    no new tables, no new middleware. Everything routes through the
    existing channel primitives so the transcript is visible in the
    dashboard + CLI + API the moment a round resolves.
    """
    # Lazy import: agent_runtime pulls in the adapter stack and we
    # don't want that on every ``ab --help``.
    try:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        from agent_runtime.errors import (
            AgentStalledError,
            AgentTimeoutError,
            AgentUnavailableError,
            RateLimitedError,
        )
        from agent_runtime.runner import invoke as runtime_invoke
    except ImportError as e:
        print(f"❌ agent_runtime unavailable: {e}", file=sys.stderr)
        print(
            "   ab discuss needs the runtime adapters to be importable.",
            file=sys.stderr,
        )
        return 1

    # ── validate inputs ────────────────────────────────────────────
    with_agents = _parse_csv(args.with_agents)
    if not with_agents:
        print("❌ --with requires at least one agent", file=sys.stderr)
        return 1
    if len(with_agents) > 4:
        print(
            f"❌ --with accepts at most 4 agents, got {len(with_agents)}",
            file=sys.stderr,
        )
        return 1
    unknown = [a for a in with_agents if a not in _channels.VALID_AGENTS]
    if unknown:
        print(
            f"❌ unknown agent(s): {', '.join(unknown)} "
            f"(valid: {', '.join(sorted(_channels.VALID_AGENTS))})",
            file=sys.stderr,
        )
        return 1

    # Round 1 is parallel fan-out (agents haven't seen each other yet),
    # so the convergence guard at line ~1115 disallows round-1 short-
    # circuit. Setting `max_rounds = 1` would let the loop exit before
    # round 2 ever runs — agents would print "Forcing round 2" and then
    # immediately hit the `round_idx == max_rounds` break. Clamp the
    # floor to 2 so the round-1-cannot-converge invariant is actually
    # enforceable. Caught by codex review of PR #889.
    MAX_ROUNDS_CAP = 4
    MAX_ROUNDS_FLOOR = 2
    max_rounds = min(max(MAX_ROUNDS_FLOOR, args.max_rounds), MAX_ROUNDS_CAP)
    if args.max_rounds > MAX_ROUNDS_CAP:
        print(
            f"ℹ️  clamping --max-rounds {args.max_rounds} to {MAX_ROUNDS_CAP} "
            f"(hard cap — escalate to a human if 4 rounds don't converge)"
        )
    elif args.max_rounds < MAX_ROUNDS_FLOOR:
        print(
            f"ℹ️  clamping --max-rounds {args.max_rounds} to {MAX_ROUNDS_FLOOR} "
            f"(round 1 is parallel fan-out and cannot converge by design — "
            f"see _handle_discuss docstring)"
        )

    if _channels.get_channel(args.channel) is None:
        print(f"❌ channel '{args.channel}' does not exist", file=sys.stderr)
        return 1

    body = _resolve_body(args.body)
    if not body.strip():
        print("❌ empty discussion topic", file=sys.stderr)
        return 1

    # ── post the root question ────────────────────────────────────
    try:
        root = _channels.post(
            args.channel,
            "user",
            body,
            to_agents=with_agents,
            auto_snapshot=True,
        )
    except ValueError as e:
        print(f"❌ post failed: {e}", file=sys.stderr)
        return 1

    root_id = root["message_id"]
    correlation_id = root["thread_id"]  # one correlation per discussion
    print(
        f"📢 discuss #{args.channel} (max {max_rounds} round{'s' if max_rounds > 1 else ''}, "
        f"{len(with_agents)} participants)"
    )
    print(f"   root message: {root_id[:12]} / thread {correlation_id[:12]}")
    print()

    def _invoke_one(
        agent_name: str, prompt_text: str, round_idx: int
    ) -> tuple[str, str, bool]:
        """Run one agent for a specific round. Returns (agent, text, ok).

        ``round_idx`` is woven into the task_id so the agent_runtime
        usage log shows one row per (agent, round) — otherwise every
        row in a 4-round discussion would collide on the same task_id
        and the dashboard couldn't tell them apart.
        """
        try:
            result = runtime_invoke(
                agent_name,
                prompt_text,
                mode="read-only",
                task_id=f"discuss-{correlation_id[:8]}-r{round_idx}-{agent_name}",
                entrypoint="delegate",
                hard_timeout=900,
            )
        except RateLimitedError as exc:
            return (agent_name, f"[rate-limited: {exc}]", False)
        except (AgentStalledError, AgentTimeoutError) as exc:
            return (agent_name, f"[timeout: {exc}]", False)
        except AgentUnavailableError as exc:
            return (agent_name, f"[unavailable: {exc}]", False)
        except Exception as exc:  # defensive — never let one agent's
            # crash take down the whole discussion. KeyboardInterrupt
            # is BaseException, not Exception, so Ctrl+C still bubbles
            # up to the pool-shutdown branch in the main loop.
            return (agent_name, f"[error: {type(exc).__name__}: {exc}]", False)

        if not result.ok:
            return (
                agent_name,
                f"[failed: {result.stderr_excerpt or 'no response'}]",
                False,
            )
        return (agent_name, result.response.strip(), True)

    completed_rounds = 0
    for round_idx in range(1, max_rounds + 1):
        completed_rounds = round_idx
        print(f"── round {round_idx}/{max_rounds} ──────────────────────")

        # Every agent sees the full channel history (pinned context +
        # monitor state + recent posts including the root). The per-
        # round directive tells them what to produce.
        #
        # Round-1 vs round-2+ semantics differ structurally:
        #
        # - Round 1 is parallel fan-out — every agent answers the root
        #   question independently, NONE of them have seen any other
        #   agent's reply yet. So `[AGREE]` in round 1 cannot mean
        #   "I agree with the other agents" (no replies to agree with).
        #   It can only mean "I'm satisfied with my own first take."
        #   The convergence check below explicitly disallows round-1
        #   short-circuit because of this — see comment there.
        #
        # - Round 2+ is where agents see each other's round-1 (and
        #   later) replies via the channel history, and `[AGREE]` /
        #   `[DISAGREE]` becomes meaningful as cross-agent assent or
        #   pushback.
        #
        # This was originally a single uniform directive; that produced
        # false convergence in the собака-gender deliberation 2026-05-05
        # in the learn-ukrainian project (3 agents disagreed substantively
        # but all signed [AGREE] in round 1, short-circuiting before any
        # agent saw the disagreements). Ported to kubedojo from learn-
        # ukrainian commit 872d8376b0.
        if round_idx == 1:
            directive = (
                f"You are participating in a bounded multi-agent discussion "
                f"on #{args.channel}. This is round 1 of at most "
                f"{max_rounds}. The other participants are answering this "
                f"same root question in parallel right now — you have NOT "
                f"seen their replies. Produce your independent first take.\n\n"
                f"- Be concise but substantive. Cite file:line when relevant.\n"
                f"- Quote authoritative sources with specific entries; do "
                f"not paraphrase from memory.\n"
                f"- End your response with one of:\n"
                f"    [DISAGREE]  — your default in round 1; you have a "
                f"substantive position and want round 2 to compare it "
                f"against the other agents' first takes.\n"
                f"    [AGREE]     — only if your reading of the channel "
                f"context (pinned rules) makes the question trivially "
                f"resolved before any cross-agent comparison is needed. "
                f"Rare; default is [DISAGREE] in round 1.\n"
                f"- Even if all agents sign [AGREE] in round 1, the "
                f"protocol will NOT short-circuit until round 2+ — round 2 "
                f"is where you read each other and either confirm or push back."
            )
        else:
            directive = (
                f"You are participating in a bounded multi-agent discussion "
                f"on #{args.channel}. This is round {round_idx} of at most "
                f"{max_rounds}. Read the prior-round replies in the history "
                f"above (they are posted as replies to the root). Compare "
                f"them to your own prior position and decide.\n\n"
                f"- Be concise but substantive. Cite file:line when relevant.\n"
                f"- Push back on any other agent's claim you disagree with — "
                f"name the agent, quote the claim, give the counter-evidence.\n"
                f"- End your response with one of:\n"
                f"    [AGREE]     — you have read the other agents' prior "
                f"replies and you accept the converging position (or yours "
                f"is unchanged and the others now match it).\n"
                f"    [DISAGREE]  — you still have open substantive objections "
                f"after reading the others.\n"
                f"- If every agent ends with [AGREE], the discussion "
                f"short-circuits and stops before round {max_rounds}."
            )

        # history_tail must be big enough to preserve the root
        # question across every round. `tail` truncates from the
        # OLDEST end, so older messages can never push the root out —
        # we just need the window to span (1 root + all in-discussion
        # replies). The +10 is headroom for some pre-root channel
        # context so agents see recent project activity too.
        needed_history = 1 + len(with_agents) * max_rounds + 10
        try:
            prompt_obj = _channels.build_agent_prompt(
                args.channel, directive, history_tail=needed_history
            )
        except ValueError as e:
            print(f"❌ prompt build failed: {e}", file=sys.stderr)
            return 1
        prompt_text = prompt_obj["prompt"]
        print(
            f"   prompt {len(prompt_text)} chars "
            f"(history_tail={needed_history}, "
            f"dropped {prompt_obj.get('history_dropped', 0)})"
        )

        # ── parallel fan-out ──────────────────────────────────────
        # The `with` block calls pool.shutdown(wait=True) on exit. If
        # the user hits Ctrl+C mid-round we catch KeyboardInterrupt,
        # cancel all queued futures, and re-raise so the process
        # exits promptly instead of blocking on in-flight invocations
        # (which could be hold for up to hard_timeout=900 seconds).
        responses: dict[str, tuple[str, bool]] = {}
        pool = ThreadPoolExecutor(max_workers=len(with_agents))
        try:
            futures = {
                pool.submit(_invoke_one, agent, prompt_text, round_idx): agent
                for agent in with_agents
            }
            try:
                for fut in as_completed(futures):
                    agent, text, ok = fut.result()
                    responses[agent] = (text, ok)
                    status = "✅" if ok else "⚠️ "
                    preview = text.replace("\n", " ")[:80]
                    print(f"   {status} {agent}: {preview}")
            except KeyboardInterrupt:
                print(
                    "\n⚠️  interrupted — cancelling pending agent invocations",
                    file=sys.stderr,
                )
                for pending in futures:
                    pending.cancel()
                raise
        finally:
            # cancel_futures is Py3.9+. Tasks already running cannot
            # be cancelled mid-flight, but queued ones will be.
            pool.shutdown(wait=False, cancel_futures=True)

        # ── post each response as a reply to root ─────────────────
        # auto_snapshot=False here — the root message captured the
        # state of the world for the discussion; re-snapshotting on
        # every reply would mean N*max_rounds redundant Monitor API
        # fetches + context file reads + extra storage. The reply's
        # context is implicit from its parent_id anyway.
        for agent in with_agents:
            text, ok = responses[agent]
            reply_recipients = [name for name in with_agents if name != agent]
            try:
                _channels.post(
                    args.channel,
                    agent,
                    text,
                    to_agents=reply_recipients,
                    parent_id=root_id,
                    correlation_id=correlation_id,
                    kind="reply",
                    auto_snapshot=False,
                    pre_delivered=True,
                )
            except ValueError as e:
                print(
                    f"⚠️  failed to store {agent} response: {e}",
                    file=sys.stderr,
                )

        # ── convergence check ─────────────────────────────────────
        # All agents must (1) have succeeded, and (2) end their
        # response with the literal `[AGREE]` token at the tail.
        # Strict endswith() — substring match would false-positive on
        # "I don't [AGREE] with that. [DISAGREE]".
        #
        # CRITICAL: round 1 cannot short-circuit, even if every agent
        # signs [AGREE]. Round 1 is parallel fan-out — no agent has
        # seen any other agent's reply yet, so [AGREE] in round 1 is
        # an "I'm done with my own answer" signal, not cross-agent
        # assent. Forcing round 2 ensures at least one pass where
        # agents read each other's first takes and can surface
        # disagreement. Discovered 2026-05-05 in the собака-gender
        # deliberation in learn-ukrainian: Gemini hallucinated a
        # claim, Claude and Codex contradicted it, but all three
        # signed [AGREE] in round 1 and the protocol short-circuited
        # without any cross-agent comparison. Hallucination would have
        # shipped to curriculum if the transcript were taken at face
        # value. Ported from learn-ukrainian commit 872d8376b0.
        all_ok = all(ok for (_, ok) in responses.values())
        all_agreed = all_ok and all(
            text.strip().endswith("[AGREE]") for (text, _) in responses.values()
        )
        if all_agreed and round_idx >= 2:
            print()
            print(f"✅ converged at round {round_idx} — all agents signed off [AGREE]")
            break
        elif all_agreed and round_idx == 1:
            print()
            print(
                "ℹ️  all agents signed [AGREE] in round 1, but round 1 cannot "
                "short-circuit (parallel fan-out — agents have not seen each "
                "other's replies). Forcing round 2 for cross-agent comparison."
            )

        if round_idx == max_rounds:
            # Tell the caller WHY we stopped so escalation is obvious.
            # Same strict endswith check as convergence — substring
            # match would false-positive on "I don't [AGREE] with
            # that. [DISAGREE]" and report no disagreements.
            disagreeing = [
                a
                for a, (t, _) in responses.items()
                if not t.strip().endswith("[AGREE]")
            ]
            print()
            print(
                f"⚠️  hit max_rounds={max_rounds} without convergence. "
                f"Still disagreeing: {', '.join(disagreeing) or '(none? see errors)'}"
            )
            print(
                "   Escalate to a human or re-open the discussion with a "
                "tighter brief."
            )

    print()
    print(
        f"📊 discuss done after {completed_rounds} round(s). "
        f"Full thread: ab channel tail {args.channel} --thread {root_id}"
    )
    return 0
