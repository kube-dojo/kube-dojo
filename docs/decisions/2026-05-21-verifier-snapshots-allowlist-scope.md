# ADR: Verifier Snapshots — Allowlist Scope and Phase Boundary

**Date:** 2026-05-21
**Issue:** [#1382](https://github.com/kube-dojo/kube-dojo.github.io/issues/1382)
**Status:** Accepted (Phase 1 implemented)

---

## Context

Issue #1382 proposes capturing stdout from commands in module bash code blocks so that future runs
can detect silent output drift (e.g., `kubectl explain pod` output changing between k8s 1.34 and
1.35). The issue notes the approach is "risk-bounded" and explicitly calls out Phase 2 (diff
alerting) as a follow-up.

The design question was: which commands should the snapshot capture actually execute?

---

## Decision

**Phase 1 implements an opt-in allowlist-driven approach (`--snapshot` flag on `verify_module.py`)
that executes only commands that are safe to run without a live cluster or at worst produce
well-defined error output when a cluster is absent.**

### Allowlist (what runs)

| Command | Subcommand / condition | Rationale |
|---------|----------------------|-----------|
| `kubectl` | `version`, `explain`, `help`, `api-resources`, `api-versions` | Client-side; no cluster needed |
| `kubectl` | `get`, `describe` | Informational; produces "connection refused" when offline, which is itself capturable |
| `kubectl` | `apply`, `create`, `patch`, `run` + `--dry-run=client` | Validates YAML syntax client-side |
| `kubectl` | `delete` + `--dry-run=client` | Dry-run only; write path blocked otherwise |
| `helm` | `template`, `version`, `help` | Template rendering is cluster-free |
| `kind` | `get`, `version`, `help` | Cluster lifecycle info only |
| `k3d` | `version`, `help`, or `--help` flag | Version/help info only |

### Denylist (always blocked, regardless of allowlist match)

- **Shell metacharacters** — any line containing `|`, `;`, `&&`, `||`, `&`,
  `>`, `>>`, `<`, `` ` ``, or `$(` is rejected before the allowlist is
  consulted.  This closes the pipe-bypass class: `kubectl get pods | xargs
  kubectl delete pod` would otherwise pass the allowlist check because
  `shlex.split` presents `cmd='kubectl'`, `sub='get'` to `is_allowed`, hiding
  the destructive second command entirely.  Redirection (`> file`) and command
  substitution (`` `...` `` / `$(...)`) are denied for the same reason.
- Any token that is `--force`
- Bare commands `rm`, `kill`, `drop`, `truncate`
- `kubectl delete` without `--dry-run=client` (handled in allowlist logic;
  `kubectl delete` *with* `--dry-run=client` and no metacharacters is allowed)
- Any command not in {kubectl, helm, kind, k3d} is implicitly denied

### Snapshot format

```
calibration/v1/verifier-snapshots/<module-key>/<YYYY-MM-DD>.txt
```

Each file contains per-block, per-command: the command string, exit code, combined stdout+stderr,
and a SHA256 hash of all outputs for quick change detection.

---

## Alternatives considered

### A. Run ALL commands in the code block

**Rejected.** Modules contain `kubectl apply -f https://raw.githubusercontent.com/...` and
similar live-cluster bootstrap commands. Running those without gating causes:
- Network calls from CI
- Real Kubernetes resource creation/deletion if a kubeconfig is present
- Non-deterministic output dependent on cluster state

### B. Run only `kubectl version --client` and `kubectl explain`

**Rejected as too narrow.** The value of snapshots is capturing the full range of commands
learners see — including `kubectl get`, `kubectl describe`, and `helm template` — so that changes
in output format (column names, field ordering, deprecation warnings) are surfaced. Pure-client
commands are a subset of what matters.

### C. Shell-parse + rewrite every command with `--dry-run=client` appended

**Rejected.** Rewriting shell commands is fragile: pipes, variable substitution, here-docs,
and multi-command chains all break naively. The allowlist pattern is simpler and safer.

### D. Store expected output and fail on mismatch (Phase 2 in Phase 1)

**Rejected for this phase.** Diffing and alerting require baseline management, version tagging,
and a decision about what constitutes "acceptable drift" — all out of scope for #1382 Phase 1.
Phase 1's job is to build the snapshot corpus; Phase 2 reads it.

---

## Consequences

**Positive:**
- `--snapshot` is opt-in; default `verify_module.py` behavior is unchanged — existing CI unaffected.
- The snapshot corpus grows organically as engineers run `--snapshot` on modules.
- SHA256 hashes enable Phase 2 to detect drift cheaply (compare hash files before loading content).
- Offline environments produce useful snapshots too (connection-refused output is versioned output).

**Negative / accepted risk:**
- `kubectl get` and `kubectl describe` without `--dry-run=client` execute against whatever
  cluster the current kubeconfig points to. Engineers must be aware when running `--snapshot`
  on a production kubeconfig. (Mitigation: these commands are read-only.)
- Commands that need files (e.g., `kubectl apply --dry-run=client -f pod.yaml`) fail with "no
  such file" in isolation; the snapshot captures the error, which is still useful for tracking
  whether the error message format changes.

---

## Phase 2 (out of scope, tracked as follow-up)

- Diff-aware alerting: compare `<YYYY-MM-DD>.txt` SHA256 against a previous date's file.
- Schema-change detection: structured diff of `kubectl explain` JSON fields.
- CI integration: run `--snapshot` in the verify job and fail if SHA256 changes unexpectedly.
- Version tagging: record the k8s client version in the snapshot header.
