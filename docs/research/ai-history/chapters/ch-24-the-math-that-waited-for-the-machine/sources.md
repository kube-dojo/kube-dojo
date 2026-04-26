# Sources: Chapter 24 - The Math That Waited for the Machine

## Verification Key

- Green: claim has primary evidence plus independent confirmation.
- Yellow: claim has one strong source or unresolved attribution nuance.
- Red: claim should not be drafted yet.

## Primary Sources

| Source | Use | Verification |
|---|---|---|
| David E. Rumelhart, Geoffrey E. Hinton, Ronald J. Williams, "Learning representations by back-propagating errors," *Nature* 323, 533-536, 1986. DOI: `10.1038/323533a0`. URL: https://www.nature.com/articles/323533a0 | Anchor the public 1986 breakthrough, hidden-unit/internal-representation claim, and contrast with perceptron-style learning. | Green for publication details and stated contribution; Yellow for priority/invention claims because the paper is not the whole lineage. |
| David E. Rumelhart, Geoffrey E. Hinton, Ronald J. Williams, "Learning Internal Representations by Error Propagation," in *Parallel Distributed Processing*, Vol. 1, MIT Press, 1986, pp. 318-362. URL: https://gwern.net/doc/ai/nn/fully-connected/1986-rumelhart.pdf | Longer technical version for examples, algorithm description, and the PDP framing around internal representations. | Green for PDP framing; page anchors still needed before prose lock. |
| Paul J. Werbos, *Beyond Regression: New Tools for Prediction and Analysis in the Behavioral Sciences*, Harvard PhD thesis, 1974/1975. URL: https://gwern.net/doc/ai/nn/1974-werbos.pdf | Prior-art anchor for adapting dynamic systems by propagating derivatives backward. | Yellow until exact pages are extracted; important for avoiding false invention claims. |
| Seppo Linnainmaa, "Taylor Expansion of the Accumulated Rounding Error," *BIT Numerical Mathematics* 16, 146-160, 1976. DOI: `10.1007/BF01931367`. | Automatic-differentiation lineage: reverse accumulation of derivatives before neural-network popularization. | Yellow until full source/page access is verified. |
| Francis Crick, "The recent excitement about neural networks," *Nature* 337, 129-132, 1989. DOI: `10.1038/337129a0`. URL: https://www.nature.com/articles/337129a0 | Contemporary critique for biological plausibility and over-reading artificial neural networks as brain models. | Yellow until exact passages are anchored; resolves the prior Red gap enough for cautious drafting. |
| Marvin Minsky and Seymour Papert, *Perceptrons*, MIT Press, 1969. | Background source for why the field cared about the limits of perceptron-style learning and hidden-layer training. | Yellow; core source belongs to Ch17, but Chapter 24 needs cross-reference anchors. |

## Secondary and Context Sources

| Source | Use | Verification |
|---|---|---|
| Andreas Griewank, "Who Invented the Reverse Mode of Differentiation?", *Documenta Mathematica*, Extra Volume ISMP, 389-400, 2012. URL: https://ems.press/books/dms/251/4949 | Historical survey for reverse-mode automatic differentiation and priority nuance around Linnainmaa and earlier adjoint/reverse-mode ideas. | Green for AD-history context; still needs exact page anchors before prose lock. |
| Yann LeCun, Yoshua Bengio, Geoffrey Hinton, "Deep learning," *Nature* 521, 436-444, 2015. URL: https://www.nature.com/articles/nature14539 | Retrospective technical framing: backpropagation changes internal parameters and enables layered representation learning. | Green for modern consensus framing. |
| Yann LeCun, Leon Bottou, Genevieve B. Orr, Klaus-Robert Mueller, "Efficient BackProp," in *Neural Networks: Tricks of the Trade*, 1998. URL: https://cs.nyu.edu/~yann/2006f-G22-2565-001/diglib/lecun-98b.pdf | Later engineering view of why raw backprop needed scaling, initialization, normalization, and conditioning tricks. | Yellow for Chapter 24; mostly useful as bridge to Ch27. |
| Michael Nielsen, "How the backpropagation algorithm works," 2014. URL: https://michaelnielsen.org/ddi/how-the-backpropagation-algorithm-works/ | Pedagogical support for explaining gradients without turning the chapter into a textbook. | Yellow; secondary teaching source only. |
| Geoffrey Hinton Reddit response quoted in 2020 backprop priority discussions. URL: https://www.reddit.com/r/artificial/comments/g6ypng | Useful conflict note: Hinton explicitly distinguishes invention of versions of backprop from making internal representation learning persuasive. | Yellow; use only as a conflict note, not as a scholarly anchor. |

