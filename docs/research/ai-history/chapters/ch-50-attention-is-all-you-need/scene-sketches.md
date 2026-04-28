# Scene Sketches: Chapter 50

## Scene 1: The Recurrent Bottleneck
- **Action:** Start with machine translation as an engineering workflow: a source sentence enters an encoder, a target sentence emerges from a decoder, and an LSTM/GRU hidden state marches position by position.
- **Evidence anchors:** Sutskever 2014 Abstract/Introduction for fixed-dimensional LSTM sequence-to-sequence; Vaswani 2017 Section 1 for recurrent computation aligned to sequence positions and the parallelization bottleneck.
- **Drafting warning:** Do not reduce this to "LSTMs forget everything." The verified bottleneck is sequential computation and long-dependency difficulty, not universal memory failure.

## Scene 2: Attention Before the Break
- **Action:** Show Bahdanau attention as the bridge: the decoder no longer has to rely on one fixed vector, but can retrieve source-side annotations through learned alignment.
- **Evidence anchors:** Bahdanau 2014 Abstract/Introduction and Sections 3.1-3.2; Vaswani 2017 Section 1's statement that attention was already integral but usually paired with recurrent networks.
- **Drafting warning:** This scene is an attribution guardrail. It prevents the chapter from falsely treating attention as a 2017 invention.

## Scene 3: Dropping the Recurrence
- **Action:** Describe the Transformer as an encoder-decoder architecture built from repeated blocks: self-attention, feed-forward layers, residual connections, and layer normalization. The decoder has its own masked self-attention plus encoder-decoder attention.
- **Evidence anchors:** Vaswani 2017 Sections 2, 3, 3.1, and 3.2.3.
- **Drafting warning:** The decoder remains autoregressive. Future-token masking is a load-bearing detail.

## Scene 4: Matrix-Friendly Attention
- **Action:** Explain scaled dot-product attention as a set of query-key comparisons and value-weighted summaries, computed for many queries as matrices. Then explain why multi-head attention repeats this in parallel projected subspaces.
- **Evidence anchors:** Vaswani 2017 Sections 3.2.1 and 3.2.2; Figure 2.
- **Drafting warning:** Keep math accessible. The reader needs the shape of the computation, not a textbook proof.

## Scene 5: The Hardware and Results Receipt
- **Action:** Move from architecture to measurement: Table 1's sequential-operations comparison, one machine with 8 P100 GPUs, 12-hour base training, 3.5-day big training, and WMT BLEU results.
- **Evidence anchors:** Vaswani 2017 Section 4/Table 1, Section 5.2, Section 6.1/Table 2.
- **Drafting warning:** "Matrix-friendly" and "more parallelizable" are verified; "perfectly aligned with hardware" is not.

## Scene 6: The Door Opens
- **Action:** End by naming the consequence without racing ahead: the paper did not yet produce BERT, GPT-2, model hubs, scaling laws, RLHF, or diffusion systems, but it created the architecture later chapters will scale, distribute, and productize.
- **Evidence anchors:** Chapter outline and Part 8 issue scope; no new historical claims without later chapter sources.
