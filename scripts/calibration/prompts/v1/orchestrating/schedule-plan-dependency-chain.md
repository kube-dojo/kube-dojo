You are scheduling the next KubeDojo calibration prep block. Produce a plan; do not dispatch a calibration wave yet.

Work items waiting:
- PR-A: author orchestrating fixture #2 and register it in `run_wave.py`.
- PR-B: author orchestrating fixture #3; it should not reuse PR-A's exact rubric pattern.
- PR-C: update the calibration README/index after PR-A and PR-B both merge.
- PR-D: run schema/ruff smoke checks on the combined registry after PR-C.
- PR-E: open the one-fixture-per-model wave issue only after PR-D is green.

Binding constraints:
- Only one Gemini reviewer is available; reviewer SLA is 30 minutes per PR, and no more than two PRs may sit in review at once.
- The CI pool has 2 runners. Each PR gate takes 18 minutes; the combined registry
  smoke takes 25 minutes and must have a free runner.
- Codex has 6 high-tier runs left this weekly cap, and OpenAI-family agent work must be serialized: max 1 codex/sonnet task inflight.
- Cross-family review is mandatory: a Codex-authored PR needs Gemini review before
  merge. Claude is throttled today, so do not count on Claude review capacity.

Deliver:
1. An ordered timeline with dependencies for all five work items.
2. Which steps are serialized vs parallel and why, naming the binding constraint.
3. A kill-switch or fallback if review, CI, or the codex weekly cap blocks progress.
4. A rough cost/time budget. If there is a real tradeoff, use the KubeDojo Decision Card vocabulary: Option A, Option B, disagreement, awaiting.
