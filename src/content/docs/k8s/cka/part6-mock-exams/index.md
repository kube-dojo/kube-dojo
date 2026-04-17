---
title: "Mock Exams"
sidebar:
  order: 1
  label: "Mock Exams"
---
**Deferred for now, but planned explicitly.**

This section is intentionally not on the active execution path yet. The goal is to avoid turning CKA prep into a giant mock-exam factory before the rest of the curriculum and route system are stable.

If you are preparing right now, do not wait on this section. Use:
- [CKA Part 5](../part5-troubleshooting/) for timed troubleshooting pressure
- your weakest earlier domains for targeted drills
- the `killer.sh` environment included with the real exam purchase for realistic timing and interface pressure

## Why This Section Exists

Mock exams are high-value only when the learner already has:
- solid `kubectl` speed
- YAML editing fluency
- a real troubleshooting method
- enough breadth across cluster architecture, workloads, networking, storage, and day-2 operations

Without that base, mock exams mostly measure panic and typing speed.

## Deferred Planned Modules

These are the current planned slots for this section:

| # | Planned Module | Focus |
|---|---|---|
| 6.1 | Cluster Architecture, Security Controls, and Troubleshooting Mock Exam | control plane, kubeadm, RBAC, admission, audit, node recovery, admin workflow |
| 6.2 | Workloads, Networking, and Storage Mock Exam | workloads, services, policies, storage, debugging under time pressure |
| 6.3 | Full Mixed-Domain CKA Mock Exam | realistic end-to-end timed exam covering the major domains |

## When To Use These

These should come after most of the main CKA path, not near the beginning.

Safest order:

```text
CKA Part 0-5
   |
Timed drills on weak areas
   |
Mock Exams
```

## Why It Is Deferred

This backlog is explicit, not forgotten.

It is deferred because the higher-value work right now is:
- keeping the core routes coherent
- hardening the status and pipeline surfaces
- improving learner guidance across the main tracks

The activation condition is concrete: this section should move into active build only after the core CKA path and adjacent prerequisite routes are production-cleared under the current review pipeline. At that point, a small `3`-exam set is enough; this does not need to grow into a large exam bank.

When this section is activated, it should be built as a small, high-quality exam set rather than a large pile of repetitive mocks.
