#!/usr/bin/env python3
"""Direct CLI dispatch for Gemini and Claude — no broker, no database.

V2: Adds rate limit detection, inter-call pacing, MCP tool support for
Ukrainian translations (shared RAG server from learn-ukrainian), and
fallback model support. Based on learn-ukrainian V6 dispatch.

Usage:
    python scripts/dispatch.py gemini "Review this module" [--model MODEL] [--github ISSUE_NUM]
    python scripts/dispatch.py gemini "Translate this" --mcp --model gemini-3-flash-preview
    python scripts/dispatch.py claude "Expand this draft" [--model MODEL] [--mcp]
    python scripts/dispatch.py logs [-n 10] [--full]
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
LOG_DIR = REPO_ROOT / ".dispatch-logs"
MCP_CONFIG = REPO_ROOT / ".mcp.json"

# Resolve CLI paths at import time
GEMINI_CLI = shutil.which("gemini") or "gemini"

# Environment for subprocesses
_ENV = os.environ.copy()
_ENV["GEMINI_SESSION"] = "1"        # Disable hostile aliases (eza, bat, zoxide)
_ENV["KUBEDOJO_PIPELINE"] = "1"     # Suppress inbox hooks during pipeline runs

# GitHub comment char limit (65,536 minus safety margin)
GH_CHAR_LIMIT = 64000

# ---------------------------------------------------------------------------
# Model defaults
# ---------------------------------------------------------------------------

GEMINI_DEFAULT_MODEL = "gemini-3-flash-preview"
GEMINI_FALLBACK_MODEL = "auto"
CLAUDE_DEFAULT_MODEL = "claude-sonnet-4-6"

# ---------------------------------------------------------------------------
# Rate limit detection + pacing
# ---------------------------------------------------------------------------

_RATE_LIMIT_PATTERNS = (
    "429",
    "RESOURCE_EXHAUSTED",
    "rate limit",
    "rate_limit",
    "quota exceeded",
    "No capacity available",
    "capacity",
    "too many requests",
    "Too Many Requests",
)

_GEMINI_INTER_CALL_DELAY = 3.0
_last_gemini_call_time: float = 0.0


def _is_rate_limited(text: str) -> bool:
    """Check if a failure was caused by rate limiting."""
    text_lower = text.lower()
    return any(pat.lower() in text_lower for pat in _RATE_LIMIT_PATTERNS)


def _pace_gemini_calls() -> None:
    """Enforce minimum delay between Gemini CLI calls to avoid bursts."""
    global _last_gemini_call_time
    if _last_gemini_call_time > 0:
        elapsed = time.monotonic() - _last_gemini_call_time
        if elapsed < _GEMINI_INTER_CALL_DELAY:
            wait = _GEMINI_INTER_CALL_DELAY - elapsed
            time.sleep(wait)
    _last_gemini_call_time = time.monotonic()


# ---------------------------------------------------------------------------
# MCP tools for Ukrainian translations (shared RAG server)
# ---------------------------------------------------------------------------

# Claude with MCP: Ukrainian verification + quality tools
CLAUDE_TRANSLATION_TOOLS = (
    "mcp__rag__verify_word,"
    "mcp__rag__verify_words,"
    "mcp__rag__verify_lemma,"
    "mcp__rag__search_text,"
    "mcp__rag__search_literary,"
    "mcp__rag__query_pravopys,"
    "mcp__rag__search_style_guide,"
    "mcp__rag__query_cefr_level,"
    "mcp__rag__search_definitions,"
    "mcp__rag__search_etymology,"
    "mcp__rag__search_idioms,"
    "mcp__rag__search_synonyms,"
    "mcp__rag__translate_en_uk,"
    "mcp__rag__query_grac,"
    "mcp__rag__query_ulif,"
    "mcp__rag__query_r2u,"
    "Read"
)

# ---------------------------------------------------------------------------
# Gemini review context
# ---------------------------------------------------------------------------

REVIEW_CONTEXT = """PROJECT CONTEXT:
KubeDojo is a free, open-source Kubernetes curriculum with 568+ modules:
- Certification tracks: CKA, CKAD, CKS, KCNA, KCSA (exam-aligned, K8s 1.35+)
- Platform Engineering: SRE, GitOps, DevSecOps, MLOps (209 modules)
- On-Premises Kubernetes: 30 modules
- Cloud: AWS/GCP/Azure (84 modules)
- Quality standard: Every module has learning outcomes, inline prompts, scenario-based quizzes

