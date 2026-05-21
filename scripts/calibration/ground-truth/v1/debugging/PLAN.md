# Debugging — fixture expansion plan

## Current state

- `pod-pending-topology-mismatch.yaml` — EKS multi-AZ debugging scenario where a PV is bound to `us-east-1a` but available nodes are in `us-east-1b`, requiring PV nodeAffinity analysis and a scoped remediation.
- `resourcequota-pvc-mismatch.yaml` — PVC quota mismatch scenario from PR #1353 where PVC requests sum to `320Gi` but the `ResourceQuota` allows only `300Gi`.

## Target

- Target count: 5 fixtures.
- Current count: 2 fixtures.
- Add 3 fixtures so the lane covers common Kubernetes and systems failure classes beyond storage/quota diagnosis.
- The brief listed 4 failure classes, but quota/config mismatch stays as a distinct fifth case because exact arithmetic and scoped remediation catch a different failure mode from topology, CrashLoop, OOM, and deadlock diagnosis.
- Keep each fixture anchored in logs, manifests, events, traces, or code snippets that make the root cause discoverable.

## Variety dimensions

- Pod-pending: keep `pod-pending-topology-mismatch.yaml` as the topology and scheduling fixture.
- CrashLoop: add a fixture where logs and probes point to a startup/configuration failure, not a generic restart answer.
- OOM: add a fixture where memory limits, process behavior, and evidence distinguish OOMKilled from CPU or liveness failures.
- Deadlock: add a code or distributed-systems fixture where stack traces or goroutine dumps identify a real deadlock.
- Quota/config mismatch: keep the ResourceQuota PVC fixture as an additional calibration case for exact arithmetic and scoped remediation.

## Acceptance criteria per fixture

- Passing answers identify the configured root-cause terms and propose a fix that matches the fixture's allowed fix terms.
- Strong answers cite the specific evidence path, avoid broad rewrites, and reach `judge_score>=7` or the fixture-specific root-cause threshold.
- If a fixture has a deterministic reproduction or test command, `pytest_exit=1` may be the expected failing reproduction and the fix must then make the targeted test pass.

## Open questions

- Should debugging fixtures score root-cause identification and remediation separately?
- How should expected failing states be represented when `pytest_exit=1` is correct before the fix but incorrect after the fix?
- Who verifies that each new failure class has enough evidence to be solvable without hidden assumptions?

## Refs

- #1413
- Memory: `feedback_single_fixture_v1_calibration.md`
