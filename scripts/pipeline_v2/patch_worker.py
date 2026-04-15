from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from dispatch import dispatch_codex

from .control_plane import ControlPlane, Lease
from .escalation import should_dead_letter_rewrite, should_escalate_patch
from .review_worker import PRO_MODEL


PATCH_ESTIMATED_USD = 0.0150
PATCH_CONTEXT_WINDOW_LINES = 30
REPEATED_EXCEPTION_WINDOW_SECONDS = 3600
REPEATED_EXCEPTION_THRESHOLD = 3


@dataclass(frozen=True)
class PatchRunOutcome:
    status: str
    module_key: str | None = None
    lease_id: str | None = None
    details: dict[str, Any] | None = None


class MalformedPatchResponse(ValueError):
    pass


class PatchWorker:
    def __init__(
        self,
        control_plane: ControlPlane,
        *,
        worker_id: str = "patch-worker",
        dispatch_fn: Callable[..., tuple[bool, str]] = dispatch_codex,
    ):
        self.control_plane = control_plane
        self.worker_id = worker_id
        self.dispatch_fn = dispatch_fn

    def run_once(self) -> PatchRunOutcome:
        lease = self.control_plane.lease_next_job(
            self.worker_id,
            phase="patch",
            requested_calls=1,
            estimated_usd=PATCH_ESTIMATED_USD,
        )
        if lease is None:
            return PatchRunOutcome(status="idle")

        module_path = self._module_path_for_lease(lease)
        self.control_plane.emit_event(
            "attempt_started",
            module_key=lease.module_key,
            lease_id=lease.lease_id,
            payload={
                "job_id": lease.job_id,
                "phase": lease.phase,
                "worker_id": self.worker_id,
            },
        )

        try:
            review_payload = self._latest_review_failure(lease.module_key)
            failed_checks = review_payload.get("failed_checks") or review_payload.get("checks") or []
            feedback = str(review_payload.get("feedback", ""))
            module_text = module_path.read_text(encoding="utf-8")
            decision = should_escalate_patch(
                failed_checks=failed_checks,
                feedback=feedback,
                patch_attempts=self._patch_attempts_for_module(lease.module_key),
                patch_apply_failed=False,
                partial_apply=False,
                patch_degraded=self.control_plane.count_events_for_module(
                    lease.module_key,
                    "patch_degraded",
                )
                > 0,
            )
            if decision.should_escalate:
                return self._escalate(
                    lease,
                    failed_checks=failed_checks,
                    feedback=feedback,
                    reasons=decision.reasons,
                )

            patch_result, actual_calls = self._dispatch_with_retry(
                self._patch_prompt(
                    module_text,
                    module_path,
                    failed_checks=failed_checks,
                    feedback=feedback,
                ),
                model=lease.model,
            )
            patched, applied, failed = apply_review_edits(module_text, patch_result["edits"])

            if failed:
                patch_apply_failed = not applied
                if patch_apply_failed:
                    self.control_plane.emit_event(
                        "patch_apply_failed",
                        module_key=lease.module_key,
                        lease_id=lease.lease_id,
                        payload={
                            "job_id": lease.job_id,
                            "failed_edits": failed,
                            "attempted_edits": len(patch_result["edits"]),
                        },
                    )
                decision = should_escalate_patch(
                    failed_checks=failed_checks,
                    feedback=feedback,
                    patch_attempts=self._patch_attempts_for_module(lease.module_key),
                    patch_apply_failed=patch_apply_failed,
                    partial_apply=bool(applied),
                    patch_degraded=False,
                )
                return self._escalate(
                    lease,
                    failed_checks=failed_checks,
                    feedback=feedback,
                    reasons=decision.reasons,
                    actual_calls=actual_calls,
                    actual_usd=round(actual_calls * PATCH_ESTIMATED_USD, 4),
                    extra_payload={
                        "applied_edits": len(applied),
                        "failed_edits": failed,
                    },
                )

            _atomic_write_text(module_path, patched)
            self.control_plane.enqueue(
                lease.module_key,
                phase="review",
                model=PRO_MODEL,
                priority=lease.job_id,
            )
            details = {
                "applied_edits": len(applied),
                "review_reenqueued": True,
            }
            self.control_plane.complete_lease(
                lease.lease_id,
                actual_calls=actual_calls,
                actual_usd=round(actual_calls * PATCH_ESTIMATED_USD, 4),
                outcome="attempt_succeeded",
                event_payload={"phase": "patch", **details},
            )
            return PatchRunOutcome(
                status="patched",
                module_key=lease.module_key,
                lease_id=lease.lease_id,
                details=details,
            )
        except MalformedPatchResponse as exc:
            self.control_plane.release_lease(
                lease.lease_id,
                reason="malformed_patch_response",
            )
            return PatchRunOutcome(
                status="retry_scheduled",
                module_key=lease.module_key,
                lease_id=lease.lease_id,
                details={"reason": "malformed_json", "error": str(exc)},
            )
        except Exception as exc:
            recent_failures = self.control_plane.count_events_for_module(
                lease.module_key,
                "attempt_failed",
                since=int(datetime.now(UTC).timestamp()) - REPEATED_EXCEPTION_WINDOW_SECONDS,
            )
            if recent_failures >= REPEATED_EXCEPTION_THRESHOLD - 1:
                details = {
                    "phase": "patch",
                    "reason": "patch_worker_repeated_exception",
                    "error": str(exc),
                    "recent_attempt_failed_count": recent_failures + 1,
                }
                self.control_plane.fail_lease_terminal(
                    lease.lease_id,
                    reason="patch_worker_repeated_exception",
                    event_payload=details,
                )
                return PatchRunOutcome(
                    status="needs_human_intervention",
                    module_key=lease.module_key,
                    lease_id=lease.lease_id,
                    details=details,
                )

            self.control_plane.complete_lease(
                lease.lease_id,
                actual_calls=0,
                actual_usd=0.0,
                outcome="attempt_failed",
                event_payload={"phase": "patch", "reason": "worker_error", "error": str(exc)},
            )
            return PatchRunOutcome(
                status="attempt_failed",
                module_key=lease.module_key,
                lease_id=lease.lease_id,
                details={"reason": "worker_error", "error": str(exc)},
            )

    def loop_forever(self, *, sleep_seconds: float = 5.0) -> None:
        while True:
            outcome = self.run_once()
            if outcome.status == "idle":
                time.sleep(sleep_seconds)

    def _module_path_for_lease(self, lease: Lease) -> Path:
        module_path = Path(lease.module_key)
        if not module_path.is_absolute():
            module_path = self.control_plane.repo_root / module_path
        return module_path

    def _latest_review_failure(self, module_key: str) -> dict[str, Any]:
        for event in reversed(self.control_plane.iter_events("check_failed")):
            if str(event["module_key"]) != module_key:
                continue
            payload = json.loads(event["payload_json"])
            if isinstance(payload, dict):
                return payload
        raise MalformedPatchResponse(f"no check_failed event found for {module_key}")

    def _patch_attempts_for_module(self, module_key: str) -> int:
        attempts = 0
        for event in self.control_plane.iter_events("attempt_started"):
            if str(event["module_key"]) != module_key:
                continue
            payload = json.loads(event["payload_json"])
            if isinstance(payload, dict) and payload.get("phase") == "patch":
                attempts += 1
        return attempts

    def _dispatch_with_retry(self, prompt: str, *, model: str) -> tuple[dict[str, Any], int]:
        last_error: Exception | None = None
        calls_used = 0
        for attempt in range(2):
            ok, output = self.dispatch_fn(prompt, model=model, timeout=900)
            calls_used += 1
            if not ok:
                raise MalformedPatchResponse(output.strip() or f"{model} dispatch failed")
            try:
                return _validate_patch_payload(output), calls_used
            except MalformedPatchResponse as exc:
                last_error = exc
                if attempt == 1:
                    break
        assert last_error is not None
        raise last_error

    def _escalate(
        self,
        lease: Lease,
        *,
        failed_checks: list[dict],
        feedback: str,
        reasons: list[str],
        actual_calls: int = 0,
        actual_usd: float = 0.0,
        extra_payload: dict[str, Any] | None = None,
    ) -> PatchRunOutcome:
        payload = {
            "job_id": lease.job_id,
            "phase": "patch",
            "failed_checks": failed_checks,
            "feedback": feedback,
            "reasons": reasons,
            **(extra_payload or {}),
        }
        self.control_plane.emit_event(
            "rewrite_escalated",
            module_key=lease.module_key,
            lease_id=lease.lease_id,
            payload=payload,
        )
        rewrite_attempts = self.control_plane.count_events_for_module(
            lease.module_key,
            "rewrite_escalated",
        )
        if should_dead_letter_rewrite(rewrite_attempts):
            details = {**payload, "rewrite_attempts": rewrite_attempts}
            self.control_plane.fail_lease_terminal(
                lease.lease_id,
                reason="rewrite_attempt_limit",
                event_payload=details,
            )
            return PatchRunOutcome(
                status="needs_human_intervention",
                module_key=lease.module_key,
                lease_id=lease.lease_id,
                details=details,
            )

        self.control_plane.complete_lease(
            lease.lease_id,
            actual_calls=actual_calls,
            actual_usd=actual_usd,
            outcome="attempt_succeeded",
            event_payload={"phase": "patch", "reason": "rewrite_escalated"},
        )
        self.control_plane.enqueue(
            lease.module_key,
            phase="write",
            model=PRO_MODEL,
            priority=0,
        )
        return PatchRunOutcome(
            status="rewrite_escalated",
            module_key=lease.module_key,
            lease_id=lease.lease_id,
            details={**payload, "rewrite_attempts": rewrite_attempts},
        )

    def _patch_prompt(
        self,
        module_text: str,
        module_path: Path,
        *,
        failed_checks: list[dict],
        feedback: str,
    ) -> str:
        checks_text = _format_failed_checks(failed_checks)
        slices = _build_content_slices(module_text, failed_checks)
        slice_blocks = "\n\n".join(_format_content_slice(module_text, item) for item in slices)
        return f"""You are a KubeDojo patch worker.

Return JSON only with this exact schema:
{{
  "edits": [
    {{"type": "replace", "find": "...", "new": "...", "reason": "..."}}
  ],
  "feedback": "..."
}}

Generate only targeted bounded edits. Do not rewrite the full file.
Allowed edit types: replace, insert_after, insert_before, delete.
Every `find` anchor must be a literal substring from the module and must be unique.
Every `new` value must be final concrete text, not placeholders.

Module path: {module_path}

Failed checks:
{checks_text}

Reviewer feedback:
{feedback}

Relevant content slices:
{slice_blocks}

Return JSON only with anchored edits that fix the failed checks using the provided slices.
"""

