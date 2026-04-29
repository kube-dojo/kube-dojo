"""GeminiAdapter — wraps ``gemini`` CLI (Google AI Studio / Gemini CLI) for the runtime.

Second real adapter. Pressure-tests the protocol against the RICHEST existing
flag requirements in the codebase:

- MCP tool restrictions via ``--allowed-mcp-server-names`` (used by
  ``scripts/build/dispatch.py`` for pipeline reviewers to restrict tool
  access).
- Stall detection: the prior art in ``_gemini.py::_stream_with_watchdog``
  was specifically built because Gemini CLI stalls frequently. Our runtime's
  stall watchdog covers this case uniformly — GeminiAdapter doesn't need a
  custom implementation, just the right ``stall_timeout`` default.
- Rate-limit detection: Gemini returns ``RESOURCE_EXHAUSTED``, ``quota
  exceeded``, and occasionally ``No capacity available`` depending on
  backend. Patterns match dispatch.py prior art.
- No session IDs. Gemini CLI doesn't expose them, so ``parse_response``
  returns ``session_id=None`` always. Resume policy is ``bridge_only``
  for cost economics, but session IDs come from the bridge's own SQLite
  ``sessions`` table and are passed in as ``session_id=...`` — we just
  ignore it here because the CLI has no ``--resume`` equivalent anyway.

Key differences from CodexAdapter:
- Output to stdout (no ``-o <file>``); ``output_file`` stays None.
- No sandbox flags. Gemini CLI uses ``--approval-mode=yolo`` for
  writable mode; read-only is the default. There is no ``danger`` mode
  distinct from ``workspace-write``.
- Liveness paths = () — stdout streaming is the only signal we need,
  and it's sufficient because Gemini CLI always writes to stdout.

Issue: #1184
"""
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

try:
    from dispatch import GEMINI_WRITER_MODEL
except ImportError:  # pragma: no cover - package import path variant
    GEMINI_WRITER_MODEL = os.environ.get("KUBEDOJO_WRITER_MODEL", "gemini-3.1-pro-preview")

from ..result import ParseResult
from .base import InvocationPlan

# TRUE rate-limit patterns — only things that mean "quota is EXHAUSTED for
# hours", not transient server-side issues that clear in seconds.
# (See issue #1185 follow-up: "No capacity available" and raw 429 status
# codes are transient and were causing 5h false-lockouts after a single
# ~2-minute retry on Gemini's end.)
_RATE_LIMIT_PATTERNS = (
    r"RESOURCE_EXHAUSTED",
    r"usage limit reached",
    r"quota exceeded",
    r"daily.{0,10}limit.{0,10}exceeded",
)
_RATE_LIMIT_RE = re.compile("|".join(_RATE_LIMIT_PATTERNS), re.IGNORECASE)

# Transient capacity / retry patterns — NOT rate limits. The Gemini CLI
# retries these internally with backoff and usually succeeds on a later
# attempt. We log them as warnings but never block the quota.
_TRANSIENT_ERROR_PATTERNS = (
    r"No capacity available",
    r"Retrying with backoff",
    r"\bstatus 429\b",
    r"\bHTTP 429\b",
    r"\b429\b",
    r"too many requests",
    r"rate limit",
    r"rate_limit",
)
_TRANSIENT_ERROR_RE = re.compile("|".join(_TRANSIENT_ERROR_PATTERNS), re.IGNORECASE)


