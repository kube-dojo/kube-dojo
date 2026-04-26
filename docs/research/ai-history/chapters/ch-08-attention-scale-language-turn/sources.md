# Sources: Chapter 8

## Annotated Bibliography

### Primary
- [x] **"Attention Is All You Need" (Vaswani et al., NIPS 2017)**
  - Verification: Green. The foundational paper describing the Transformer architecture. Explicitly notes its superiority in parallelization and computational efficiency over RNNs. Anchors Scene 2.
- [x] **"In-Datacenter Performance Analysis of a Tensor Processing Unit" (Jouppi et al., ISCA 2017)**
  - Verification: Green. Provides the hardware context (Google's TPUv1/v2) regarding matrix multiplication capabilities that the Transformer architecture exploited. Anchors Scene 2.
- [x] **"Sequence to Sequence Learning with Neural Networks" (Sutskever et al., NIPS 2014)**
  - Verification: Green. The foundational paper for the prior RNN/LSTM sequence paradigm, outlining the computational limits that Transformers solved. Anchors Scene 1.
- [x] **"BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding" (Devlin et al., NAACL 2019)**
  - Verification: Green. The breakthrough paper demonstrating the massive scaling capability of bidirectional Transformers. Anchors Scene 3.
- [x] **"Scaling Laws for Neural Language Models" (Kaplan et al., 2020)**
  - Verification: Green. Formalizes the observation that Transformer performance scales predictably with compute, dataset size, and parameters. Anchors Scene 3.

### Secondary
- [x] **"How the Transformer architecture changed AI forever" (MIT Technology Review, 2024 / contemporary retrospectives)**
  - Verification: Green. Secondary analysis explicitly detailing how the paper's focus on parallelization unlocked scaling laws and broke the RNN bottleneck. Anchors Scenes 1 and 2.
- [x] **"Genius Makers: The Mavericks Who Brought AI to Google, Facebook, and the World" (Cade Metz, 2021)**
  - Verification: Green. Covers Google Brain's internal shift towards scaling, the hardware alignment, and the genesis of the NLP revolution. Anchors Scenes 1 and 3.

## Conflict Notes
- **Linguistic vs. Infrastructural Breakthrough:** The Transformer is often framed in popular science purely as a linguistic or algorithmic breakthrough (e.g., "it understands context better"). This chapter will rigorously enforce the epic's infrastructural angle. The primary texts (Vaswani et al.) and secondary analysis will be used to show that the algorithmic elegance of attention was initially a means to an end: infrastructural efficiency and parallelization.