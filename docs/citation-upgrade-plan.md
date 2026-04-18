# Citation-First Upgrade Plan

This plan governs the `4/5` and `5/5` quality-upgrade work.

## Goal

Raise module quality **without** creating a dry, over-cited reading experience.

The rule is:
- pedagogy still comes first
- citations must support trust, not replace explanation
- a module only counts as upgraded when it is both:
  - strong enough to pass the rubric
  - evidenced well enough to avoid hallucinated war stories or unsupported factual claims

## Hard Gate

For upgrade work, a module is **not review-passed** until it satisfies all of these:

1. `## Sources` section exists
2. every war story has an explicit citation or `Source:` line
3. important factual claims are traceable to cited sources
4. the formal rubric score still passes:
   - every dimension `>= 4`
   - total `>= 29/35`

## What Must Be Cited

- war stories
- incident timelines
- legal cases
- standards / regulations / curricula
- vendor or model capability claims
- pricing / costs / benchmarks
- security or safety claims that depend on a real incident

## What Does Not Need Inline Citation Every Time

- basic connective teaching prose
- analogies used to explain a concept
- instructor framing like "this is risky because..."

Those still need to remain consistent with the sourced material, but they do not need to turn into a citation after every sentence.

## Writing Standard

Citations must not make the module worse.

Good:
- cited war story with one clean source line
- `## Sources` section at the end
- sourced facts used where trust depends on them

Bad:
- citation spam after every sentence
- dumping links without integrating them into the teaching
- replacing explanation with reference lists

## Reset Rule

Any module previously treated as upgraded but lacking citations is reset to:
- `needs re-review`

That means:
- do not count it as `4/5 passed`
- do not count it as `5/5 candidate`
- do not present it as complete in issue tracking

## Execution Order

1. Update process docs and checker
2. Reset tracking state for uncited upgraded modules
3. Rework the current AI batch with citations
4. Re-run review and scoring
5. Continue section by section

## First Batch

Current first citation-first re-review batch:
- `ai/foundations/module-1.1-what-is-ai`
- `ai/foundations/module-1.2-what-are-llms`
- `ai/foundations/module-1.3-prompting-basics`
