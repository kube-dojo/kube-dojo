from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from dispatch import dispatch_gemini

from .control_plane import ControlPlane, Lease
from .preflight import PreflightFinding, run_preflight


FLASH_MODEL = "gemini-3-flash-preview"
PRO_MODEL = "gemini-3.1-pro-preview"
PATCH_MODEL = "codex"
CHECK_PRE_MODEL = "deterministic"
SIMPLE_CHECK_IDS = ("PRES", "NO_EMOJI", "K8S_API")
DEEP_CHECK_IDS = ("COV", "DEPTH", "WHY")
MODEL_ESTIMATED_USD = {
    FLASH_MODEL: 0.0025,
    PRO_MODEL: 0.0350,
}


@dataclass(frozen=True)
class ReviewRunOutcome:
    status: str
    module_key: str | None = None
    lease_id: str | None = None
    details: dict[str, Any] | None = None


class MalformedReviewerResponse(ValueError):
    pass


class ReviewWorker:
    def __init__(
        self,
        control_plane: ControlPlane,
        *,
        worker_id: str = "review-worker",
        dispatch_fn: Callable[..., tuple[bool, str]] = dispatch_gemini,
    ):
        self.control_plane = control_plane
        self.worker_id = worker_id
        self.dispatch_fn = dispatch_fn

    def run_once(self) -> ReviewRunOutcome:
        lease = self.control_plane.lease_next_job(
            self.worker_id,
            phase="review",
            requested_calls=1,
            estimated_usd=self._estimated_review_cost(),
        )
        if lease is None:
            return ReviewRunOutcome(status="idle")

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
            preflight = run_preflight(module_path, repo_root=self.control_plane.repo_root)
            if not preflight.passed:
                payload = {
                    "job_id": lease.job_id,
                    "source": "preflight",
                    "verdict": "REJECT",
                    "checks": [finding.to_dict() for finding in preflight.failed_findings()],
                    "feedback": "Deterministic pre-flight checks failed; skipping LLM review.",
                }
                self.control_plane.emit_event(
                    "check_failed",
                    module_key=lease.module_key,
                    lease_id=lease.lease_id,
                    payload=payload,
                )
                self.control_plane.enqueue(
                    lease.module_key,
                    phase="patch",
                    model=PATCH_MODEL,
                    priority=lease.job_id,
                )
                self.control_plane.complete_lease(
                    lease.lease_id,
                    actual_calls=0,
                    actual_usd=0.0,
                    outcome="attempt_succeeded",
                    event_payload={"phase": "review", "reason": "preflight_failed"},
                )
                return ReviewRunOutcome(
                    status="preflight_failed",
                    module_key=lease.module_key,
                    lease_id=lease.lease_id,
                    details=payload,
                )

            review_result, actual_calls, actual_usd = self._run_llm_review(
                module_path,
                lease=lease,
            )
            failed_checks = [check for check in review_result["checks"] if not check["passed"]]
            event_payload = {
                "job_id": lease.job_id,
                "verdict": review_result["verdict"],
                "checks": review_result["checks"],
                "feedback": review_result["feedback"],
            }
            if failed_checks:
                self.control_plane.emit_event(
                    "check_failed",
                    module_key=lease.module_key,
                    lease_id=lease.lease_id,
                    payload={**event_payload, "failed_checks": failed_checks},
                )
                self.control_plane.enqueue(
                    lease.module_key,
                    phase="patch",
                    model=PATCH_MODEL,
                    priority=lease.job_id,
                )
                status = "rejected"
            else:
                self.control_plane.emit_event(
                    "check_passed",
                    module_key=lease.module_key,
                    lease_id=lease.lease_id,
                    payload=event_payload,
                )
                self.control_plane.enqueue(
                    lease.module_key,
                    phase="check_pre",
                    model=CHECK_PRE_MODEL,
                    priority=lease.job_id,
                )
                status = "approved"

            self.control_plane.complete_lease(
                lease.lease_id,
                actual_calls=actual_calls,
                actual_usd=actual_usd,
                outcome="attempt_succeeded",
                event_payload={"phase": "review", "verdict": review_result["verdict"]},
            )
            return ReviewRunOutcome(
                status=status,
                module_key=lease.module_key,
                lease_id=lease.lease_id,
                details=event_payload,
            )
        except MalformedReviewerResponse as exc:
            self.control_plane.complete_lease(
                lease.lease_id,
                actual_calls=0,
                actual_usd=0.0,
                outcome="attempt_failed",
                event_payload={"phase": "review", "reason": "malformed_json", "error": str(exc)},
            )
            return ReviewRunOutcome(
                status="attempt_failed",
                module_key=lease.module_key,
                lease_id=lease.lease_id,
                details={"reason": "malformed_json", "error": str(exc)},
            )
        except Exception as exc:
            self.control_plane.complete_lease(
                lease.lease_id,
                actual_calls=0,
                actual_usd=0.0,
                outcome="attempt_failed",
                event_payload={"phase": "review", "reason": "worker_error", "error": str(exc)},
            )
            raise

    def loop_forever(self, *, sleep_seconds: float = 5.0) -> None:
        while True:
            outcome = self.run_once()
            if outcome.status == "idle":
                time.sleep(sleep_seconds)

    def _run_llm_review(
        self,
        module_path: Path,
        *,
        lease: Lease,
    ) -> tuple[dict[str, Any], int, float]:
        module_text = module_path.read_text(encoding="utf-8")
        aggregated_checks: list[dict[str, Any]] = []
        feedback_parts: list[str] = []
        actual_calls = 0
        actual_usd = 0.0

        for check_id in SIMPLE_CHECK_IDS:
            result, calls_used = self._dispatch_with_retry(
                self._simple_prompt(module_text, module_path, check_id),
                expected_checks={check_id},
                model=FLASH_MODEL,
            )
            aggregated_checks.extend(result["checks"])
            if result["feedback"]:
                feedback_parts.append(result["feedback"])
            actual_calls += calls_used
            actual_usd += MODEL_ESTIMATED_USD[FLASH_MODEL] * calls_used

        deep_result, deep_calls_used = self._dispatch_with_retry(
            self._deep_prompt(module_text, module_path),
            expected_checks=set(DEEP_CHECK_IDS),
            model=PRO_MODEL,
        )
        aggregated_checks.extend(deep_result["checks"])
        if deep_result["feedback"]:
            feedback_parts.append(deep_result["feedback"])
        actual_calls += deep_calls_used
        actual_usd += MODEL_ESTIMATED_USD[PRO_MODEL] * deep_calls_used

        checks_by_id = {check["id"]: check for check in aggregated_checks}
        ordered_checks = [
            checks_by_id[check_id]
            for check_id in (*SIMPLE_CHECK_IDS, *DEEP_CHECK_IDS)
            if check_id in checks_by_id
        ]
        verdict = "APPROVE" if all(check["passed"] for check in ordered_checks) else "REJECT"
        feedback = "\n\n".join(part for part in feedback_parts if part).strip()
        if not feedback:
            feedback = "All requested review checks passed." if verdict == "APPROVE" else "Review checks failed."
        return {
            "verdict": verdict,
            "checks": ordered_checks,
            "feedback": feedback,
        }, actual_calls, round(actual_usd, 4)

    def _dispatch_with_retry(
        self,
        prompt: str,
        *,
        expected_checks: set[str],
        model: str,
    ) -> tuple[dict[str, Any], int]:
        last_error: Exception | None = None
        calls_used = 0
        for attempt in range(2):
            ok, output = self.dispatch_fn(prompt, model=model, review=False, timeout=900)
            calls_used += 1
            if not ok:
                raise MalformedReviewerResponse(output.strip() or f"{model} dispatch failed")
            try:
                return _validate_review_payload(output, expected_checks=expected_checks), calls_used
            except MalformedReviewerResponse as exc:
                last_error = exc
                if attempt == 1:
                    break
        assert last_error is not None
        raise last_error

    def _module_path_for_lease(self, lease: Lease) -> Path:
        module_path = Path(lease.module_key)
        if not module_path.is_absolute():
            module_path = self.control_plane.repo_root / module_path
        return module_path

    def _estimated_review_cost(self) -> float:
        return round((3 * MODEL_ESTIMATED_USD[FLASH_MODEL]) + MODEL_ESTIMATED_USD[PRO_MODEL], 4)

    def _simple_prompt(self, module_text: str, module_path: Path, check_id: str) -> str:
        return f"""You are a strict KubeDojo review worker.

Return JSON only with this exact schema:
{{
  "verdict": "APPROVE" | "REJECT",
  "checks": [
    {{"id": "{check_id}", "passed": true, "evidence": "...", "fix_hint": "...", "line_range": [1, 1]}}
  ],
  "feedback": "..."
}}

Review ONLY the {check_id} check for this module. Do not add any other checks.
- PRES: unique concepts and exercises are preserved; report missing unique value.
- NO_EMOJI: emoji characters are not allowed in prose.
- K8S_API: deprecated Kubernetes APIs outside acceptable teaching context should fail.

Module path: {module_path}

Module content:
{module_text}
"""

    def _deep_prompt(self, module_text: str, module_path: Path) -> str:
        return f"""You are a strict KubeDojo review worker.

Return JSON only with this exact schema:
{{
  "verdict": "APPROVE" | "REJECT",
  "checks": [
    {{"id": "COV", "passed": true, "evidence": "...", "fix_hint": "...", "line_range": [1, 1]}},
    {{"id": "DEPTH", "passed": true, "evidence": "...", "fix_hint": "...", "line_range": [1, 1]}},
    {{"id": "WHY", "passed": true, "evidence": "...", "fix_hint": "...", "line_range": [1, 1]}}
  ],
  "feedback": "..."
}}

Review ONLY these checks:
- COV: every learning outcome is covered with concrete teaching content.
- DEPTH: include practitioner-grade nuance such as tradeoffs, failure modes, or gotchas.
- WHY: major design choices explain rationale, not just procedure.

Module path: {module_path}

Module content:
{module_text}
"""