def _format_failed_checks(failed_checks: list[dict[str, Any]]) -> str:
    if not failed_checks:
        return "(none)"

    blocks: list[str] = []
    for check in failed_checks:
        check_id = str(check.get("id", "unknown"))
        evidence = str(check.get("evidence", "")).strip() or "(no evidence provided)"
        fix_hint = str(check.get("fix_hint", "")).strip() or "(none)"
        line_range = _normalize_line_range(check.get("line_range"), total_lines=None)
        if line_range is None:
            location = "in inferred section context"
        else:
            location = f"at lines {line_range[0]}-{line_range[1]}"
        blocks.append(
            "\n".join(
                [
                    f"Failed check {check_id} {location}:",
                    evidence,
                    f"Fix hint: {fix_hint}",
                ]
            )
        )
    return "\n\n".join(blocks)


def _build_content_slices(module_text: str, failed_checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lines = module_text.splitlines()
    if not lines:
        return [{"start": 1, "end": 1, "checks": failed_checks}]

    requests: list[dict[str, Any]] = []
    for check in failed_checks:
        line_range = _normalize_line_range(check.get("line_range"), total_lines=len(lines))
        if line_range is None:
            start, end = _section_bounds_for_check(lines, check)
        else:
            start = max(1, line_range[0] - PATCH_CONTEXT_WINDOW_LINES)
            end = min(len(lines), line_range[1] + PATCH_CONTEXT_WINDOW_LINES)
        requests.append({"start": start, "end": end, "checks": [check]})

    if not requests:
        return [{"start": 1, "end": len(lines), "checks": []}]

    requests.sort(key=lambda item: (item["start"], item["end"]))
    merged: list[dict[str, Any]] = [requests[0]]
    for item in requests[1:]:
        current = merged[-1]
        if item["start"] <= current["end"] + 1:
            current["end"] = max(current["end"], item["end"])
            current["checks"].extend(item["checks"])
            continue
        merged.append(item)
    return merged


def _format_content_slice(module_text: str, item: dict[str, Any]) -> str:
    lines = module_text.splitlines()
    if not lines:
        return "Content slice (lines 1 to 1):\n1:"

    start = max(1, min(int(item["start"]), len(lines)))
    end = max(start, min(int(item["end"]), len(lines)))
    width = len(str(len(lines)))
    numbered = "\n".join(
        f"{line_no:>{width}}: {lines[line_no - 1]}"
        for line_no in range(start, end + 1)
    )
    return f"Content slice (lines {start} to {end}):\n{numbered}"


def _normalize_line_range(
    line_range: Any,
    *,
    total_lines: int | None,
) -> tuple[int, int] | None:
    if (
        not isinstance(line_range, list)
        or len(line_range) != 2
        or not all(isinstance(value, int) for value in line_range)
    ):
        return None

    start, end = line_range
    if end < start:
        start, end = end, start
    if total_lines is not None:
        start = max(1, min(start, total_lines))
        end = max(1, min(end, total_lines))
    if start < 1 or end < 1:
        return None
    return start, end


def _section_bounds_for_check(lines: list[str], check: dict[str, Any]) -> tuple[int, int]:
    anchor_line = _find_check_anchor_line(lines, check)
    if anchor_line is None:
        return _default_section_bounds(lines)
    return _markdown_section_bounds(lines, anchor_line)


def _find_check_anchor_line(lines: list[str], check: dict[str, Any]) -> int | None:
    candidates = [
        str(check.get("evidence", "")).strip(),
        str(check.get("fix_hint", "")).strip(),
        str(check.get("id", "")).strip(),
    ]
    normalized_lines = [_collapse_whitespace(line).lower() for line in lines]
    for candidate in candidates:
        if len(candidate) < 4:
            continue
        normalized_candidate = _collapse_whitespace(candidate).lower()
        for index, line in enumerate(normalized_lines, start=1):
            if normalized_candidate in line:
                return index
    return None


def _markdown_section_bounds(lines: list[str], anchor_line: int) -> tuple[int, int]:
    header_pattern = re.compile(r"^(#{1,6})\s+\S")
    total_lines = len(lines)
    start = 1
    level = 1

    for index in range(min(anchor_line, total_lines), 0, -1):
        match = header_pattern.match(lines[index - 1].strip())
        if match:
            start = index
            level = len(match.group(1))
            break

    end = total_lines
    for index in range(start + 1, total_lines + 1):
        match = header_pattern.match(lines[index - 1].strip())
        if match and len(match.group(1)) <= level:
            end = index - 1
            break
    return start, end


def _default_section_bounds(lines: list[str]) -> tuple[int, int]:
    for index, line in enumerate(lines, start=1):
        if line.strip().lower() == "## content":
            return _markdown_section_bounds(lines, index)
    for index, line in enumerate(lines, start=1):
        if re.match(r"^(#{1,6})\s+\S", line.strip()):
            return _markdown_section_bounds(lines, index)
    return 1, len(lines)


def _collapse_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _find_anchor(content: str, anchor: str) -> tuple[int, int] | None:
    if not anchor:
        return None

    count = content.count(anchor)
    if count == 1:
        start = content.index(anchor)
        return start, start + len(anchor)
    if count > 1:
        return None

    norm_anchor = _collapse_whitespace(anchor)
    if len(norm_anchor) < 20:
        return None

    orig_positions: list[int] = []
    norm_chars: list[str] = []
    prev_ws = False
    for idx, ch in enumerate(content):
        if ch.isspace():
            if not prev_ws and norm_chars:
                norm_chars.append(" ")
                orig_positions.append(idx)
            prev_ws = True
            continue
        norm_chars.append(ch)
        orig_positions.append(idx)
        prev_ws = False
    normalized = "".join(norm_chars).strip()
    if normalized.count(norm_anchor) != 1:
        return None

    norm_start = normalized.index(norm_anchor)
    if norm_start >= len(orig_positions):
        return None
    orig_start = orig_positions[norm_start]

    consumed = 0
    orig_end = orig_start
    in_whitespace_run = False
    while orig_end < len(content) and consumed < len(norm_anchor):
        ch = content[orig_end]
        if ch.isspace():
            if not in_whitespace_run:
                consumed += 1
                in_whitespace_run = True
        else:
            consumed += 1
            in_whitespace_run = False
        orig_end += 1
    return orig_start, orig_end


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    unique = f".{os.getpid()}.{datetime.now(UTC).strftime('%H%M%S%f')}.tmp"
    tmp = path.with_suffix(path.suffix + unique)
    try:
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, path)
    except Exception:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise


