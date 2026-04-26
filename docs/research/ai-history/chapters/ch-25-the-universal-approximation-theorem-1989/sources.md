# Sources: Chapter 25 - The Universal Approximation Theorem (1989)

## Verification Legend

- Green: source is strong enough for drafting the stated claim once page/section anchors are recorded.
- Yellow: source is relevant but needs exact passage extraction, access verification, or corroboration.
- Red: claim should not be drafted except as an open question.

## Primary Sources

| Source | Use | Verification |
|---|---|---|
| George Cybenko, "Approximation by superpositions of a sigmoidal function," *Mathematics of Control, Signals, and Systems* 2, 303-314, 1989. DOI: `10.1007/BF02551274`. URL: https://link.springer.com/article/10.1007/BF02551274 | Core theorem: finite sums of sigmoidal units can uniformly approximate continuous functions on the unit hypercube, under stated conditions. | Green for bibliographic anchor and abstract-level claim; page anchors still needed before prose lock. |
| Kurt Hornik, Maxwell Stinchcombe, Halbert White, "Multilayer feedforward networks are universal approximators," *Neural Networks* 2(5), 359-366, 1989. DOI: `10.1016/0893-6080(89)90020-8`. | Parallel 1989 result; useful for showing the theorem was part of a broader representational turn, not a one-paper miracle. | Yellow until full text/page anchors are verified. |
| Ken-ichi Funahashi, "On the approximate realization of continuous mappings by neural networks," *Neural Networks* 2(3), 183-192, 1989. DOI: `10.1016/0893-6080(89)90003-8`. URL: https://math.bu.edu/people/mkon/MA751/FunahashiTheorem.pdf | Parallel 1989 result about continuous mappings and three-layer networks; helps avoid an overly US-centric or single-author account. | Yellow; PDF access found, exact page anchors needed. |
| A. N. Kolmogorov, "On the representation of continuous functions of many variables by superposition of continuous functions of one variable and addition," *Doklady Akademii Nauk SSSR* 114, 953-956, 1957. | Mathematical prehistory; only use to explain why "superposition" and multivariable approximation were older mathematical concerns. | Yellow; should be mediated by a survey unless exact translation/source is obtained. |

## Secondary and Context Sources

| Source | Use | Verification |
|---|---|---|
| Allan Pinkus, "Approximation theory of the MLP model in neural networks," *Acta Numerica* 8, 143-195, 1999. DOI: `10.1017/S0962492900002919`. URL: https://www.cambridge.org/core/journals/acta-numerica/article/approximation-theory-of-the-mlp-model-in-neural-networks/18072C558C8410C4F92A82BCC8FC8CF9 | Sober survey of approximation-theoretic results and open problems; useful to discipline the slogan "networks approximate anything." | Green for survey role; page anchors still needed. |
| Andrew R. Barron, "Universal approximation bounds for superpositions of a sigmoidal function," *IEEE Transactions on Information Theory* 39(3), 930-945, 1993. DOI: `10.1109/18.256500`. | Canonical follow-up for approximation-rate/efficiency bounds; anchors the distinction between bare existence and how costly approximation may be. | Yellow until exact passages are extracted; use as afterlife/efficiency context, not as the 1989 event. |
| Moshe Leshno, Vladimir Ya. Lin, Allan Pinkus, Shimon Schocken, "Multilayer feedforward networks with a nonpolynomial activation function can approximate any function," *Neural Networks* 6(6), 861-867, 1993. DOI: `10.1016/S0893-6080(05)80131-5`. | Later condition-cleanup: nonpolynomial activation functions; use only as afterlife/precision, not as 1989 event. | Yellow until full text/anchors are verified. |
| L. G. Valiant, "A theory of the learnable," *Communications of the ACM* 27(11), 1134-1142, 1984. | Background distinction between representability and learnability; useful if the chapter needs a compact way to explain why approximation does not equal learning. | Yellow; use cautiously and keep it as context, not neural-network-specific proof. |

## Scene-Level Claim Table

| Claim | Scene | Primary Anchor | Secondary Anchor | Status | Notes |
|---|---|---|---|---|---|
| Cybenko proved a one-hidden-layer sigmoidal network family is dense enough to uniformly approximate continuous functions on compact/unit-hypercube domains under stated conditions. | Existence, Not Recipe | Cybenko 1989 | Pinkus 1999 | Green | Phrase with the actual mathematical conditions; do not say "any function" without qualifiers. |
| Hornik/Stinchcombe/White and Funahashi published related 1989 universal-approximation results. | The 1989 Cluster | Hornik/Stinchcombe/White 1989; Funahashi 1989 | Pinkus 1999 | Yellow | Need exact passage/page anchors before making a priority narrative. |
| The theorem addressed representation capacity, not the ability to train a useful finite network from data. | A Useful Misunderstanding | Cybenko 1989 scope; Hornik/Stinchcombe/White 1989 scope | Pinkus 1999; Valiant 1984 context | Yellow | This is the chapter's most important caveat; source it tightly. |
| The theorem mattered historically because it helped counter the perception that neural networks were intrinsically too weak after perceptron-era limitations. | The Aftertaste of Perceptrons | Cybenko references Minsky/Papert and PDP context | Ch17 research; Pinkus 1999 | Yellow | Needs cross-chapter anchor from Ch17. |
| Universal approximation became a durable slogan that can mislead if detached from optimization, sample complexity, approximation rates, and compute. | A Useful Misunderstanding | The theorem papers' limited claims | Pinkus 1999; Barron 1993; Leshno et al. 1993 | Yellow | This is interpretation from source limits, not a direct quotation. |

## Conflict Notes

- Do not write "the Universal Approximation Theorem proved neural networks can solve any problem." It proved approximation capacity under mathematical restrictions.
- Do not credit a single author as "the" inventor without explaining the 1989 cluster and earlier Kolmogorov-Arnold background.
- Do not imply the theorem caused the 1990s neural-network revival alone. It was one legitimacy layer beside backpropagation, better benchmarks, and improving compute.
- Do not turn the proof into a textbook chapter. The narrative job is to show what kind of doubt the theorem removed and what kind it left intact.

## Page Anchor Worklist

- Cybenko 1989: extract abstract/theorem statement pages and any passage discussing decision regions or neural-network relevance.
- Hornik/Stinchcombe/White 1989: extract theorem statement and any passage emphasizing nonconstant bounded continuous activation functions or multilayer feedforward networks.
- Funahashi 1989: extract abstract/theorem statement and the network-depth conditions.
- Pinkus 1999: extract survey passages that distinguish approximation-theoretic results from unresolved questions.
- Barron 1993: extract rate/efficiency passages that sharpen the existence-versus-size caveat.
- Kolmogorov 1957: decide whether to cite directly or through Pinkus to avoid weak translation sourcing.
