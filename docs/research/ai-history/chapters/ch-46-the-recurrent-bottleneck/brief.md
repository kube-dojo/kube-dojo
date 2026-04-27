# Brief: Chapter 46 - The Recurrent Bottleneck

## Thesis
While CNNs conquered computer vision, sequence data (text and audio) was dominated by Long Short-Term Memory (LSTM) networks. However, the fundamental mathematics of recurrent networks required processing data sequentially, creating a hard physical bottleneck that GPUs could not accelerate through massive parallelism.

## Scope
- IN SCOPE: Sepp Hochreiter, Jürgen Schmidhuber, the 1997 LSTM paper, the vanishing gradient problem in RNNs, the sequential processing constraint.
- OUT OF SCOPE: Transformers (Part 8).

## Scenes Outline
1. **The Vanishing Gradient:** Why standard RNNs forget early information in a sequence.
2. **The Constant Error Carousel:** Hochreiter and Schmidhuber invent the LSTM to preserve error gradients across long time steps.
3. **The O(N) Ceiling:** Despite their mathematical brilliance, LSTMs must read a sentence one word at a time, severely limiting GPU utilization and training scale.

## 4k-7k Prose Capacity Plan

This chapter can support a long narrative only if it is built from verified layers rather than padding:

- 500-800 words: Historical context and setup, bridging from the previous era.
- 933-1233 words: Detailed narrative surrounding The Vanishing Gradient:, heavily anchored to primary sources.
- 933-1233 words: Detailed narrative surrounding The Constant Error Carousel:, heavily anchored to primary sources.
- 933-1233 words: Detailed narrative surrounding The O(N) Ceiling:, heavily anchored to primary sources.
- 400-700 words: Honest close that summarizes the infrastructural shift and transitions to the next chapter.

Most layers now have page-level anchors. Do not invent lab drama or dialogue to reach the top of the range. If the verified evidence runs out, cap the chapter.
