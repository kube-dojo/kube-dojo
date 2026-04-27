# OCR Excerpts: Chapter 17 - The Perceptron's Fall

This file records OCR verification points so later agents do not need to
rediscover the same scanned-page anchors. It is not a replacement for the
source PDFs in `sources.md`.

## Olazaran 1996

Source: Mikel Olazaran, "A Sociological Study of the Official History of the
Perceptrons Controversy," *Social Studies of Science* 26(3), 611-659 (1996).
PDF used: `https://gwern.net/doc/ai/1996-olazaran.pdf`.

OCR command used locally:

```bash
ocrmypdf --force-ocr /tmp/ch17-sources/olazaran-1996.pdf /tmp/ch17-sources/olazaran-1996-forceocr.pdf
pdftotext -layout /tmp/ch17-sources/olazaran-1996-forceocr.pdf /tmp/ch17-sources/olazaran-1996-forceocr.txt
```

Verified page anchors:

- p.613: official-history framing says the neural-net approach was treated as
  impossible/abandoned, but Olazaran argues that interpretation emerged through
  controversy closure and neural nets were not completely abandoned.
- p.629: strict proof boundary. Minsky/Papert showed limits for single-layer
  nets defined in a certain way; multilayer pessimism was a conjecture about
  learning.
- pp.630-631: parity is connected to XOR, but the broader order-growth argument
  also includes connectedness.
- pp.637-638: ARPA/ONR funding context, including Denicoff interview and Guice's
  ARPA-focused work.
- pp.640-641: abandonment narrative is exaggerated; neural-net work continued
  outside mainstream AI.

## Rosenblatt 1961

Source: Frank Rosenblatt, *Principles of Neurodynamics: Perceptrons and the
Theory of Brain Mechanisms* (1961).
PDF used:
`https://lucidar.me/en/neural-networks/files/1961-principles-of-neurodynamics-perceptrons-and-the-theory-of-brain-mechanisms.pdf`.

OCR command used locally:

```bash
pdftotext -layout /tmp/ch17-sources/rosenblatt-1961.pdf /tmp/ch17-sources/rosenblatt-1961.txt
```

Verified page anchors:

- p.5: Part II covers three-layer series-coupled "minimal perceptrons"; Part III
  covers multilayer and cross-coupled perceptrons, with the theory still
  incomplete.
- pp.94-95: Part II begins by defining three-layer series-coupled perceptrons
  and describing their learning capabilities and deficiencies.
- pp.303-308: Rosenblatt summarizes three-layer systems as universal in
  principle but practically limited by size, learning time, generalization,
  analysis, and dependence on external evaluation.
- pp.575-576: summary claims a three-layer series-coupled perceptron is a
  minimal system; adding a fourth layer or cross-coupling is claimed to improve
  generalization and detailed pattern recognition.
