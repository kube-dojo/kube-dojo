# Sources: Chapter 27 - The Convolutional Breakthrough

## Verification Legend

- Green: source is strong enough for drafting the stated claim once page/section anchors are recorded.
- Yellow: source is relevant but needs exact passage extraction, access verification, or corroboration.
- Red: claim should not be drafted except as an open question.

## Primary Sources

| Source | Use | Verification |
|---|---|---|
| Kunihiko Fukushima, "Neocognitron: A self-organizing neural network model for a mechanism of pattern recognition unaffected by shift in position," *Biological Cybernetics* 36, 193-202, 1980. DOI: `10.1007/BF00344251`. | Architectural prehistory for hierarchical, shift-tolerant visual recognition. | Green for lineage anchors: p.193 abstract/introduction describes self-organization, geometric-similarity recognition, S-cells/C-cells, hierarchy, and position tolerance; p.194 frames hierarchy, widening receptive fields, and position-invariant recognition; pp.197-198 explain C-cell response under shifted input; p.199 explains cascade modules, wider receptive fields, and last-layer position tolerance. |
| Yann LeCun, Bernhard Boser, John S. Denker, Donnie Henderson, Richard E. Howard, Wayne Hubbard, Lawrence D. Jackel, "Backpropagation Applied to Handwritten Zip Code Recognition," *Neural Computation* 1(4), 541-551, 1989. DOI: `10.1162/neco.1989.1.4.541`. URL: https://direct.mit.edu/neco/article/1/4/541/5515/Backpropagation-Applied-to-Handwritten-Zip-Code | Core primary source for domain constraints, backpropagation, and U.S. Postal Service handwritten zip-code digits. | Green for core claims: p.541 states task-domain constraints, USPS zip-code digits, and end-to-end normalized-image-to-classification framing; p.542 gives Buffalo USPS data, 7,291/2,007 train/test split, contractor location/segmentation, 16x16 normalization, and adaptive network setup; pp.544-546 describe feature maps, local receptive fields, weight sharing, undersampling, architecture, and 9,760 independent parameters; pp.547-550 provide SUN-4/260 training, 23 passes, 5.0% raw test error, 12.1% rejection for 1% error, three-day training comparison, DSP/PC implementation, and 10-12 classifications/sec. Official PDF endpoint returned 403 during extraction; page anchors were verified against a mirrored MIT PDF copy. |
| Yann LeCun, Bernhard Boser, John S. Denker, Donnie Henderson, Richard E. Howard, Wayne Hubbard, Lawrence D. Jackel, "Handwritten digit recognition with a back-propagation network," *Advances in Neural Information Processing Systems 2*, 396-404, 1990. URL: https://proceedings.neurips.cc/paper/1989/hash/53c3bce66e43be4f209556518c2fcb54-Abstract.html | Conference version/context for handwritten digit recognition and early network architecture. | Green as corroborating/expanded conference account: p.396 states minimal preprocessing, constrained architecture, normalized isolated digits, and 1% error/about 9% reject on USPS zipcode digits; p.397 gives 9,298 handwritten Buffalo USPS numerals plus printed-font augmentation and train/test splits; pp.398-400 detail contractor preprocessing, 16x16 normalization, local receptive fields, convolutional feature maps, shared weights, subsampling, and neocognitron/backprop distinction; pp.402-403 record SUN SPARCstation 1/SN2 training, AT&T DSP-32C implementation, 10-12 classifications/sec including acquisition, and more than 30/sec on normalized digits. |
| Yann LeCun, Leon Bottou, Yoshua Bengio, Patrick Haffner, "Gradient-Based Learning Applied to Document Recognition," *Proceedings of the IEEE* 86(11), 2278-2324, 1998. DOI: `10.1109/5.726791`. URL: https://bottou.org/papers/lecun-98h | Mature LeNet/document-recognition synthesis, including LeNet-5 and bank-check/document-processing framing. | Green for LeNet-5 and document-system anchors: p.2278 abstract frames document systems as field extraction, segmentation, recognition, and language modeling, and states a commercial bank-check GTN system reads several million checks per day; p.2279 introduction ties progress to large databases, fast machines, LeNet-5, NCR check-recognition systems, and millions of checks per month; pp.2283-2284 define convolutional networks, LeNet-5, local receptive fields, shared weights, subsampling, parameter reduction, and the Fukushima lineage; pp.2286-2287 describe MNIST construction from NIST SD-1/SD-3 and 60,000/10,000 split; pp.2291-2292 give LeNet-5 compute/training context and why LeNet-5 was not considered in 1989; pp.2296-2298 describe segmentation graphs, GTN character-string recognition, and Viterbi interpretation; pp.2304-2305 describe avoiding explicit segmentation by sweeping/replicating convolutional recognizers. |

