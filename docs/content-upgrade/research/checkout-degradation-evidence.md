# Checkout dependency trade-offs — #2403

Scope: complexity module Q5 at `c8de21c0537e041af6245e9afa64c93c1b6bf22c`. Research only; no lab execution or acceptance of other questions.

## Inspected primary operator accounts

1. Alejandro Forero Cuervo, [Handling Overload](https://sre.google/sre-book/handling-overload/), Google SRE book chapter21. HTML49,202bytes, SHA256 `8ca912a82390e7f61e8bbae7baab3a74489f5068d71dee1ff24aed99375e0373`. The opening describes cheaper degraded responses, including a local result copy that may be out of date, and notes that extreme overload can defeat that option. This supports a possible mitigation, not permission to return stale checkout prices.
2. Mike Ulrich, [Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/), chapter22. HTML82,467bytes, SHA256 `f16f9a582bab016af83c9393e56d7571ba91b49e371bd6b55e7a482c041dddb3`. Inspected: resource-exhaustion discussion, CPU subsection's missed-deadline entry; degradation section's opening and cautions; retry section's example and subsequent recommendations; testing section's stateful/cache correctness paragraph; final degraded-mode response section.

Root retrieved and read these body passages on2026-09-05, then retained HTML copies. Kimi's earlier fetch was rejected by its automatic approval review; its report supplied no verified source evidence. These are practitioner accounts, not controlled comparisons of the question's two architectures. The chapter's Shakespeare examples must not become claimed real checkout incidents. Figures and sample retry code were not executed or visually validated; no reproduction of Google-scale results is claimed.

## Claim dispositions

| Q5 claim | Evidence and boundary | Disposition |
|---|---|---|
| Dependency delay and retries can increase load. | Chapter22 CPU/deadline entry and retry example describe this feedback; later guidance addresses retry limits, budgets and retries at multiple layers. | Retain conditionally. Synchronous invocation alone does not establish retry amplification. |
| Cached responses preserve useful service. | Chapter21 opening offers degradation as an option with limits. Chapter22's final degraded-mode section requires knowing which traffic can be degraded. | Ask which operation and correctness requirements the fallback preserves. |
| Async boundaries and bulkheads make Design B superior. | Inspected passages do not compare these two designs or establish this ranking. | Remove automatic ranking; treat isolation as a proposal requiring its own mechanism and evidence. |
| Checkout can safely use stale prices. | No inspected passage establishes that business requirement. Chapter22's testing guidance explicitly includes correctness under load for stateful/cached services. | Do not infer safety from continued responses. Specify requirements before choosing behavior. |
| Degradation is an uncomplicated improvement. | Chapter22 cautions that complex fallback behavior can itself introduce problems. | Include validation of the fallback and its failure conditions. |

## Acceptance boundary

The replacement learning objective should ask learners to compare designs using requirements, actual retry behavior, dependency criticality and observed outcomes. Examples remain hypothetical. Independent SOURCE acceptance precedes prose; separate PROSE review, build, CI and live checks follow. This does not authorize load testing, accept the whole module, or establish Ukrainian parity.
