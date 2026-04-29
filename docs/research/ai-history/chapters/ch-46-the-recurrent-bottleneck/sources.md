# Sources: Chapter 46 - The Recurrent Bottleneck

## Verification Key

- **Green**: claim has a page, section, DOI+page, or stable primary-source anchor, with independent confirmation where available.
- **Yellow**: source is credible but the specific claim is not page-located, is broader than the anchor, or depends on a source not fully extracted.
- **Red**: no verifiable anchor yet; do not draft as fact.

Shell note: direct `curl` attempts failed in this sandbox with DNS resolution errors. Anchors below were verified through accessible PDF/HTML text where available; claims that depend only on snippets or bibliographic records are kept narrow.

## Primary Sources

| ID | Source | Use | Verification |
|---|---|---|---|
| P1 | Sepp Hochreiter and Jurgen Schmidhuber, "Long Short-Term Memory," *Neural Computation* 9(8), 1735-1780, 1997. DOI: `10.1162/neco.1997.9.8.1735`. Open PDF: https://www.bioinf.jku.at/publications/older/2604.pdf | Anchor for the vanishing/exploding-error diagnosis, LSTM, constant error carousel, input/output gates, complexity, and >1000-step artificial long-lag result. | **Green**. PDF text verified via browser extraction: abstract on PDF p. 0 / journal p. 1735; Hochreiter 1991 analysis outline on PDF pp. 2-4; CEC discussion on PDF pp. 4-5; algorithm complexity and error-flow appendix on PDF pp. 26-28. |
| P2 | Yoshua Bengio, Patrice Simard, and Paolo Frasconi, "Learning long-term dependencies with gradient descent is difficult," *IEEE Transactions on Neural Networks* 5(2), 157-166, 1994. DOI: `10.1109/72.279181`. | Anchor for the independent 1994 statement that gradient learning becomes harder as dependency duration increases. | **Green for abstract-level claims on p. 157** from PubMed/CiNii bibliographic record and abstract. Full PDF page extraction not available in this sandbox; do not use interior-page claims. |
| P3 | Felix A. Gers, Jurgen Schmidhuber, and Fred Cummins, "Learning to Forget: Continual Prediction with LSTM," *Neural Computation* 12(10), 2451-2471, 2000. DOI: `10.1162/089976600300015015`. | Anchor for the adaptive forget gate and the weakness of unreset continual LSTM streams. | **Green for abstract-level claims on p. 2451** via MIT Press/PubMed/CiNii records. Full article interior not extracted; keep claims at abstract level unless full PDF is retrieved. |
| P4 | Alex Graves, Abdel-rahman Mohamed, and Geoffrey Hinton, "Speech Recognition with Deep Recurrent Neural Networks," ICASSP 2013, pp. 6645-6649. DOI: `10.1109/ICASSP.2013.6638947`; arXiv:1303.5778. | Anchor for deep LSTM RNNs in speech recognition and the 17.7% TIMIT phoneme error claim. | **Green for paper abstract / p. 6645 claim** from open abstract and bibliographic records. Full PDF page extraction not completed. |
| P5 | Ilya Sutskever, Oriol Vinyals, and Quoc V. Le, "Sequence to Sequence Learning with Neural Networks," NeurIPS 2014. PDF mirror: https://www.cs.cmu.edu/~jeanoh/16-785/papers/sutskever-nips2014-rnn-mt.pdf; arXiv:1409.3215. | Anchor for LSTM seq2seq, reverse-source trick, 4-layer deep LSTMs, 8-GPU parallelization, words/sec, and ten-day training. | **Green**. PDF text verified: abstract and introduction on PDF pp. 1-2; model and reverse-source discussion on pp. 2-4; training/parallelization on pp. 4-5; BLEU tables on p. 5. |
| P6 | Yonghui Wu et al., "Google's Neural Machine Translation System: Bridging the Gap between Human and Machine Translation," arXiv:1609.08144, 2016. PDF: https://arxiv.org/pdf/1609.08144 | Anchor for GNMT as a production NMT system built from deep LSTM encoder/decoder stacks, residual connections, attention, model parallelism, wordpieces, and low-precision inference. | **Green**. PDF text verified: abstract and introduction on pp. 1-2; model architecture on pp. 3-4; model parallelism constraints on pp. 6-7. |
| P7 | Ashish Vaswani et al., "Attention Is All You Need," arXiv:1706.03762, 2017. PDF: https://arxiv.org/pdf/1706.03762; HTML: https://arxiv.org/html/1706.03762 | Anchor for the recurrent bottleneck: state-of-art recurrent sequence models, sequential computation precluding parallelization, O(n) sequential operations for recurrent layers, Transformer hardware/training comparison. | **Green**. HTML/PDF text verified: Introduction p. 1; "Why Self-Attention" / Table 1 on p. 6; hardware and schedule on p. 7; conclusion on p. 9. |

