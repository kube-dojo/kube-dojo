Given this multi-task brief, output:

1. dispatch plan with model, effort, and lane per sub-task
2. parallelization decisions
3. decision-card draft if disagreement is plausible
4. cost estimate

Brief:

We need to fix a small Python bug in `scripts/check_links.py`, review the PR
for security regressions, write a concise module handoff for the CKS rewrite
queue, and fact-check two Kubernetes API-version claims. The code fix and
handoff can happen in parallel, but OpenAI/Codex tasks share one family queue.
If reviewers disagree on whether to add an OpenRouter override, capture a
decision card instead of forcing a merge.

