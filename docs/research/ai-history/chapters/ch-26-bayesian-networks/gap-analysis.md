# Gap Analysis: Chapter 26 - Bayesian Networks

Source: Gemini gap analysis on PR #409, recorded 2026-04-27.

## Current Verdict

Research contract approved, and the first anchor-extraction pass has moved the chapter out of the zero-word state. Cooper 1990, Charniak 1991, and Lauritzen/Spiegelhalter 1988 now have usable page anchors. Pearl 1986 is currently anchored at the ScienceDirect abstract/page-241 level because the full article is closed access; Pearl 1988 has chapter/page anchors and publisher-description anchors from ScienceDirect, but not internal passage anchors. This is enough for a cautious research contract, but Gemini should decide whether full Pearl access is required before prose lock.

## Claims Still Yellow or Red

| Claim Area | Status | Why |
|---|---|---|
| Bayesian networks as a move away from brittle certainty factors | Green | Lauritzen/Spiegelhalter 1988 pp.157-160 directly contrasts exact probabilistic methods with MYCIN certainty factors and other informal expert-system schemes. |
| Computational hardness of exact inference | Green | Cooper 1990 pp.393-403 anchors NP-hardness, restricted efficient cases, and the move toward special-case/average-case/approximation algorithms. |
| Bridge to later causal reasoning | Yellow | Needs a later source and should remain a forward pointer, not the chapter center. |
| 1985 term "Bayesian network" | Yellow | Needs a verified source before inclusion. |
| Lauritzen/Spiegelhalter and Charniak | Green | Page anchors extracted. |
| Neapolitan, Heckerman, Pearl 1995 | Yellow | Still optional later/context sources; no exact anchors extracted. |

## Required Anchors Before Prose Readiness

- Pearl 1986: full-article access for detailed internal passages beyond the ScienceDirect abstract.
- Pearl 1988: internal passage anchors for Markov/Bayesian networks and belief updating, beyond chapter ranges and publisher description.
- A verified source for the 1985 "Bayesian network" terminology claim, or drop that timeline row.
- Decide whether Ch19-Ch23 MYCIN/certainty-factor anchors are still needed now that Lauritzen/Spiegelhalter supplies a direct expert-system uncertainty contrast.

## Scene Strength

| Scene | Strength | Notes |
|---|---|---|
| Rules Meet Uncertainty | Medium to strong | Lauritzen/Spiegelhalter now anchors certainty factors, PROSPECTOR, CASNET, INTERNIST, exact probabilistic manipulation, and MUNIN. |
| The Graph as a Memory Aid | Medium | Charniak gives a strong tutorial explanation; Pearl 1986 supports the definition at abstract level; Pearl 1988 internal pages still needed for prose lock. |
| Propagation Instead of Global Recalculation | Medium | Pearl 1986 abstract and Pearl 1988 Chapter 4 range support the claim; detailed Pearl passages still need access. |
| The Cost Returns | Strong | Cooper 1990 anchors the limit-setting scene. |

## Word Count Assessment

- Core range now: 3,500-4,500 words.
- Stretch range with full Pearl 1986/1988 access or a verified early application/terminology source: 4,500-6,000 words.

The stretch path requires more than generic probability explanation. It should use expert-system contrast, Pearl propagation, MUNIN/PATHFINDER context, computational limits, and the infrastructure cost of eliciting/maintaining probability tables.

## Responsible Expansion Path

To reach 4,000-7,000 words without bloat:

- Use Lauritzen/Spiegelhalter for the expert-system uncertainty contrast instead of hand-waving about brittle rules.
- Use Charniak for a reader-friendly DAG/probability-table explanation, backed by Pearl 1986 abstract-level claims.
- Use Cooper 1990 to keep the "structured uncertainty" story honest about computational limits.
- Use MUNIN and PATHFINDER as examples only within the evidence collected; do not invent deployment scenes.
- Keep causal reasoning as a short forward pointer unless a later Pearl source is added.

## Handoff Requests

- Ask Gemini whether abstract-level Pearl 1986 plus full anchors from Lauritzen/Spiegelhalter, Charniak, and Cooper are enough to proceed to prose outline.
- If Gemini requires full Pearl anchors, use library access before drafting.
- Either source the 1985 terminology claim or remove it from the final timeline.
- Decide whether Neapolitan/Heckerman/Pearl 1995 are necessary for the final prose, or only optional context.
