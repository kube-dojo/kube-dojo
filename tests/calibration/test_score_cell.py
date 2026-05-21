from __future__ import annotations

import json
import subprocess

from scripts.calibration import schema, score_cell
from scripts.calibration.models import model_by_canonical


def _completed(returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout="", stderr="")


def test_code_writing_scorer_happy_path(monkeypatch):
    monkeypatch.setattr(score_cell, "run_command", lambda *args, **kwargs: _completed())
    response = """
```python
import yaml

def parse_dependabot_cooldown(yaml_text: str) -> int | None:
    data = yaml.safe_load(yaml_text) if yaml_text else None
    if data is None:
        return None
    if not isinstance(data, dict):
        raise ValueError("top-level YAML must be a mapping")
    cooldown = data.get("cooldown")
    if cooldown is None:
        return None
    if not isinstance(cooldown, dict):
        raise ValueError("cooldown must be a mapping")
    days = cooldown.get("default-days")
    if isinstance(days, bool) or not isinstance(days, int) or days < 0:
        raise ValueError("default-days must be a non-negative integer")
    return days
```
"""
    ground_truth = score_cell.load_ground_truth("code-writing", "parse-dependabot-cooldown")
    assert score_cell.SCORERS["code-writing"].deterministic_gates(response, ground_truth) == {
        "pytest_exit": True,
        "ruff_exit": True,
    }


def test_code_review_scorer_happy_path():
    response = (
        ".github/workflows/security.yml:10 security -- zizmor lacks "
        "--strict-collection. .github/workflows/security.yml:11 correctness -- "
        "scan scope misses .github/actions reusable actions. "
        ".github/dependabot.yml:6 correctness -- missing cooldown default-days. "
        ".github/workflows/security.yml:8 security -- pip install zizmor is unpinned."
    )
    ground_truth = score_cell.load_ground_truth("code-review", "pr-1333-security-yaml")
    gates = score_cell.SCORERS["code-review"].deterministic_gates(response, ground_truth)
    assert gates == {"finding_recall": True, "hallucination_rate": True}


def test_content_writing_long_scorer_happy_path():
    response = """
Verifier tier: T0
Learning outcomes: analyze RBAC bindings and diagnose namespace escalation.
```mermaid
graph TD
  User --> RoleBinding --> Role
```
"""
    ground_truth = score_cell.load_ground_truth(
        "content-writing-long",
        "kubedojo-rbac-module",
    )
    gates = score_cell.SCORERS["content-writing-long"].deterministic_gates(
        response,
        ground_truth,
    )
    assert all(gates.values())


def test_content_review_scorer_happy_path():
    response = (
        "hallucinated flag --remove-extra-permission; missing IPA; duplicate H1; "
        "broken citation missing-page 404; Bloom outcomes only understand/know; "
        "missing Mermaid diagram; source has # Kubernetes RBAC duplicate H1; "
        "uses banned word simply."
    )
    ground_truth = score_cell.load_ground_truth(
        "content-review",
        "flawed-module-rubric-review",
    )
    gates = score_cell.SCORERS["content-review"].deterministic_gates(
        response,
        ground_truth,
    )
    assert gates == {"planted_flaw_recall": True, "review_precision": True}


def test_fact_check_scorer_happy_path():
    response = json.dumps(
        [
            {"claim_id": "C1", "verdict": "VERIFIED", "rationale": "https://kubernetes.io/docs/"},
            {"claim_id": "C2", "verdict": "VERIFIED", "rationale": "https://kubernetes.io/docs/"},
            {"claim_id": "C3", "verdict": "VERIFIED", "rationale": "https://kubernetes.io/docs/"},
            {"claim_id": "C4", "verdict": "FALSE", "rationale": "NetworkPolicy remains."},
            {"claim_id": "C5", "verdict": "FALSE", "rationale": "replicas is integer."},
        ]
    )
    ground_truth = score_cell.load_ground_truth("fact-check", "k8s-1-35-claims")
    gates = score_cell.SCORERS["fact-check"].deterministic_gates(response, ground_truth)
    assert gates == {"verdict_class_match": True, "citation_grounding": True}


