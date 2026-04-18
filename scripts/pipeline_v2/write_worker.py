from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from dispatch import GEMINI_WRITER_MODEL
from v1_pipeline import _extract_frontmatter_data, find_module_path, step_write

from .control_plane import ControlPlane, Lease
from .review_worker import REVIEW_MODEL


WRITE_MODEL = GEMINI_WRITER_MODEL
WRITE_ESTIMATED_USD = 0.0350
STUB_BODY_CHAR_THRESHOLD = 400
STUB_MARKERS = ("todo", "tbd", "stub", "placeholder", "coming soon")


@dataclass(frozen=True)
class WriteRunOutcome:
    status: str
    module_key: str | None = None
    lease_id: str | None = None
    details: dict[str, Any] | None = None


class WriteWorker:
    def __init__(
        self,
        control_plane: ControlPlane,
        *,
        worker_id: str = "write-worker",
        write_fn: Callable[..., str | None] = step_write,
    ):
        self.control_plane = control_plane
        self.worker_id = worker_id
        self.write_fn = write_fn

    def run_once(self) -> WriteRunOutcome:
        lease = self.control_plane.lease_next_job(
            self.worker_id,
            phase="write",
            requested_calls=1,
            estimated_usd=WRITE_ESTIMATED_USD,
        )
        if lease is None:
            return WriteRunOutcome(status="idle")

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
            module_path = self._module_path_for_lease(lease)
            current_content = module_path.read_text(encoding="utf-8")
            mode, plan = self._build_write_plan(
                lease.module_key,
                module_path=module_path,
                current_content=current_content,
            )
            rewritten = self.write_fn(
                module_path,
                plan,
                model=WRITE_MODEL,
                rewrite=mode == "rewrite",
                previous_output=current_content,
            )
            if rewritten is None:
                self.control_plane.release_lease(lease.lease_id, reason="write_failed")
                return WriteRunOutcome(
                    status="retry_scheduled",
                    module_key=lease.module_key,
                    lease_id=lease.lease_id,
                    details={"reason": "write_failed", "mode": mode},
                )

            _atomic_write_text(module_path, rewritten)
            self.control_plane.enqueue(
                lease.module_key,
                phase="review",
                model=REVIEW_MODEL,
                priority=lease.job_id,
            )
            details = {
                "mode": mode,
                "module_path": str(module_path),
                "output_chars": len(rewritten),
                "review_reenqueued": True,
            }
            self.control_plane.complete_lease(
                lease.lease_id,
                actual_calls=1,
                actual_usd=WRITE_ESTIMATED_USD,
                outcome="attempt_succeeded",
                event_payload={"phase": "write", **details},
            )
            return WriteRunOutcome(
                status="written",
                module_key=lease.module_key,
                lease_id=lease.lease_id,
                details=details,
            )
        except Exception as exc:
            self.control_plane.release_lease(lease.lease_id, reason="write_worker_error")
            return WriteRunOutcome(
                status="retry_scheduled",
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
        module_key = lease.module_key
        candidate = Path(module_key)
        if candidate.is_absolute() and candidate.exists():
            return candidate

        repo_candidate = self.control_plane.repo_root / module_key
        if repo_candidate.exists():
            return repo_candidate

        key_without_suffix = module_key[:-3] if module_key.endswith(".md") else module_key
        resolved = find_module_path(key_without_suffix)
        if resolved is not None and resolved.exists():
            return resolved

        raise FileNotFoundError(f"Unable to resolve module path for {module_key}")

    def _build_write_plan(
        self,
        module_key: str,
        *,
        module_path: Path,
        current_content: str,
    ) -> tuple[str, str]:
        escalation = self._latest_event_payload(module_key, "rewrite_escalated")
        if escalation:
            return "rewrite", _rewrite_plan(
                module_key,
                module_path=module_path,
                current_content=current_content,
                escalation=escalation,
                failure_history=self._failure_history(module_key),
            )

        if _is_stub_or_empty(current_content):
            return "initial", _initial_write_plan(module_key, module_path, current_content)

        return "initial", _initial_write_plan(module_key, module_path, current_content)

    def _latest_event_payload(self, module_key: str, event_type: str) -> dict[str, Any] | None:
        for event in reversed(self.control_plane.iter_events(event_type)):
            if str(event["module_key"]) != module_key:
                continue
            payload = json.loads(event["payload_json"])
            if isinstance(payload, dict):
                return payload
        return None

    def _failure_history(self, module_key: str) -> list[dict[str, Any]]:
        relevant = {
            "check_failed",
            "attempt_failed",
            "rewrite_escalated",
            "patch_apply_failed",
            "patch_degraded",
            "needs_human_intervention",
        }
        history: list[dict[str, Any]] = []
        for event in self.control_plane.iter_events():
            if str(event["module_key"]) != module_key or str(event["type"]) not in relevant:
                continue
            payload = json.loads(event["payload_json"])
            history.append(
                {
                    "type": str(event["type"]),
                    "payload": payload if isinstance(payload, dict) else {"raw": payload},
                }
            )
        return history


def _initial_write_plan(module_key: str, module_path: Path, current_content: str) -> str:
    frontmatter = _extract_frontmatter_data(current_content)
    title = str(frontmatter.get("title", module_path.stem)).strip()
    learning_outcomes = frontmatter.get("learning_outcomes") or frontmatter.get("learningOutcomes") or []
    if isinstance(learning_outcomes, list):
        outcomes_text = "\n".join(f"- {item}" for item in learning_outcomes if isinstance(item, str))
    else:
        outcomes_text = ""
    body = _body_without_frontmatter(current_content).strip()
    return (
        f"Initial module write for {module_key}.\n"
        f"Draft the full markdown module from the frontmatter spec for '{title}'.\n"
        "Preserve the existing YAML frontmatter and satisfy every stated learning outcome.\n"
        "Use any existing TODO notes only as hints; replace stub text with final teaching content.\n\n"
        f"Learning outcomes:\n{outcomes_text or '- Infer from the frontmatter and filename if omitted.'}\n\n"
        f"Existing stub/body:\n{body or '(empty module body)'}"
    )


def _rewrite_plan(
    module_key: str,
    *,
    module_path: Path,
    current_content: str,
    escalation: dict[str, Any],
    failure_history: list[dict[str, Any]],
) -> str:
    reasons = escalation.get("reasons") or []
    failed_checks = escalation.get("failed_checks") or []
    feedback = str(escalation.get("feedback", "")).strip()
    history_lines: list[str] = []
    for item in failure_history:
        payload = item["payload"]
        history_lines.append(
            f"- {item['type']}: {json.dumps(payload, sort_keys=True)}"
        )
    checks_text = json.dumps(failed_checks, indent=2, sort_keys=True) if failed_checks else "[]"
    return (
        f"Severe rewrite for {module_key}.\n"
        "Preserve valid material from the current module where possible, but fully rewrite sections that caused the failures.\n"
        "Do not discard accurate frontmatter or useful explanations unless you replace them with better content.\n\n"
        f"Module path: {module_path}\n"
        f"Escalation reasons: {', '.join(str(reason) for reason in reasons) or 'rewrite_escalated'}\n"
        f"Reviewer feedback: {feedback or '(none provided)'}\n"
        f"Failed checks:\n{checks_text}\n\n"
        "Failure history:\n"
        f"{chr(10).join(history_lines) if history_lines else '- rewrite_escalated'}\n\n"
        "Current content to preserve and improve is attached as the rewrite source."
    )


def _body_without_frontmatter(content: str) -> str:
    if not content.startswith("---\n"):
        return content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return content
    return parts[2]


def _is_stub_or_empty(content: str) -> bool:
    body = _body_without_frontmatter(content).strip()
    if not body:
        return True
    lowered = body.lower()
    if any(marker in lowered for marker in STUB_MARKERS):
        return True
    stripped_lines = [line.strip() for line in body.splitlines() if line.strip()]
    prose_lines = [line for line in stripped_lines if not line.startswith("#")]
    meaningful_chars = sum(len(line) for line in prose_lines)
    return meaningful_chars < STUB_BODY_CHAR_THRESHOLD


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    tmp_path.write_text(content, encoding="utf-8")
    tmp_path.replace(path)