REVIEW PROTOCOL:
- Read every referenced file COMPLETELY before reviewing. Do not skim.
- For EVERY issue, cite exact content (quote the line, value, or field).
- If you cannot cite evidence from the actual file, do NOT report it.

REVIEW CRITERIA:
- Technical accuracy: K8s commands correct and runnable? Version numbers accurate?
- Exam alignment: Matches current CNCF exam curriculum?
- Completeness: Acceptance criteria thorough? Edge cases covered?
- Junior-friendly: Beginner-accessible? "Why" explained, not just "what"?

Respond with:
1. Clear verdict: APPROVE / NEEDS CHANGES / REJECT
2. Specific, actionable feedback
3. Concise — focus on what needs changing
"""


# ---------------------------------------------------------------------------
# Core dispatch functions
# ---------------------------------------------------------------------------

def dispatch_gemini(prompt: str, model: str = GEMINI_DEFAULT_MODEL,
                    review: bool = False, timeout: int = 900,
                    mcp: bool = False) -> tuple[bool, str]:
    """Call Gemini CLI directly. Returns (success, output)."""
    full_prompt = f"{REVIEW_CONTEXT}\n---\n\nTASK:\n{prompt}" if review else prompt
    cmd = [GEMINI_CLI, "-m", model, "-y"]
    if mcp:
        cmd.extend(["--allowed-mcp-server-names", "rag"])
    t0 = time.time()

    _pace_gemini_calls()

    try:
        proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, cwd=str(REPO_ROOT), env=_ENV,
        )

        # Write stdin in a background thread to avoid deadlock on large prompts
        stderr_lines: list[str] = []

        def _write_stdin():
            try:
                if proc.stdin:
                    proc.stdin.write(full_prompt)
                    proc.stdin.close()
            except OSError:
                pass

        def _read_stderr():
            try:
                if proc.stderr:
                    for line in proc.stderr:
                        stderr_lines.append(line)
            except (OSError, ValueError):
                pass

        stdin_thread = threading.Thread(target=_write_stdin, daemon=True)
        stderr_thread = threading.Thread(target=_read_stderr, daemon=True)
        stdin_thread.start()
        stderr_thread.start()

        quiet = os.environ.get("KUBEDOJO_QUIET", "") == "1"
        output_lines, timed_out = _stream_with_timeout(proc, timeout, quiet=quiet)
        proc.wait()
        stdin_thread.join(timeout=5)
        stderr_thread.join(timeout=5)
        stderr = "".join(stderr_lines)
        elapsed = time.time() - t0

        if timed_out:
            print(f"Gemini timed out after {timeout}s", file=sys.stderr)
            _log("gemini", model, full_prompt, "", False, elapsed, "TIMEOUT")
            return False, "TIMEOUT"

        if proc.returncode != 0:
            output = "".join(output_lines).strip()
            if output and len(output) > 50:
                # Non-zero exit but got output — likely usable
                _log("gemini", model, full_prompt, output, True, elapsed, stderr)
                return True, output
            print(f"Gemini error (exit {proc.returncode}): {stderr[:500]}", file=sys.stderr)
            _log("gemini", model, full_prompt, output, False, elapsed, stderr)
            return False, stderr

        output = "".join(output_lines).strip()
        _log("gemini", model, full_prompt, output, True, elapsed)
        return True, output

    except FileNotFoundError:
        _log("gemini", model, full_prompt, "", False, time.time() - t0, "CLI not found")
        print("gemini CLI not found. Install: https://github.com/google-gemini/gemini-cli", file=sys.stderr)
        return False, ""


def dispatch_gemini_with_retry(prompt: str, model: str = GEMINI_DEFAULT_MODEL,
                               review: bool = False, max_retries: int = 3,
                               timeout: int = 900, mcp: bool = False) -> tuple[bool, str]:
    """Call Gemini with retry on rate limits + fallback model."""
    base_delay = 30
    output = ""
    for attempt in range(max_retries):
        ok, output = dispatch_gemini(prompt, model, review, timeout, mcp)
        if ok:
            return True, output

        # Check for rate limit
        if _is_rate_limited(output):
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"Rate limited (attempt {attempt + 1}/{max_retries}). Waiting {delay}s...",
                      file=sys.stderr)
                time.sleep(delay)
                continue
            # All retries exhausted on rate limit — don't try fallback (same quota)
            return False, output

        # Timeout — don't retry, just fail (Gemini is slow, not broken)
        if output == "TIMEOUT":
            return False, output

        # Non-rate-limit, non-timeout failure — try fallback model once
        if model != GEMINI_FALLBACK_MODEL:
            print(f"Retrying with fallback model: {GEMINI_FALLBACK_MODEL}", file=sys.stderr)
            return dispatch_gemini(prompt, GEMINI_FALLBACK_MODEL, review, timeout, mcp)

        return False, output

    return False, output


def dispatch_claude(prompt: str, model: str = CLAUDE_DEFAULT_MODEL,
                    timeout: int = 600, mcp: bool = False) -> tuple[bool, str]:
    """Call Claude CLI directly. Returns (success, output)."""
    cmd = [
        "npx", "@anthropic-ai/claude-code@latest", "-p",
        "--model", model,
        "--output-format", "text",
    ]
    if mcp and MCP_CONFIG.exists():
        cmd.extend([
            "--mcp-config", str(MCP_CONFIG),
            "--allowedTools", CLAUDE_TRANSLATION_TOOLS,
        ])

    t0 = time.time()

    try:
        result = subprocess.run(
            cmd, input=prompt, capture_output=True, text=True,
            timeout=timeout, cwd=str(REPO_ROOT), env=_ENV,
        )
        elapsed = time.time() - t0
        if result.returncode != 0:
            print(f"Claude error (exit {result.returncode}): {result.stderr[:500]}", file=sys.stderr)
            _log("claude", model, prompt, "", False, elapsed, result.stderr)
            return False, result.stderr
        output = result.stdout.strip()
        _log("claude", model, prompt, output, True, elapsed)
        return True, output

    except FileNotFoundError:
        _log("claude", model, prompt, "", False, time.time() - t0, "CLI not found")
        print("claude CLI not found.", file=sys.stderr)
        return False, ""
    except subprocess.TimeoutExpired:
        _log("claude", model, prompt, "", False, time.time() - t0, "TIMEOUT")
        print(f"Claude timed out after {timeout}s", file=sys.stderr)
        return False, ""


def post_to_github(issue_num: int, content: str, model: str) -> bool:
    """Post review content to a GitHub issue as comment(s)."""
    if not content:
        return False

    chunks = _split_content(content)
    total = len(chunks)

    for i, chunk in enumerate(chunks, start=1):
        if total > 1:
            body = f"**[Part {i}/{total}]** Review ({model})\n\n{chunk}"
        else:
            body = f"**Review** ({model})\n\n{chunk}"

        try:
            result = subprocess.run(
                ["gh", "issue", "comment", str(issue_num), "-F", "-"],
                input=body, text=True, capture_output=True, timeout=15,
            )
            if result.returncode != 0:
                print(f"GitHub comment failed: {result.stderr[:200]}", file=sys.stderr)
                return False
        except FileNotFoundError:
            print("gh CLI not found — skipping GitHub posting", file=sys.stderr)
            return False
        except subprocess.TimeoutExpired:
            print("GitHub posting timed out", file=sys.stderr)
            return False

    print(f"Review posted to #{issue_num} ({total} part{'s' if total > 1 else ''})")
    return True


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def _log(agent: str, model: str, prompt: str, output: str, ok: bool,
         duration_s: float, stderr: str = "") -> Path:
    """Write a JSON log entry. Returns the log file path."""
    LOG_DIR.mkdir(exist_ok=True)
    ts = datetime.now(UTC)
    slug = ts.strftime("%Y%m%d-%H%M%S")
    log_file = LOG_DIR / f"{slug}-{agent}.json"

    entry = {
        "timestamp": ts.isoformat(),
        "agent": agent,
        "model": model,
        "success": ok,
        "duration_s": round(duration_s, 1),
        "prompt_chars": len(prompt),
        "output_chars": len(output),
        "prompt": prompt[:5000] + ("..." if len(prompt) > 5000 else ""),
        "output": output[:10000] + ("..." if len(output) > 10000 else ""),
    }
    if stderr:
        entry["stderr"] = stderr[:2000]

    log_file.write_text(json.dumps(entry, indent=2, ensure_ascii=False))
    return log_file


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _stream_with_timeout(proc, timeout: int, quiet: bool = False) -> tuple[list[str], bool]:
    """Stream stdout lines, kill if timeout exceeded. Returns (lines, timed_out)."""
    output_lines: list[str] = []
    timed_out = False

    if timeout:
        def _kill():
            nonlocal timed_out
            timed_out = True
            try:
                proc.kill()
            except OSError:
                pass

        timer = threading.Timer(timeout, _kill)
        timer.daemon = True
        timer.start()
    else:
        timer = None

    try:
        for line in proc.stdout:
            if not quiet:
                print(line, end="")
                sys.stdout.flush()
            output_lines.append(line)
    except (OSError, ValueError):
        pass

    if timer:
        timer.cancel()

    return output_lines, timed_out


def _split_content(content: str, limit: int = GH_CHAR_LIMIT) -> list[str]:
    """Split content into chunks at newline boundaries."""
    chunks = []
    pos = 0
    length = len(content)
    while pos < length:
        end = min(pos + limit, length)
        if end >= length:
            chunks.append(content[pos:])
            break
        split_at = content.rfind("\n", pos, end)
        if split_at <= pos:
            split_at = end
        chunks.append(content[pos:split_at])
        pos = split_at + (1 if split_at < length and content[split_at] == "\n" else 0)
    return chunks


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Direct CLI dispatch for Gemini/Claude — V2 with rate limiting + MCP",
    )
    subparsers = parser.add_subparsers(dest="agent", help="Target agent")

    # gemini
    gp = subparsers.add_parser("gemini", help="Dispatch prompt to Gemini CLI")
    gp.add_argument("prompt", help="Prompt text (use '-' to read from stdin)")
    gp.add_argument("--model", default=GEMINI_DEFAULT_MODEL, help=f"Gemini model (default: {GEMINI_DEFAULT_MODEL})")
    gp.add_argument("--review", action="store_true", help="Prepend KubeDojo review context")
    gp.add_argument("--mcp", action="store_true", help="Enable RAG MCP tools (for translations)")
    gp.add_argument("--github", type=int, metavar="ISSUE", help="Post output to GitHub issue")
    gp.add_argument("--retry", type=int, default=3, help="Max retries on rate limit (default: 3)")
    gp.add_argument("--timeout", type=int, default=900, help="Timeout in seconds (default: 900)")

    # claude
    cp = subparsers.add_parser("claude", help="Dispatch prompt to Claude CLI")
    cp.add_argument("prompt", help="Prompt text (use '-' to read from stdin)")
    cp.add_argument("--model", default=CLAUDE_DEFAULT_MODEL, help=f"Claude model (default: {CLAUDE_DEFAULT_MODEL})")
    cp.add_argument("--mcp", action="store_true", help="Enable RAG MCP tools (for translations)")
    cp.add_argument("--timeout", type=int, default=600, help="Timeout in seconds (default: 600)")

    # logs
    lp = subparsers.add_parser("logs", help="Show recent dispatch logs")
    lp.add_argument("-n", type=int, default=10, help="Number of entries (default: 10)")
    lp.add_argument("--full", action="store_true", help="Show full prompt/output (not truncated)")
    lp.add_argument("--id", dest="log_id", help="Show a specific log file by timestamp prefix")

    args = parser.parse_args()

    if not args.agent:
        parser.print_help()
        sys.exit(1)

    if args.agent == "gemini":
        prompt = sys.stdin.read() if args.prompt == "-" else args.prompt
        ok, output = dispatch_gemini_with_retry(
            prompt, args.model, args.review, args.retry, args.timeout, args.mcp,
        )
        if ok and args.github:
            post_to_github(args.github, output, args.model)
        sys.exit(0 if ok else 1)

    elif args.agent == "claude":
        prompt = sys.stdin.read() if args.prompt == "-" else args.prompt
        ok, output = dispatch_claude(prompt, args.model, args.timeout, args.mcp)
        if ok:
            print(output)
        sys.exit(0 if ok else 1)

    elif args.agent == "logs":
        _show_logs(args.n, args.full, args.log_id)


def _show_logs(n: int, full: bool, log_id: str | None):
    """Show recent dispatch logs."""
    if not LOG_DIR.exists():
        print("No logs yet.")
        return

    if log_id:
        matches = sorted(LOG_DIR.glob(f"{log_id}*.json"))
        if not matches:
            print(f"No log matching '{log_id}'")
            return
        for m in matches:
            entry = json.loads(m.read_text())
            print(json.dumps(entry, indent=2, ensure_ascii=False))
        return

    logs = sorted(LOG_DIR.glob("*.json"), reverse=True)[:n]
    if not logs:
        print("No logs yet.")
        return

    for log_file in reversed(logs):
        entry = json.loads(log_file.read_text())
        status = "OK" if entry["success"] else "FAIL"
        prompt_preview = entry["prompt"][:80].replace("\n", " ")
        if not full:
            print(f"  {entry['timestamp'][:19]}  {entry['agent']:6s}  {status:4s}  "
                  f"{entry['duration_s']:6.1f}s  {entry['prompt_chars']:>6} -> {entry['output_chars']:>6} chars  "
                  f"{prompt_preview}...")
        else:
            print(f"\n{'='*60}")
            print(json.dumps(entry, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