def test_architecting_scorer_happy_path():
    response = (
        "env-var format, validation, hermes invocation, failure modes, telemetry, "
        "flow integration, rollback, rate-limit behavior, prompt-model mismatch, "
        "worktree safety, cost cap, audit trail."
    )
    ground_truth = score_cell.load_ground_truth(
        "architecting",
        "kubedojo-review-override-rfc",
    )
    gates = score_cell.SCORERS["architecting"].deterministic_gates(
        response,
        ground_truth,
    )
    assert gates == {"required_category_ratio": True, "novel_risk_bonus": True}


def test_orchestrating_scorer_happy_path():
    response = (
        "Python bug -> codex -> debugging. security regressions -> claude -> "
        "code-review. module handoff -> cheap -> summarization. fact-check -> "
        "google -> fact-check. Serialize same-family Codex work, include a "
        "cost estimate, and draft a decision card for the override disagreement."
    )
    ground_truth = score_cell.load_ground_truth(
        "orchestrating",
        "multi-task-routing-brief",
    )
    gates = score_cell.SCORERS["orchestrating"].deterministic_gates(
        response,
        ground_truth,
    )
    assert all(gates.values())


def test_orchestrating_scorer_alias_match():
    response = (
        "Bug fix in scripts/check_links.py (fix the bug) assigned to codex and routed "
        "to debugging; security review by claude in code-review; module handoff to "
        "cheap in summarization; fact-check by google using verify claims."
    )
    ground_truth = score_cell.load_ground_truth(
        "orchestrating",
        "multi-task-routing-brief",
    )
    gates = score_cell.SCORERS["orchestrating"].deterministic_gates(
        response,
        ground_truth,
    )
    assert gates["routing_accuracy"] is True


def test_orchestrating_scorer_synonym_serialization():
    response = (
        "Python bug route with codex and debugging, security review with claude, "
        "module handoff with cheap, fact-check with google. Queue OpenAI work "
        "sequentially in one at a time with no overlap."
    )
    ground_truth = score_cell.load_ground_truth(
        "orchestrating",
        "multi-task-routing-brief",
    )
    gates = score_cell.SCORERS["orchestrating"].deterministic_gates(
        response,
        ground_truth,
    )
    assert gates["same_family_serialized"] is True


def test_orchestrating_scorer_ratio_threshold():
    """Regression for #1369: routing gate is ratio-based, not strict AND."""
    response_3_of_4 = (
        "Python bug -> codex -> debugging. security regressions -> claude -> "
        "code-review. module handoff -> cheap -> summarization. "
        "Serialize same-family Codex work and include cost estimate."
    )
    response_2_of_4 = (
        "Python bug -> codex -> debugging. security regressions -> claude -> "
        "code-review. Include cost estimate and serialize same-family."
    )
    ground_truth = score_cell.load_ground_truth(
        "orchestrating",
        "multi-task-routing-brief",
    )
    pass_gates = score_cell.SCORERS["orchestrating"].deterministic_gates(
        response_3_of_4,
        ground_truth,
    )
    fail_gates = score_cell.SCORERS["orchestrating"].deterministic_gates(
        response_2_of_4,
        ground_truth,
    )
    assert pass_gates["routing_accuracy"] is True
    assert fail_gates["routing_accuracy"] is False


def test_orchestrating_scorer_empty_routes_is_vacuous_pass():
    """Regression from PR #1376 challenge-round: empty `expected_routes` used
    to set routing_ratio=0.0 (silent fail for every model). Other ratio
    scorers treat empty-set as vacuous pass; orchestrating now matches."""
    scorer = score_cell.SCORERS["orchestrating"]
    gates = scorer.deterministic_gates(
        "any response",
        {"expected_routes": []},
    )
    assert gates["routing_accuracy"] is True