def _validate_review_payload(raw: str, *, expected_checks: set[str]) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MalformedReviewerResponse(f"invalid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise MalformedReviewerResponse("review payload must be a JSON object")
    verdict = payload.get("verdict")
    if verdict not in {"APPROVE", "REJECT"}:
        raise MalformedReviewerResponse("review payload verdict must be APPROVE or REJECT")
    feedback = payload.get("feedback")
    if not isinstance(feedback, str):
        raise MalformedReviewerResponse("review payload feedback must be a string")
    checks = payload.get("checks")
    if not isinstance(checks, list):
        raise MalformedReviewerResponse("review payload checks must be a list")

    normalized_checks: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for item in checks:
        if not isinstance(item, dict):
            raise MalformedReviewerResponse("each review check must be an object")
        check_id = item.get("id")
        if check_id not in expected_checks:
            raise MalformedReviewerResponse(f"unexpected review check id: {check_id}")
        if check_id in seen_ids:
            raise MalformedReviewerResponse(f"duplicate review check id: {check_id}")
        passed = item.get("passed")
        evidence = item.get("evidence")
        fix_hint = item.get("fix_hint")
        line_range = item.get("line_range")
        if not isinstance(passed, bool):
            raise MalformedReviewerResponse(f"{check_id} passed must be boolean")
        if not isinstance(evidence, str):
            raise MalformedReviewerResponse(f"{check_id} evidence must be string")
        if not isinstance(fix_hint, str):
            raise MalformedReviewerResponse(f"{check_id} fix_hint must be string")
        if (
            not isinstance(line_range, list)
            or len(line_range) != 2
            or not all(isinstance(value, int) for value in line_range)
        ):
            raise MalformedReviewerResponse(f"{check_id} line_range must be [start, end]")
        normalized_checks.append(
            {
                "id": check_id,
                "passed": passed,
                "evidence": evidence,
                "fix_hint": fix_hint,
                "line_range": line_range,
            }
        )
        seen_ids.add(check_id)

    if seen_ids != expected_checks:
        missing = sorted(expected_checks - seen_ids)
        raise MalformedReviewerResponse(f"missing review checks: {', '.join(missing)}")

    return {
        "verdict": verdict,
        "checks": normalized_checks,
        "feedback": feedback,
    }


def findings_to_review_checks(findings: list[PreflightFinding]) -> list[dict[str, Any]]:
    return [finding.to_dict() for finding in findings]
