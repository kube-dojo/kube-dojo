# Sources: Chapter 50 - Attention Is All You Need

## Verification Key

- Green: claim has primary evidence plus independent confirmation or internally corroborating paper sections/tables.
- Yellow: claim has one strong source, a narrow attribution nuance, or useful context not yet independently confirmed.
- Red: claim should not be drafted except as a myth or blocked framing.

## Primary Sources

| Source | Use | Verification |
|---|---|---|
| Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser, Illia Polosukhin, "Attention Is All You Need," arXiv:1706.03762 / NeurIPS 2017. URL: https://arxiv.org/pdf/1706.03762 | Core source for the Transformer architecture, the motivation to remove recurrence, scaled dot-product attention, multi-head attention, positional encoding, WMT results, and 8-P100 training setup. | Green for core claims: Abstract states the model is based solely on attention mechanisms and dispenses with recurrence and convolutions; Section 1 says recurrent models' inherently sequential computation precludes parallelization within training examples and that the Transformer relies entirely on attention; Section 2 says it is the first transduction model relying entirely on self-attention without sequence-aligned RNNs or convolution; Sections 3.1-3.5 define encoder/decoder stacks, decoder masking, scaled dot-product attention, multi-head attention, and positional encoding; Section 4/Table 1 compare self-attention, recurrence, and convolution by complexity, sequential operations, and path length; Section 5.2 states training on one machine with 8 NVIDIA P100 GPUs, 12 hours for base models and 3.5 days for big models; Section 6.1/Table 2 give WMT BLEU and training-cost comparison; the equal-contribution footnote anchors team-contribution facts. |
| Dzmitry Bahdanau, Kyunghyun Cho, Yoshua Bengio, "Neural Machine Translation by Jointly Learning to Align and Translate," arXiv:1409.0473, 2014/2015. URL: https://arxiv.org/pdf/1409.0473 | Pre-Transformer attention source: fixed-vector encoder-decoder bottleneck, learned soft alignment, and attention as a solution inside a recurrent model. | Green for predecessor framing: Abstract and Introduction state that conventional encoder-decoder models compress the source sentence into a fixed-length vector and that this may be difficult for long sentences; the paper proposes learning to align and translate jointly. Sections 3.1-3.2 describe an attention/annotation mechanism that avoids encoding the whole input into a single fixed-length vector and lets the decoder retrieve source-side information selectively. Conclusion restates that the approach relieves the encoder of encoding all information into one fixed-length vector. |
| Ilya Sutskever, Oriol Vinyals, Quoc V. Le, "Sequence to Sequence Learning with Neural Networks," arXiv:1409.3215 / NIPS 2014. URL: https://arxiv.org/pdf/1409.3215 | Baseline sequence-to-sequence source: LSTM encoder-decoder using a fixed-dimensional vector, reversed source order, WMT 2014 result, and multi-GPU training constraints. | Green for immediate predecessor framing: Abstract and Introduction describe a multilayer LSTM reading an input sequence into a fixed-dimensional vector and decoding the target sequence; Section 2 describes reading input one timestep at a time and reversing source order; the paper reports WMT 2014 BLEU and notes a single GPU was too slow, so training was parallelized across an 8-GPU machine. Yellow only for direct comparison to the Transformer unless quoted through Vaswani et al. Table 2. |

## Secondary and Context Sources

| Source | Use | Verification |
|---|---|---|
| Alexander M. Rush, "The Annotated Transformer," Harvard NLP, 2018. URL: http://nlp.seas.harvard.edu/annotated-transformer/ | Pedagogical support for explaining the architecture in prose and code terms. | Yellow; useful teaching companion only, not a substitute for the 2017 paper. |
| Lilian Weng, "Attention? Attention!" 2018. URL: https://lilianweng.github.io/posts/2018-06-24-attention/ | Secondary explainer for attention taxonomy and intuition. | Yellow; use sparingly for pedagogy after primary anchors are in place. |
| Wikipedia pages on Transformer, attention, and neural machine translation. | Discovery aid only for finding names, chronology, and source leads. | Yellow/Red for citation: do not use as a prose anchor unless a claim is independently verified in primary or stronger secondary sources. |

## Scene-Level Claim Table