## Secondary Sources

| ID | Source | Use | Verification |
|---|---|---|---|
| S1 | Ian Goodfellow, Yoshua Bengio, and Aaron Courville, *Deep Learning*, MIT Press, 2016, Chapter 10, https://www.deeplearningbook.org/contents/rnn.html | Secondary framing for vanishing/exploding gradients, gated RNNs, LSTM, forget gate, and LSTM applications. | **Green for section-level anchors**: section 10.7 "The Challenge of Long-Term Dependencies"; section 10.10.1 "LSTM"; section 10.11 "Optimization for Long-Term Dependencies." |
| S2 | Jurgen Schmidhuber, "Deep Learning in Neural Networks: An Overview," *Neural Networks* 61, 85-117, 2015. DOI: `10.1016/j.neunet.2014.09.003`. | Possible secondary history for LSTM lineage and deep-learning context. | Yellow. Useful but not needed for the anchored capacity plan. Pull exact pages only if prose wants broader retrospective framing. |

## Scene-Level Claim Table

| ID | Claim | Scene | Primary Anchor | Independent Confirmation | Status | Notes |
|---|---|---|---|---|---|---|
| G1 | Conventional BPTT/RTRL training in recurrent networks faces error signals that can vanish or blow up across long time lags. | 1 | P1, PDF p. 0 / journal p. 1735 abstract; PDF pp. 2-4 outlines Hochreiter's 1991 analysis and exponential vanishing/blow-up. | S1 section 10.7 | **Green** | Safe to explain without deriving every equation. |
| G2 | Bengio, Simard, and Frasconi independently argued that gradient-based learning becomes increasingly difficult as the duration of dependencies increases, exposing a trade-off between efficient gradient learning and robust long-term storage. | 1 | P2, *IEEE TNN* 5(2), p. 157 abstract, DOI `10.1109/72.279181`. | S1 section 10.7 cites Bengio et al. 1994. | **Green** | Abstract-level only; do not cite interior experiments without PDF extraction. |
| G3 | Hochreiter and Schmidhuber introduced LSTM in 1997 as a gradient-based method addressing insufficient, decaying error backflow. | 2 | P1, PDF p. 0 / journal p. 1735 abstract. | S1 section 10.10.1 | **Green** | Core chapter anchor. |
| G4 | The original LSTM paper claims the architecture can bridge minimal time lags in excess of 1000 discrete steps by enforcing constant error flow through constant error carousels, with multiplicative gates controlling access. | 2 | P1, PDF p. 0 / journal p. 1735 abstract. | S1 section 10.10.1 | **Green** | Keep "artificial tasks" context when drafting. |
| G5 | The constant error carousel is a self-connected, linear memory-cell path with self-connection weight 1.0; the 1997 paper calls it LSTM's central feature. | 2 | P1, PDF pp. 4-5, section 3.2 "Constant Error Flow: Naive Approach." | S1 section 10.10.1 | **Green** | PDF OCR spells "carrousel"; prose may use modern "carousel." |
| G6 | The 1997 LSTM architecture used input and output gates to protect memory content and downstream units; the adaptive forget gate was not part of the original 1997 anchor. | 2, 3 | P1, PDF pp. 5-6 discusses input/output weight conflicts and gates; P3, p. 2451 abstract identifies the forget gate as the 2000 remedy. | S1 section 10.10.1 distinguishes initial LSTM self-loop and Gers et al. 2000 gated self-loop. | **Green** | Important anti-anachronism row. |
| G7 | Gers, Schmidhuber, and Cummins introduced an adaptive forget gate for continual prediction, where unreset internal state could grow indefinitely and break down. | 3 | P3, *Neural Computation* 12(10), p. 2451 abstract, DOI `10.1162/089976600300015015`. | S1 section 10.10.1 | **Green** | Abstract-level; no interior page claims. |
| G8 | Deep LSTM RNNs achieved a 17.7% TIMIT phoneme recognition error in Graves, Mohamed, and Hinton's 2013 speech-recognition paper, which they described as the best recorded score to their knowledge. | 4 | P4, ICASSP 2013 pp. 6645-6649, abstract / p. 6645. | S1 section 10.10.1 lists speech recognition applications. | **Green** | Good for showing LSTMs were practical, not just theoretical. |
| G9 | Sutskever, Vinyals, and Le used a multilayer LSTM encoder and decoder for sequence-to-sequence learning and reported 34.8 BLEU on WMT'14 English-French in the abstract. | 4 | P5, PDF p. 1 abstract. | Vaswani et al. 2017 cites Sutskever et al. as sequence transduction state of art context. | **Green** | Avoid saying this was production Google Translate. |
| G10 | Their model read the input sentence one time step at a time into a vector, then decoded with another LSTM; reversing source sentences reduced the minimal time lag and improved optimization. | 4 | P5, PDF pp. 1-2 for one-time-step reading; p. 4 section 3.3 for reversing and reduced minimal time lag. | S1 sequence-to-sequence discussion | **Green** | This is the narrative hinge between long dependency and engineering workaround. |
| G11 | The 2014 seq2seq implementation used an 8-GPU machine: one GPU per LSTM layer, four GPUs for the softmax, about 6,300 words/sec, and roughly ten days of training. | 4 | P5, PDF p. 4 section 3.5 "Parallelization." | None required; primary systems detail. | **Green** | Strong infrastructure anchor; do not generalize to all LSTMs. |
| G12 | GNMT described NMT systems as computationally expensive in training and inference, sometimes prohibitively for very large datasets and models. | 4 | P6, PDF p. 1 abstract and p. 2 introduction. | Vaswani et al. p. 1 parallelization critique | **Green** | Useful setup for bottleneck. |
| G13 | GNMT used deep LSTM networks with 8 encoder and 8 decoder layers, residual connections, attention, wordpieces, and low-precision inference. | 4 | P6, PDF p. 1 abstract; p. 2 introduction. | P6 architecture details pp. 3-4 | **Green** | Use as production-era LSTM system, not as "pure LSTM." |
| G14 | GNMT partitioned encoder and decoder layers across multiple GPUs; the authors explicitly describe model-parallelism constraints, including why all encoder layers could not be bidirectional without reducing GPU parallelism. | 4, 5 | P6, PDF pp. 4 and 6, Figure 1 caption and section 3.3. | None required; primary systems detail. | **Green** | This row supports infrastructure-log details. |
| G15 | In 2017, Vaswani et al. described recurrent, LSTM, and GRU models as firmly established state-of-the-art approaches in sequence modeling/transduction such as language modeling and machine translation. | 5 | P7, PDF p. 1 / HTML Introduction. | P5 and P6 as examples | **Green** | Limit to the tasks listed by the paper. |
| G16 | Vaswani et al. state that recurrent models factor computation along symbol positions and that the inherently sequential nature precludes parallelization within training examples, especially at longer sequence lengths. | 5 | P7, PDF p. 1 / HTML Introduction. | P6 model-parallelism constraints | **Green** | The chapter's title claim. |
| G17 | Vaswani et al.'s Table 1 compares layer types and lists recurrent layers as requiring O(n) sequential operations, while self-attention requires O(1) sequential operations. | 5 | P7, PDF p. 6 / HTML section 4 "Why Self-Attention." | P7 introduction | **Green** | Keep solution detail brief; Ch50 owns the Transformer. |
| G18 | Vaswani et al. trained the base Transformer for 100,000 steps / 12 hours and the big model for 300,000 steps / 3.5 days on one machine with 8 NVIDIA P100 GPUs. | 5 | P7, PDF p. 7 section 5.2 "Hardware and Schedule." | P7 conclusion p. 9 says Transformer trains faster than recurrent/convolutional alternatives for translation tasks. | **Green** | Use as contrast only; do not make this chapter a Transformer chapter. |
| G19 | Vaswani et al. concluded the Transformer replaced commonly used recurrent encoder-decoder layers with multi-headed self-attention and trained significantly faster for translation tasks. | 5 | P7, PDF p. 9 conclusion. | P7 abstract / p. 1 | **Green** | Forward-reference Ch50. |
| G20 | Later deep LSTM systems still needed extra training aids: Sutskever et al. used gradient norm clipping; GNMT used residual connections to improve gradient flow in deep stacks. | 4 | P5, PDF p. 4 training details; P6, PDF p. 4 residual connections. | S1 section 10.11 on optimization | **Green** | Prevents overclaiming "LSTM solved gradients completely." |
| Y1 | Hochreiter's 1991 diploma thesis contains the original vanishing-gradient analysis with exact pp. 19-21. | 1 | P1 summarizes the thesis and cites pp. 19-21, but the thesis itself was not retrieved. | S1 section 10.7 | Yellow | Do not cite thesis pages directly unless the thesis is fetched. |
| Y2 | LSTMs were the dominant architecture for "sequence data" broadly across all text and audio domains before Transformers. | 4, 5 | P7 supports state of art for language modeling and machine translation; P4 supports one speech benchmark. | S1 lists applications. | Yellow | Too broad as written. Use narrower Green task-specific claims. |
| Y3 | cuDNN or vendor kernels had specific recurrent-network GPU-utilization limits before Transformers. | 5 | None extracted. | None. | Yellow | A systems source may exist, but not anchored here. |
| Y4 | Exact hardware and runtime of Hochreiter and Schmidhuber's 1997 experiments. | 2 | P1 has experiments but no extracted machine/runtime anchor. | None. | Yellow | Keep original LSTM infrastructure generic unless pages are extracted. |
| R1 | Engineers in 2015 observed expensive GPUs sitting at "20% utilization" because LSTM could not parallelize across sequence positions. | 5 | None. | None. | Red | Removed from scene plan. Needs primary systems source or deletion. |
| R2 | A specific internal Google decision to replace LSTMs with Transformers because of GNMT training cost. | 5 | None. | None. | Red | Ch50 may have sources; not available here. |
| R3 | Exact deployment scale, traffic volume, or production latency of GNMT. | 4 | P6 gives methods and evaluation, not deployment volume. | None. | Red | Do not invent production scale. |

