# Open Questions: Chapter 29 - Support Vector Machines

## Scrub Status

- Upstream scrub note: all previous placeholder claims were downgraded to Yellow until backed by real empirical page/section anchors from verified online PDFs or archives.
- Current Codex pass resolves the core scrub for Vapnik/Chervonenkis 1971, Boser/Guyon/Vapnik 1992, Cortes/Vapnik 1995, and Burges 1998 with page-level anchors in `sources.md`.
- Remaining Yellow items are intentionally narrow: optional Bottou OCR context and optional Vapnik book context.

## Must Resolve Before Prose

- Resolved after Gemini gap review: add clean Vapnik/Chervonenkis 1971 page anchors before prose. Source now appears as Green in `sources.md`.
- Should Bottou et al. 1994/1995 be added for independent OCR benchmark context, or is Cortes/Vapnik 1995 enough because it contains the comparison details needed for Ch29?
- How much contrast with neural networks is safe? Current contract supports "SVMs looked more controlled and benchmark-ready," not "neural networks were defeated."

## Optional Expansion Paths

- Add a short Bell Labs/AT&T scene if sources support why OCR was such a fertile benchmark terrain.
- Add a small optimization-infrastructure paragraph on quadratic programming packages and chunking if the prose needs more capacity.
- Add a later handoff note to why deep learning eventually regained the lead with data/compute scale.

## Do Not Draft Without Support

- "SVMs solved overfitting." Safer: SVMs supplied margin/capacity-control tools and performed strongly on benchmark tasks.
- "Kernels were invented in 1992." Safer: Boser/Guyon/Vapnik made the kernelized maximum-margin training algorithm central to SVMs; Aizerman et al. and Mercer are part of the lineage.
- "The NIST result is MNIST." Keep NIST/MNIST chronology separate.
