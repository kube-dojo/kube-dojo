"""Smart-routing headless dispatcher.

Single CLI for dispatching work to a headless agent that picks an
appropriate model based on the task class — instead of always burning
the top-tier model from the orchestrator session.

Why: the orchestrator runs on claude-opus-4-8. Routine search/edit work
shouldn't burn opus (or gpt-5.5) when a smaller model would do fine.
This wrapper lets the orchestrator say "do this kind of work, pick the
right model" without manually choosing model + mode + worktree every
time. Mirrors the economical multi-agent policy in AGENTS.md (PR #870)
so cross-agent dispatches follow the same tiering as Codex's internal
subagents.

Usage:
    # Cheap search (haiku, read-only) — default agent=claude
    .venv/bin/python scripts/dispatch_smart.py search \
        "Find every place that imports agent_runtime.runner.invoke."

    # Same task class, routed to codex (gpt-5.4-mini)
    .venv/bin/python scripts/dispatch_smart.py search --agent codex \
        "Find every place that imports agent_runtime.runner.invoke."

    # Mid-tier edit — codex picks gpt-5.3-codex-spark (separate counter)
    .venv/bin/python scripts/dispatch_smart.py edit --agent codex \
        --worktree .worktrees/codex-fix-issue-500 \
        --new-branch codex/fix-issue-500 \
        "Fix the off-by-one in scripts/foo.py:142, add a regression test."

    # Heavy work — judgment / integration (opus or gpt-5.5)
    .venv/bin/python scripts/dispatch_smart.py architect \
        --worktree .worktrees/claude-redesign-pipeline \
        --new-branch claude/redesign-pipeline \
        "Redesign the quality pipeline so phase ordering is data-driven."

Skill auto-loading:
    Role-specific shared skills are prepended to dispatched prompts by task
    class. ``draft`` and ``edit`` load ``curriculum-writer``; ``review``
    loads ``cross-family-reviewer``; ``architect`` and ``search`` do not
    load a skill. Override with ``--skill <name>`` or disable with
    ``--no-skill`` for narrow mechanical dispatches where the brief is
    already self-contained::

        .venv/bin/python scripts/dispatch_smart.py review \
            --agent codex --skill k8s-cert-expert \
            "Review this Kubernetes certification module."

Task classes — model mapping per agent:

    class       claude                       codex
    -------     -------------------------    ----------------------
    search      claude-haiku-4-5-20251001    gpt-5.4-mini
    edit        claude-sonnet-4-6            gpt-5.3-codex-spark
    draft       claude-sonnet-4-6            gpt-5.5
    review      claude-sonnet-4-6            gpt-5.5
    architect   claude-opus-4-8              gpt-5.5

Each dispatch is recorded to ``logs/smart_dispatch.jsonl`` for usage
auditing. The FULL response body is also persisted to
``logs/dispatch_responses/<task_id>.txt`` so callers that pipe stdout
through ``tail``/``head`` (e.g. background bash tasks) can recover the
body even if the live stream was truncated. The JSONL row's
``response_path`` field is the canonical pointer. Pattern::

    python scripts/dispatch_smart.py review --task-id review-foo ... | tail -N
    # body may be truncated in stdout; recover from disk:
    cat "$(jq -r 'select(.task_id == "review-foo") | .response_path' logs/smart_dispatch.jsonl)"

Reuse with --dry-run to print the chosen plan without firing.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _primary_checkout_root(repo_root: Path) -> Path:
    """Resolve the primary checkout root when this script runs in a worktree."""
    if repo_root.parent.name == ".worktrees":
        return repo_root.parent.parent
    return repo_root


PRIMARY_REPO = _primary_checkout_root(REPO)
# Anchor logs to the primary checkout so worktree dispatches do not
# fragment the audit trail across .worktrees/*/logs/.
LOG_PATH = PRIMARY_REPO / "logs" / "smart_dispatch.jsonl"
RESPONSE_DIR = PRIMARY_REPO / "logs" / "dispatch_responses"

# Skill auto-loading — R2 follow-up to PR #1575 and the agents_extensions/
# layout introduced there.
SKILL_FOR_TASK_CLASS: dict[str, str] = {
    "draft": "curriculum-writer",
    "edit": "curriculum-writer",
    "review": "cross-family-reviewer",
    # architect, search -> no skill
}

SHARED_SKILLS_DIR = PRIMARY_REPO / "agents_extensions" / "shared" / "skills"
CLAUDE_SKILLS_DIR = PRIMARY_REPO / "agents_extensions" / "claude" / "skills"


SUPPORTED_AGENTS = (
    "agy",
    "claude",
    "codex",
    "cursor",
    "deepseek",
    "gemini",
    "hermes",
    "opencode",
    "qwen",
)


@dataclass(frozen=True)
class TaskClassConfig:
    models: dict[str, str]  # agent -> model
    default_mode: str  # "read-only" | "workspace-write" | "danger"
    default_timeout_s: int
    description: str
    codex_search: bool = False  # opt-in per class


# Note on the "agy" model entries below: Antigravity CLI's model is selected
# interactively in its TUI panel and cannot be overridden per-invocation
# (no -m / --model flag as of agy 1.0.0). The string `tui-controlled`
# is an informational placeholder — the actual model in flight is whatever
# the operator last picked in `agy`'s panel and is reported in the model
# self-identify probe (`agy -p 'what model are you?'`). The per-class
# distinction is therefore meaningless for agy until Google adds a model
# flag or config-file path.
TASK_CLASSES: dict[str, TaskClassConfig] = {
    "search": TaskClassConfig(
        models={
            "agy": "tui-controlled",
            "claude": "claude-haiku-4-5-20251001",
            "codex": "gpt-5.4-mini",
            "deepseek": "deepseek-v4-flash",
            "gemini": "gemini-3.1-flash-lite-preview",
            "cursor": "composer-2.5-fast",
            "hermes": "qwen-3.6-flash",
            "opencode": "openrouter/qwen/qwen3.6-flash",
            "qwen": "qwen/qwen3.6-flash",
        },
        default_mode="read-only",
        default_timeout_s=600,
        description="cheap codebase scans, file lookups, factual Q&A",
        codex_search=False,
    ),
    "edit": TaskClassConfig(
        models={
            "agy": "tui-controlled",
            "claude": "claude-sonnet-4-6",
            "codex": "gpt-5.3-codex-spark",
            "deepseek": "deepseek-v4-pro",
            "gemini": "gemini-3.1-pro-preview",
            "cursor": "composer-2.5",
            "hermes": "grok-4.3",
            "opencode": "openrouter/qwen/qwen3.7-max",
            "qwen": "qwen/qwen3.6-plus",
        },
        default_mode="workspace-write",
        default_timeout_s=1800,
        description="small/medium code edits, single-file fixes",
        codex_search=False,
    ),
    "draft": TaskClassConfig(
        models={
            "agy": "tui-controlled",
            "claude": "claude-sonnet-4-6",
            "codex": "gpt-5.5",
            "deepseek": "deepseek-v4-pro",
            "gemini": "gemini-3.1-pro-preview",
            "cursor": "composer-2.5",
            "hermes": "grok-4.3",
            "opencode": "openrouter/qwen/qwen3.7-max",
            "qwen": "qwen/qwen3.6-plus",
        },
        default_mode="workspace-write",
        default_timeout_s=3600,
        description="prose/content drafting and expansion",
        codex_search=True,
    ),
    "review": TaskClassConfig(
        models={
            "agy": "tui-controlled",
            "claude": "claude-sonnet-4-6",
            "codex": "gpt-5.5",
            "deepseek": "deepseek-v4-pro",
            "gemini": "gemini-3.1-pro-preview",
            "cursor": "gpt-5.5",
            "hermes": "claude-sonnet-4-6",
            "opencode": "openrouter/qwen/qwen3.7-max",
            "qwen": "qwen/qwen3.6-plus",
        },
        default_mode="read-only",
        default_timeout_s=1800,
        description="cross-family review of authored work (judgment)",
        codex_search=False,
    ),
    "architect": TaskClassConfig(
        models={
            "agy": "tui-controlled",
            "claude": "claude-opus-4-8",
            "codex": "gpt-5.5",
            "deepseek": "deepseek-v4-pro",
            "gemini": "gemini-3.1-pro-preview",
            "cursor": "composer-2.5",
            "hermes": "claude-opus-4-6",
            "opencode": "openrouter/anthropic/claude-sonnet-4.5",
            "qwen": "qwen/qwen3.6-plus",
        },
        default_mode="workspace-write",
        default_timeout_s=3600,
        description="deep reasoning, multi-file refactors, design",
        codex_search=True,
    ),
}


def _resolve_skill_path(skill_name: str) -> Path | None:
    """Resolve a skill name to its SKILL.md path. Searches shared/ then claude/.

    Returns None if neither location has the skill.
    """
    for parent in (SHARED_SKILLS_DIR, CLAUDE_SKILLS_DIR):
        candidate = parent / skill_name / "SKILL.md"
        if candidate.is_file():
            return candidate
    return None


def _load_skill_body(skill_name: str) -> tuple[str, Path] | None:
    """Read a skill body. Returns (body_text, source_path) or None if missing."""
    path = _resolve_skill_path(skill_name)
    if path is None:
        return None
    try:
        return path.read_text(encoding="utf-8"), path
    except OSError:
        return None


def _wrap_prompt_with_skill(prompt: str, skill_body: str, skill_name: str) -> str:
    """Prepend the skill body to the prompt with a clear marker."""
    return (
        f"<auto-loaded-skill name=\"{skill_name}\">\n"
        f"{skill_body.rstrip()}\n"
        f"</auto-loaded-skill>\n\n"
        f"{prompt}"
    )


def _skill_to_load_for_dispatch(
    *,
    task_class: str,
    explicit_skill: str | None,
    no_skill: bool,
) -> str | None:
    """Return the explicit or task-class-mapped skill name, if enabled."""
    if explicit_skill is not None:
        return explicit_skill
    if no_skill:
        return None
    return SKILL_FOR_TASK_CLASS.get(task_class)


def _display_path(path: Path) -> Path:
    """Return a primary-relative path when possible, else the original path."""
    try:
        return path.relative_to(PRIMARY_REPO)
    except ValueError:
        return path


def make_task_id(task_class: str, agent: str) -> str:
    return f"smart-{agent}-{task_class}-{int(time.time())}"


def ensure_worktree(worktree: Path, new_branch: str | None,
                    base: str = "main") -> None:
    """Create a worktree if it doesn't exist; reuse if it does.

    Caller is responsible for picking a sensible path under .worktrees/.
    """
    if worktree.exists():
        return
    if new_branch is None:
        raise SystemExit(
            f"[smart] worktree {worktree} does not exist and no "
            f"--new-branch was given; refusing to invent a branch name"
        )
    cmd = ["git", "worktree", "add", "-b", new_branch, str(worktree), base]
    subprocess.run(cmd, cwd=PRIMARY_REPO, check=True)
    primary_venv = PRIMARY_REPO / ".venv"
    worktree_venv = worktree / ".venv"
    if primary_venv.exists() and not (
            worktree_venv.exists() or worktree_venv.is_symlink()
    ):
        worktree_venv.symlink_to(primary_venv)
    primary_node_modules = PRIMARY_REPO / "node_modules"
    worktree_node_modules = worktree / "node_modules"
    if primary_node_modules.exists() and not (
            worktree_node_modules.exists() or worktree_node_modules.is_symlink()
    ):
        worktree_node_modules.symlink_to(primary_node_modules)


def append_log(entry: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a") as fp:
        fp.write(json.dumps(entry) + "\n")


def persist_response(task_id: str, response: str, stderr_excerpt: str) -> Path:
    """Write the full response body (and stderr excerpt) to disk.

    Returns the path of the response file. Callers that pipe dispatch output
    through ``tail`` or similar truncation can still recover the full body
    from this file. Prior to this, only ``response_chars`` was captured in
    the JSONL row and the body lived solely in stdout, which got silently
    dropped on ~3 of session-31's review dispatches.
    """
    RESPONSE_DIR.mkdir(parents=True, exist_ok=True)
    response_path = RESPONSE_DIR / f"{task_id}.txt"
    response_path.write_text(response or "", encoding="utf-8")
    if stderr_excerpt:
        stderr_path = RESPONSE_DIR / f"{task_id}.stderr.txt"
        stderr_path.write_text(stderr_excerpt, encoding="utf-8")
    return response_path


def _opencode_binary() -> str:
    """Resolve the opencode CLI path with an env override for local installs."""
    return (
        os.environ.get("KUBEDOJO_OPENCODE_CMD")
        or shutil.which("opencode")
        or "/opt/homebrew/bin/opencode"
    )


def _hermes_binary() -> str:
    """Resolve the hermes CLI path with an env override for local installs."""
    return (
        os.environ.get("KUBEDOJO_HERMES_CMD")
        or shutil.which("hermes")
        or str(Path.home() / ".local" / "bin" / "hermes")
    )


def _cursor_binary() -> str:
    """Resolve the cursor-agent CLI path with an env override for local installs."""
    return (
        os.environ.get("KUBEDOJO_CURSOR_CMD")
        or shutil.which("cursor-agent")
        or str(Path.home() / ".local" / "bin" / "cursor-agent")
    )


def _hermes_provider_for_model(model: str) -> str:
    """Pick a Hermes provider from the model name, unless env overrides it."""
    override = os.environ.get("KUBEDOJO_HERMES_PROVIDER")
    if override:
        return override
    if model.startswith("openrouter/"):
        return "openrouter"
    if model.startswith("claude-"):
        return "anthropic"
    if model.startswith("grok-"):
        return "xai"
    return "openrouter"


def _hermes_cli_model(model: str) -> str:
    """Map KubeDojo's route labels to Hermes v0.14 CLI model IDs."""
    if model.startswith("qwen-"):
        return f"qwen/qwen{model.removeprefix('qwen-')}"
    return model