| Claim | Scene | Primary Anchor | Independent Confirmation | Status | Notes |
|---|---|---|---|---|---|
| Before the Transformer, recurrent and LSTM/GRU encoder-decoder models were established sequence-transduction approaches. | Recurrent Bottleneck | Vaswani 2017 Section 1; Sutskever 2014 Abstract/Introduction | Bahdanau 2014 Introduction | Green | This can open the chapter without overstating that RNNs were the only possible architecture. |
| Recurrent models factor computation along sequence positions, creating an inherently sequential dependency that limits parallelization within a training example. | Recurrent Bottleneck | Vaswani 2017 Section 1 | Sutskever 2014 Section 2 one-timestep LSTM framing | Green | Use "limits" or "precludes parallelization within training examples" for the specific dependency; avoid "cannot use GPUs." |
| Attention existed before the Transformer and was commonly combined with recurrent networks. | Attention Before the Transformer | Bahdanau 2014 Abstract/Sections 3.1-3.2; Vaswani 2017 Section 1 | Sutskever 2014 fixed-vector baseline as contrast | Green | Important to avoid implying the 2017 paper invented attention. |
| Bahdanau attention addressed the fixed-vector bottleneck by allowing selective retrieval from source-side annotations/alignment. | Attention Before the Transformer | Bahdanau 2014 Abstract, Introduction, Sections 3.1-3.2, Conclusion | Vaswani 2017 cites attention as already integral | Green | Good evidence layer for a 600-850 word predecessor scene. |
| The Transformer retained the encoder-decoder sequence-transduction frame but used stacked self-attention and point-wise feed-forward layers instead of recurrence. | Architecture Swap | Vaswani 2017 Sections 1, 2, 3.1 | Vaswani 2017 Conclusion | Green | Precise enough for prose. |
| The decoder is still autoregressive and uses masking to prevent positions from attending to future positions. | Architecture Swap | Vaswani 2017 Section 3 and Section 3.2.3 | Figure 1/Figure 2 architecture description | Green | Blocks the unsafe "all tokens generated simultaneously" simplification. |
| Scaled dot-product attention packs queries, keys, and values into matrices and computes attention for a set of queries simultaneously. | Why Matrix Hardware Cared | Vaswani 2017 Section 3.2.1 | Rush 2018 for pedagogy only | Green | Equation can be explained verbally; do not overuse math. |
| Dot-product attention is faster and more space-efficient in practice than additive attention because it can use optimized matrix multiplication code. | Why Matrix Hardware Cared | Vaswani 2017 Section 3.2.1 | Hardware/training metrics in Vaswani 2017 Sections 4-5 | Green/Yellow | Green for the paper's claim; Yellow for broad GPU generalization beyond the paper. |
| Multi-head attention runs several projected attention operations in parallel and lets the model attend to different representation subspaces/positions. | Architecture Swap | Vaswani 2017 Section 3.2.2 | Figure 2 | Green | Good pedagogical scene anchor. |
| Because the model contains no recurrence or convolution, positional encodings are added to provide sequence-order information. | Architecture Swap | Vaswani 2017 Section 3.5 | Table 3 row on learned vs sinusoidal encoding | Green | Avoid saying the Transformer ignores order. |
| Table 1's comparison is the cleanest technical anchor: self-attention has O(1) sequential operations per layer, while recurrent layers require O(n), with caveats about sequence length and representation dimensionality. | Why Matrix Hardware Cared | Vaswani 2017 Section 4/Table 1 | Section 1's bottleneck motivation | Green | Use with caveat: self-attention can become expensive for very long sequences. |
| The paper's reported hardware was one machine with 8 NVIDIA P100 GPUs; base models trained for 12 hours and big models for 3.5 days. | Measured Break | Vaswani 2017 Section 5.2 | Abstract/Section 6.1 report training time/results | Green | Strong infrastructure anchor. |
| The big Transformer reached 28.4 BLEU on WMT 2014 English-German and the paper reports state-of-the-art translation quality at lower training cost than prior competitive models. | Measured Break | Vaswani 2017 Abstract; Section 6.1/Table 2 | Section 5.2 hardware/schedule | Green | For English-French, prefer the exact table/section wording to avoid abstract/table mismatches. |
| The author footnote can support limited team-role statements. | Architecture Swap | Vaswani 2017 equal-contribution footnote | Author affiliations on title page | Green/Yellow | Green for what the footnote says; Yellow for motivations, meetings, emotions, or lab narrative beyond it. |
| A 4,000-5,200 word chapter is feasible without padding if it uses the predecessor-attention layer, architecture pedagogy, hardware/complexity layer, and measured WMT break. | All | This source table and brief capacity plan | Ch24/Ch25 contract pattern | Green/Yellow | Stretch beyond 5.2k requires more primary team/deployment history. |

## Conflict Notes

- Do not write that the Transformer "invented attention." Bahdanau et al. is the necessary predecessor.
- Do not write that the Transformer processes every output token simultaneously at generation time. The decoder is autoregressive and masked.
- Do not write that the architecture "perfectly aligns" with GPUs. Safer: it reduced recurrent sequential dependencies and used matrix-friendly operations that trained well on the reported 8-P100 setup.
- Do not write private lab scenes unless a source is added. The contribution footnote is the available team-history anchor.
- Keep "first" claims narrow: the paper says, to the authors' knowledge, the first transduction model relying entirely on self-attention without sequence-aligned RNNs or convolution.

## Page/Section Anchor Worklist

- Vaswani 2017: Done for abstract, author footnote, Sections 1-4, 5.2, 6.1, Table 1, Table 2, Table 3, and Conclusion.
- Bahdanau 2014: Done for abstract, fixed-vector bottleneck in Introduction, attention/annotation mechanism in Sections 3.1-3.2, and Conclusion.
- Sutskever 2014: Done for abstract/introduction, fixed-dimensional vector, reversed source order, one-timestep LSTM framing, and 8-GPU training note.
- Optional expansion: find a sourced oral history or interview about the Google Brain/Research collaboration before raising the cap above roughly 5,200 words.
