---
name: cross-family-reviewer
description: Cross-family PR review protocol for KubeDojo. Different model family than the author per docs/review-protocol.md. For ANY agent acting as reviewer (codex, composer-2.5, gemini, agy, claude). Triggers on "review PR", "R1 review", "R2 review", "cross-family review".
last_calibrated: 2026-05-24
---

# Cross-family Reviewer Skill

Run a rigorous PR review on KubeDojo code or content. **Different model family than the author** ([`docs/review-protocol.md`](../../../docs/review-protocol.md)) — that's the load-bearing property. Author-family review is allowed for style/lint but never substitutes for cross-family.

> **Routing source-of-truth precedence**: `docs/review-protocol.md` defines the cross-family *principle* but its concrete pairings (Claude → Codex etc.) predate Decision Card C (2026-05-24). The active routing table below + [`STATUS.md`](../../../STATUS.md) "Active policies" supersede the stale defaults in `review-protocol.md` until that doc is refreshed.

This skill describes the **review contract**. For pedagogical content scoring against the 7-dim rubric, layer in [[module-quality-reviewer]].

## Routing table (Decision Card C, 2026-05-24)

| Author family | Cross-family reviewer (primary) | Fallback |
|---|---|---|
| claude (orchestrator inline OR headless) | composer-2.5 (cursor-agent CLI OR cursor IDE) | codex gpt-5.5 |
| composer-2.5 (cursor-agent CLI OR cursor IDE) | codex gpt-5.5 (danger mode, worktree) | gemini-3.1-pro-preview |
| codex (gpt-5.5 / spark / mini) | composer-2.5 | gemini-3.1-pro-preview, agy (Claude tier) |
| deepseek-v4-pro | composer-2.5 OR codex | gemini-3.1-pro-preview |
| gemini-3.1-pro-preview | composer-2.5 OR codex | agy |
| agy (Claude tier) | codex OR composer-2.5 | — |

**Do NOT use `gemini-3-flash-preview` as a code/lab reviewer** — calibrated 0/2 bugs caught on PR #1229 ([[feedback_never_flash_for_code_review]]).

## How to run a review (R1)

1. **Pull the PR locally** (or read the diff via `gh pr diff <N>`).
2. **Read changed files in full**, not just the hunk. A diff hides surrounding-context bugs.
3. **For curriculum content**: also run [[module-quality-reviewer]] (7-dim rubric).
4. **For code**: run the relevant linter + tests (`.venv/bin/ruff check`, `npx tsc --noEmit`, `npx eslint`, `.venv/bin/pytest`, `npm test`).
5. **For workflows** (`.github/workflows/**`): `uvx zizmor --offline --strict-collection .github/` ([[.claude/rules/github-actions-security]]).
6. **For modules**: `.venv/bin/python scripts/quality/verify_module.py <path>` for density gates.
7. **For lab content**: actually run the `bash`/`kubectl`/`yaml` snippets in a sandbox.
8. **Verify all external citations** ([[feedback_citation_verify_or_remove]]) — burden of proof is on KEEPING. If not `supports`, flag for removal.
9. **Grep for sibling failures** — same anti-pattern likely elsewhere.
10. **Output the verdict** in the format below.

> **Coverage over filtering — report everything.** Report every issue you find, including ones you are uncertain about or consider low-severity. Do NOT filter for importance or confidence at this stage — the P1/P2/Nits ranking below plus the R2 verification cycle handle that. For each finding, state your confidence and estimated severity. (Opus-4.8-class reviewers follow "only report high-severity" / "don't nitpick" / "be conservative" instructions *literally* and silently drop lower-severity findings — a measured recall regression, not a capability one. This skill therefore instructs the opposite: surface, then rank.)

## Output format

```markdown
## Review: PR #<N> — <title>
**Reviewer**: <agent + model>
**Round**: R1 / R2
**Verdict**: APPROVE / APPROVE_WITH_NITS / NEEDS_CHANGES

### Findings (priority-ranked)

#### P1 (blocker — must fix before merge)
1. `file:line` — <finding>. Quote the exact line. Suggest a fix.

#### P2 (should fix)
1. `file:line` — <finding>.

#### Nits (optional)
1. `file:line` — <finding>.

### Verified
- [x] Linter (`<command>` output)
- [x] Tests (`<command>` output)
- [x] Density gates (for modules)
- [x] Citations (X claims verified, Y flagged)
- [x] Lab snippets executed

### Out of scope
- <things the PR did not touch and you did not review>
```

