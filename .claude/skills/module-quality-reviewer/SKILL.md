---
name: module-quality-reviewer
description: Review KubeDojo modules against the 7-dim pedagogical rubric. For ANY agent acting as reviewer (codex, composer-2.5, gemini, agy, claude). Use when reviewing, scoring, or checking modules. Triggers on "review module", "check quality", "score module".
last_calibrated: 2026-05-24
---

# Module Quality Reviewer Skill

Review KubeDojo modules against the quality rubric at `docs/quality-rubric.md`. **Agent-agnostic** — applies whether you are codex gpt-5.5, composer-2.5, gemini-3.1-pro-preview, agy on Claude tier, or claude headless.

## Who reviews what (cross-family routing, Decision Card C, 2026-05-24)

```
Author                                  →  Cross-family reviewer
codex / deepseek / gemini / claude /
agy / anyone else                       →  composer-2.5 (cursor IDE)
composer-2.5                            →  codex (gpt-5.5, danger mode, worktree)
orchestrator inline edits               →  composer-2.5
```

Every PR must be reviewed by a different model family than the author per [`docs/review-protocol.md`](../../../docs/review-protocol.md). "Tests passing" is not a substitute ([[feedback_review_policy]]).

## How to Review

1. **Read the module fully** — line-by-line, not skim ([[code-editing-safety §3]]).
2. **Run the verifier first**: `python scripts/quality/verify_module.py <path>`. Density gates failing (median_wpp < 28, mean_wpp < 30, short-para > 20%) = immediate NEEDS_CHANGES, no rubric needed yet.
3. **Score against ALL 7 rubric dimensions** (1-5 each).
4. **Be STRICT** — a 4 means genuinely good, a 5 is exceptional.
5. **Flag specific issues with line numbers** — vague critique is reviewer-malpractice.
6. **Verify all external facts**. Burden of proof on keeping: if a citation `supports` the claim → keep; partial/no/fetch-fail/ambiguous → flag for removal ([[feedback_citation_verify_or_remove]]).
7. **Test runnability** — actually run `bash`/`kubectl`/`yaml` snippets in a sandbox. Composer-2.5 verifier-pass ≠ runnability ([[feedback_composer_2_5_viable_for_t0_content]]).

## Rubric Dimensions (1-5 each)

| Dimension | What to Check |
|-----------|--------------|
| **Learning Outcomes** | Are they stated? Measurable? Bloom's L3+? |
| **Scaffolding** | Does content build simple→complex? Narrative bridges between sections? |
| **Active Learning** | Are there inline prompts? Or is all practice back-loaded to the end? |
| **Real-World Connection** | War stories with specific details? Or generic "in production" handwaving? |
| **Assessment Alignment** | Do quiz questions test understanding (scenarios) or recall (what is X?)? |
| **Cognitive Load** | Well-chunked? Diagrams integrated? Or information dump? |
| **Engagement** | Memorable tone? Would you recommend this to a colleague? Or dry/robotic? |

## Structure Checklist