def _router_command(agent: str, model: str, prompt: str) -> list[str]:
    """Build the subprocess command for direct router CLIs."""
    if agent == "opencode":
        return [_opencode_binary(), "run", "-m", model, "-"]
    if agent == "cursor":
        return [
            _cursor_binary(),
            "--print",
            "--force",
            "--trust",
            "--model",
            model,
            "--output-format",
            "text",
            prompt,
        ]
    if agent == "hermes":
        cli_model = _hermes_cli_model(model)
        # --oneshot (-z): one-shot mode; PROMPT must be a single argv token.
        # Use ``--oneshot=<prompt>`` so flag-like prompts (e.g. ``--provider``)
        # are bound as the flag value, not parsed as a separate CLI flag.
        return [
            _hermes_binary(),
            "--provider",
            _hermes_provider_for_model(model),
            "-m",
            cli_model,
            f"--oneshot={prompt}",
        ]
    raise ValueError(f"unsupported direct router agent: {agent}")


def _run_router_agent(
    *,
    agent: str,
    prompt: str,
    model: str,
    cwd: Path,
    timeout_s: int,
) -> tuple[bool, str, str]:
    """Invoke a session-less router CLI and return (ok, stdout, stderr)."""
    cmd = _router_command(agent, model, prompt)
    stdin_payload = prompt if agent == "opencode" else ""
    if agent == "cursor":
        stdin_payload = ""
    try:
        proc = subprocess.run(
            cmd,
            input=stdin_payload,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return False, stdout, f"{agent} timed out after {timeout_s}s\n{stderr}".strip()
    except OSError as exc:
        return False, "", f"{type(exc).__name__}: {exc}"

    response = proc.stdout or ""
    stderr = proc.stderr or ""
    ok = proc.returncode == 0 and bool(response.strip())
    if not ok and not stderr.strip():
        stderr = f"{agent} exited {proc.returncode} with no stdout"
    return ok, response.strip(), stderr.strip()


def fire(*, agent: str, task_class: str, prompt: str, mode: str, model: str,
         worktree: Path | None, task_id: str, timeout_s: int) -> int:
    print(f"[smart] agent={agent} task_class={task_class} model={model} "
          f"mode={mode} timeout={timeout_s}s")
    if worktree:
        print(f"[smart] cwd={worktree}")
    print(f"[smart] task_id={task_id}")
    if agent in {"cursor", "hermes", "opencode"}:
        print("[smart] mode is advisory for this router CLI")

    started = time.time()
    previous_search: str | None = None
    previous_dispatched: str | None = None
    try:
        previous_search = os.environ.get("KUBEDOJO_CODEX_SEARCH")
        previous_dispatched = os.environ.get("KUBEDOJO_DISPATCHED")
        if agent == "codex":
            cfg = TASK_CLASSES[task_class]
            os.environ["KUBEDOJO_CODEX_SEARCH"] = "1" if cfg.codex_search else "0"
        env = os.environ.copy()
        env["KUBEDOJO_DISPATCHED"] = "1"
        os.environ.update(env)
        if agent in {"cursor", "hermes", "opencode"}:
            ok, response, stderr_excerpt = _run_router_agent(
                agent=agent,
                prompt=prompt,
                model=model,
                cwd=worktree or Path.cwd(),
                timeout_s=timeout_s,
            )
            session_id = None
        else:
            sys.path.insert(0, str(REPO / "scripts"))
            from agent_runtime.runner import invoke

            result = invoke(
                agent,
                prompt,
                mode=mode,
                cwd=worktree,
                model=model,
                task_id=task_id,
                entrypoint="delegate",
                hard_timeout=timeout_s,
            )
            ok = bool(result.ok)
            response = result.response or ""
            session_id = result.session_id
            stderr_excerpt = result.stderr_excerpt or ""
    except Exception as exc:  # surface the failure but still log it
        ok = False
        response = ""
        session_id = None
        stderr_excerpt = f"{type(exc).__name__}: {exc}"
    finally:
        if agent == "codex":
            if previous_search is None:
                os.environ.pop("KUBEDOJO_CODEX_SEARCH", None)
            else:
                os.environ["KUBEDOJO_CODEX_SEARCH"] = previous_search
        if previous_dispatched is None:
            os.environ.pop("KUBEDOJO_DISPATCHED", None)
        else:
            os.environ["KUBEDOJO_DISPATCHED"] = previous_dispatched

    elapsed = time.time() - started
    response_path = persist_response(task_id, response, stderr_excerpt)
    rel_response_path = str(response_path.relative_to(PRIMARY_REPO))
    append_log({
        "ts": int(started),
        "elapsed_s": round(elapsed, 1),
        "task_id": task_id,
        "agent": agent,
        "task_class": task_class,
        "model": model,
        "mode": mode,
        "cwd": str(worktree) if worktree else None,
        "ok": ok,
        "session_id": session_id,
        "response_chars": len(response),
        "response_path": rel_response_path,
        "stderr_excerpt": stderr_excerpt[:400] if stderr_excerpt else None,
    })

    # Print response_path BEFORE the body so callers that truncate stdout
    # (tail -N, head -N) still see the path and can `cat` the full file.
    print("=" * 70)
    print(f"OK: {ok}  |  elapsed: {elapsed:.0f}s  |  "
          f"resp_chars: {len(response)}")
    print(f"response_path: {rel_response_path}")
    print("=" * 70)
    if response:
        print(response)
    if stderr_excerpt:
        print("---- stderr ----")
        print(stderr_excerpt[:400])
    return 0 if ok else 1


def main() -> int:
    p = argparse.ArgumentParser(
        description="Dispatch a headless agent with a "
                    "task-class-based model choice. Mirrors the AGENTS.md "
                    "economical multi-agent policy across agents.",
    )
    p.add_argument("task_class", choices=sorted(TASK_CLASSES),
                   help="Picks the model + default mode.")
    p.add_argument("prompt", nargs="?", default=None,
                   help="Prompt text. Pass `-` to read from stdin.")
    p.add_argument("--agent", choices=SUPPORTED_AGENTS, default="claude",
                   help="Which agent to dispatch (default: claude).")
    p.add_argument("--worktree",
                   help="Path to a git worktree under .worktrees/. "
                        "Required for write modes.")
    p.add_argument("--new-branch",
                   help="If --worktree doesn't exist, create it on this "
                        "branch off main.")
    p.add_argument("--mode",
                   choices=["read-only", "workspace-write", "danger"],
                   help="Override task-class default mode. For opencode, "
                        "hermes, and cursor this is advisory; their CLIs "
                        "enforce their own sandbox behavior.")
    p.add_argument("--model",
                   help="Override task-class default model "
                        "(rarely needed — let the class+agent pick).")
    p.add_argument("--timeout", type=int,
                   help="Override task-class default hard timeout (s).")
    p.add_argument("--task-id",
                   help="Override auto-generated task_id.")
    p.add_argument("--dry-run", action="store_true",
                   help="Print the resolved plan and exit without firing.")
    p.add_argument(
        "--skill",
        default=None,
        help=(
            "Override the auto-mapped skill for the task class. Looks up "
            "agents_extensions/shared/skills/<name>/SKILL.md first, then "
            "agents_extensions/claude/skills/<name>/SKILL.md. Fails if not found."
        ),
    )
    p.add_argument(
        "--no-skill",
        action="store_true",
        help="Disable skill auto-loading entirely.",
    )
    args = p.parse_args()

    cfg = TASK_CLASSES[args.task_class]
    model = args.model or cfg.models[args.agent]
    mode = args.mode or cfg.default_mode
    timeout_s = args.timeout or cfg.default_timeout_s
    task_id = args.task_id or make_task_id(args.task_class, args.agent)

    # Codex always runs in danger mode — read-only starves it of
    # network/filesystem and produces garbage (rc=-9 stale-rollout salvage).
    if args.agent == "codex" and mode != "danger":
        if args.mode is not None and args.mode != "danger":
            p.error(
                f"--agent codex always runs in danger mode (you passed "
                f"--mode {args.mode!r}). Codex needs network + filesystem "
                f"to fact-check; read-only/workspace-write break it. "
                f"Drop --mode to use the default."
            )
        mode = "danger"

    # Agy always runs in danger mode for write classes — read-only would cause
    # tool-permission prompts to hang waiting for human input in a headless
    # dispatch, since the runtime cannot answer the prompt.
    # `--dangerously-skip-permissions` is the equivalent of codex's danger
    # sandbox: auto-approve all tool calls. User direction 2026-05-19.
    if (
        args.agent == "agy"
        and args.task_class not in ("review", "search")
        and mode != "danger"
    ):
        if args.mode is not None and args.mode != "danger":
            p.error(
                f"--agent agy always runs in danger mode (you passed "
                f"--mode {args.mode!r}). agy in headless dispatch needs "
                f"--dangerously-skip-permissions to avoid hanging on "
                f"interactive permission prompts. Drop --mode to use the default."
            )
        mode = "danger"

    # Read-only task classes for codex run in danger mode, but they do not
    # require a worktree.
    codex_readonly_class = (
        args.agent == "codex"
        and args.task_class in {"review", "search"}
    )

    if args.prompt is None:
        sys.stderr.write("[smart] no prompt — pass as arg or `-` for stdin\n")
        return 2
    prompt = sys.stdin.read() if args.prompt == "-" else args.prompt
    if not prompt.strip():
        sys.stderr.write("[smart] prompt is empty\n")
        return 2

    skill_to_load = _skill_to_load_for_dispatch(
        task_class=args.task_class,
        explicit_skill=args.skill,
        no_skill=args.no_skill,
    )
    if skill_to_load is not None:
        loaded = _load_skill_body(skill_to_load)
        if loaded is None:
            if args.skill is not None:
                print(
                    f"[dispatch_smart] error: skill '{skill_to_load}' not found in "
                    "agents_extensions/shared/skills/ or "
                    "agents_extensions/claude/skills/",
                    file=sys.stderr,
                )
                return 2
            print(
                f"[dispatch_smart] warning: auto-mapped skill '{skill_to_load}' "
                "not found; proceeding without skill context",
                file=sys.stderr,
            )
        else:
            skill_body, source_path = loaded
            prompt = _wrap_prompt_with_skill(prompt, skill_body, skill_to_load)
            rel = _display_path(source_path)
            print(
                f"[dispatch_smart] auto-loaded skill: {skill_to_load} "
                f"(from {rel})",
                file=sys.stderr,
            )

    if mode == "danger" and not args.worktree and not args.dry_run:
        # agy carve-out: agy under danger mode only suppresses interactive
        # permission prompts (--dangerously-skip-permissions); it does not
        # write files. Review-class agy dispatches don't need a worktree.
        # codex review/search carve-out: read-only task classes; no worktree.
        if args.agent != "agy" and not codex_readonly_class:
            p.error("--mode danger requires --worktree (no override)")

    worktree: Path | None = None
    if args.worktree:
        worktree = Path(args.worktree)
        if not worktree.is_absolute():
            worktree = PRIMARY_REPO / worktree
    elif (
        mode != "read-only"
        and not args.dry_run
        and args.agent != "agy"
        and not codex_readonly_class
    ):
        sys.stderr.write(
            f"[smart] mode={mode} requires --worktree to avoid trampling "
            "the main checkout\n"
        )
        return 2

    if args.dry_run:
        print(f"[dry-run] agent={args.agent} task_class={args.task_class} "
              f"model={model} mode={mode} timeout={timeout_s}s")
        _wt_label = worktree or f"(none — {mode})"
        print(f"[dry-run] worktree={_wt_label}")
        print(f"[dry-run] task_id={task_id}")
        print(f"[dry-run] prompt_chars={len(prompt)}")
        print("[dry-run] prompt_begin")
        print(prompt)
        print("[dry-run] prompt_end")
        if args.agent in {"cursor", "hermes", "opencode"}:
            print(f"[dry-run] argv={_router_command(args.agent, model, prompt)!r}")
        return 0

    if worktree and mode != "read-only":
        ensure_worktree(worktree, args.new_branch)

    return fire(
        agent=args.agent,
        task_class=args.task_class,
        prompt=prompt,
        mode=mode,
        model=model,
        worktree=worktree,
        task_id=task_id,
        timeout_s=timeout_s,
    )


if __name__ == "__main__":
    raise SystemExit(main())