**Quote evidence inline** — pasted command output, exact file:line, exact diff hunk. Do not summarize "tests pass" without the run output.

## Common reviewer hallucinations (watch yourself)

| You are | Watch out for | Mitigation |
|---|---|---|
| codex gpt-5.5 | Fabricating GitHub Actions / Dependabot schema claims, fabricating commands ([[feedback_deepseek_hallucinates_on_gh_schemas]]) | Verify CLI schema via `--help` before flagging |
| composer-2.5 | Verifier-pass ≠ runnability gap; hallucinated paths in findings | Quote exact lines from diff; run the bash |
| gemini-3.1-pro-preview | Mixing legit findings with cosmetic over-corrections ([[feedback_gemini_review_partial_apply]]); calling a REAL recent feature "fabricated" because it postdates your cutoff (e.g. Dependabot `cooldown` — it is real; PR #1825, 2026-06-07) | Only flag findings you'd defend in a re-review; never assert a recent schema/feature is fake — mark it unverifiable |
| deepseek-v4-pro | Rule attribution slippage (shellcheck rule numbers, semver exact, version-specific behavior) | Verify version-specific claims against current docs |
| agy (Claude tier) | Historically 0 hallucinations on code review — strong default | — |
| claude headless | Yes-man drift; favoring author's framing | Frame your read independent of the PR description |

**You are sandboxed from fact-check tools.** A review runs with NO web, NO `gh api`, NO MCP (writes are blocked by design). So you CANNOT verify a live commit SHA, a post-cutoff incident/date/CVE, a CNCF maturity level, or a current package/tool version. Do NOT assert such a claim is real OR fabricated from memory — label it `UNVERIFIABLE — orchestrator must check (gh api / web)` and move on. Guessing real/fake is how confident false positives reach the verdict: on PR #1825 (2026-06-07) deepseek called a *real* `actions/checkout` commit "not found" while correctly catching a different *fabricated* SHA, and gemini called the *real* Dependabot `cooldown` schema "hallucinated." For **Ukrainian-translation** reviews you ARE given the RAG MCP (`dispatch.py --mcp` / `dispatch_smart --mcp rag`) — use it to verify lemmas/quotes/Russicisms instead of guessing ([[feedback_reviewers_sandboxed_from_factcheck_tools]]).

## Anti-patterns to flag (codebase-wide)

- Tests that mock the database when an integration target exists — favor a real DB / fixtures over mocks for boundary tests.
- Hard-coded SHAs as version pins without comment (must be `# vX.Y.Z` for Dependabot) ([[.claude/rules/github-actions-security §1]]).
- `persist-credentials: true` (default) on `actions/checkout` without a push need ([[.claude/rules/github-actions-security §3]]).
- Workflow-level `permissions:` with privileged scopes ([[.claude/rules/github-actions-security §4]]).
- Comments explaining WHAT instead of WHY.
- Dead code (unused imports, orphaned functions) — flag for cleanup before structural refactor.
- Backwards-compat shims for code you're certain is unused — delete instead.

## R2 cycle (after fix-pass)

1. Re-read the changed lines + sibling files (cleanup may have introduced new issues).
2. Re-run the same gates (linter, tests, density, citations).
3. **Verify each R1 finding was addressed** — explicitly check off the list, don't just say "looks good".
4. Output a second verdict block. If still NEEDS_CHANGES on the same finding, raise the priority (P2 → P1) and explain why.

## When to escalate to a Decision Card

For contested NEEDS_CHANGES (author defends, reviewer blocks, repeat), trigger `scripts/ab discuss --with claude,codex,gemini` per [[.claude/rules/decision-card]]. Do NOT just hold the PR hostage — escalate cleanly.

## References

- [[module-quality-reviewer]] — pedagogical 7-dim rubric for content reviews.
- [[curriculum-writer]] — what the author was contracted to deliver.
- [[dispatch-router]] — picking the right reviewer agent.
- [`docs/review-protocol.md`](../../../docs/review-protocol.md) — cross-family review contract.
- [`.claude/rules/decision-card.md`](../../rules/decision-card.md) — escalation pattern for contested reviews.
- [`.claude/rules/github-actions-security.md`](../../rules/github-actions-security.md) — workflow review rules.
