# Infrastructure Log: Chapter 8

## Technical Metrics & Constraints

### The Recurrent Bottleneck
- **RNNs/LSTMs (circa 2014-2016):**
  - Constraint: Sequential computation. Word $N$ cannot be processed until word $N-1$ is finished.
  - Impact: Cannot be effectively distributed across thousands of GPU cores. Training large models takes too long.

### The Transformer & TPU Alignment
- **TPU v2 (2017):**
  - Capability: 180 TFLOPs, 64 GB High Bandwidth Memory (HBM).
  - Design: Purpose-built for massive matrix multiplications.
- **The Transformer Architecture:**
  - Operation: Self-attention calculates the relationship between all words in a sequence simultaneously via matrix multiplication.
  - Impact: $O(1)$ sequential operations. Can utilize 100% of a GPU/TPU pod's parallel cores.

### The Scaling Unlock
- **Parameter Growth (The result of parallelization):**
  - 2014 (Seq2Seq): ~380 Million parameters (training took 10 days on 8 GPUs, hitting the sequential wall).
  - 2018 (BERT-Large): 340 Million parameters (but trained in 4 days on 64 TPUs due to parallelization).
  - 2020 (GPT-3): 175 Billion parameters (only possible because the architecture scales perfectly with added compute).