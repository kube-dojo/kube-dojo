# Sources: Chapter 55 - The Scaling Laws

## Verification Key

- Green: claim has direct primary evidence from the paper/blog and a section-level anchor.
- Yellow: claim is interpretive, later-retrospective, or supported by one source with careful phrasing required.
- Red: claim should not be drafted unless new evidence is added.

## Primary Sources

| Source | Use | Verification |
|---|---|---|
| Jared Kaplan, Sam McCandlish, Tom Henighan, Tom B. Brown, Benjamin Chess, Rewon Child, Scott Gray, Alec Radford, Jeffrey Wu, Dario Amodei, "Scaling Laws for Neural Language Models," arXiv:2001.08361, 2020. URL: https://arxiv.org/pdf/2001.08361 | Core source for empirical scaling laws, model/dataset/compute variables, sample efficiency, compute-optimal allocation, and caveats. | Green: Abstract says cross-entropy loss scales as a power law with model size, dataset size, and training compute over more than seven orders of magnitude, while width/depth have minimal effects within a wide range. Section 1 Summary says model performance depends strongly on scale (parameters N, dataset tokens D, compute C), weakly on model shape within reasonable limits; power laws appear when not bottlenecked by the other factors; all three factors must scale in tandem; large models are more sample-efficient; convergence can be inefficient; compute-efficient training favors very large models stopped short of convergence. Section 1.2 gives the power-law equations. Appendix C lists caveats: no solid theoretical understanding, trust circumstances unclear without correction theory, poor fits in smallest-data regime, hyperparameter tuning limits, and compute-estimate limitations. |
| Richard S. Sutton, "The Bitter Lesson," 2019. URL: http://www.incompleteideas.net/IncIdeas/BitterLesson.html | Philosophical setup for computation-leveraging methods over hand-coded human knowledge. | Green/Yellow: essay says the biggest lesson from 70 years of AI is that general methods leveraging computation are ultimately the most effective, with search and learning as core methods; it gives chess, Go, speech, and vision examples. It is a blog essay, not evidence for Kaplan's equations. |
| Jordan Hoffmann et al., "Training Compute-Optimal Large Language Models," arXiv:2203.15556, 2022. URL: https://arxiv.org/pdf/2203.15556 | Later correction/refinement of compute-optimal model/data allocation. | Green: Abstract says current large language models were significantly undertrained because of focus on scaling model size while keeping training data roughly constant; for compute-optimal training, model size and training tokens should be scaled equally; Chinchilla used the same compute as Gopher with 70B parameters and 4x more data and outperformed larger models. Introduction says Kaplan found a power-law relationship and recommended increasing model size faster than tokens, while Hoffmann et al. find equal proportions. |

## Scene-Level Claim Table

| Claim | Scene | Primary Anchor | Independent Confirmation | Status | Notes |
|---|---|---|---|---|---|
| Sutton's "Bitter Lesson" argues that general methods leveraging computation tend to win over approaches relying on built-in human knowledge. | Bitter Lesson | Sutton 2019 essay | Historical examples in same essay | Green/Yellow | Use as frame, not proof of scaling equations. |
| Kaplan et al. study language-model cross-entropy loss, not "intelligence" directly. | Loss Curve | Kaplan Abstract; Section 1.2 definitions | Caveats Appendix C | Green | Essential guardrail. |
| Kaplan et al. report power-law relationships between loss and model size, dataset size, and training compute. | Loss Curve | Kaplan Abstract; Section 1 Summary; Section 1.2 | Hoffmann Introduction cites Kaplan power-law framing | Green | Say empirical, not universal law. |
| Scaling involves three knobs: non-embedding parameters N, dataset tokens D, and compute C; all must scale in tandem to avoid bottlenecks. | Three Knobs | Kaplan Section 1 Summary | Kaplan overfitting and compute-budget sections | Green | Prevents "just bigger model" simplification. |
| Within reasonable limits, Kaplan finds performance depends weakly on depth-vs-width and related architectural hyperparameters compared with scale. | Three Knobs | Kaplan Abstract and Section 1 Summary | Caveats narrow the claim | Green | Do not say architecture does not matter. |
| Larger models are more sample-efficient and can reach a target loss with fewer optimization steps/data points. | Compute-Optimal Training | Kaplan Section 1 Summary | Section 6 compute allocation | Green | Useful for explaining why "bigger but shorter" seemed rational. |
| Kaplan's compute-optimal result favored training very large models and stopping well short of convergence under a fixed compute budget. | Compute-Optimal Training | Kaplan Section 1 Summary; Figure 3; Section 6 | Hoffmann Introduction describes the conclusion | Green | Later corrected on token/model ratio by Chinchilla. |
| Kaplan's authors explicitly list caveats including lack of solid theory, unclear trust boundaries, small-data poor fits, hyperparameter uncertainty, and compute-estimate simplification. | Caveats | Kaplan Appendix C | Chinchilla later correction | Green | Must appear in prose. |
| Chinchilla confirms the scaling-law planning frame while changing the compute-optimal recipe: scale model size and tokens roughly equally. | Chinchilla | Hoffmann Abstract and Introduction | Kaplan as source being revised | Green | Do not frame as "Kaplan was fake." |
| Scaling laws shifted research planning toward forecasting returns to compute, but current sources do not support exact dollar-cost or cluster-procurement claims. | Transition | Kaplan compute-budget framing | Chinchilla compute-budget framing | Green/Yellow | Keep as interpretation; no invented capital numbers. |

## Conflict Notes

- Do not write "proved mathematically that intelligence scales." The anchored claim is empirical cross-entropy loss scaling.
- Do not write "architecture matters far less than raw scale" without the tested-limits caveat.
- Do not write "dumb model" or "throwing compute reliably yields intelligence." These are hype metaphors, not source claims.
- Do not treat Chinchilla as a contradiction of scaling laws; treat it as a compute-optimal allocation correction.
- Do not invent human-level AGI forecasts, dollar budgets, data-center purchases, or executive planning scenes.
- Do not claim the laws apply to all architectures, modalities, tasks, or scales beyond the tested and caveated evidence.

## Page/Section Anchor Worklist

- Kaplan 2020: Done for Abstract, Section 1 Summary, Section 1.2 equations, Figure 3 summary, Section 6 allocation, and Appendix C caveats.
- Sutton 2019: Done for computation/general-method thesis and chess/Go/speech/vision examples.
- Hoffmann 2022: Done for Abstract, Introduction, Figure 1 framing, and Kaplan-ratio correction.
