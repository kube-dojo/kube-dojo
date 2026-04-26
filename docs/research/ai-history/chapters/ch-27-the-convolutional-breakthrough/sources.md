# Sources: Chapter 27 - The Convolutional Breakthrough

## Verification Legend

- Green: source is strong enough for drafting the stated claim once page/section anchors are recorded.
- Yellow: source is relevant but needs exact passage extraction, access verification, or corroboration.
- Red: claim should not be drafted except as an open question.

## Primary Sources

| Source | Use | Verification |
|---|---|---|
| Kunihiko Fukushima, "Neocognitron: A self-organizing neural network model for a mechanism of pattern recognition unaffected by shift in position," *Biological Cybernetics* 36, 193-202, 1980. DOI: `10.1007/BF00344251`. | Architectural prehistory for hierarchical, shift-tolerant visual recognition. | Yellow until exact passages are extracted. |
| Yann LeCun, Bernhard Boser, John S. Denker, Donnie Henderson, Richard E. Howard, Wayne Hubbard, Lawrence D. Jackel, "Backpropagation Applied to Handwritten Zip Code Recognition," *Neural Computation* 1(4), 541-551, 1989. DOI: `10.1162/neco.1989.1.4.541`. URL: https://direct.mit.edu/neco/article/1/4/541/5515/Backpropagation-Applied-to-Handwritten-Zip-Code | Core primary source for domain constraints, backpropagation, and U.S. Postal Service handwritten zip-code digits. | Green for bibliographic/abstract-level claims; page anchors needed. |
| Yann LeCun, Bernhard Boser, John S. Denker, Donnie Henderson, Richard E. Howard, Wayne Hubbard, Lawrence D. Jackel, "Handwritten digit recognition with a back-propagation network," *Advances in Neural Information Processing Systems 2*, 396-404, 1990. URL: https://proceedings.neurips.cc/paper/1989/hash/53c3bce66e43be4f209556518c2fcb54-Abstract.html | Conference version/context for handwritten digit recognition and early network architecture. | Yellow; need exact PDF/page anchors. |
| Yann LeCun, Leon Bottou, Yoshua Bengio, Patrick Haffner, "Gradient-Based Learning Applied to Document Recognition," *Proceedings of the IEEE* 86(11), 2278-2324, 1998. DOI: `10.1109/5.726791`. URL: https://bottou.org/papers/lecun-98h | Mature LeNet/document-recognition synthesis, including LeNet-5 and bank-check/document-processing framing. | Green for source authority; exact deployment/hardware passages needed. |

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
| Fukushima's neocognitron is important architectural prehistory for hierarchical, shift-tolerant visual recognition. | From Neocognitron to Backprop | Fukushima 1980 | Later retrospectives | Yellow | Do not call it LeNet or a backprop-trained CNN. |
| LeCun et al. showed that task-domain constraints built into a backpropagation network improved handwritten zip-code recognition. | The Postal Code Laboratory | LeCun et al. 1989 | LeCun et al. 1990 | Green | MIT abstract directly supports domain-constraint framing; page anchors still needed. |
| The U.S. Postal Service digit data made the 1989 task concrete and industrially meaningful. | The Postal Code Laboratory | LeCun et al. 1989 | MNIST/USPS context still to verify | Yellow | Need exact dataset/source details before prose. |
| LeNet-5/document recognition belongs to a production pipeline story involving preprocessing, segmentation, and engineering, not an isolated neural net. | Checks, Throughput, and Engineering | LeCun et al. 1998 | Bottou page; later retrospectives | Yellow | Must extract exact operational claims and avoid unsupported throughput numbers. |
| Convolutional networks became historically powerful because architecture reduced the search problem that generic multilayer networks left too unconstrained. | Pixels With Structure | LeCun et al. 1989; LeCun et al. 1998 | LeCun/Bengio/Hinton 2015 | Yellow | Interpretive synthesis; source carefully. |

## Conflict Notes

- Do not claim LeNet was the first convolutional neural network without a strong qualifier and source.
- Do not conflate MNIST with the original USPS zip-code dataset.
- Do not invent deployment scale. "Several million checks per day" or similar claims require exact LeCun 1998 page anchors before drafting.
- Do not make the chapter a modern CNN tutorial. The historical point is constrained architecture meeting a real document pipeline.

## Page Anchor Worklist

- Fukushima 1980: extract shift-invariance/hierarchical architecture passages.
- LeCun et al. 1989: extract domain-constraint, USPS data, architecture, and performance passages.
- LeCun et al. 1990: extract network diagram/architecture and training details if available.
- LeCun et al. 1998: extract LeNet-5 architecture, check/document-recognition pipeline, deployment/throughput, and preprocessing passages.
- MNIST page: extract dataset origin details and distinguish from original USPS data.
