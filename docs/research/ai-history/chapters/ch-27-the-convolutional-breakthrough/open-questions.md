# Open Questions: Chapter 27 - The Convolutional Breakthrough

## Must Resolve Before `reviewing`

- Confirm whether the mirrored MIT PDF used for LeCun et al. 1989 extraction is acceptable for page anchors when the official MIT PDF endpoint returns 403, or whether another library-access copy should be used before prose lock.
- Decide whether the chapter needs Denker et al. 1988/1989 as additional Bell Labs lineage, or whether LeCun 1989/1990 plus Fukushima 1980 provide enough pre-LeNet grounding.
- Decide how much of the 1998 GTN/check-recognition pipeline belongs in this chapter versus a later systems/deployment chapter. The anchors are strong, but the prose should not let GTNs displace the convolutional breakthrough story.

## Nice To Resolve

- Whether an archival Bell Labs video/demo source is acceptable as supporting color if primary paper anchors already cover claims.
- Whether to include a small LeNet-5 architecture diagram in the eventual prose.
- Whether to cite the MNIST web page directly for reader convenience, even though LeCun et al. 1998 already anchors the NIST-to-MNIST dataset construction.

## Resolved Anchors

- Fukushima 1980: pp.193-194 establish self-organization, hierarchy, S-cells/C-cells, and position-invariant recognition; pp.197-199 show how shifted patterns and cascading S/C modules support position tolerance.
- LeCun et al. 1989: p.541 frames task-domain constraints and USPS zip-code recognition; p.542 anchors Buffalo USPS data, contractor preprocessing, 16x16 normalization, and train/test split; pp.544-546 anchor feature maps, local receptive fields, weight sharing, undersampling, and parameter counts; pp.547-550 anchor training, raw/rejection results, SUN-4/260 environment, DSP implementation, and throughput.
- LeCun et al. 1990: pp.396-400 corroborate minimal preprocessing, USPS/printed-font data, constrained architecture, feature maps, convolution, shared weights, subsampling, and neocognitron/backprop contrast; pp.402-403 anchor SPARCstation/SN2 training and AT&T DSP-32C throughput.
- LeCun et al. 1998: pp.2278-2279 anchor document systems, check-recognition deployment, and NCR context; pp.2283-2284 define LeNet-5 and convolutional architecture; pp.2286-2287 anchor MNIST construction from NIST; pp.2291-2292 anchor compute/training context; pp.2296-2298 and 2304-2305 anchor GTN/segmentation and replicated convolutional recognizers.

## Human/Agent Collaboration Notes

- Deployment details are now anchored for the 1998 bank-check system, but not for the 1989 USPS digit recognizer. Keep those timelines separate.
- A responsible 4k-6k draft is now plausible if the chapter is structured as architecture plus data plus document pipeline. Do not pad with a modern CNN tutorial.
