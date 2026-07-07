"""Hermes interaction: ask_hermes and process_for_hermes."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from ._config import REPO_ROOT
from ._db import get_db
from ._messaging import acknowledge, send_message

_AGENT_NAME = "hermes"
_AGENT_TITLE = "Hermes"
_DEFAULT_BRIDGE_TIMEOUT_SECONDS = 900
_NO_TIMEOUT_BRIDGE_TIMEOUT_SECONDS = 24 * 60 * 60
_DEFAULT_MODEL = os.environ.get("AB_HERMES_MODEL", "grok-4.3")
_TIMEOUT_ENV = "HERMES_BRIDGE_TIMEOUT"


def _hermes_binary() -> str:
    """Resolve the hermes executable."""
    return (
        os.environ.get("KUBEDOJO_HERMES_CMD")
        or shutil.which("hermes")
        or str(Path.home() / ".local" / "bin" / "hermes")
    )


def _detect_provider(model: str) -> str:
    """Infer the Hermes provider from the model name.

    NO silent metered fallback: the old catch-all returned ``openrouter``,
    which billed the OpenRouter account for any model without an explicit
    branch (``ask-hermes --to-model deepseek-v4-pro`` silently drained
    OpenRouter instead of hitting the first-party DeepSeek API — incident
    #2245, 2026-07-07). Unknown models now raise.
    """
    override = os.environ.get("KUBEDOJO_HERMES_PROVIDER")
    if override:
        return override
    if model.startswith("openrouter/"):
        return "openrouter"
    if model.startswith("claude-"):
        return "anthropic"
    if model.startswith("grok-"):
        return "xai"
    if model.startswith("deepseek"):
        # First-party DeepSeek API (api.deepseek.com) — NEVER the OpenRouter
        # proxy unless the caller opts in explicitly (#2245).
        return "deepseek"
    if model.startswith("qwen"):
        # The documented metered qwen lane rides OpenRouter deliberately
        # ([[reference_qwen_hermes_openrouter]]) — explicit, not a fallback.
        return "openrouter"
    raise ValueError(
        f"No Hermes provider mapping for model {model!r} — refusing to fall "
        "back to a metered proxy (incident #2245). Set "
        "KUBEDOJO_HERMES_PROVIDER or use an explicit 'openrouter/<vendor>/"
        "<model>' slug."
    )


def _cli_model(model: str) -> str:
    """Map KubeDojo's route labels to Hermes v0.14 CLI model IDs."""
    if model.startswith("openrouter/"):
        # The ``openrouter/`` prefix is only the explicit provider opt-in
        # marker (#2245); OpenRouter's catalog ids are ``vendor/model``.
        return model.removeprefix("openrouter/")
    if model.startswith("qwen-"):
        return f"qwen/qwen{model.removeprefix('qwen-')}"
    return model


def _build_command(
    prompt: str,
    model: str,
    provider: str | None = None,
) -> list[str]:
    """Build the hermes one-shot command."""
    # --oneshot (-z): one-shot mode; PROMPT must be a single argv token.
    # Use ``--oneshot=<prompt>`` so flag-like prompts (e.g. ``--provider``)
    # are bound as the flag value, not parsed as a separate CLI flag.
    return [
        _hermes_binary(),
        "--provider",
        provider or _detect_provider(model),
        "-m",
        _cli_model(model),
        f"--oneshot={prompt}",
    ]


def _resolve_bridge_timeout(no_timeout: bool = False) -> int:
    """Resolve the hard timeout from CLI flag/env with a safe fallback."""
    if no_timeout:
        return _NO_TIMEOUT_BRIDGE_TIMEOUT_SECONDS

    raw = os.environ.get(_TIMEOUT_ENV)
    if raw is None:
        return _DEFAULT_BRIDGE_TIMEOUT_SECONDS

    value = raw.strip().lower()
    if value in {"0", "none", "off", "false", "no"}:
        return _NO_TIMEOUT_BRIDGE_TIMEOUT_SECONDS

    try:
        timeout = int(value)
    except ValueError:
        print(
            f"Invalid {_TIMEOUT_ENV}={raw!r}; "
            f"falling back to {_DEFAULT_BRIDGE_TIMEOUT_SECONDS}s"
        )
        return _DEFAULT_BRIDGE_TIMEOUT_SECONDS

    if timeout <= 0:
        return _NO_TIMEOUT_BRIDGE_TIMEOUT_SECONDS
    return timeout


def ask_hermes(
    content: str,
    task_id: str | None = None,
    msg_type: str = "query",
    data: str | None = None,
    new_session: bool = False,
    from_llm: str = "gemini",
    from_model: str | None = None,
    to_model: str | None = None,
    no_timeout: bool = False,
    review: bool = False,
) -> int:
    """Send a message to Hermes and invoke it to process the message."""
    msg_id = send_message(
        content,
        task_id,
        msg_type,
        data,
        from_llm=from_llm,
        to_llm=_AGENT_NAME,
        from_model=from_model,
        to_model=to_model,
    )
    print(f"\nInvoking {_AGENT_TITLE} to process message #{msg_id}...")
    process_for_hermes(msg_id, new_session, no_timeout, review=review)
    return msg_id


def process_for_hermes(
    message_id: int,
    new_session: bool = False,
    no_timeout: bool = False,
    review: bool = False,
) -> None:
    """Read a message addressed to Hermes, invoke the CLI, and reply."""
    msg = _fetch_message(message_id)
    if not msg:
        return

    _ = new_session  # Hermes is session-less for bridge calls.
    timeout_val = _resolve_bridge_timeout(no_timeout)
    model = _extract_target_model(msg) or _DEFAULT_MODEL
    provider = _detect_provider(model)
    prompt = _build_prompt(msg, review)

    print(f"Message #{msg['id']}")
    print(f"   From: {msg['from']} -> To: {msg['to']}")
    print(f"   Type: {msg['type']}")
    print(f"   Task: {msg['task_id'] or 'N/A'}")
    print(f"   Model: {model}")
    print(f"   Provider: {provider}")
    if timeout_val == _NO_TIMEOUT_BRIDGE_TIMEOUT_SECONDS:
        print("   Hard timeout: no-timeout requested (24h ceiling)")
    else:
        print(f"   Hard timeout: {timeout_val}s")

    ok, response, stderr_excerpt = _invoke_hermes(
        prompt,
        model,
        provider=provider,
        timeout_s=timeout_val,
        cwd=REPO_ROOT,
    )
    if not ok:
        _handle_error(
            msg,
            message_id,
            stderr_excerpt or f"{_AGENT_TITLE} returned no final message",
        )
        return

    print(f"\n{_AGENT_TITLE} finished ({len(response)} chars)")
    reply_id = send_message(
        content=response,
        task_id=msg["task_id"],
        msg_type="response",
        from_llm=_AGENT_NAME,
        to_llm=msg["from"],
    )
    acknowledge(message_id)
    acknowledge(reply_id)


def _invoke_hermes(
    prompt: str,
    model: str,
    *,
    provider: str | None = None,
    timeout_s: int,
    cwd: Path | None = None,
) -> tuple[bool, str, str]:
    """Run hermes and return (ok, stdout response, stderr excerpt)."""
    command = _build_command(prompt, model, provider)
    try:
        completed = subprocess.run(
            command,
            input="",
            cwd=cwd or REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return False, stdout.strip(), (
            f"{_AGENT_TITLE} timed out after {timeout_s}s\n{stderr}"
        ).strip()
    except OSError as exc:
        return False, "", f"{type(exc).__name__}: {exc}"

    response = completed.stdout.strip()
    stderr_excerpt = completed.stderr.strip()
    ok = completed.returncode == 0 and bool(response)
    if not ok and not stderr_excerpt:
        stderr_excerpt = (
            f"{_AGENT_TITLE} exited {completed.returncode} with no stdout"
        )
    return ok, response, stderr_excerpt[:500]


def _fetch_message(message_id: int) -> dict[str, object] | None:
    """Fetch a message addressed to this agent from the database."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, task_id, from_llm, to_llm, message_type, content, data, timestamp
        FROM messages
        WHERE id = ? AND to_llm = ?
        """,
        (message_id, _AGENT_NAME),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        print(f"Message {message_id} not found or not addressed to {_AGENT_TITLE}")
        return None

    return {
        "id": row[0],
        "task_id": row[1],
        "from": row[2],
        "to": row[3],
        "type": row[4],
        "content": row[5],
        "data": row[6],
        "timestamp": row[7],
    }


def _extract_target_model(msg: dict[str, object]) -> str | None:
    """Read optional to_model from message metadata JSON."""
    data = msg.get("data")
    if not data:
        return None
    try:
        payload = json.loads(data)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    model = payload.get("to_model")
    return str(model) if model else None


def _build_prompt(msg: dict[str, object], review: bool = False) -> str:
    """Build a direct one-shot bridge prompt."""
    prompt = f"""You are {_AGENT_TITLE}, receiving a message from {msg['from'].title()} via the message broker.

---
Task ID: {msg['task_id'] or 'none'}
Type: {msg['type']}
From: {msg['from']}

{msg['content']}
"""
    if msg["data"]:
        prompt += f"""
---
Attached data:
{msg['data']}
"""
    prompt += """

---

Standing rules for bridge Q&A:
- Respond directly. Be concise. This bridge is for quick questioning
  and short coordination, not long-running task execution.
- Do NOT use broker or MCP messaging tools to send your response.
  Output your response directly.
"""
    return _prepend_review_protocol(prompt, review)


def _prepend_review_protocol(prompt: str, review: bool) -> str:
    """Prepend docs/review-protocol.md when --review is requested."""
    if not review:
        return prompt
    prefix = (REPO_ROOT / "docs" / "review-protocol.md").read_text(
        encoding="utf-8"
    ).rstrip()
    return f"{prefix}\n\n{prompt}"


def _handle_error(
    msg: dict[str, object],
    message_id: int,
    reason: str,
) -> None:
    """Record an agent failure as an error response and acknowledge it."""
    print(f"\n{_AGENT_TITLE} error for message #{message_id}: {reason}")
    reply_id = send_message(
        content=f"[{_AGENT_TITLE} error] {reason}",
        task_id=msg["task_id"],
        msg_type="error",
        from_llm=_AGENT_NAME,
        to_llm=msg["from"],
    )
    acknowledge(message_id)
    acknowledge(reply_id)