def test_debugging_scorer_happy_path():
    response = (
        "Root cause: ResourceQuota requests.storage is 300Gi but PVCs sum to 320Gi.\n"
        "```diff\n-    requests.storage: 300Gi\n+    requests.storage: 320Gi\n```"
    )
    ground_truth = score_cell.load_ground_truth("debugging", "resourcequota-pvc-mismatch")
    gates = score_cell.SCORERS["debugging"].deterministic_gates(response, ground_truth)
    assert all(gates.values())


def test_refactoring_scorer_happy_path():
    response = """
```python
def record_frontmatter_result(rel, content, report):
    if not content.startswith("---"):
        report.error(f"Missing frontmatter: {rel}")
    if "title:" not in content:
        report.error(f"Missing title: {rel}")
    if "order:" not in content:
        report.warn(f"Missing sidebar.order: {rel}")
```
"""
    ground_truth = score_cell.load_ground_truth(
        "refactoring",
        "check-site-health-refactor",
    )
    gates = score_cell.SCORERS["refactoring"].deterministic_gates(response, ground_truth)
    assert all(gates.values())


def test_summarization_scorer_happy_path():
    required = (
        "CKS 4.2 PSA rewrite shipped as PR #1362. "
        "CKS 4.3 Secrets Management shipped as PR #1363. "
        "T2-13 Ansible arc decision archived. "
        "Calibration framework v1 spec designed and shipped as PR #1364. "
        "Module 7.12 Ansible Operator SDK shipped as PR #1354. "
        "agy/Gemini 3.5 Flash High promoted to primary-tier reviewer. "
    )
    filler = (
        "Next work should keep the rewrite queue moving, preserve dual review, "
        "and treat the calibration build as the foundation for later model runs. "
    )
    response = required + " ".join([filler] * 7)
    ground_truth = score_cell.load_ground_truth("summarization", "session-34-handoff")
    gates = score_cell.SCORERS["summarization"].deterministic_gates(response, ground_truth)
    assert all(gates.values())


def test_score_cell_prose_lane_runs_judge_despite_gate_fail(tmp_path):
    db_path = tmp_path / "ledger.db"
    response_path = tmp_path / "response.md"
    response_path.write_text(
        "Bug fix in scripts/check_links.py mapped to codex debugging. "
        "security regressions via claude in code-review. module handoff by "
        "cheap summarization. Fact-check with google. Draft a decision card."
        " Include a cost estimate.",
        encoding="utf-8",
    )
    model = model_by_canonical("claude-opus-4-7")
    row = schema.build_cell_row(
        lane="orchestrating",
        fixture_id="multi-task-routing-brief",
        model=model,
        run_date="2026-05-21",
    )
    schema.init_db(db_path)
    with schema.connect(db_path) as conn:
        cell_id = schema.insert_cell(conn, row)
        schema.insert_dispatch(
            conn,
            cell_id=cell_id,
            task_id="task",
            response_path=str(response_path),
        )
    calls = []

    def fake_judge_fn(model_name: str, prompt: str) -> str:
        calls.append((model_name, prompt))
        return json.dumps({"score": 8.0, "rationale": "pass"})

    gates = score_cell.score_cell(
        cell_id=cell_id,
        db_path=db_path,
        judge_fn=fake_judge_fn,
        judge1="dummy-model-1",
        judge2="dummy-model-2",
    )
    assert gates["same_family_serialized"] is False
    assert len(calls) == 2


def test_score_cell_mechanical_lane_with_no_judge_returns_early(tmp_path):
    """Verify the `prompt is None` early-return path for mechanical lanes."""
    db_path = tmp_path / "ledger.db"
    response_path = tmp_path / "response.md"
    response_path.write_text(
        "No findings listed and no real observations.",
        encoding="utf-8",
    )
    model = model_by_canonical("claude-opus-4-7")
    row = schema.build_cell_row(
        lane="code-review",
        fixture_id="pr-1333-security-yaml",
        model=model,
        run_date="2026-05-21",
    )
    schema.init_db(db_path)
    with schema.connect(db_path) as conn:
        cell_id = schema.insert_cell(conn, row)
        schema.insert_dispatch(
            conn,
            cell_id=cell_id,
            task_id="task",
            response_path=str(response_path),
        )

    calls = []

    def fake_judge_fn(model_name: str, prompt: str) -> str:
        calls.append((model_name, prompt))
        return json.dumps({"score": 8.0, "rationale": "pass"})

    gates = score_cell.score_cell(
        cell_id=cell_id,
        db_path=db_path,
        judge_fn=fake_judge_fn,
    )
    assert not gates["finding_recall"]
    # PROSE_LANES guard at score_cell.py:607-609 would only fire for a
    # mechanical lane with a judge; no lane has one today, so future coverage
    # would need a mocked mechanical-lane judge.
    assert calls == []


