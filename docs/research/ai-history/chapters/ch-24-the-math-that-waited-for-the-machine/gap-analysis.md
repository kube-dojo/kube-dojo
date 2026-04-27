# Gap Analysis: Chapter 24 - The Math That Waited for the Machine

Source: Gemini gap analysis on PR #408, recorded 2026-04-27.

## Current Verdict

Research contract approved, but not prose-ready. The chapter can plausibly stretch to a long chapter if the priority, hardware, and demonstration-task anchors are extracted. Without those anchors, only the PDP demonstration and general internal-representation framing are safe.

## Claims Still Yellow or Red

| Claim Area | Status | Why |
|---|---|---|
| Biological plausibility | Yellow | Crick 1989 is listed, but exact passages critiquing biological realism have not been extracted. |
| Werbos and automatic-differentiation priority | Yellow | Werbos, Linnainmaa, and Griewank are present, but exact pages and transmission/terminology cautions are unresolved. |
| Perceptron-era context | Yellow | Needs a cross-link anchor to Ch17's Minsky/Papert research for hidden-layer credit assignment. |
| Hardware and compute scale | Yellow/Red | The exact 1986 experiment hardware and computing environment are not yet sourced. |

## Required Anchors Before Prose Readiness

- Rumelhart, Hinton, and Williams 1986 *Nature*: internal-representation claim and perceptron-convergence contrast.
- Rumelhart, Hinton, and Williams 1986 PDP chapter: algorithm walkthrough and a concrete encoder/symmetry task.
- Werbos 1974/1975 thesis: exact pages for backward derivative propagation and terminology mapping.
- Linnainmaa 1976 and Griewank 2012: exact pages for reverse accumulation and priority history.
- Crick 1989: exact biological-plausibility critique passages.
- Minsky/Papert 1969 through Ch17 research: passage setting up hidden-layer/credit-assignment limits.
- Hardware source: exact machine or compute environment used for the 1986 demonstrations.

## Scene Strength

| Scene | Strength | Notes |
|---|---|---|
| The Frozen Hidden Layer | Thin | Needs Ch17 anchor and careful bridge from perceptron limits to hidden-unit credit assignment. |
| The Chain Rule Becomes Machinery | Thin | Needs PDP task anchor and Werbos/AD page anchors before a full walkthrough. |
| The PDP Demonstration | Strongest | Nature/PDP sources support the core narrative once page anchors are extracted. |
| The Delayed Infrastructure Fit | Thin | Depends on hardware and compute details that are not yet sourced. |

## Word Count Assessment

- Core range today: 1,000-1,500 words.
- Stretch range with anchors: 4,000-7,000 words.

The stretch path is credible if the chapter uses separate evidence layers: perceptron context, grounded backprop walkthrough, prior-art correction, PDP demonstration, compute limits, and biological caveats.

## Responsible Expansion Path

To reach 4,000-7,000 words without bloat, source:

- a concrete walkthrough grounded in the 1986 encoder or symmetry tasks, not a generic toy network
- exact hardware/compute constraints from the 1986 experiments
- anchored Werbos/Linnainmaa/Griewank passages for an attribution-correction narrative
- Crick 1989 passages for a compact biological-plausibility caveat

## Handoff Requests

- Extract exact Werbos thesis pages for backward derivative propagation.
- Locate the 1986 PDP experiment hardware/computing environment.
- Obtain or verify full text/page access for Linnainmaa 1976 and Griewank 2012.
- Pull the Ch17 Minsky/Papert anchor needed for the opening scene.
