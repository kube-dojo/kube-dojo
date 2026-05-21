#!/usr/bin/env python3
"""Stdout snapshots for verify_module.py — Phase 1 capture only.

For each bash code block in a module, extracts commands that match the
allowlist (kubectl dry-run/get variants, helm template, kind/k3d version/help),
runs them with a 30-second timeout, captures stdout+stderr, and writes a
dated snapshot file under calibration/v1/verifier-snapshots/<module-key>/.

Phase 2 (diff-aware alerting when output schemas change across runs) is
tracked in a follow-up issue.
"""
from __future__ import annotations

import hashlib
import re
import shlex
import subprocess
from datetime import date
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_DIR = REPO_ROOT / "calibration" / "v1" / "verifier-snapshots"

_RUNNABLE_LANGS = {"bash", "sh", "shell", "zsh"}

# Tokens that are always denied regardless of surrounding context.
_DENY_WORDS = {"rm", "kill", "drop", "truncate"}

# Matches any shell metacharacter that enables command chaining, redirection,
# or command substitution.  A line containing any of these is rejected before
# the allowlist is consulted so that piped/chained invocations (e.g.
# "kubectl get pods | xargs kubectl delete") cannot bypass per-command checks.
_SHELL_METACHAR_RE = re.compile(r'[|;&<>`]|\$\(')

CMD_TIMEOUT = 30


class CommandResult(NamedTuple):
    cmd: str
    exit_code: int
    output: str  # stdout + stderr combined


# ---------------------------------------------------------------------------
# Markdown parsing (thin reimplementation; avoids circular import from verify_module)
# ---------------------------------------------------------------------------

def _fenced_code_blocks(text: str) -> list[tuple[str, str]]:
    """Return (info_string, code) pairs for all fenced code blocks."""
    return [
        (m.group(1).strip(), m.group(2))
        for m in re.finditer(r"```([^\n]*)\n(.*?)```", text, re.DOTALL)
    ]


def _fence_language(info: str) -> str:
    return info.strip().split(maxsplit=1)[0].lower() if info.strip() else ""


def _strip_frontmatter(text: str) -> str:
    match = re.match(r"^---\s*\n.*?\n---\s*(?:\n|$)", text, re.DOTALL)
    return text[match.end():] if match else text


def _logical_lines(code: str) -> list[str]:
    """Join continuation lines and return logical shell commands."""
    lines: list[str] = []
    current = ""
    for physical in code.splitlines():
        stripped = physical.strip()
        if not stripped or stripped.startswith("#"):
            if current:
                lines.append(current)
                current = ""
            continue
        # Strip leading shell-prompt marker
        if stripped.startswith("$ "):
            stripped = stripped[2:]
        current = f"{current} {stripped}" if current else stripped
        if current.rstrip().endswith("\\"):
            current = current.rstrip()[:-1].rstrip()
        else:
            lines.append(current)
            current = ""
    if current:
        lines.append(current)
    return lines


# ---------------------------------------------------------------------------
# Allowlist / denylist
# ---------------------------------------------------------------------------

def _tokens(line: str) -> list[str]:
    try:
        return shlex.split(line, comments=True, posix=True)
    except ValueError:
        return line.split()


def _has_flag(tokens: list[str], *flags: str) -> bool:
    for tok in tokens:
        for flag in flags:
            if tok == flag or tok.startswith(f"{flag}="):
                return True
    return False


def _has_shell_metachar(line: str) -> bool:
    """True when the line contains a shell metacharacter making it unsafe to execute.

    Catches pipes (|), semicolons (;), &&/||, background (&), redirections
    (> >> <), backtick command substitution, and $() command substitution.
    A piped command like "kubectl get pods | xargs kubectl delete pod" would
    otherwise pass is_allowed() because shlex sees cmd='kubectl', sub='get'.
    """
    return bool(_SHELL_METACHAR_RE.search(line))


def _has_deny_token(tokens: list[str]) -> bool:
    """True when any token is an unconditionally-denied word or flag."""
    for tok in tokens:
        if tok == "--force":
            return True
        # Match bare command tokens only (not substrings of flags/resource names)
        bare = tok.lstrip("-").split("=")[0]
        if bare in _DENY_WORDS:
            return True
    return False


def _kubectl_allowed(tokens: list[str]) -> bool:
    if len(tokens) < 2:
        return False
    sub = tokens[1]

    if sub in ("version", "explain", "help", "--help", "-h", "api-resources", "api-versions"):
        return True

    # get and describe are informational (may need cluster; output captured regardless)
    if sub in ("get", "describe"):
        return True

    # apply/create/patch/run/delete require --dry-run=client
    if sub in ("apply", "create", "patch", "run"):
        return _has_flag(tokens, "--dry-run=client", "--dry-run")

    # delete is allowlist-denied UNLESS --dry-run=client is present
    if sub == "delete":
        return _has_flag(tokens, "--dry-run=client", "--dry-run")

    return False