def apply_review_edits(content: str, edits: list) -> tuple[str, list, list]:
    if not isinstance(edits, list) or not edits:
        return content, [], []

    resolved: list[tuple[dict, int, int]] = []
    failed: list[dict[str, Any]] = []

    for edit in edits:
        if not isinstance(edit, dict):
            failed.append({"edit": edit, "reason": "edit is not a JSON object"})
            continue
        etype = edit.get("type")
        if etype not in ("replace", "insert_after", "insert_before", "delete"):
            failed.append({"edit": edit, "reason": f"unknown edit type: {etype!r}"})
            continue
        find = edit.get("find", "")
        if not isinstance(find, str) or not find:
            failed.append({"edit": edit, "reason": "missing or empty 'find' field"})
            continue
        loc = _find_anchor(content, find)
        if loc is None:
            count = content.count(find)
            reason = f"anchor appears {count} times (ambiguous)" if count > 1 else "anchor not found in module"
            failed.append({"edit": edit, "reason": f"{reason}: {find[:100]!r}"})
            continue
        resolved.append((edit, loc[0], loc[1]))

    resolved.sort(key=lambda item: item[1])
    non_conflicting: list[tuple[dict, int, int]] = []
    prev_end = -1
    for edit, start, end in resolved:
        if start < prev_end:
            failed.append(
                {
                    "edit": edit,
                    "reason": (
                        f"overlaps a previous edit ending at position {prev_end} "
                        f"(this edit starts at {start})"
                    ),
                }
            )
            continue
        non_conflicting.append((edit, start, end))
        prev_end = end

    patched = content
    applied: list[dict[str, Any]] = []
    for edit, start, end in reversed(non_conflicting):
        etype = edit["type"]
        new = edit.get("new", "")
        if not isinstance(new, str):
            failed.append({"edit": edit, "reason": "'new' field is not a string"})
            continue
        if etype == "replace":
            patched = patched[:start] + new + patched[end:]
        elif etype == "insert_after":
            patched = patched[:end] + new + patched[end:]
        elif etype == "insert_before":
            patched = patched[:start] + new + patched[start:]
        elif etype == "delete":
            patched = patched[:start] + patched[end:]
        applied.append(edit)

    return patched, applied, failed


