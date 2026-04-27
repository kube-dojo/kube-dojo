# AI History Team Workflow

This is a living operating document for the AI History book. Update it when the team learns a better practice. Do not treat it as frozen policy.

## Operating Principle

Honesty over output is the highest rule. The team should still strive for the intended 4,000-7,000 word range when the subject can support it, but expansion must come from verified evidence, not filler. Agents must not invent scenes, dialogue, institutional motives, deployment numbers, hardware details, or causal links to satisfy a word target.

## Roles

- Human editor: sets ambition, accepts scope tradeoffs, resolves taste and book-level direction.
- Primary researcher: owns the chapter contract and keeps claims tied to evidence.
- Cross-family reviewer: stress-tests research completeness, source choice, word-count honesty, and prose readiness. The reviewer must not be from the same model family as the primary researcher or prose writer.
- Claude reviewer: when available and cross-family for the current author, provides review for narrative coherence, overclaiming, and final prose quality.
- Gemini reviewer: when cross-family for the current author, provides review for research completeness, source gaps, and prose readiness.
- Codex reviewer/writer: may research, implement docs, draft prose after gates, maintain workflow artifacts, or review non-Codex-authored work.

Agents should help each other by naming gaps plainly. A useful refusal or downgrade is better than a confident but unsupported expansion.

## Chapter Lifecycle

### 0. GitOps Coordination: One Branch, One PR, One Phase

To prevent merge conflicts, keep cross-family reviews isolated, and protect `main`, all agents must strictly follow the "One Branch, One PR, One Phase" model:
- **Research Phase PR:** Create a branch `[agent]/394-chNN-research` off `main`. Complete the research contract, extract real empirical anchors, and NEVER fabricate or hallucinate historical data/page numbers. Open a PR. Ping Codex (anchor verification) and Claude (prose-capacity/gap review) **in parallel** via the Agent Bridge. Status `accepted` requires both to be Green. Merge only when approved.
- **Prose Phase PR:** Once the research PR is merged, create a branch `[agent]/394-chNN-prose` off `main`. Draft the prose strictly adhering to the approved Prose Capacity Plan without padding. Open a new PR and request a cross-family Prose Review. Merge only when approved.
- **NEVER** use massive batch PRs or long-lived epic branches.

### 1. Research Contract

Create or fill the standard chapter files:

- `brief.md`
- `sources.md`
- `timeline.md`
- `people.md`
- `infrastructure-log.md`
- `scene-sketches.md`
- `open-questions.md`
- `status.yaml`

The contract must include:

- thesis and scope
- boundary contract for what not to overclaim
- primary and secondary source table
- scene-level claim table with Green/Yellow/Red status
- timeline and people map
- infrastructure constraints
- open questions
- a `## Prose Capacity Plan` section in `brief.md` (see capacity-plan gate below)

Research-contract approval means the structure and source plan are good enough to continue research. It does not mean prose drafting may begin.

#### Prose Capacity Plan gate

Every `brief.md` must contain a `## Prose Capacity Plan` section. The plan is a contract for what the chapter is *allowed* to spend words on, not a wishlist:

- Each evidence layer is a bullet of the form `N-M words: <topic>` and must reference at least one specific scene from `scene-sketches.md` and at least one anchored entry in `sources.md` (page number, section, or stable identifier — not just the source title).
- Layer budgets must reflect evidence depth, not equal splits. A scene with 3 page anchors carries more words than a scene with 1.
- Sum of layer budgets is the chapter's allowed range. Writers cannot land outside it.
- The total range must match one of the Word Count Discipline labels (`4k-7k supported`, `4k-7k stretch`, `3k-5k likely`, `2k-4k natural`, `short chapter recommended`).
- The plan ends with a one-line honesty close: "If the verified evidence runs out, cap the chapter."

A plan whose bullets reference no `sources.md` page anchors is a *templated plan*, not an anchored plan. Templated plans pass `capacity_plan_drafted` but do not unlock prose drafting. See `chapters/ch-24-the-math-that-waited-for-the-machine/brief.md` for the canonical anchored-plan example.

### 2. Research Gap Analysis

After research-contract approval, request or create a gap analysis before prose readiness. The gap analysis should answer:

- Which claims remain Yellow or Red?
- Which page, section, figure, table, or archival anchors are missing?
- Which sources are primary, secondary, tertiary, or merely convenient?
- Which narrative scenes are strong enough to draft?
- Which scenes are too thin or speculative?
- What word count is naturally supported by verified evidence?
- What would be required to reach 4,000-7,000 words without bloat?
- Which chapter ambitions should be reduced?
- What should Gemini, Claude, Codex, or the human editor help source?

Gap analysis should be concrete. "Need more sources" is weak. "Need Pearl 1986 page anchor for local propagation in singly connected networks" is useful.

### 3. Anchor Extraction

Before prose readiness, extract exact anchors for high-value claims:

- page numbers for books and PDFs
- section names for HTML sources
- theorem, figure, table, or equation identifiers where useful
- DOI, stable URL, archival URL, or bibliographic identifier

Do not upgrade a claim to Green just because a source is famous. Upgrade it only when the specific claim is anchored.

