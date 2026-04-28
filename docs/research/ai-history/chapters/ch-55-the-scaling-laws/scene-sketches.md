# Scene Sketches: Chapter 55 - The Scaling Laws

## Scene 1: The Bitter Lesson
- **Action:** Introduce Sutton as a warning against over-engineering human knowledge into systems. The historical pattern is that search and learning benefit from rising computation.
- **Evidence:** Sutton essay: general methods leveraging computation are ultimately most effective; search and learning are the main ways to use massive computation.
- **Do not say:** "Always wins" without qualification. This is a philosophical framing essay, not a theorem.

## Scene 2: Plotting Loss Against Scale
- **Action:** Make the math visual and accessible: when the team plotted loss against model size, data, and compute on log scales, the curves were smoother than ordinary research intuition expected.
- **Evidence:** Kaplan Abstract and Section 1 Summary: loss scales as a power law with model size, dataset size, and compute; trends span many orders of magnitude.
- **Do not say:** "Perfect straight line." The paper has caveats and eventual flattening.

## Scene 3: Three Knobs
- **Action:** Explain N, D, and C as a control panel: parameters, tokens, and compute. If one knob is starved, the others stop paying off cleanly.
- **Evidence:** Kaplan Section 1 Summary and Section 1.2.
- **Pedagogy:** Use a simple bottleneck analogy, but keep it tied to cross-entropy loss.

## Scene 4: The Compute-Optimal Bet
- **Action:** Show why the result changes planning: under a fixed compute budget, it may be better to train a larger model briefly than a smaller model to convergence.
- **Evidence:** Kaplan Section 1 Summary, Figure 3 description, Section 6.
- **Do not say:** "A $100M cluster guarantees X loss." No dollar figures are anchored.

## Scene 5: The Correction
- **Action:** End with Chinchilla: the scaling frame survived, but the recipe changed. DeepMind found large models had often been undertrained, and that tokens needed to scale with parameters more evenly.
- **Evidence:** Hoffmann Abstract and Introduction.
- **Transition:** This leads naturally into Chapter 56, where the ability to build and schedule huge compute systems becomes part of the research program.