## Scene-Level Claim Table

| Claim | Scene | Primary Anchor | Independent Confirmation | Status | Notes |
|---|---|---|---|---|---|
| The 1986 Nature paper described repeated weight adjustment to minimize output error and make hidden units represent task regularities. | PDP Demonstration | Rumelhart/Hinton/Williams 1986 Nature abstract and pp. 533-536 | LeCun/Bengio/Hinton 2015 | Green | Safe to draft once exact page references are added. |
| Backpropagation's key mechanism is efficient chain-rule reuse over a layered computation, not a mysterious brain-like force. | Chain Rule Becomes Machinery | PDP chapter algorithm sections | Nielsen 2014; LeCun et al. 1998 | Yellow | Needs exact PDP section/page anchors. |
| Werbos described a related backward derivative method before the 1986 neural-network revival. | Chain Rule Becomes Machinery | Werbos thesis | Hinton priority note; later histories | Yellow | Do not overstate as direct adoption unless evidence supports transmission. |
| Reverse-mode automatic differentiation predates the PDP revival. | Chain Rule Becomes Machinery | Linnainmaa 1976 | AD histories still to verify | Yellow | Need a stable secondary history of AD before Green. |
| The breakthrough was historically important because it trained hidden layers after the perceptron era had made single-layer limits salient. | Frozen Hidden Layer | Rumelhart/Hinton/Williams contrast with perceptron-convergence procedure | Minsky/Papert source belongs in Ch17; LeCun/Bengio/Hinton 2015 | Yellow | Requires cross-link to Ch17 research. |
| Backprop was not biologically settled or obviously brain-plausible. | Delayed Infrastructure Fit | Crick 1989 | LeCun/Bengio/Hinton 2015 for engineering framing | Yellow | Gemini identified Crick as the canonical contemporary critique; extract exact passages before prose lock. |
| A 4k-7k chapter is feasible without padding if it uses separate evidence layers: perceptron context, backprop mechanism, prior art, PDP demonstration, compute limits, and biological caveats. | All | This source table | Chapter brief prose-capacity plan | Yellow | Feasibility claim depends on resolving page anchors, not just listing sources. |

## Conflict Notes

- Priority is disputed. The safest formulation is: earlier derivative machinery existed; Werbos connected backward derivatives to trainable systems; Rumelhart/Hinton/Williams popularized and demonstrated backpropagation for neural-network internal representations.
- "Invented backpropagation" should not appear in prose unless qualified.
- The chapter should not imply that 1986 systems were large by modern standards. The drama is algorithmic and infrastructural: the method made hidden-layer learning executable, but the hardware still limited depth, data, and experiment scale.

## Page Anchor Worklist

- Nature 1986: extract one anchor for the hidden-unit/internal-representation claim and one for the perceptron-convergence contrast.
- PDP chapter: extract one anchor for the algorithm walkthrough and one for a concrete demonstration/task.
- Werbos thesis: extract exact pages for backward derivative propagation and note whether the terminology maps cleanly to later neural-network backpropagation.
- Linnainmaa 1976 and Griewank 2012: verify exact pages for reverse accumulation and priority history.
- Minsky/Papert: identify the specific passage that sets up the hidden-layer training problem so this chapter does not re-litigate Ch17.
- Crick 1989: extract the specific critique of biological realism/plausibility and cite it before drafting any claim about brains.