def _validate_patch_payload(raw: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MalformedPatchResponse(f"invalid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise MalformedPatchResponse("patch payload must be a JSON object")

    feedback = payload.get("feedback", "")
    if not isinstance(feedback, str):
        raise MalformedPatchResponse("patch feedback must be a string")

    edits = payload.get("edits")
    if not isinstance(edits, list) or not edits:
        raise MalformedPatchResponse("patch payload edits must be a non-empty list")

    normalized_edits: list[dict[str, Any]] = []
    for edit in edits:
        if not isinstance(edit, dict):
            raise MalformedPatchResponse("each patch edit must be an object")
        if edit.get("type") not in {"replace", "insert_after", "insert_before", "delete"}:
            raise MalformedPatchResponse(f"unexpected patch edit type: {edit.get('type')}")
        if not isinstance(edit.get("find"), str) or not edit.get("find"):
            raise MalformedPatchResponse("patch edit find must be a non-empty string")
        reason = edit.get("reason", "")
        if not isinstance(reason, str):
            raise MalformedPatchResponse("patch edit reason must be a string")
        if edit["type"] != "delete" and not isinstance(edit.get("new"), str):
            raise MalformedPatchResponse("patch edit new must be a string")
        normalized_edits.append(edit)

    return {"edits": normalized_edits, "feedback": feedback}
