"""CLI entry point: argument parsing, interactive mode, batch processing."""

import argparse
import sys
from pathlib import Path

from ._broker import bridge_status, broker_cleanup
from ._claude import ask_claude, process_for_claude
from ._db import get_db
from ._gemini import ask_gemini, converse_gemini, process_and_respond
from ._messaging import (
    acknowledge,
    acknowledge_all,
    check_inbox,
    get_conversation,
    read_message,
    send_message,
)
from ._model import check_model


def interactive_mode():
    """Interactive mode for testing."""
    print("🔄 AI Agent Bridge Interactive Mode")
    print("Commands: inbox [agent], read <id>, send <text> --to <agent>, ack <id>, conv <task_id>, process <id>, quit")
    print()

    while True:
        try:
            cmd = input("bridge> ").strip()
            if not cmd:
                continue

            if cmd.lower() in ["quit", "q", "exit"]:
                break

            parts = cmd.split()
            action = parts[0].lower()

            _dispatch_interactive(action, parts)

        except KeyboardInterrupt:
            print("\nBye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def _dispatch_interactive(action: str, parts: list[str]):
    """Dispatch a single interactive mode command."""
    if action == "inbox":
        agent = parts[1] if len(parts) > 1 else "gemini"
        check_inbox(agent)
    elif action == "read" and len(parts) > 1:
        read_message(int(parts[1]))
    elif action == "send" and len(parts) > 1:
        content = " ".join(parts[1:])
        send_message(content)
    elif action == "ack" and len(parts) > 1:
        ids = [int(x) for x in parts[1:]]
        acknowledge(ids)
    elif action == "conv" and len(parts) > 1:
        get_conversation(parts[1])
    elif action == "process" and len(parts) > 1:
        process_and_respond(int(parts[1]))
    else:
        print("Unknown command or missing arguments.")


def process_all_gemini(model: str = "gemini-3-flash-preview"):
    """Process ALL unread messages for Gemini in batch."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, task_id, from_llm, message_type, substr(content, 1, 50)
        FROM messages
        WHERE to_llm = 'gemini' AND acknowledged = 0
        ORDER BY id ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("📭 No unread messages for Gemini to process")
        return

    print(f"📬 Processing {len(rows)} unread message(s) for Gemini...\n")

    success = 0
    failed = 0

    for row in rows:
        msg_id, _task_id, from_llm, _msg_type, preview = row
        preview = preview.replace('\n', ' ')[:40]
        print(f"━━━ Processing [{msg_id}] from {from_llm}: {preview}...")

        try:
            process_and_respond(msg_id, model)
            success += 1
            print("    ✅ Done\n")
        except Exception as e:
            failed += 1
            print(f"    ❌ Failed: {e}\n")

    print(f"\n{'═' * 50}")
    print(f"📊 Results: {success} succeeded, {failed} failed out of {len(rows)} total")


def process_all_claude(new_session: bool = False):
    """Process ALL unread messages for Claude in batch (headless)."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, task_id, from_llm, message_type, substr(content, 1, 50)
        FROM messages
        WHERE to_llm = 'claude' AND acknowledged = 0
        ORDER BY id ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("📭 No unread messages for Claude to process")
        return

    print(f"📬 Processing {len(rows)} unread message(s) for Claude (headless)...\n")

    success = 0
    failed = 0

    for row in rows:
        msg_id, _task_id, from_llm, _msg_type, preview = row
        preview = preview.replace('\n', ' ')[:40]
        print(f"━━━ Processing [{msg_id}] from {from_llm}: {preview}...")

        try:
            process_for_claude(msg_id, new_session)
            success += 1
            print("    ✅ Done\n")
        except Exception as e:
            failed += 1
            print(f"    ❌ Failed: {e}\n")

    print(f"\n{'═' * 50}")
    print(f"📊 Results: {success} succeeded, {failed} failed out of {len(rows)} total")


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(description="AI Agent Bridge - Claude/Gemini/LLM Communication")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # inbox
    inbox_parser = subparsers.add_parser("inbox", help="Check inbox for messages")
    inbox_parser.add_argument("--for", dest="for_llm", default="gemini", choices=['gemini', 'claude'],
                             help="Check inbox for which agent (default: gemini)")

    # read
    read_parser = subparsers.add_parser("read", help="Read a specific message")
    read_parser.add_argument("message_id", type=int, help="Message ID to read")

    # send
    send_parser = subparsers.add_parser("send", help="Send message to another agent")
    send_parser.add_argument("content", help="Message content")
    send_parser.add_argument("--to", dest="to_llm", default="claude", choices=['claude', 'gemini'],
                            help="Target agent (default: claude)")
    send_parser.add_argument("--from", dest="from_llm", default="gemini",
                            help="Sender agent name (default: gemini)")
    send_parser.add_argument("--task-id", help="Task ID for grouping")
    send_parser.add_argument("--type", default="response", help="Message type")
    send_parser.add_argument("--data", help="Path to data file to attach")
    send_parser.add_argument("--from-model", dest="from_model", help="Specific model ID of sender")
    send_parser.add_argument("--to-model", dest="to_model", help="Specific model ID of receiver")

    # ack
    ack_parser = subparsers.add_parser("ack", help="Acknowledge message(s)")
    ack_parser.add_argument("message_ids", type=int, nargs='+', help="Message ID(s) to acknowledge")

    # ack-all
    ack_all_parser = subparsers.add_parser("ack-all", help="Acknowledge ALL unread messages for an agent")
    ack_all_parser.add_argument("agent", choices=['claude', 'gemini'], help="Agent whose inbox to clear")

    # conversation
    conv_parser = subparsers.add_parser("conversation", help="Get conversation history")
    conv_parser.add_argument("task_id", help="Task ID")

    # process (for Gemini)
    proc_parser = subparsers.add_parser("process", help="Process message with Gemini and respond")
    proc_parser.add_argument("message_id", type=int, help="Message ID to process")
    proc_parser.add_argument("--model", default="gemini-3-flash-preview", help="Gemini model")
    proc_parser.add_argument("--no-timeout", dest="no_timeout", action="store_true",
                             help="Run sync without timeout (used internally by fire-and-forget)")

    # process-claude
    proc_claude_parser = subparsers.add_parser("process-claude", help="Process message with Claude CLI (headless)")
    proc_claude_parser.add_argument("message_id", type=int, help="Message ID for Claude to process")
    proc_claude_parser.add_argument("--new-session", dest="new_session", action="store_true",
                                    help="Force new session even if one exists for this task")
    proc_claude_parser.add_argument("--async", dest="fire_and_forget", action="store_true",
                                    help="Launch Claude in background (no timeout).")
    proc_claude_parser.add_argument("--no-timeout", dest="no_timeout", action="store_true",
                                    help="Run sync without timeout (used internally by fire-and-forget)")

    # ask-claude
    ask_claude_parser = subparsers.add_parser("ask-claude", help="Send message AND invoke Claude (one-step)")
    ask_claude_parser.add_argument("content", help="Message content")
    ask_claude_parser.add_argument("--task-id", required=True, help="Task ID (required for session tracking)")
    ask_claude_parser.add_argument("--type", default="query", help="Message type (default: query)")
    ask_claude_parser.add_argument("--data", help="Path to data file to attach")
    ask_claude_parser.add_argument("--new-session", dest="new_session", action="store_true",
                                   help="Force new session even if one exists")
    ask_claude_parser.add_argument("--from", dest="from_llm", default="gemini",
                                   help="Sender agent family (gemini, claude). Default: gemini")
    ask_claude_parser.add_argument("--from-model", dest="from_model",
                                   help="Exact sender model ID")
    ask_claude_parser.add_argument("--to-model", dest="to_model",
                                   help="Target model ID")

    # ask-gemini
    ask_gemini_parser = subparsers.add_parser("ask-gemini", help="Send message AND invoke Gemini (one-step)")
    ask_gemini_parser.add_argument("content", help="Message content (use '-' to read from stdin)")
    ask_gemini_parser.add_argument("--task-id", required=True, help="Task ID (required for session tracking)")
    ask_gemini_parser.add_argument("--type", default="query", help="Message type (default: query)")
    ask_gemini_parser.add_argument("--data", help="Path to data file to attach")
    ask_gemini_parser.add_argument("--model", default="gemini-3-flash-preview", help="Gemini model to use")
    ask_gemini_parser.add_argument("--from-model", dest="from_model",
                                   help="Exact sender model ID")
    ask_gemini_parser.add_argument("--async", dest="async_mode", action="store_true",
                                   help="Queue only, don't invoke Gemini CLI")
    ask_gemini_parser.add_argument("--stdout-only", dest="stdout_only", action="store_true",
                                   help="Don't route full response through broker.")
    ask_gemini_parser.add_argument("--output-path", dest="output_path",
                                   help="Gemini writes output to this file.")
    ask_gemini_parser.add_argument("--extract", nargs="*", metavar="TAG",
                                   help="Extract delimited content from output.")
    ask_gemini_parser.add_argument("--skip-model-check", dest="skip_model_check", action="store_true",
                                   help="Skip the model availability pre-flight check.")
    ask_gemini_parser.add_argument("--allow-write", dest="allow_write", action="store_true",
                                   help="Grant Gemini full bash + write access.")
    ask_gemini_parser.add_argument("--delimiters", dest="delimiters",
                                   help="Comma-separated delimiter names for --allow-write mode.")
    ask_gemini_parser.add_argument("--no-github", dest="no_github", action="store_true",
                                   help="Skip auto-posting review to GitHub issue")

    # converse — multi-turn conversation with Gemini
    converse_parser = subparsers.add_parser("converse", help="Multi-turn conversation with Gemini (includes history)")
    converse_parser.add_argument("content", help="Message content (use '-' to read from stdin)")
    converse_parser.add_argument("--task-id", required=True, help="Conversation thread ID (e.g., 'a1-1-planning')")
    converse_parser.add_argument("--model", default="gemini-3.1-pro-preview", help="Gemini model")
    converse_parser.add_argument("--no-github", dest="no_github", action="store_true",
                                 help="Skip auto-posting to GitHub")

    # process-all
    proc_all_parser = subparsers.add_parser("process-all", help="Process ALL unread messages with Gemini")
    proc_all_parser.add_argument("--model", default="gemini-3-flash-preview", help="Gemini model")

    # process-claude-all
    proc_claude_all_parser = subparsers.add_parser("process-claude-all", help="Process ALL unread messages with Claude")
    proc_claude_all_parser.add_argument("--new-session", dest="new_session", action="store_true",
                                        help="Force new sessions for each message")

    # check-model
    check_model_parser = subparsers.add_parser("check-model", help="Check if a Gemini model is available")
    check_model_parser.add_argument("model", help="Model name")

    # cleanup
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean stuck broker state")
    cleanup_parser.add_argument("--max-age", type=int, default=24, help="Force-ack messages older than N hours")
    cleanup_parser.add_argument("--dry-run", action="store_true", help="Report what would be cleaned")

    # status
    subparsers.add_parser("status", help="Show running bridge processes")

    # interactive
    subparsers.add_parser("interactive", help="Interactive mode")

    return parser


def _dispatch_command(args):
    """Dispatch parsed CLI arguments to the appropriate handler."""
    if args.command == "inbox":
        check_inbox(args.for_llm)
    elif args.command == "read":
        read_message(args.message_id)
    elif args.command == "send":
        data = None
        if args.data:
            data = Path(args.data).read_text()
        send_message(args.content, args.task_id, args.type, data,
                     args.from_llm, args.to_llm, args.from_model, args.to_model)
    elif args.command == "ack":
        acknowledge(args.message_ids)
    elif args.command == "ack-all":
        acknowledge_all(args.agent)
    elif args.command == "conversation":
        get_conversation(args.task_id)
    elif args.command == "process":
        process_and_respond(args.message_id, args.model, no_timeout=args.no_timeout)
    elif args.command == "process-claude":
        process_for_claude(args.message_id, args.new_session, args.fire_and_forget, args.no_timeout)
    elif args.command == "ask-claude":
        _handle_ask_claude(args)
    elif args.command == "ask-gemini":
        _handle_ask_gemini(args)
    elif args.command == "converse":
        content = sys.stdin.read() if args.content == "-" else args.content
        converse_gemini(content, args.task_id, args.model,
                        getattr(args, 'no_github', False))
    elif args.command == "process-all":
        process_all_gemini(args.model)
    elif args.command == "process-claude-all":
        process_all_claude(args.new_session)
    elif args.command == "check-model":
        ok = check_model(args.model, force=True)
        sys.exit(0 if ok else 1)
    elif args.command == "cleanup":
        broker_cleanup(args.max_age, args.dry_run)
    elif args.command == "status":
        bridge_status()
    elif args.command == "interactive":
        interactive_mode()
    else:
        return False
    return True


def _handle_ask_claude(args):
    """Handle ask-claude subcommand."""
    data = None
    if args.data:
        data = Path(args.data).read_text()
    ask_claude(args.content, args.task_id, args.type, data,
               args.new_session, args.from_llm, args.from_model, args.to_model)


def _handle_ask_gemini(args):
    """Handle ask-gemini subcommand."""
    data = None
    if args.data:
        data = Path(args.data).read_text()
    content = sys.stdin.read() if args.content == "-" else args.content
    ask_gemini(content, args.task_id, args.type, data, args.model,
               getattr(args, 'from_model', None),
               getattr(args, 'async_mode', False),
               getattr(args, 'stdout_only', False),
               getattr(args, 'output_path', None),
               getattr(args, 'extract', None),
               getattr(args, 'skip_model_check', False),
               getattr(args, 'allow_write', False),
               getattr(args, 'delimiters', None),
               getattr(args, 'no_github', False))


def main():
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args()
    if not _dispatch_command(args):
        parser.print_help()
