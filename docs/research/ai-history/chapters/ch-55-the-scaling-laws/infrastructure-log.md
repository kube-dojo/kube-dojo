# Infrastructure Log: Chapter 55

## Technical Metrics & Constraints
- **Measured quantity:** Kaplan studies cross-entropy loss for autoregressive Transformer language models, not intelligence directly.
- **Core variables:** `N` is non-embedding parameter count, `D` is dataset size in tokens, and `C` is estimated non-embedding training compute.
- **Training setup:** Kaplan uses WebText2 tokenized with byte-pair encoding, vocabulary size 50,257, and a 1024-token context as principal evaluation setup.
- **Scaling claim:** Loss follows empirical power laws with model size, dataset size, and compute when the other factors are not bottlenecks.
- **Architecture caveat:** Width/depth and related architectural hyperparameters had weak effects within the paper's tested range; this is not a claim that architecture never matters.
- **Compute-optimal claim:** Under a fixed compute budget, Kaplan's analysis favored larger models, bigger batches, and early stopping short of convergence.
- **Kaplan caveats:** No solid theoretical understanding; unclear trust boundaries; small-data poor fits; possible missing hyperparameter effects; compute estimate excludes some context-length-related terms.
- **Chinchilla correction:** Hoffmann et al. train over 400 models from 70M to over 16B parameters on 5B to 500B tokens and conclude compute-optimal training scales model size and training tokens equally.

## Unknowns / Do Not Invent
- Exact dollars, GPU counts, cluster layouts, and procurement decisions are not anchored.
- Claims about human-level intelligence, AGI timelines, or guaranteed benchmark wins are not anchored.
- Applicability to non-language modalities or future architectures is not anchored here.
