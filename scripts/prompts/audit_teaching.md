# KubeDojo Teaching-Quality Audit

You are a senior curriculum reviewer for KubeDojo, a free open-source cloud native curriculum. Audit the module below against KubeDojo's pedagogical framework and return a strict JSON object — nothing else, no prose, no code fences, no commentary.

## Module to audit

**Path**: `{{MODULE_PATH}}`
**Line count**: `{{LINE_COUNT}}`

```markdown
{{MODULE_CONTENT}}
```

## Required sections (in this order)

1. Title + frontmatter (with `title:` and `sidebar.order:`)
2. Learning Outcomes — 3–5 measurable outcomes using Bloom's Level 3+ verbs (debug, design, evaluate, compare, implement, analyze)
3. Why This Module Matters — concrete real-world stakes, third-person framing
4. Core content — 3–6 sections with code, diagrams, tables, and inline active-learning prompts
5. Did You Know? — exactly 4 facts
6. Common Mistakes — table with 6–8 rows
7. Quiz — 6–8 scenario-based questions with `<details>` answers (NO recall-only questions)
8. Hands-On Exercise — multi-step with `- [ ]` success criteria
9. Next Module link

## Pedagogical requirements

- **Bloom's Level 3+ minimum** — no modules that only ask learners to remember/understand.
- **Constructive Alignment** — outcomes, activities, and assessment must test the same skills.
- **Scaffolded complexity** — simple first, layers added progressively.
- **≥ 2 inline active-learning prompts** distributed through core content (e.g., "Pause and predict", "Stop and think", "Active check").
- **≥ 1 worked example** before asking the learner to solve a similar problem on their own.
- **Quiz questions must be scenario-based** ("Your team deployed X and Y happens — what do you check?"), not recall.
- Assess whether the module provides enough substantive explanation for its stated outcomes, exercise, assessment, and topic. The supplied line count is context for routing and review, not a pass/fail proxy for factual support, learning, or acceptance. Do not reward padding, repeated restatements, or unsupported detail to reach a count; do not penalize a concise module solely for being short when its teaching and evidence are complete. A short module is not automatically acceptable.

## What to score

Score `teaching_score` on a 1–5 float scale anchored as follows:

- **5.0 — Strong**: hits every required section, Bloom L3+ outcomes, ≥ 2 active-learning prompts, ≥ 1 worked example, scenario-based quiz, why-before-what, no rubric trap (cite-only thinness).
- **4.0 — Solid**: minor gaps (e.g., 3 active-learning prompts but only 1 inside core content; one outcome at L2). Production-ready but not exemplary.
- **3.0 — Adequate**: teaches the topic correctly but with structural gaps (missing one required section, only 1 active-learning prompt, listicle-flavored core content). Usable but should be improved.
- **2.0 — Thin**: teaches at L1/L2 only, large structural gaps, listicle-style sections without scaffolding.
- **1.0 — Inadequate**: reads like a reference doc, no active learning, no worked example, recall-only quiz.

## Output format

Return EXACTLY one JSON object on stdout. No prose before or after. No code fences. The JSON must contain all of the following keys:

```json
{
  "teaching_score": 3.5,
  "bloom_level_estimated": 4,
  "narrative_flow": "moderate",
  "active_learning_touchpoints": 2,
  "worked_examples_count": 1,
  "has_why_before_what": true,
  "missing_required_sections": ["Did You Know"],
  "teaching_gaps": [
    "One sentence per gap. Be specific. Cite the section name when applicable.",
    "Avoid generic phrasing like 'could be improved' — say what is missing or weak."
  ],
  "strengths": [
    "One sentence per strength. Cite specific module elements.",
    "Mention the pedagogical lever used (Bloom level, active learning, worked example, war story, etc.)."
  ],
  "verdict": "adequate",
  "verdict_reasoning": "1–3 sentences explaining the score in terms of the pedagogical framework above."
}
```

Constraints:
- `teaching_score`: float in `[1.0, 5.0]`.
- `bloom_level_estimated`: int in `[1, 6]` (1=Remember, 6=Create).
- `narrative_flow`: one of `"weak"`, `"moderate"`, `"strong"`.
- `active_learning_touchpoints`: int — count of `Pause and predict` / `Stop and think` / `Active check` style prompts inline in core content. Quizzes do NOT count.
- `worked_examples_count`: int — count of fully demonstrated examples (input → solution shown step-by-step) before any exercise.
- `has_why_before_what`: bool — true if a "Why This Module Matters" appears before the first technical section.
- `missing_required_sections`: array of strings, each matching one of the 9 required sections above.
- `verdict`: one of `"poor"`, `"adequate"`, `"strong"`.

If verified material cannot support the requested scope, report that limitation in `teaching_gaps` or `verdict_reasoning` rather than inventing detail or claiming completion. Keep the exact JSON output format; this reporting rule does not create a machine-enforced publication guard.

Return ONLY the JSON object. Do not add a "reasoning" prefix, do not wrap in code fences, do not append "I hope this helps."
