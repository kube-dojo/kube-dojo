---
name: curriculum-writer
description: Write KubeDojo curriculum modules. For ANY agent acting as the T0 author (cursor composer-2.5, codex, deepseek-v4-pro, claude headless). Use when creating modules, writing theory, exercises, quizzes. Triggers on "write module", "create module", "new module", "rewrite module".
last_calibrated: 2026-05-24
---

# Curriculum Writer Skill

Author skill for new KubeDojo curriculum modules. Ensures consistent structure, tone, and quality across all educational content. **Agent-agnostic** — applies whether you are cursor composer-2.5, codex, deepseek-v4-pro, claude headless, or agy.

## When to Use
- Creating new curriculum modules
- Expanding existing module content
- Writing theory sections, exercises, or quizzes
- Rewriting modules failing the verifier (`median_wpp < 28` etc.) or the 8-dimension rubric

## Author lanes (who writes what — 2026-05-24 snapshot)

> **T0 primary author is CODEX-OR-CURSOR depending on codex weekly-cap state.** Quality-best lane wins ([[feedback_quality_over_budget_in_role_allocation]]). When codex cap is healthy → codex gpt-5.5 is the primary writer; cursor composer-2.5 takes over during throttle / thin-cap windows. The reviewer side (Decision Card C symmetric routing) is unchanged regardless of who authored.

| Lane | Agent | When | Notes |
|---|---|---|---|
| T0 primary author (codex cap healthy) | codex (`.venv/bin/python scripts/dispatch_smart.py draft --agent codex --mode danger --worktree X`) | Default when codex weekly cap is not thin | Default model is `gpt-5.3-codex-spark` (per `TASK_CLASSES["draft"]`); override with `--model gpt-5.5` for top-tier first-pass quality at higher per-call cost. Codex `--search` auto-enables via task-class `codex_search=True` (env export `KUBEDOJO_CODEX_SEARCH=1` to the codex CLI); do NOT pass `--search` to `dispatch_smart.py`. Quality-best lane: stronger on factual / version / runnability accuracy than composer-2.5 (session 52 cursor-authored tooling/api/docs cohort measured 4/7 = 57% first-pass NEEDS_CHANGES — proxy signal, no curriculum-T0 cohort at scale yet). See [[feedback_codex_writer_needs_search]]. |
| T0 primary author (codex cap thin / throttle) | composer-2.5 (cursor-agent CLI OR cursor IDE) | Codex weekly cap throttled | Pair with codex R1 — composer-2.5 verifier passes ≠ runnability ([[feedback_composer_2_5_viable_for_t0_content]]). |
| Bug fixer (any cap state) | composer-2.5 (cursor-agent CLI OR cursor IDE) | Bug fix PRs — separate lane from T0 author | Proven 3/3 first-commit on session 51 bug PRs per [[feedback_cursor_is_strong_bug_fixer]]. Use regardless of codex cap state. |
| T0 off-load (spread author load) | deepseek-v4-pro | When 3+ codex authors already in-flight (parallel-cap discipline per [[feedback_parallel_rewrite_cap_three]]) | Pair with vigilant code-domain reviewer; hallucinates rule attribution ([[feedback_deepseek_v4_pro_viable_for_t0_content]]). |
| Drafter (needs Claude expansion) | agy (gemini-3.1-pro-high) | When deeper structure scoped but final-form latency cheap | Outputs 350-400 lines, expand to 700-900+ |
| Source-fidelity expansion | claude opus (post-2026-06-15 inline) OR codex (pre, danger mode) | Strict-source rewrites | [[feedback_codex_default_prose_expander]] |

**Important**: every author lane is bound by the same density gates and 8-dim rubric below. The agent identity changes the dispatch wrapper, not the content contract.

## Author contract (every lane)

Every authored/rewritten module MUST satisfy ALL of:

1. **Density gates** (deterministic, enforced by `scripts/quality/verify_module.py`):
   - `median_wpp ≥ 28` (median words per paragraph)
   - `mean_wpp ≥ 30` (mean words per paragraph)
   - `short-para-rate ≤ 20%` (paragraphs under 18 words — see `verify_module.py:799`)