def _helm_allowed(tokens: list[str]) -> bool:
    if len(tokens) < 2:
        return False
    return tokens[1] in ("template", "version", "help", "--help", "-h")


def _kind_allowed(tokens: list[str]) -> bool:
    if len(tokens) < 2:
        return False
    return tokens[1] in ("get", "version", "help", "--help", "-h")


def _k3d_allowed(tokens: list[str]) -> bool:
    if len(tokens) < 2:
        return False
    return tokens[1] in ("version", "help", "--help", "-h") or _has_flag(tokens, "--help", "-h")


def is_allowed(line: str) -> bool:
    """Return True when this shell line is safe to snapshot."""
    if _has_shell_metachar(line):
        return False
    toks = _tokens(line)
    if not toks:
        return False
    if _has_deny_token(toks):
        return False
    cmd = toks[0].rsplit("/", 1)[-1]  # basename
    if cmd == "kubectl":
        return _kubectl_allowed(toks)
    if cmd == "helm":
        return _helm_allowed(toks)
    if cmd == "kind":
        return _kind_allowed(toks)
    if cmd == "k3d":
        return _k3d_allowed(toks)
    return False


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def run_command(line: str) -> CommandResult:
    """Run a shell command and capture combined stdout+stderr."""
    try:
        result = subprocess.run(
            line,
            shell=True,
            capture_output=True,
            text=True,
            timeout=CMD_TIMEOUT,
        )
        output = (result.stdout + result.stderr).strip()
        return CommandResult(cmd=line, exit_code=result.returncode, output=output)
    except subprocess.TimeoutExpired:
        return CommandResult(cmd=line, exit_code=-1, output=f"[TIMEOUT after {CMD_TIMEOUT}s]")
    except Exception as exc:  # noqa: BLE001
        return CommandResult(cmd=line, exit_code=-2, output=f"[ERROR: {exc}]")


# ---------------------------------------------------------------------------
# Module key
# ---------------------------------------------------------------------------

def _module_key(path: Path) -> str:
    """Produce a filesystem-safe identifier from the module path."""
    try:
        rel = path.resolve().relative_to(REPO_ROOT / "src" / "content" / "docs").as_posix()
    except ValueError:
        rel = path.as_posix()
        prefix = str(REPO_ROOT) + "/"
        if rel.startswith(prefix):
            rel = rel[len(prefix):]
        if rel.startswith("src/content/docs/"):
            rel = rel[len("src/content/docs/"):]
    if rel.endswith(".md"):
        rel = rel[:-3]
    return rel.replace("/", "__")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def snapshot_module(path: Path, out_dir: Path | None = None) -> Path | None:
    """Extract, filter, execute, and snapshot commands from a module's bash blocks.

    Returns the path of the written snapshot file, or None when no runnable
    commands were found (no snapshot file is created).
    """
    text = path.read_text(encoding="utf-8")
    body = _strip_frontmatter(text)
    blocks = _fenced_code_blocks(body)

    # (block_number, list[CommandResult])
    block_results: list[tuple[int, list[CommandResult]]] = []
    block_num = 0
    for info, code in blocks:
        if _fence_language(info) not in _RUNNABLE_LANGS:
            continue
        block_num += 1
        results: list[CommandResult] = []
        for line in _logical_lines(code):
            if is_allowed(line):
                results.append(run_command(line))
        if results:
            block_results.append((block_num, results))

    if not block_results:
        return None

    module_key = _module_key(path)
    today = date.today().isoformat()
    target_dir = (out_dir or SNAPSHOT_DIR) / module_key
    target_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = target_dir / f"{today}.txt"

    all_outputs: list[str] = []
    section_lines: list[str] = []
    for block_idx, results in block_results:
        section_lines.append(f"## Block {block_idx}")
        for r in results:
            section_lines += [
                f"### Command: {r.cmd}",
                f"### Exit: {r.exit_code}",
                "### Output:",
                r.output,
                "",
            ]
            all_outputs.append(r.output)

    content_hash = hashlib.sha256("\n".join(all_outputs).encode()).hexdigest()
    header = [
        f"# Snapshot: {path}",
        f"# Module: {module_key}",
        f"# Date: {today}",
        f"# SHA256: {content_hash}",
        "",
    ]
    snapshot_path.write_text("\n".join(header + section_lines) + "\n", encoding="utf-8")
    return snapshot_path
