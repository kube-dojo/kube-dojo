# Sources: Chapter 29 - Support Vector Machines

## Verification Legend

- Green: source is strong enough for drafting the stated claim with recorded page anchors.
- Yellow: source is relevant but needs another anchor, access check, or cautious wording.
- Red: claim should remain out of prose until sourced.

## Primary and Near-Primary Sources

| Source | Use | Verification |
|---|---|---|
| Bernhard E. Boser, Isabelle M. Guyon, and Vladimir N. Vapnik, ["A Training Algorithm for Optimal Margin Classifiers"](https://doi.org/10.1145/130385.130401), *Proceedings of the Fifth Annual Workshop on Computational Learning Theory*, 144-152, ACM, 1992. | Origin paper for kernelized optimal-margin classifier training. | Green. p.1 frames the goal as maximizing margin/capacity control for better generalization and says the resulting classifier depends only on supporting patterns; pp.2-4 describe kernel representation, supporting patterns, and quadratic optimization; p.5 discusses support-pattern counts as an effective capacity much smaller than feature-space dimensionality; pp.6-8 report handwritten digit experiments and show high-order polynomial/RBF classifiers with workstation-scale training; p.9 summarizes automatic capacity tuning and support-pattern representation. |
| Corinna Cortes and Vladimir Vapnik, ["Support-Vector Networks"](https://link.springer.com/article/10.1007/BF00994018), *Machine Learning* 20, 273-297, 1995. Local accessible PDF used for page extraction: https://homepages.math.uic.edu/~lreyzin/papers/cortes95.pdf | Mature SVM paper: support-vector network definition, soft margins, kernels, USPS/NIST OCR benchmarks. | Green. p.273 abstract defines support-vector networks, high-dimensional feature mapping, generalization, and extension to non-separable training data; pp.275-276 identify the conceptual and technical high-dimensional problems, support vectors, margin, and dimension-free bound; pp.279-283 define optimal hyperplanes, support vectors, soft margins, and convex/quadratic optimization; p.283 explicitly connects kernels/Potential Functions to Aizerman et al. and Mercer's theorem; pp.287-289 cover USPS and NIST digit experiments, 7,300/2,000 USPS split, 60,000/10,000 NIST split, polynomial results, support-vector counts, LeNet comparison, and 1.1% NIST error; p.296 notes that complexity does not depend on feature-space dimensionality but on support vectors. |
| Vladimir N. Vapnik and Alexey Ya. Chervonenkis, ["On the Uniform Convergence of Relative Frequencies of Events to Their Probabilities"](https://mlanthology.org/misc/1971/vapnik1971misc-uniform/), *Theory of Probability and Its Applications* 16(2), 264-280, 1971. Accessible PDF used for page extraction: https://openeclass.panteion.gr/modules/document/file.php/PMS152/LEARNING/Vapnik%20V.N.%2C%20and%20Chervonenkis%20A.Y.%20%281971%29%20--%20On%20Uniform%20Convergence%20of%20the%20Relative%20Frequencies%20of%20Events%20to%20Their%20Probabilities%2C%20Theory%20of%20Probabilitiy%20and%20Its%20Applications%2C%20vol.%20%2C%20pp.%20264-280%20.pdf | Statistical learning theory/VC lineage. | Green. p.264 states the problem of judging probabilities for an entire class of events from one sample and requiring uniform convergence over that class; pp.265-266 define induced subsamples, system index, and growth function, including half-space examples; pp.271-272 give sufficient distribution-independent conditions, probability bounds, almost-sure uniform convergence, and sample-size framing; pp.276-278 move into necessity and the entropy/growth-condition argument. Use this for the historical claim that SVMs inherited a theory of generalization/capacity, not for a full mathematical derivation. |
| Christopher J. C. Burges, ["A Tutorial on Support Vector Machines for Pattern Recognition"](https://www.microsoft.com/en-us/research/publication/a-tutorial-on-support-vector-machines-for-pattern-recognition/), *Data Mining and Knowledge Discovery* 2, 121-167, 1998. Accessible PDF: https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/svmtutorial.pdf | Secondary/tutorial source for careful explanation of margin, kernels, convexity, implementation, and scaling limits. | Green as explanatory secondary. pp.1-2 frame SVMs as a pattern-recognition method with strong generalization and practical implementation; pp.9-13 explain margins and support vectors; pp.13-15 state the training problem is convex quadratic programming and local solutions are global; pp.20-23 explain kernel mapping and Mercer conditions; pp.29-32 discuss uniqueness/globality; pp.34-36 discuss implementation and large-problem scaling; pp.39-42 discuss VC dimension, margin bounds, and generalization arguments. |

## Optional Context Sources

| Source | Use | Verification |
|---|---|---|
| Léon Bottou et al., "Comparison of Classifier Methods: A Case Study in Handwritten Digit Recognition," *ICPR* 1994. | Benchmark context for OCR comparison against LeNet/classical methods. | Yellow. Cortes/Vapnik 1995 already quotes/summarizes the benchmark sufficiently for core prose; add only if final chapter needs independent comparison-study details. |
| Vladimir N. Vapnik, *The Nature of Statistical Learning Theory*, Springer, 1995. | Broad theory context for capacity, empirical risk, and VC theory. | Yellow. Useful if a clean accessible copy/page anchor is added; not required for current prose contract. |

## Scene-Level Claim Table

| Claim | Scene | Anchor | Status | Notes |
|---|---|---|---|---|
| SVMs addressed post-winter credibility by focusing on generalization/capacity rather than hand-coded rules. | Trust Moved to Generalization | Vapnik/Chervonenkis 1971 pp.264-266, 271-272; Boser et al. 1992 p.1; Cortes/Vapnik 1995 pp.273-276; Burges 1998 pp.1-2 | Green | Interpretive synthesis; phrase as historical framing, not author intent unless quoted. |
| VC theory supplied a way to discuss learning as uniform convergence/generalization over a class, rather than just fitting a finite training set. | Trust Moved to Generalization | Vapnik/Chervonenkis 1971 pp.264-266, 271-272, 276-278; Cortes/Vapnik 1995 pp.275-276; Burges 1998 pp.39-42 | Green | Keep the prose conceptual; avoid deriving the theorem. |
| The maximum-margin hyperplane is defined by the widest margin and a subset of training points called support vectors. | Margin Contract | Cortes/Vapnik 1995 pp.275-279; Burges 1998 pp.9-13 | Green | Good for nontechnical prose explanation. |
| The kernel move allowed high-dimensional decision surfaces without explicitly constructing the high-dimensional feature space. | Kernel Move | Boser et al. 1992 pp.2-4; Cortes/Vapnik 1995 pp.276, 283; Burges 1998 pp.20-23 | Green | Avoid saying Boser invented all kernel methods; Aizerman et al. lineage is in Cortes/Vapnik p.283. |
| Soft margins made SVMs applicable to non-separable real training data. | Soft Margins | Cortes/Vapnik 1995 pp.279-283 | Green | Strong core claim. |
| Convex/quadratic optimization made SVM training feel more controllable than neural networks' local-error-minimization story. | Soft Margins / Why It Mattered | Cortes/Vapnik 1995 pp.279-283; Burges 1998 pp.13-15, 29-32 | Green/Yellow | Green for convex/QP; Yellow for contrast with neural nets unless phrased as historical perception. |
| USPS/NIST OCR gave SVMs benchmark credibility next to LeNet and other methods. | OCR Proof Terrain | Cortes/Vapnik 1995 pp.287-289 | Green | Keep numbers exact: USPS 7,300/2,000 with 16x16 images; NIST 60,000/10,000 with 28x28 images; NIST 1.1% test error for the reported 4th-degree polynomial multiclass setup built from one-vs-rest binary classifiers. LeNet comparison figures must be attributed in prose as Cortes and Vapnik's report; if the LeNet comparison exceeds about 150 words, anchor Bottou et al. first. |
| SVMs ended neural networks in the 1990s. | Any | None | Red | Do not claim. SVMs became highly credible; neural nets continued and later deep learning scaled. |

## Conflict Notes

- Do not present SVMs as anti-neural or as the final winner over neural networks.
- Do not claim Boser/Guyon/Vapnik invented kernels from nothing; Cortes/Vapnik p.283 explicitly references Aizerman, Braverman, and Rozonoer (1964) and Mercer's theorem.
- Do not over-explain modern SVM usage. Keep the chapter historical: 1990s statistical learning, OCR benchmarks, and post-winter credibility.
- Do not turn the VC-theory anchor into a theorem derivation. The page anchors support conceptual prose about uniform convergence, capacity, and generalization; they do not require technical proof in the chapter.
- Do not conflate USPS, NIST, and later MNIST; Cortes/Vapnik's NIST benchmark is not the same as the later MNIST standard in Ch27.

## Page Anchor Worklist

- Resolved: clean Vapnik/Chervonenkis 1971 PDF extracted for conceptual VC-theory lineage.
- Optional: add Bottou et al. 1994/1995 page anchors if prose leans heavily on the benchmark comparison quote.
- Ask Gemini whether the current Boser/Cortes/Burges anchors support 4,000-5,500 words or whether Ch29 needs additional AT&T/Bell Labs context before drafting.