### 4. Prose-Readiness Review

Ask a cross-family reviewer to review the full contract plus gap analysis. The expected verdicts are:

- `READY_TO_DRAFT`: page anchors and gaps are sufficient for a faithful chapter.
- `READY_TO_DRAFT_WITH_CAP`: draft, but cap the word count below the target.
- `NEEDS_ANCHORS`: source list is good, but page/section anchors are missing.
- `NEEDS_RESEARCH`: source list or scope is inadequate.
- `SCOPE_DOWN`: the chapter should be shorter or narrower.

Only `READY_TO_DRAFT` and `READY_TO_DRAFT_WITH_CAP` unlock prose drafting.

### 5. Drafting

Draft only from verified evidence. Use Yellow claims only with explicit caution and never as structural load-bearing claims. Red claims stay out of prose except as clearly labeled open questions.

If a chapter cannot honestly reach 4,000 words, write the natural chapter length and document why. The target is quality, not padding.

### 6. Prose Review

Ask a cross-family reviewer to review the drafted chapter for:

- factual overclaims
- unsupported scenes
- missing citations
- source misuse
- narrative coherence
- word-count inflation
- book-level continuity

Do not merge prose on tests alone. Cross-family review remains required.

### 7. Claude / Cross-Family Review

When Claude is available, ask for an independent-family review before final acceptance. Claude should especially check:

- whether the prose outpaced the research contract
- whether the story is compelling without fabrication
- whether chapter transitions and part-level arcs work

### 8. Human Final Pass

The human editor decides:

- whether the chapter's natural length is acceptable
- whether to source more material or scope down
- whether tone and pacing match the book
- whether unresolved questions can remain as future work

## Status Terms

- `researching`: contract or anchors are still incomplete.
- `capacity_plan_drafted`: brief.md has a Prose Capacity Plan section but layers do not yet reference sources.md page anchors. Does not unlock drafting.
- `capacity_plan_anchored`: every plan layer references at least one page anchor in sources.md. Eligible for `research_contract_approved` review.
- `research_contract_approved`: reviewer approved the research plan, but prose is not unlocked.
- `gap_analysis_requested`: reviewer has been asked to identify missing anchors and weak scenes.
- `anchors_in_progress`: exact page/section anchors are being extracted.
- `prose_ready`: reviewer says drafting may begin.
- `drafting`: prose is being written.
- `prose_review`: draft is under cross-family review.
- `accepted`: human/cross-family review has cleared the chapter.

A drafted chapter (prose already exists) whose `brief.md` plan is templated, not anchored, regresses to `capacity_plan_drafted` until sources.md is upgraded. The existing prose stays on disk; it just cannot be cited as "accepted" while the contract behind it is incomplete.

## Word Count Discipline

The default ambition is 4,000-7,000 words for major chapters, but agents must not min-max by either padding to the target or prematurely shrinking the scope. Use a two-number plan:

- `core range`: what the verified evidence can support today.
- `stretch range`: what the chapter could support if specific missing evidence is found.

Expansion must follow an evidence ladder:

- primary-source anchors
- deployment or institutional detail
- infrastructure and hardware constraints
- competing interpretations or priority disputes
- consequences and later reception
- clear explanation of technical ideas tied to historical sources

Expansion must not come from:

- generic textbook explanation unrelated to the historical event
- invented lab scenes or motives
- repeated summary of the same claim
- modern hindsight that the chapter's sources do not support
- unanchored deployment scale, hardware, or business impact

Use these labels in briefs and gap analyses:

- `4k-7k supported`: verified sources already support a long narrative without padding.
- `4k-7k stretch`: possible if named gaps are filled.
- `3k-5k likely`: chapter has enough evidence, but some scenes should stay compact.
- `2k-4k natural`: conceptually important but structurally compact.
- `short chapter recommended`: expansion would require filler or unrelated material.

When in doubt, do not simply lower the target. First identify the missing evidence that could support responsible expansion. Lower the target only after the team agrees the missing layer is unavailable, out of scope, or not worth the narrative cost.

## Review Request Template

Use this shape when asking for gap analysis or prose readiness:

```text
Please review Chapter N as [gap analysis / prose-readiness review].

Focus files:
- docs/research/ai-history/chapters/ch-XX-.../brief.md
- docs/research/ai-history/chapters/ch-XX-.../sources.md
- docs/research/ai-history/chapters/ch-XX-.../open-questions.md

Questions:
1. Which claims remain Yellow/Red and why?
2. Which exact page/section anchors are required before prose?
3. Which scenes are strong enough to draft, and which are thin?
4. What natural word-count range is supported by verified evidence?
5. What specific evidence would let this reach 4,000-7,000 words without bloat?
6. What should another agent or the human editor help source?

Please post a structured comment with concrete gaps and a verdict:
- READY_TO_DRAFT
- READY_TO_DRAFT_WITH_CAP
- NEEDS_ANCHORS
- NEEDS_RESEARCH
- SCOPE_DOWN
```

## Change Rule

This document should evolve through small PRs. When the team discovers a repeatable failure mode, add a rule here and cite the chapter or PR that exposed it.
