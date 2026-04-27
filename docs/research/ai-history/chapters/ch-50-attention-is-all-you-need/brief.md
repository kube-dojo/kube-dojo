# Brief: Chapter 50 - Attention Is All You Need

## Thesis
Sequential processing in Recurrent Neural Networks (RNNs) was an infrastructural bottleneck; they could not be fully parallelized across GPUs. The Transformer architecture solved this by processing all words simultaneously using "Self-Attention," perfectly aligning the algorithm with the massive parallel matrix math capabilities of modern hardware.

## Scope
- IN SCOPE: Ashish Vaswani, Noam Shazeer, the 2017 "Attention Is All You Need" paper, the elimination of recurrence, parallelization.
- OUT OF SCOPE: GPT-1/BERT (next chapters).

## Scenes Outline
1. **The Sequential Bottleneck:** Why RNNs and LSTMs are painfully slow to train on GPUs (they have to read word by word).
2. **The Google Brain Team:** A diverse team attempts to drop recurrence entirely.
3. **Self-Attention:** Pedagogical explanation of how the Transformer calculates the relationship between every word in a sentence simultaneously, unleashing massive scale.

## 4k-7k Prose Capacity Plan

This chapter can support a long narrative only if it is built from verified layers rather than padding:

- 500-800 words: Historical context and setup, bridging from the previous era.
- 933-1233 words: Detailed narrative surrounding The Sequential Bottleneck:, heavily anchored to primary sources.
- 933-1233 words: Detailed narrative surrounding The Google Brain Team:, heavily anchored to primary sources.
- 933-1233 words: Detailed narrative surrounding Self-Attention:, heavily anchored to primary sources.
- 400-700 words: Honest close that summarizes the infrastructural shift and transitions to the next chapter.

Most layers now have page-level anchors. Do not invent lab drama or dialogue to reach the top of the range. If the verified evidence runs out, cap the chapter.