- [ ] Learning Outcomes (Bloom's L3+ verbs: debug, design, evaluate)
- [ ] Why This Module Matters (war story with real impact)
- [ ] Core content (3-6 sections with code, diagrams, tables)
- [ ] Inline active learning (at least 2 prediction/try-it prompts in the body)
- [ ] Did You Know? (4 facts with real numbers)
- [ ] Common Mistakes table (6-8 rows: Mistake | Why | Fix)
- [ ] Quiz (6-8 scenario-based questions with `<details>` answers)
- [ ] Hands-On Exercise (multi-step with success criteria)
- [ ] Next Module link

## Passing Criteria

- Average score >= 3.5/5
- No single dimension scores 1
- Active Learning >= 3
- Assessment Alignment >= 3

## Output Format

```markdown
## Module Review: [Name]
**File**: [path]
**Lines**: [count]

### Scores

| Dimension | Score | Notes |
|-----------|-------|-------|
| Learning Outcomes | /5 | |
| Scaffolding | /5 | |
| Active Learning | /5 | |
| Real-World Connection | /5 | |
| Assessment Alignment | /5 | |
| Cognitive Load | /5 | |
| Engagement | /5 | |
| **Average** | **/5** | |

### Structure Checklist
- [x] or [ ] for each required element

### Key Strengths
1. ...

### Must Fix
1. ...

### Verdict: PASS / NEEDS WORK / FAIL
```

## Reference Modules (Gold Standard)

- **Platform: What is Systems Thinking?** (4.6/5) — narrative voice, inline exercises, scenario-based assessment
- **On-Prem: The Case for On-Prem** (4.4/5) — balanced perspective, deliberate quiz traps, TCO exercise
- **Cloud: AWS Secrets Management** (4.0/5) — envelope encryption diagram, debugging quiz scenarios

## Anti-Patterns to Flag

- "List of facts" style (bullet points without connecting narrative)
- Quiz questions that test recall ("What is the command for X?")
- All active learning back-loaded to the end
- Diagrams with separate legends instead of inline labels
- "Refer to official documentation for details"
- Sections that could be rearranged in any order without losing coherence
- Unverified external citations (a hard-flag, not a soft-flag — see [[feedback_citation_verify_or_remove]])
- Personal-life framing (interview/job/role narrative — [[feedback_no_personal_framing]])
- Listicle dumps without teaching arc ([[feedback_teaching_not_listicles]])

## Common reviewer hallucinations to watch for in YOURSELF

| You are | Watch out for |
|---|---|
| codex (gpt-5.5) | Fabricating GitHub Actions / Dependabot schema claims ([[feedback_deepseek_hallucinates_on_gh_schemas]] applies here too). Verify CLI/YAML schema before flagging. |
| composer-2.5 | Hallucinated file paths in findings (e.g. claimed PR #1487 path that did not exist). Always quote the exact line from the diff. Verifier-pass ≠ runnability — run the bash. |
| deepseek-v4-pro | Same as codex on schema facts; also rule attribution slippage (SC2236 vs SC2230, semver exact, expansion order). |
| gemini-3-flash-preview | DO NOT use as a code/lab reviewer ([[feedback_never_flash_for_code_review]]). Calibrated 0/2 bugs caught on PR #1229. Use gemini-3.1-pro-preview instead. |
| agy (Claude tier) | 0 hallucinations on code review historically — strong default. Surfaces 100% Claude quota independently of Anthropic chat cap ([[feedback_agy_claude_route_during_throttle]]). |
| claude headless | Yes-man drift on close reads ([[feedback_no_yes_man]]); be deliberate about flagging weaknesses, not just strengths. |

## Reviewer dispatch protocol (orchestrator perspective)

| Pair | Dispatch |
|---|---|
| Review claude-authored | Open PR; comment `cursor please review`; cursor picks up via IDE with composer-2.5 model selected. |
| Review composer-2.5-authored | `python scripts/dispatch_smart.py review --agent codex --mode danger --worktree <pr-slug>` ([[feedback_codex_review_danger_mode]]) |
| Review codex-authored | Same as claude-authored (composer-2.5 cross-family) OR `dispatch_smart review --agent gemini --model gemini-3.1-pro-preview` if cursor unavailable. Fall back to `--agent claude` on Gemini 503 ([[feedback_headless_claude_gemini_fallback]]). |
| Review agy-authored | `dispatch_smart review --agent codex` (different family). |

After R1, if NEEDS_CHANGES, dispatch the original author for a fix-pass, then re-run review (R2). On APPROVE/APPROVE_WITH_NITS, merge (orchestrator-driven; cursor does NOT self-merge per session-51 directive).

## References

- [[curriculum-writer]] — what the author was contracted to deliver.
- [[cross-family-reviewer]] — sibling skill for the cross-family routing protocol.
- [[dispatch-router]] — agent picking decisions.
- [`docs/quality-rubric.md`](../../../docs/quality-rubric.md) — full rubric definition.
- [`docs/pedagogical-framework.md`](../../../docs/pedagogical-framework.md) — research backing the rubric.
- [`docs/review-protocol.md`](../../../docs/review-protocol.md) — cross-family review contract.