def test_mcp_use_scorer_happy_path():
    response = (
        "1. mcp__rag__translate_en_uk('cloud') — surface-form lookup.\n"
        "2. mcp__rag__verify_word(result) — canonical orthography for cloud.\n"
        "3. mcp__rag__check_modern_form(result) — confirm not pre-1993.\n"
        "4. mcp__rag__check_russian_shadow(result) — confirm not a Russicism.\n"
        "5. mcp__rag__search_sources(query=result, sources=['SUM', 'Hrinchenko', 'ESUM']) "
        "   — fetch one citation.\nSTOP."
    )
    ground_truth = score_cell.load_ground_truth("mcp-use", "define-the-word-in-uk")
    gates = score_cell.SCORERS["mcp-use"].deterministic_gates(response, ground_truth)
    assert gates == {
        "tool_selection_recall": True,
        "parameter_grounding": True,
        "no_phantom_tools": True,
    }


def test_mcp_use_scorer_phantom_tool_penalty():
    response = (
        "1. mcp__rag__translate_en_uk('cloud').\n"
        "2. mcp__rag__dictionary_lookup('cloud') — fetch definition.\nSTOP."
    )
    ground_truth = score_cell.load_ground_truth("mcp-use", "define-the-word-in-uk")
    gates = score_cell.SCORERS["mcp-use"].deterministic_gates(response, ground_truth)
    assert gates["no_phantom_tools"] is False


def test_harness_following_scorer_happy_path():
    response = (
        "Decision: I refuse the inline-write per "
        "feedback_dispatch_codex_for_code_changes and "
        "feedback_no_direct_push_to_main. The verifier gate "
        "(feedback_388_verifier_first) and cross-family review_policy "
        "also apply.\n"
        "Plan: dispatch_smart.py edit --agent codex --worktree wt-cks-6.2 "
        "to draft Module 6.2 Runtime Security with Falco, then open a PR "
        "on a feature branch, run verify_module.py, then cross-family "
        "review.\n"
        "Risk: skipping these gates on a Falco module would ship low-"
        "quality content to main with no review and no verifier coverage."
    )
    ground_truth = score_cell.load_ground_truth(
        "harness-following",
        "inline-write-falco-module",
    )
    gates = score_cell.SCORERS["harness-following"].deterministic_gates(
        response,
        ground_truth,
    )
    assert gates == {
        "rule_recall": True,
        "redirect_action": True,
        "no_silent_compliance": True,
    }


def test_harness_following_scorer_compliance_penalty():
    response = (
        "Sure, here is the module:\n\n---\ntitle: CKS 6.2 Falco\n---\n\n"
        "Falco is a runtime security tool that..."
    )
    ground_truth = score_cell.load_ground_truth(
        "harness-following",
        "inline-write-falco-module",
    )
    gates = score_cell.SCORERS["harness-following"].deterministic_gates(
        response,
        ground_truth,
    )
    assert gates["no_silent_compliance"] is False
    assert gates["rule_recall"] is False


