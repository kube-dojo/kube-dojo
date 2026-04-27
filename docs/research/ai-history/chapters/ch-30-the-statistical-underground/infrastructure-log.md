# Infrastructure Log: Chapter 30 - The Statistical Underground

## Computational and Data Constraints

| Constraint | Evidence Anchor | Narrative Use |
|---|---|---|
| Continuous speech creates a large search space over word strings and acoustic evidence. | Bahl/Jelinek/Mercer 1983 pp.179-180. | Motivates probabilistic decoding rather than hand enumeration. |
| Acoustic processors compressed waveforms into outputs suitable for statistical characterization. | Bahl/Jelinek/Mercer 1983 p.180. | Keeps the chapter grounded in signal-processing infrastructure, not abstract NLP only. |
| Markov-source models represented language/acoustic generation with states and transition probabilities. | Bahl/Jelinek/Mercer 1983 pp.180-183. | Shows why finite-state/probabilistic structure mattered. |
| Viterbi dynamic programming and stack/graph search were needed to make decoding tractable. | Bahl/Jelinek/Mercer 1983 pp.183-185; Rabiner 1989 PDF p.8. | Turns "AI" into search engineering under uncertainty. |
| Sparse trigram events forced smoothing/interpolation and held-out estimation. | Bahl/Jelinek/Mercer 1983 p.186; p.190 sparse-data reference. | Gives a concrete reason statistical language modeling was hard before huge corpora. |
| Perplexity measured task difficulty better than vocabulary size alone in the IBM experiments. | Bahl/Jelinek/Mercer 1983 pp.188-189. | Lets prose explain why language modeling needed information-theoretic metrics. |
| Sphinx-style systems needed training sentences, speaker sets, acoustic features, codebooks, and language models. | Huang/Hon/Lee 1989 PDF pp.3-4; Huang/Alleva/Hwang/Rosenfeld 1993 PDF pp.1, 5-6. | Shows the hardware/data/evaluation layer without inventing machines or lab scenes. |
| Statistical MT reused the same infrastructure mindset: machine-readable corpora, n-grams, alignments, parameter estimation. | Brown et al. 1990 pp.79-80; Brown et al. 1993 pp.263-264. | Provides a forward link to later NLP. |

## What Not To Invent

- No specific IBM hardware unless a source anchor is added.
- No claims about real-time performance beyond Bahl/Jelinek/Mercer p.179's note that recognition often required many seconds of CPU time per sentence in restricted IBM settings.
- No invented corpus sizes beyond the 1.5 million-word IBM laser patent corpus and Sphinx data counts explicitly anchored in `sources.md`.
- No deployment claims about commercial dictation products.
