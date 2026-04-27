# Gap Analysis: Chapter 24 - The Math That Waited for the Machine

Source: Gemini gap analysis on PR #408, recorded 2026-04-27.

## Current Verdict

Research contract approved, and the first anchor-extraction pass has removed most of the prose-readiness blockers. Nature 1986, the PDP chapter, Werbos, and Griewank now have usable page anchors. Crick 1989 is anchored only at Nature standfirst/metadata level, and 1986 hardware/computing-environment details remain open. The chapter can now support a cautious prose outline, but Gemini should decide whether full Crick/internal hardware anchors are required before draft.

## Claims Still Yellow or Red

| Claim Area | Status | Why |
|---|---|---|
| Biological plausibility | Green/Yellow | Nature 1986 p.536 says the current learning procedure is not a plausible brain-learning model; Crick 1989 Nature standfirst gives a contemporary critique, but detailed Crick passages still need access. |
| Werbos and automatic-differentiation priority | Green/Yellow | Werbos thesis and Griewank 2012 now anchor earlier derivative machinery and reverse-mode history. Yellow only for direct transmission to PDP, which remains unproven. |
| Perceptron-era context | Green/Yellow | Nature 1986 p.533 and PDP pp.318-320 anchor the perceptron/hidden-unit bridge; direct Ch17 source remains skeletal. |
| Hardware and compute scale | Yellow/Red | The exact 1986 experiment hardware and computing environment are not yet sourced. |

## Required Anchors Before Prose Readiness

- Full Crick 1989 internal passages if the chapter wants more than the article-level critique.
- Hardware source: exact machine or compute environment used for the 1986 demonstrations, if available.
- Direct Minsky/Papert Ch17 source if the opening needs more than the PDP chapter's Minsky/Papert bridge.
- Decide whether Linnainmaa 1976 full text is required, or whether Griewank 2012 is sufficient for reverse-mode lineage.

## Scene Strength

| Scene | Strength | Notes |
|---|---|---|
| The Frozen Hidden Layer | Medium to strong | Nature 1986 and PDP pp.318-320 provide the hidden-unit bridge; Ch17 should later add a direct Perceptrons anchor. |
| The Chain Rule Becomes Machinery | Strong | PDP pp.326-327, Werbos pp.II-23-II-26, and Griewank pp.393-395 can support the mechanism and priority-correction scenes. |
| The PDP Demonstration | Strong | Nature/PDP anchors now support symmetry, family-tree/internal-representation, and algorithm walk-through. |
| The Delayed Infrastructure Fit | Medium | Biological caveat is anchored; hardware/compute environment remains the main missing piece. |

## Word Count Assessment

- Core range now: 4,000-5,000 words.
- Stretch range with hardware and full Crick/Linnainmaa/Minsky anchors: 5,000-6,500 words.

The stretch path is credible if the chapter uses separate evidence layers: perceptron context, grounded backprop walkthrough, prior-art correction, PDP demonstration, compute limits, and biological caveats.

## Responsible Expansion Path

To reach 4,000-7,000 words without bloat:

- Ground the walkthrough in the 1986 symmetry/family-tree/PDP tasks, not a generic toy network invented for the chapter.
- Use Werbos and Griewank as an attribution-correction layer: earlier derivative machinery existed, while PDP made hidden representation learning persuasive.
- Keep biological plausibility careful: Nature 1986 itself warns against treating the current procedure as a brain-learning model, and Crick 1989 supplies a contemporary critique at article level.
- Do not invent hardware constraints. If no machine/environment source is found, frame compute limits more generally or cap the chapter below the top of the range.

## Handoff Requests

- Ask Gemini whether the current anchors are enough for prose outline, with hardware and detailed Crick passages left as stretch gaps.
- Locate the 1986 PDP experiment hardware/computing environment only if it can be sourced without speculation.
- Decide whether Linnainmaa 1976 full text is necessary after Griewank 2012 anchors the reverse-mode lineage.
- Pull the direct Ch17 Minsky/Papert anchor later when Ch17 is upgraded; current Ch24 can use the PDP chapter bridge cautiously.
