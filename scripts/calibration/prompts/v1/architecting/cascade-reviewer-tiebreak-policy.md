Create a decision-card / ADR for KubeDojo’s PR-review cascade when the primary review pair disagrees.

Scenario:

- Primary code reviewer (claude-sonnet-4-6) says APPROVE.
- Cross-family reviewer (codex gpt-5.5) says NEEDS_CHANGES.
- The current runtime tiebreak is informal and undocumented.

Task:

Choose one of the three designs and justify it:

Option A — Auto-route to a third reviewer (cheapest quality-tier model such as agy/gemini-flash), then merge by majority vote.

Option B — Block the PR automatically and require explicit human decision.

Option C — Trust codex over in-family (use codex verdict as final decision).

Write a crisp decision-card that names the selected option as the default policy and explains the tradeoffs in this specific workflow. Include a brief decision matrix, explicit failure modes, and the minimum viable implementation steps.

Acceptance points for this fixture:

1. Rollback path must be first-class: how do we disable or revert this policy if it causes incorrect approvals/blocks?
2. Observability first-class: define a concrete metric (or named event) for how often tiebreak policy is triggered, and how to alert on it.
3. Independence check: consider whether auto-tiebreakers share correlated priors with existing reviewers and what that implies for false-positive risk.
4. Decision authority boundaries: what is allowed to auto-decline, what requires human approval, and when.
5. Guardrails for "false-positive rate" and adverse behavior (e.g., repetitive auto-block loops).

Output a **600–1200 word** decision-card in ADR style, with explicit recommended default and a one-paragraph rollback playbook.