## Page Anchor Worklist

### Done

- Hochreiter & Schmidhuber 1997: abstract, problem statement, Hochreiter 1991 summary, CEC, complexity, and appendix error-flow anchors.
- Sutskever, Vinyals & Le 2014: abstract, one-time-step LSTM reading, reverse-source trick, 8-GPU parallelization, words/sec, ten-day training.
- Wu et al. 2016 GNMT: abstract, architecture, model-parallelism constraints, residual connections, low-precision inference.
- Vaswani et al. 2017: Introduction bottleneck, Table 1 / section 4, hardware schedule, conclusion.

### Still Useful

- Full PDF extraction for Bengio, Simard & Frasconi 1994 beyond abstract p. 157.
- Full PDF extraction for Gers, Schmidhuber & Cummins 2000 beyond abstract p. 2451.
- A primary cuDNN/NVIDIA or systems paper on recurrent-kernel utilization and sequence-length constraints.
- Page-anchored source for the hardware used in the original 1997 LSTM experiments.

## Open Items for Cross-Family Review

- Is `3k-5k likely` the right cap, or should this be `2k-4k natural` unless a GPU-systems source is added?
- Are P2/P3 abstract-only Green rows acceptable for the contract, or should they be downgraded to Yellow until full PDF text is extracted?
- Should the chapter include attention-with-RNN bridge papers such as Bahdanau et al. 2014, or reserve that for Ch47/Ch50 to avoid scope creep?
