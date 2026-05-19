# DECISION REQUIRED — T2-13 Ansible operator arc scope

**Date:** 2026-05-19
**Agent:** claude (solo, overnight autonomous)
**Issue:** [#1304](https://github.com/kube-dojo/kube-dojo.github.io/issues/1304) Wave 2 last item
**Trigger:** user went AFK ("i am off gn, drive the project"); Wave 2 cleanup left this item un-scoped per the session-27 handoff note ("multi-module — break down into a foundational module + file sub-issues first")

## Background

T2-13 from #1304 Wave 2:
> Ansible operator arc (4-7 modules) — `platform/toolkits/infrastructure-networking/iac-tools/`

The existing iac-tools toolkit already has `module-7.4-ansible.md` (Ansible CLI / playbooks / roles / inventory). T2-13 is about the **Ansible Operator** pattern — Ansible running as a Kubernetes controller via Operator SDK — which is a different skill: it's about extending Kubernetes with Ansible-as-controller, not configuring infrastructure with Ansible-as-client.

A natural arc might be 4-6 modules:

1. Ansible Operator SDK fundamentals (`operator-sdk init --plugins=ansible`)
2. Watches.yaml + role mapping + reconciliation semantics
3. Helm Operator vs Ansible Operator decision framework
4. AWX / Tower / EDA (Event-Driven Ansible) integration
5. Production Ansible Operator patterns (idempotency, status, finalizers)
6. Testing Ansible Operators with Molecule + Kuttl

Open questions about the arc itself: (a) does the Ansible Operator pattern still warrant 4-7 modules of curriculum given the operator-SDK ecosystem has shifted toward Go/Kubebuilder, and (b) does this belong in `iac-tools` or in `k8s/extending/` (Ansible Operators ARE a K8s extension mechanism, not really IaC).

## Options

| | Option | Scope | Risk | Budget impact |
|---|---|---|---|---|
| **A** | One foundational module tonight | "Module 7.12: Ansible Operator SDK Fundamentals" — covers SDK init + watches.yaml + reconciliation semantics + simple example. File 3-5 sub-issues for remaining arc items. | LOW — same pattern as prior Wave-2 modules; ~2000-2500 lines via codex. | ~1 codex draft + 1 deepseek review (~30 min total). |
| **B** | Full arc tonight | 4-6 sequential codex dispatches. Each ~25 min draft + 5-8 min review + merge. | HIGH — chains failure risk, may hit weekly limits, multi-merge index.md conflicts. | ~3-4 hours of codex; risks running out of budget. |
| **C** | Defer entirely | Surface in handoff with sub-issue proposal; do not dispatch anything tonight. | NONE — but Wave 2 stays at 7/9 even though we have time. | Zero. |
| **D** | Re-scope to k8s/extending | Move T2-13 out of iac-tools into `k8s/extending/` (where operators conceptually live), then one foundational module + sub-issues. | MED — territorial decision deserves user input; affects astro.config.mjs sidebar. | Same as A plus the re-scope. |

## Orchestrator recommendation

**Option A** — one foundational Ansible Operator SDK module (~2000-2500 lines) tonight + file 3-5 sub-issues for the remaining arc.

Reasoning:
- Closes Wave 2 to 8/9 in the same session as the rest (7/9 currently merged + T2-23 about to land).
- One module is the lowest-risk way to break ground on Ansible Operators; the writer brief can establish vocabulary that future arc modules build on.
- Sub-issues let the user re-prioritize the remaining 3-5 modules without committing tonight.
- Avoids Option B's multi-dispatch chain risk + budget burn.
- Does not commit to the territorial question (iac-tools vs k8s/extending) — module 7.12 can be renumbered/moved later cheaply since it's the first in the arc.

If you want **B**, set a goal text for the next overnight run; the brief template is ready.
If you want **D**, the move is 4 file paths + 1 astro.config.mjs edit + 1 sidebar entry.

## Awaiting

User decision: A / B / C / D / or override scope. Will sit in `pending/` until user returns.

---

## OUTCOME — chosen 2026-05-20 (session 34)

**Selected: Option A** (foundational module + sub-issues).

**User trigger**: "i am going to sleep , please go auto and rive the project" (session-34, 2026-05-20).

**Shipped**:

- PR [#1354](https://github.com/kube-dojo/kube-dojo.github.io/pull/1354) — Module 7.12: Ansible Operator SDK Fundamentals (1567 net new lines, T0 verifier, body_words=5041, mean_wpp=54.8, 13/13 sources reachable). Codex (gpt-5.5 architect, danger, --search) drafted; claude-sonnet + agy/Gemini 3.5 Flash (High) both APPROVE_WITH_NITS in parallel cross-family review (4 sonnet nits + 3 agy nits); codex fixup applied all 7 in commit `27b46bd5`. Squash-merged.
- Sub-issues filed for the rest of the arc:
  - [#1356](https://github.com/kube-dojo/kube-dojo.github.io/issues/1356) — Module 7.13: Advanced watches.yaml patterns
  - [#1357](https://github.com/kube-dojo/kube-dojo.github.io/issues/1357) — Module 7.14: AWX + EDA integration
  - [#1358](https://github.com/kube-dojo/kube-dojo.github.io/issues/1358) — Module 7.15: Helm vs Ansible vs Go decision framework
  - [#1359](https://github.com/kube-dojo/kube-dojo.github.io/issues/1359) — Module 7.16: Production patterns (status / finalizers / idempotency)
  - [#1360](https://github.com/kube-dojo/kube-dojo.github.io/issues/1360) — Module 7.17: Testing with Molecule + Kuttl

**Wave 2 status**: 8/9 complete (T2-13 foundational scope shipped; 5 follow-up sub-issues now in the arc backlog instead of the original "4-7 modules" line item).

**Territorial question (iac-tools vs k8s/extending)**: not committed. Module 7.12 lives in iac-tools as a first-in-arc placement; can be renumbered/moved cheaply when the rest of the arc materializes if the user wants to consolidate under k8s/extending.
