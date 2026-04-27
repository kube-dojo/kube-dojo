# Brief: Chapter 47 - The Depths of Vision

## Thesis
Following AlexNet, researchers assumed deeper networks would automatically yield better results, but they hit an optimization wall: deeper networks had higher training errors. ResNet solved this by introducing skip connections, allowing gradient information to bypass layers and enabling networks to scale to hundreds of layers deep.

## Scope
- IN SCOPE: Kaiming He, the 2015 ResNet paper, the degradation problem, skip connections/residual learning.
- OUT OF SCOPE: Early CNNs (Part 5), Vision Transformers (Part 8).

## Scenes Outline
1. **The Depth Wall:** Researchers find that stacking 50 layers performs worse than 20 layers, not due to overfitting, but due to optimization failure (vanishing gradients).
2. **The Identity Mapping:** Kaiming He and the Microsoft Research team propose that layers should learn the *residual* mapping rather than the original unreferenced mapping.
3. **The Skip Connection:** The physical infrastructure of a neural network is rewired to allow data to jump past layers, enabling 152-layer networks to win ILSVRC 2015.

## 4k-7k Prose Capacity Plan

This chapter can support a long narrative only if it is built from verified layers rather than padding:

- 500-800 words: Historical context and setup, bridging from the previous era.
- 933-1233 words: Detailed narrative surrounding The Depth Wall:, heavily anchored to primary sources.
- 933-1233 words: Detailed narrative surrounding The Identity Mapping:, heavily anchored to primary sources.
- 933-1233 words: Detailed narrative surrounding The Skip Connection:, heavily anchored to primary sources.
- 400-700 words: Honest close that summarizes the infrastructural shift and transitions to the next chapter.

Most layers now have page-level anchors. Do not invent lab drama or dialogue to reach the top of the range. If the verified evidence runs out, cap the chapter.
