Design a rollout plan for KubeDojo’s rewrite lane to target **100 modules/week** safely.

Current constraints:

- `dispatch_smart.py` currently runs one codex/sonnet dispatch at a time per task class.
- Codex weekly subscription cost cap is roughly **$200/week effective** across pooled ChatGPT Plus + Pro.
- Expected cost is about **$0.10–$0.30 per dispatch** and **~$0.05 per review**, or about **$0.20/module** total.
- Wall-clock per module is **30–45 minutes** when running sequentially.

Task:

Create a concrete 500–1000 word capacity plan that answers:

1. Whether spinning up five workers immediately is correct or dangerous in this system.
2. Which system bottleneck is binding first at these constraints (include both writer and reviewer lanes).
3. A scoped rollout plan for concurrency increase that protects reliability and quality while aiming toward the 100 modules/week target.
4. Concrete gates and a kill-switch policy for stopping expansion if the rollout degrades.
5. A failure budget and rollback trigger if review quality starts regressing.

Required constraints:

- This is a weekly-cap planning problem, not a raw RPS/per-minute tuning problem.
- Include at least one **pilot with 2–3 concurrent workers** only.
- Include a **named scale-up gate** (e.g., “clean merge ratio ≥ 0.8 over 5 rolling days”) and explicit thresholds.
- Include a rollback action and an explicit kill-switch for concurrency changes.
- Address **review-stage queueing** if writers outrun reviewers.

Output a prioritized implementation plan, sequencing, and metrics stack (what to instrument, what to graph, and what fails the gate). End with a clear decision: why not full 5x rollout initially.

