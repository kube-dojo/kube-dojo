# Infrastructure Log: Chapter 50

## Technical Metrics & Constraints
- **Recurrent bottleneck:**
  - Vaswani 2017 Section 1 says recurrent models align sequence positions with computation steps, creating an inherently sequential dependency that precludes parallelization within a training example.
  - This matters most at longer sequence lengths because memory constraints limit batching across examples.

- **Attention as matrix work:**
  - Vaswani 2017 Section 3.2.1 packs queries, keys, and values into matrices and computes attention for a set of queries simultaneously.
  - The paper states dot-product attention is faster and more space-efficient in practice than additive attention because it can use optimized matrix multiplication code.

- **Multi-head structure:**
  - Vaswani 2017 Section 3.2.2 runs projected attention operations in parallel across 8 heads in the base model.
  - This supports a prose explanation of representational subspaces, but not mystical "understanding."

- **Sequential operations comparison:**
  - Vaswani 2017 Section 4/Table 1 is the strongest hardware-shape anchor: self-attention connects positions with a constant number of sequentially executed operations per layer, while a recurrent layer requires O(n).
  - Caveat: self-attention has its own costs for very long sequences; the paper says it is faster than recurrent layers when sequence length is smaller than representation dimensionality, which was usually true for then-standard sentence representations.

- **Training hardware:**
  - Vaswani 2017 Section 5.2: one machine with 8 NVIDIA P100 GPUs.
  - Base model: about 0.4 seconds per step, 100,000 steps, 12 hours.
  - Big model: about 1.0 second per step, 300,000 steps, 3.5 days.
  - Section 6.1/Table 2 reports translation quality and estimates training cost using training time, GPU count, and sustained single-precision FLOP estimates.

## Do Not Say

- Do not say the Transformer "maxes out GPU/TPU utilization." The paper reports more parallelization and a P100 training setup, not full utilization.
- Do not say "TPU" for this paper's reported experiments unless a separate source is added. The verified hardware is 8 NVIDIA P100 GPUs.
- Do not say the model ignores word order. Positional encodings are a core part of Section 3.5.
- Do not say all output tokens are generated simultaneously. Decoder masking and autoregressive generation are explicit in Section 3.