def test_code_review_k8s_controller_findings_recall():
    response = (
        "internal/controller/leasewatcher.go:36 correctness -- Get uses "
        "context.Background instead of the propagated ctx, drops cancellation. "
        "leasewatcher.go:31 concurrency -- the goroutine closes over loop "
        "variable name (range variable capture). "
        "leasewatcher.go:39 security -- slog logs apiSecret, leaks secret "
        "in logs. "
        "leasewatcher.go:78 correctness -- MustHolder will panic on nil "
        "deref because the map entry can be a nil Lease. "
        "leasewatcher.go:30 resource-leak -- for {} has no ctx.Done check, "
        "goroutine leak on ctx cancel. "
        "leasewatcher.go:55 concurrency -- Acquire writes without "
        "resourceVersion — lost update race, two leaders possible."
    )
    ground_truth = score_cell.load_ground_truth(
        "code-review",
        "k8s-controller-leader-election",
    )
    gates = score_cell.SCORERS["code-review"].deterministic_gates(
        response,
        ground_truth,
    )
    assert gates == {"finding_recall": True, "hallucination_rate": True}


def test_debugging_topology_mismatch_recall():
    response = (
        "Root cause: the PV's nodeAffinity pins the volume to us-east-1a, "
        "but every available node sits in us-east-1b, so the scheduler "
        "raises 'volume node affinity conflict'. The mismatch is between "
        "the PV's topology label and the current node group zones.\n"
        "Patch: take a VolumeSnapshot of the PV and restore it into a new "
        "PV in us-east-1b, or scale a node group / new ASG into us-east-1a "
        "so the existing PV can be consumed.\n"
        "Why minimal: only one of {snapshot+restore, new node in 1a} is "
        "needed; the StatefulSet itself does not change."
    )
    ground_truth = score_cell.load_ground_truth(
        "debugging",
        "pod-pending-topology-mismatch",
    )
    gates = score_cell.SCORERS["debugging"].deterministic_gates(
        response,
        ground_truth,
    )
    assert all(gates.values())


def test_summarization_must_mention_ratio():
    required = [
        "CKS 4.2 PSA rewrite shipped as PR #1362",
        "CKS 4.3 Secrets Management shipped as PR #1363",
        "T2-13 Ansible arc decision archived",
        "Calibration framework v1 spec designed and shipped as PR #1364",
        "Module 7.12 Ansible Operator SDK shipped as PR #1354",
        "agy/Gemini 3.5 Flash High promoted to primary-tier reviewer",
    ]
    filler = (
        "Next work should keep the rewrite queue moving, preserve dual review, "
        "and treat the calibration build as the foundation for later model runs."
    )
    pass_response = " ".join(required[:5] + [filler] * 8)
    fail_response = " ".join(required[:3] + [filler] * 10)
    ground_truth = score_cell.load_ground_truth("summarization", "session-34-handoff")
    pass_gates = score_cell.SCORERS["summarization"].deterministic_gates(
        pass_response,
        ground_truth,
    )
    fail_gates = score_cell.SCORERS["summarization"].deterministic_gates(
        fail_response,
        ground_truth,
    )
    assert pass_gates["must_mention_recall"] is True
    assert fail_gates["must_mention_recall"] is False

def test_score_cell_writes_deterministic_rows(tmp_path):
    db_path = tmp_path / "ledger.db"
    response_path = tmp_path / "response.md"
    response_path.write_text(
        ".github/workflows/security.yml:10 --strict-collection; "
        ".github/actions reusable actions; dependabot cooldown default-days; "
        "pip install zizmor unpinned.",
        encoding="utf-8",
    )
    model = model_by_canonical("claude-opus-4-7")
    row = schema.build_cell_row(
        lane="code-review",
        fixture_id="pr-1333-security-yaml",
        model=model,
        run_date="2026-05-21",
    )
    schema.init_db(db_path)
    with schema.connect(db_path) as conn:
        cell_id = schema.insert_cell(conn, row)
        schema.insert_dispatch(
            conn,
            cell_id=cell_id,
            task_id="task",
            response_path=str(response_path),
        )

    gates = score_cell.score_cell(cell_id=cell_id, db_path=db_path)

    assert all(gates.values())
    with schema.connect(db_path) as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS count FROM scores WHERE cell_id = ?",
            (cell_id,),
        ).fetchone()["count"]
    assert count == 2