2. **Frontmatter**: `title:` + `sidebar.order:` (mandatory per [[.claude/rules/new-content-checklist]]).
3. **Slug**: if filename has dots (e.g. `module-1.1-foo.md`), explicit `slug:` to preserve them.
4. **Parent index.md**: add module to section's index table.
5. **Internal links**: slug format (`module-foo/`), never `.md` extension.
6. **Build green**: `npm run build` with 0 warnings.
7. **Health check**: `.venv/bin/python scripts/check_site_health.py` returns 0 errors.
8. **Citation discipline**: every external fact verified, unverified removed ([[feedback_citation_verify_or_remove]]).
9. **No personal framing**: no interview/job/role narrative ([[feedback_no_personal_framing]]).
10. **Pedagogy over listicles**: modules must TEACH, not dump facts ([[feedback_teaching_not_listicles]]).

The 8-dimension rubric (Learning Outcomes, Scaffolding, Active Learning, Real-World Connection, Assessment Alignment, Cognitive Load, Engagement, Practitioner Depth — complexity-scaled) is the reviewer's contract — see [[module-quality-reviewer]] and `docs/quality-rubric.md`. Author for sum ≥ 33/40 with every dimension ≥ 4.

## Track-Specific Guidelines

These examples illustrate different track focuses:

### Kubernetes Certifications (src/content/docs/k8s/)
- Exam-focused content
- Aligned with official CNCF curriculum
- Time-boxed complexity (exam speed matters)
- kubectl commands emphasized

### Prerequisites (src/content/docs/prerequisites/)
- Beginner-friendly fundamentals
- No assumed knowledge
- Build foundation for certifications

### Platform Engineering (src/content/docs/platform/)
- Post-certification, practitioner content
- Theory-first approach (principles over tools)
- Three layers: Foundations → Disciplines → Toolkits

---

## Platform Track Structure

Platform modules have **three tiers**:

### Foundations (src/content/docs/platform/foundations/)
Timeless theory that doesn't change:
- Systems Thinking
- Reliability Engineering
- Observability Theory
- Security Principles
- Distributed Systems

### Disciplines (src/content/docs/platform/disciplines/)
Applied practices and mental models:
- SRE
- Platform Engineering
- GitOps
- DevSecOps
- MLOps

### Toolkits (src/content/docs/platform/toolkits/)
Current tools (will evolve over time):
- Observability (Prometheus, OTel, Grafana)
- GitOps Tools (ArgoCD, Flux)
- Security Tools (Vault, OPA, Falco)
- Platforms (Backstage, Crossplane)
- ML Platforms (Kubeflow, MLflow)

---

## Module Template (Certification Track)

```markdown
# Module X.Y: [Topic Name]

> **Complexity**: `[QUICK]` | `[MEDIUM]` | `[COMPLEX]`
>
> **Time to Complete**: X-Y minutes
>
> **Prerequisites**: [List required modules or knowledge]

---

## Why This Module Matters

[2-3 paragraphs explaining WHY this topic matters]

> **Optional analogy: [Topic]**
>
> [Use only when it clarifies the concept; state the mapping and its limits.]

---

## What You'll Learn

[Clear learning objectives]

---

## Part 1: [Theory/Concepts]

### 1.1 [Subsection]

[Content with diagrams/examples]

> **Did You Know?**
>
> [Interesting fact]

---

## Part 2: [Practical Application]

[Hands-on content]

> **Optional documented case or labeled scenario**
>
> [Use a cited real incident, or label `Hypothetical scenario:`/`Simulation:` and state what is simulated.]

---

## Did You Know?

- **[Fact 1]**: [Detail]
- **[Fact 2]**: [Detail]
- **[Fact 3]**: [Detail]

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| [Mistake 1] | [What goes wrong] | [How to fix] |
| [Mistake 2] | [What goes wrong] | [How to fix] |

---

## Quiz

1. **[Question]**
   <details>
   <summary>Answer</summary>
   [Detailed answer explaining why]
   </details>

[4 questions total]

---

## Hands-On Exercise

**Task**: [What to do]

**Steps**:
1. [Step 1]
2. [Step 2]

**Success Criteria**:
- [ ] [Verifiable outcome]

**Verification**:
```bash
[Commands to verify]
```

---

## Next Module

[Link to next module]
```

---

## Module Template (Platform Track)

Platform modules include additional sections:

```markdown
# Module X.Y: [Topic Name]

> **Complexity**: `[QUICK]` | `[MEDIUM]` | `[COMPLEX]`
>
> **Time to Complete**: X-Y minutes
>
> **Prerequisites**: [List required modules]
>
> **Track**: Foundations | Disciplines | Toolkits

---

## Why This Module Matters

[Real-world motivation - not exam-focused]

> **Optional analogy: [Topic]**
>
> [If useful, connect the concept to something familiar and state where the analogy stops matching.]

---

## What You'll Learn

[Learning objectives]

---

## Key Concepts

### [Concept 1]

[Theory explanation with diagrams]

### [Concept 2]

[More theory]

---

## Current Landscape

How this concept is implemented in practice:

| Tool/Approach | Description | When to Use |
|---------------|-------------|-------------|
| [Tool 1] | [What it does] | [Use case] |
| [Tool 2] | [What it does] | [Use case] |

---

## Best Practices

What good looks like:

1. **[Practice 1]** - [Explanation]
2. **[Practice 2]** - [Explanation]
3. **[Practice 3]** - [Explanation]

---

## Anti-Patterns

What to avoid:

| Anti-Pattern | Why It's Bad | Better Approach |
|--------------|--------------|-----------------|
| [Pattern 1] | [Problem] | [Solution] |
| [Pattern 2] | [Problem] | [Solution] |

---

## Did You Know?

- **[Fact 1]**: [Detail]
- **[Fact 2]**: [Detail]

---

## Common Mistakes

| Mistake | Problem | Solution |
|---------|---------|----------|
| [Mistake 1] | [Impact] | [Fix] |

---

## Quiz

[4 questions with hidden answers]

---

## Hands-On Exercise

[Practical exercise with verification]

---

## Further Reading

Books, talks, and papers for deeper understanding:

- **[Book/Resource]** - [Why it's valuable]
- **[Talk/Video]** - [Key takeaway]
- **[Paper/Article]** - [What you'll learn]

---

## Next Module

[Link to next module]
```

---

## Writing Guidelines

### Tone
- Conversational, not academic
- Empathetic to learner struggles
- Confident but not arrogant
- Use "you" and "we" freely

### Analogies
- Use an analogy only when it clarifies the concept; it is optional, not a quota.
- State the mapping and where it stops matching; an analogy is not evidence for a factual claim.
- Do not add mystery, clue hunts, or gamification just to satisfy an engagement expectation.

### War Stories and Scenarios
- Use a documented real incident only when its details have a citation or `Source:` line.
- Otherwise use an explicitly labeled `Hypothetical scenario:` or `Simulation:` and state what is simulated; omit it when evidence is insufficient.
- Never present invented incidents, dialogue, motives, timelines, metrics, consequences, or results as documented facts. An anonymous “authentic-feeling” story is not evidence.
- End with a lesson learned grounded in the cited or labeled scenario.

### Code Examples
- All code must be complete and runnable
- Use realistic names (not foo/bar)
- Label output as observed only after a recorded run. Otherwise label it expected, illustrative, or simulated; do not imply it was executed.
- Include verification steps

### Diagrams
- Use ASCII art for architecture diagrams
- Keep diagrams simple and focused
- Every complex concept should have a visual

### Technical Accuracy
- Use current versions of tools
- Note when something is deprecated
- Link to official docs for deep dives
- Check equations and state their assumptions and limits.
- For Platform track: cover principles before tools

### Quiz Questions
- Test understanding, not memorization
- Answers should explain "why"
- Mix of conceptual and practical
- 4 questions per module

### Complexity Tags
- `[QUICK]`: Simple concept, fast read
- `[MEDIUM]`: Moderate complexity
- `[COMPLEX]`: Deep topic, requires focus

---

## Quality Checklist

Before considering a module complete:

### All Tracks
- [ ] **Density gates pass** (`.venv/bin/python scripts/quality/verify_module.py <path>`): median_wpp ≥ 28, mean_wpp ≥ 30, short-para-rate ≤ 20%
- [ ] All structural elements present
- [ ] Any analogy materially clarifies the concept and states its limits
- [ ] Any case or scenario is cited or explicitly labeled `Hypothetical scenario:`/`Simulation:`; no invented details presented as fact
- [ ] No forced mystery, clue hunt, or gamification layer
- [ ] 2-3 "Did You Know?" facts
- [ ] Common mistakes table filled
- [ ] 4 quiz questions with detailed answers
- [ ] Hands-on exercise with verification
- [ ] All code tested and working (runnability ≠ verifier-pass — actually run `bash` snippets in a sandbox)
- [ ] All external facts cited and verified ([[feedback_citation_verify_or_remove]])
- [ ] Links to next module
- [ ] Proofread for clarity

