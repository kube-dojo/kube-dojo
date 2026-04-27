# Scene Sketches: Chapter 30 - The Statistical Underground

## Scene 1: Speech After the Rule Boom

Open with speech as a domain where uncertainty is intrinsic: a waveform has to become phonetic evidence, then words, then a sentence. The chapter should connect to Ch28/Ch29 without repeating them: post-winter credibility meant measurable performance, and speech forced measurement because every recognition attempt produced errors.

Evidence anchors:
- Bahl/Jelinek/Mercer 1983 p.179.
- IBM Research page for Jelinek 1976 abstract only.

## Scene 2: The Noisy-Channel Decomposition

Present the speech recognizer as a pipeline with a text generator, speaker, acoustic processor, and linguistic decoder. The historical importance is the decomposition: language model probability and acoustic-channel probability together decide the most likely word string.

Evidence anchors:
- Bahl/Jelinek/Mercer 1983 pp.179-180.

## Scene 3: Markov Models Make Search Possible

Explain Markov-source modeling at a high level: a system of states and transition probabilities can generate candidate strings. Then show why decoding needs algorithms. Viterbi and stack search are not decorative math; they are the machinery that lets the system avoid enumerating every possible sentence.

Evidence anchors:
- Bahl/Jelinek/Mercer 1983 pp.180-185.
- Rabiner 1989 PDF p.8.

## Scene 4: Sparse Data Becomes the Central Enemy

The statistical approach did not magically turn data into certainty. It exposed a new engineering problem: most useful language-model events are rare or unseen. Use the IBM laser patent corpus and trigram/sparse-data discussion to show why smoothing/interpolation mattered.

Evidence anchors:
- Bahl/Jelinek/Mercer 1983 p.186.
- Bahl/Jelinek/Mercer 1983 pp.188-189 for perplexity and reported task results.

## Scene 5: HMMs Become a Shared Toolkit

By 1989, Rabiner could write a tutorial because HMMs had become a shared technical language. Use the three HMM problems as a simple structure: score a model, find a state path, train parameters. Then include limitations so the section does not become triumphalist.

Evidence anchors:
- Rabiner 1989 PDF pp.1-2.
- Rabiner 1989 PDF p.5.
- Rabiner 1989 PDF p.8.
- Rabiner 1989 PDF p.28.

## Scene 6: From IBM to Sphinx and Statistical NLP

Close by showing diffusion rather than a single lab victory. CMU Sphinx demonstrates large-vocabulary, speaker-independent HMM work in DARPA-style evaluations. IBM statistical machine translation shows the same probabilistic culture crossing into text: n-grams, parameter estimation, alignments, and minimal hand linguistic content.

Evidence anchors:
- Huang/Hon/Lee 1989 PDF pp.1, 3-4.
- Huang/Alleva/Hwang/Rosenfeld 1993 PDF pp.1, 5-6.
- Brown et al. 1990 pp.79-80.
- Brown et al. 1993 pp.263-264.