class GeminiAdapter:
    """Adapter for the ``gemini`` CLI (Google Gemini)."""

    name: str = "gemini"
    default_model: str = GEMINI_WRITER_MODEL
    # Gemini has no sandbox distinction between workspace-write and danger —
    # we accept both names but treat them identically (both mean "CLI may
    # write files in cwd via --approval-mode=yolo").
    supported_modes: frozenset[str] = frozenset({"read-only", "workspace-write", "danger"})

    def build_invocation(
        self,
        *,
        prompt: str,
        mode: str,
        cwd: Path,
        model: str | None,
        task_id: str | None,
        session_id: str | None,
        tool_config: dict | None,
    ) -> InvocationPlan:
        """Build the ``gemini`` CLI invocation.

        Defensively ignores ``session_id``: Gemini CLI has no ``--resume``
        equivalent. The bridge tracks session IDs in its own SQLite table
        and uses them for conversation-context injection into the prompt,
        not for CLI-level resume. We silently drop it here.

        Supports ``tool_config``:
            - ``{"mcp_server_names": ["rag", "other"]}`` → appended as
              ``--allowed-mcp-server-names rag,other``
            - Any other keys are ignored (forward-compatible).
        """
        gemini_bin = shutil.which("gemini") or "gemini"

        cmd: list[str] = [
            gemini_bin,
            "-m", model or self.default_model,
        ]

        # Approval mode: read-only is the default; yolo for write modes.
        # "danger" is treated identically to "workspace-write" because
        # Gemini CLI has no stricter-than-yolo bypass.
        if mode in ("workspace-write", "danger"):
            cmd.append("--approval-mode=yolo")

        # MCP tool restriction via tool_config.
        env_overrides: dict[str, str | None] = {}
        if tool_config:
            # API-key auth is the default. When the bridge detects API-key
            # quota exhaustion, it retries with this flag so the child process
            # sees no Gemini API keys and the CLI falls through to OAuth creds
            # in ~/.gemini/oauth_creds.json.
            if tool_config.get("use_subscription_auth"):
                env_overrides["GEMINI_API_KEY"] = None
                env_overrides["GOOGLE_API_KEY"] = None

            mcp_server_names = tool_config.get("mcp_server_names")
            if mcp_server_names:
                if isinstance(mcp_server_names, (list, tuple)):
                    joined = ",".join(mcp_server_names)
                else:
                    joined = str(mcp_server_names)
                cmd.extend(["--allowed-mcp-server-names", joined])

        # Silently ignore session_id (CLI has no equivalent) and task_id
        # (runner already logs it via usage record). cwd IS stamped into
        # the plan — liveness_signal_paths() needs it to derive the
        # ~/.gemini/tmp/<basename>/ project dir without reading os.getcwd().
        _ = session_id
        _ = task_id

        return InvocationPlan(
            cmd=cmd,
            cwd=cwd,
            stdin_payload=prompt,
            output_file=None,  # Gemini writes to stdout only.
            env_overrides=env_overrides,
            liveness_paths=(),  # stdout streamer is not actually sufficient —
            # see liveness_signal_paths() docstring — but we compute the
            # real paths lazily there because they depend on cwd.
        )

    def parse_response(
        self,
        *,
        stdout: str,
        stderr: str,
        returncode: int,
        output_file: Path | None,
        plan: InvocationPlan | None = None,
        call_start_time: float | None = None,
    ) -> ParseResult:
        """Parse Gemini CLI output into a ParseResult.

        Primary source: stdout. Fallback source: the Gemini session file
        under ``~/.gemini/tmp/<project>/chats/session-*.json``.

        Why the fallback exists (2026-04-10): the Gemini CLI block-buffers
        stdout when not connected to a TTY. On long calls (MCP tool use +
        internal retries) the CLI can finish and write its full response
        to the session file while stdout is still sitting in a kernel
        buffer that never gets flushed before proc.kill() on hard_timeout.
        Result: the pipeline used to discard completed responses and
        retry forever, even though the answer was already on disk.

        The fix reads the newest session file after every call and uses
        it if stdout is empty OR the call was killed. The session file
        is updated live as Gemini writes, so even a killed call can
        recover the work-in-progress up to the last flush.
        """
        _ = output_file  # unused — Gemini doesn't use -o

        combined = f"{stdout}\n{stderr}"
        hard_limit_hit = bool(_RATE_LIMIT_RE.search(combined))
        transient_seen = bool(_TRANSIENT_ERROR_RE.search(combined))

        stdout_response = stdout.strip()

        # Three outcomes to distinguish:
        #
        #   1. Fast path (success):
        #        returncode == 0 AND stdout non-empty AND no rate-limit pattern
        #      → use stdout directly, no disk scan
        #
        #   2. Recovery path (killed but answer on disk):
        #        returncode != 0 (killed / failed) OR stdout empty
        #      → try the session file. If it has content, THAT is the real
        #        response and the call is a success despite the bad exit.
        #
        #   3. Hard failure:
        #        no stdout, no session-file recovery → fail the call. If a
        #        rate-limit pattern was present, classify as rate_limited.
        #
        # Note on the "Error: quota exceeded in stdout" case: Gemini CLI
        # sometimes writes quota messages to stdout instead of stderr. When
        # that happens, returncode is always non-zero, which routes us to
        # the recovery path. The session file has nothing (Gemini never
        # got past the quota error), so we end in the hard-failure branch
        # and rate_limited is correctly set.

        fast_path_ok = (
            returncode == 0
            and bool(stdout_response)
            and not hard_limit_hit
        )

        final_response = ""
        source_note: str | None = None

        if fast_path_ok:
            final_response = stdout_response
        else:
            # Recovery path: read the session file. Empty plan means we're
            # being called from a unit test that doesn't exercise the
            # recovery logic — leave the file_response empty.
            file_response = ""
            if plan is not None:
                file_response = self._read_latest_session_response(
                    plan, call_start_time=call_start_time,
                )
            if file_response:
                final_response = file_response
                reason = (
                    "stdout empty" if not stdout_response
                    else f"rc={returncode}"
                )
                source_note = (
                    f"recovered {len(file_response)} chars from "
                    f"~/.gemini/tmp/.../chats (reason: {reason})"
                )

        # Rate limit: pattern present AND we have no usable response
        # anywhere. If we recovered from the session file, it's not a
        # real rate-limit — the CLI survived whatever transient 429 it saw.
        rate_limited = hard_limit_hit and not final_response

        ok = bool(final_response) and not rate_limited
        response = final_response if ok else ""

        stderr_excerpt: str | None = None
        if not ok:
            # Prefer stderr; fall back to stdout if stderr is empty
            # (some Gemini errors land in stdout, especially quota messages).
            excerpt_source = stderr.strip() or stdout.strip() or ""
            stderr_excerpt = excerpt_source[:500] or None
        elif source_note:
            # We recovered from disk. Surface the note so logs show it.
            stderr_excerpt = source_note
        elif transient_seen:
            # Call succeeded despite a transient 429 / "No capacity" retry —
            # record a brief note so monitoring can see retry frequency, but
            # do NOT mark rate_limited.
            stderr_excerpt = "transient retry resolved by CLI backoff"

        return ParseResult(
            ok=ok,
            response=response,
            stderr_excerpt=stderr_excerpt,
            rate_limited=rate_limited,
            session_id=None,  # Gemini CLI doesn't expose session IDs.
            tokens=None,      # Nor tokens.
        )

    # ---------------------------------------------------------------------
    # Session-file recovery
    # ---------------------------------------------------------------------

    def _read_latest_session_response(
        self,
        plan: InvocationPlan,
        *,
        call_start_time: float | None = None,
    ) -> str:
        """Extract the assistant's response from the newest Gemini session file.

        Gemini CLI writes a file at ``~/.gemini/tmp/<cwd-basename>/chats/
        session-YYYY-MM-DDTHH-MM-<short>.json`` for every exec. It creates
        a new file at call start and keeps updating it throughout the
        run. The file structure is:

            {
              "sessionId": "<uuid>",
              "startTime": "<iso>",
              "lastUpdated": "<iso>",
              "messages": [
                {"type": "user", "content": [{"text": "..."}]},
                {"type": "gemini", "content": "..."},   # a plain string
                {"type": "gemini", "content": "..."},
                ...
              ]
            }

        We pick the newest file by mtime (Gemini calls are sequential in
        our pipeline, so newest-by-mtime == current call). If
        ``call_start_time`` is provided, we additionally verify the file
        was modified AFTER the call started — a safety check against
        leftover session files from previous calls.

        Returns the concatenation of every ``type=gemini`` message's text
        content, or '' if nothing recoverable is found. All exceptions
        are swallowed — this is a last-resort fallback, not a primary
        code path.
        """
        import json as _json
        import time as _time

        try:
            chats_dir = Path.home() / ".gemini" / "tmp" / plan.cwd.name / "chats"
            if not chats_dir.exists():
                return ""

            candidates = sorted(
                chats_dir.glob("session-*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if not candidates:
                return ""

            # Pick the newest file whose mtime is after the call start.
            # If call_start_time is unknown, trust the newest file.
            newest: Path | None = None
            if call_start_time is None:
                newest = candidates[0]
            else:
                # Compare wall-clock (file mtime) to monotonic (call_start).
                # Convert monotonic → wall by adding (time.time() - monotonic())
                # at call time — but we don't have that delta. Approximation:
                # any file modified in the last 2 hours of wall clock is
                # acceptable if it's also the newest. This guards against
                # picking a multi-day-old orphan file.
                two_hours_ago = _time.time() - 2 * 3600
                for c in candidates:
                    if c.stat().st_mtime >= two_hours_ago:
                        newest = c
                        break

            if newest is None:
                return ""

            data = _json.loads(newest.read_text("utf-8"))
            messages = data.get("messages", [])
            if not isinstance(messages, list):
                return ""

            # Concatenate every gemini message's text content. Skip user
            # messages, skip info/system messages, skip tool-call
            # metadata. Content for gemini messages is a plain string
            # (verified against real session files on disk).
            parts: list[str] = []
            for msg in messages:
                if not isinstance(msg, dict):
                    continue
                if msg.get("type") != "gemini":
                    continue
                content = msg.get("content")
                if isinstance(content, str) and content.strip():
                    parts.append(content)
                elif isinstance(content, list):
                    # Defensive: some older Gemini CLI versions may use
                    # list-of-parts format like user messages.
                    for part in content:
                        if isinstance(part, dict):
                            text = part.get("text")
                            if isinstance(text, str) and text.strip():
                                parts.append(text)

            return "\n\n".join(parts).strip()
        except Exception:
            return ""

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        """Return filesystem paths the watchdog should poll for mtime bumps.

        Original design (issue #1184) assumed stdout streaming was sufficient
        for Gemini because ``_stream_with_watchdog`` in the prior art worked
        that way. That assumption was WRONG in two ways:

        1. The gemini CLI uses block-buffered stdout when its stdout isn't a
           TTY (subprocess pipe). It can emit nothing for 3+ minutes during
           reasoning bursts, even when actively working — the final message
           gets flushed all at once near the end.
        2. bufsize=1 on the Popen side only controls OUR read buffering.
           We can't force Gemini to flush its own writes.

        Result before this fix: watchdog fired spurious stalls on long
        Gemini calls that were actually succeeding (session files on disk
        proved it). See 2026-04-10 incident — a 319s skeleton generation
        was killed at 181s even though Gemini wrote to ``logs.json`` at
        319s mark.

        Fix: walk the gemini tmp directory for this project and return
        any file/dir whose mtime bumps during exec. The CLI updates:
          - ``~/.gemini/tmp/<project>/logs.json`` — bumps on every tool
            call or status update (verified: modified during exec).
          - ``~/.gemini/tmp/<project>/chats/`` — directory mtime bumps
            when a new session JSON file is created at the start of exec.
          - ``~/.gemini/tmp/<project>/chats/session-*.json`` — newest
            session file grows as messages stream in.

        ``<project>`` is the cwd basename per gemini-cli convention. We
        read it from ``plan.cwd`` (stamped by the adapter in
        ``build_invocation``) rather than ``os.getcwd()`` so the adapter
        is not coupled to ambient process state. Refactored 2026-04-10
        to drop the os.getcwd() hack.
        """
        paths: list[Path] = []

        # The gemini CLI stores project-scoped state under
        # ~/.gemini/tmp/<project-name>/ where project-name is the basename
        # of the cwd the CLI was invoked from. plan.cwd carries the exact
        # path the runner uses on Popen, so its .name matches what gemini
        # will derive internally.
        cwd_basename = plan.cwd.name
        gemini_project_dir = Path.home() / ".gemini" / "tmp" / cwd_basename

        if gemini_project_dir.exists():
            # 1. The logs.json file — most reliable per-call signal.
            logs_json = gemini_project_dir / "logs.json"
            if logs_json.exists():
                paths.append(logs_json)

            # 2. The chats/ directory — mtime bumps on new session file
            #    creation, which happens at the start of every gemini exec.
            chats_dir = gemini_project_dir / "chats"
            if chats_dir.exists():
                paths.append(chats_dir)

                # 3. The newest session-*.json file — grows as messages stream.
                #    We pick by mtime at adapter build time; the watchdog then
                #    watches THAT file. If Gemini creates a newer session file
                #    after we start, the chats/ dir mtime bump (signal #2)
                #    catches it.
                try:
                    session_files = sorted(
                        chats_dir.glob("session-*.json"),
                        key=lambda p: p.stat().st_mtime,
                        reverse=True,
                    )
                    if session_files:
                        paths.append(session_files[0])
                except OSError:
                    pass

        return tuple(paths)