### Platform Track Additional
- [ ] Current Landscape section (tools/approaches)
- [ ] Best Practices section
- [ ] Anti-Patterns section
- [ ] Further Reading section
- [ ] Theory explained before tools
- [ ] Principles emphasized over implementation

---

## Naming Conventions

### File Names
```
module-X.Y-topic-name.md
```

Examples:
- `module-1.1-what-is-sre.md`
- `module-2.3-error-budgets.md`

### Directory Structure
```
src/content/docs/platform/disciplines/sre/
├── README.md           # Part overview
├── module-1.1-xxx.md
├── module-1.2-xxx.md
└── ...
```

---

## Cross-References

When referencing other modules:
- Use relative links: `../foundations/systems-thinking/module-1.1-xxx.md`
- For prerequisites: Link to specific module, not just track
- For further learning: "See also [Module X.Y: Topic]"

---

## Dispatch Recipes (orchestrator perspective)

When the orchestrator delegates authoring to an agent, the recipe is:

### Codex (T0 primary when codex cap healthy)
```bash
.venv/bin/python scripts/dispatch_smart.py draft --agent codex \
  --mode danger --worktree .worktrees/<slug> --new-branch feat/codex-<slug> \
  - < /tmp/<slug>-brief.md
```
The brief MUST include: module spec, density gates, citation discipline rule, target word count, frontmatter requirements. **No `--search` flag on `dispatch_smart.py`** — `draft` task class auto-sets `codex_search=True` which exports `KUBEDOJO_CODEX_SEARCH=1` to the codex CLI ([[feedback_codex_writer_needs_search]] still applies at the codex layer). Default model is `gpt-5.3-codex-spark`; override with `--model gpt-5.5` when first-pass quality matters more than per-call cost. Cross-family reviewer = cursor composer-2.5 per Decision Card C.

### Cursor composer-2.5 (T0 primary when codex cap thin / throttle)
1. File a GH issue with the module spec (use [[curriculum-writer]] template + density gates).
2. Either dispatch headless via `.venv/bin/python scripts/dispatch_smart.py review --agent cursor --model composer-2.5` (note: `draft` task class also supports `--agent cursor`) OR comment "cursor please claim" so cursor IDE picks it from the queue.
3. Cursor opens a PR from a worktree.
4. Orchestrator picks PR up → dispatches codex R1 ([[cross-family-reviewer]]).
5. On NEEDS_CHANGES (session-52 cursor-authored tooling/api/docs cohort measured 4/7 = 57% first-pass NEEDS_CHANGES — proxy signal pending a true curriculum-T0 cohort), comment with R1 findings; cursor fix-passes.
6. On APPROVE, orchestrator merges (cursor does NOT merge per session-51 directive).

### Deepseek-v4-pro (off-load when 3+ codex authors in-flight)
Same shape as codex via `.venv/bin/python scripts/dispatch_smart.py draft --agent deepseek`. Pair with a vigilant code-domain reviewer; deepseek hallucinates rule attribution ([[feedback_deepseek_v4_pro_viable_for_t0_content]]).

### Post-author orchestrator checklist
1. Run `.venv/bin/python scripts/quality/verify_module.py <path>` → must pass density gates.
2. Run `npm run build` → 0 warnings.
3. Run `.venv/bin/python scripts/check_site_health.py` → 0 errors.
4. Dispatch cross-family reviewer per [[cross-family-reviewer]] routing table.
5. On R1 APPROVE, merge through PR (rebase). On NEEDS_CHANGES, fix-pass + R2.

## References

- [[module-quality-reviewer]] — the 8-dimension rubric your authored module is graded against.
- [[cross-family-reviewer]] — post-author review protocol.
- [[dispatch-router]] — agent routing decisions.
- [[k8s-cert-expert]] — domain expertise for k8s/cert content.
- [[platform-expert]] — domain expertise for platform-engineering content.
- Read `docs/quality-rubric.md` from the repository root for the full rubric definition.
- Read `docs/pedagogical-framework.md` from the repository root for research and guidelines.
- Read `scripts/prompts/module-writer.md` from the repository root for the standard writing prompt.