## Secondary and Context Sources

| Source | Use | Verification |
|---|---|---|
| Yann LeCun, Yoshua Bengio, Geoffrey Hinton, "Deep learning," *Nature* 521, 436-444, 2015. URL: https://www.nature.com/articles/nature14539 | Retrospective context for convolutional nets and representation learning. | Yellow; use for broad framing only. |
| The MNIST database of handwritten digits, maintained by Yann LeCun, Corinna Cortes, and Christopher J. C. Burges. URL: https://yann.lecun.com/exdb/mnist/ | Dataset/context source for later standardized handwritten-digit benchmark; not the same as the original USPS story. | Yellow; use carefully to avoid anachronism. |
| Leon Bottou publication page for LeCun et al. 1998. URL: https://bottou.org/papers/lecun-98h | Stable bibliographic/PDF route for the 1998 paper. | Green as access/bibliographic support, not independent analysis. |
| Jürgen Schmidhuber, "Deep learning in neural networks: An overview," *Neural Networks* 61, 85-117, 2015. DOI: `10.1016/j.neunet.2014.09.003`. | Broad historical overview; useful only as a cross-check for lineage and priority cautions. | Yellow; secondary and opinionated, use sparingly. |

## Scene-Level Claim Table

| Claim | Scene | Primary Anchor | Secondary Anchor | Status | Notes |
|---|---|---|---|---|---|
| Fukushima's neocognitron is important architectural prehistory for hierarchical, shift-tolerant visual recognition. | From Neocognitron to Backprop | Fukushima 1980, pp.193-194, 197-199 | Later retrospectives | Green | Do not call it LeNet or a backprop-trained CNN; frame it as hierarchy, S/C cells, and shift-tolerant lineage. |
| LeCun et al. showed that task-domain constraints built into a backpropagation network improved handwritten zip-code recognition. | The Postal Code Laboratory | LeCun et al. 1989, pp.541-546 | LeCun et al. 1990, pp.396-400 | Green | Strong primary anchors for domain constraints, feature maps, local receptive fields, weight sharing, and reduced free parameters. |
| The U.S. Postal Service digit data made the 1989 task concrete and industrially meaningful. | The Postal Code Laboratory | LeCun et al. 1989, p.542 | LeCun et al. 1990, pp.397-398 | Green | Keep chronology clean: USPS/Buffalo zip-code digits precede later MNIST benchmark construction. |
| LeNet-5/document recognition belongs to a production pipeline story involving preprocessing, segmentation, and engineering, not an isolated neural net. | Checks, Throughput, and Engineering | LeCun et al. 1998, pp.2278-2279, 2296-2298, 2304-2305 | Bottou page; later retrospectives | Green | Production scale is now anchored for the 1998 check system; distinguish check-system deployment from the 1989 USPS digit recognizer. |
| Convolutional networks became historically powerful because architecture reduced the search problem that generic multilayer networks left too unconstrained. | Pixels With Structure | LeCun et al. 1989, pp.541, 544-546; LeCun et al. 1998, pp.2283-2284, 2291-2292 | LeCun/Bengio/Hinton 2015 | Green | Interpretive synthesis is supported by parameter-reduction, prior-knowledge, and compute-context anchors; draft cautiously. |

## Conflict Notes

- Do not claim LeNet was the first convolutional neural network without a strong qualifier and source.
- Do not conflate MNIST with the original USPS zip-code dataset.
- Do not invent deployment scale. LeCun et al. 1998 supports "several million checks per day" on p.2278 and "millions of checks per month" in NCR systems on p.2279; do not transfer those figures to the 1989 USPS digit recognizer.
- Do not make the chapter a modern CNN tutorial. The historical point is constrained architecture meeting a real document pipeline.

## Page Anchor Worklist

- Fukushima 1980: Done for hierarchy, S/C cells, shift tolerance, and cascade-position tolerance on pp.193-194 and pp.197-199.
- LeCun et al. 1989: Done for domain constraints, USPS/Buffalo data, normalization, feature maps/weight sharing, training, performance, and DSP throughput on pp.541-550.
- LeCun et al. 1990: Done for network architecture, USPS/printed-font augmentation, preprocessing, training/hardware, and throughput on pp.396-403.
- LeCun et al. 1998: Done for LeNet-5 architecture, check/document-recognition pipeline, deployment/throughput, MNIST construction, compute context, and GTN/segmentation passages on pp.2278-2279, 2283-2287, 2291-2292, 2296-2298, and 2304-2305.
- MNIST page: Still useful as an external dataset page, but LeCun et al. 1998 already anchors the NIST-to-MNIST construction well enough for prose.
