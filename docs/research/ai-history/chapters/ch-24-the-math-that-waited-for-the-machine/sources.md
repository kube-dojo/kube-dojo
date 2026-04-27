# Sources: Chapter 24 - The Math That Waited for the Machine

## Verification Key

- Green: claim has primary evidence plus independent confirmation.
- Yellow: claim has one strong source or unresolved attribution nuance.
- Red: claim should not be drafted yet.

## Primary Sources

| Source | Use | Verification |
|---|---|---|
| David E. Rumelhart, Geoffrey E. Hinton, Ronald J. Williams, "Learning representations by back-propagating errors," *Nature* 323, 533-536, 1986. DOI: `10.1038/323533a0`. URL: https://www.nature.com/articles/323533a0 | Anchor the public 1986 breakthrough, hidden-unit/internal-representation claim, and contrast with perceptron-style learning. | Green for core claims: p.533 abstract states repeated weight adjustment to minimize output error, hidden units representing task-domain features, and contrast with perceptron-convergence; p.533 also says perceptron feature analyzers were not true hidden units because their input connections were fixed by hand; pp.533-535 give the forward/backward derivative pass and symmetry/family-tree demonstrations; p.536 explicitly says the current learning procedure is not a plausible model of learning in brains. Yellow only for priority/invention claims. |
| David E. Rumelhart, Geoffrey E. Hinton, Ronald J. Williams, "Learning Internal Representations by Error Propagation," in *Parallel Distributed Processing*, Vol. 1, MIT Press, 1986. URL: https://gwern.net/doc/ai/nn/fully-connected/1986-rumelhart.pdf | Longer technical version for examples, algorithm description, and the PDP framing around internal representations. | Green for detailed drafting anchors: pp.318-320 frame why networks without hidden units lack internal representations and cite Minsky/Papert's hidden-unit/recoding point; pp.326-327 give the generalized delta rule, recursive error signal, forward pass, backward pass, and same-complexity claim; pp.328-329 introduce simulation results and the logistic activation function; pp.340-341 give the symmetry task and learned two-hidden-unit solution; pp.337-340 can support encoder/problem examples if needed. |
| Paul J. Werbos, *Beyond Regression: New Tools for Prediction and Analysis in the Behavioral Sciences*, Harvard PhD thesis, 1974/1975. URL: https://gwern.net/doc/ai/nn/1974-werbos.pdf | Prior-art anchor for adapting dynamic systems by propagating derivatives backward. | Green/Yellow: Green for prior derivative machinery on pp.II-23-II-26 and pp.II-33-II-34, which define ordered derivatives/dynamic feedback, calculate derivatives backwards down an ordered table, and state that all derivatives can be calculated in one pass; pp.II-83-II-86 formalize the ordered derivative and chain-rule recurrence. Yellow for direct transmission to 1986 neural-network work; no transmission evidence found. |
| Seppo Linnainmaa, "Taylor Expansion of the Accumulated Rounding Error," *BIT Numerical Mathematics* 16, 146-160, 1976. DOI: `10.1007/BF01931367`. | Automatic-differentiation lineage: reverse accumulation of derivatives before neural-network popularization. | Yellow until full source/page access is verified. |
| Francis Crick, "The recent excitement about neural networks," *Nature* 337, 129-132, 1989. DOI: `10.1038/337129a0`. URL: https://www.nature.com/articles/337129a0 | Contemporary critique for biological plausibility and over-reading artificial neural networks as brain models. | Green for abstract/standfirst-level critique: Nature page and article metadata state that recent neural-network algorithms seemed to promise a fresh approach to brain computation, but that most of these neural nets were unrealistic in important respects. Full article PDF/text remains unavailable through the tested route, so detailed internal passages still need access before stronger claims. |
| Marvin Minsky and Seymour Papert, *Perceptrons*, MIT Press, 1969. | Background source for why the field cared about the limits of perceptron-style learning and hidden-layer training. | Yellow; core source belongs to Ch17, but Chapter 24 needs cross-reference anchors. |

## Secondary and Context Sources

| Source | Use | Verification |
|---|---|---|
| Andreas Griewank, "Who Invented the Reverse Mode of Differentiation?", *Documenta Mathematica*, Extra Volume ISMP, 389-400, 2012. URL: https://ems.press/books/dms/251/4949 | Historical survey for reverse-mode automatic differentiation and priority nuance around Linnainmaa and earlier adjoint/reverse-mode ideas. | Green for AD-history context: p.389 says reverse-mode ideas had multiple incarnations since the late 1960s or earlier and names Linnainmaa 1976 as round-off-error motivation; p.390 links Werbos to forward/reverse propagation of derivatives for discrete time-dependent problems; pp.393-395 describe Linnainmaa's computational graph, adjoints/impact factors, and reverse-mode recurrence; pp.397-398 explain cheap gradients and memory/checkpointing issues. |
| Yann LeCun, Yoshua Bengio, Geoffrey Hinton, "Deep learning," *Nature* 521, 436-444, 2015. URL: https://www.nature.com/articles/nature14539 | Retrospective technical framing: backpropagation changes internal parameters and enables layered representation learning. | Green for modern consensus framing. |
| Yann LeCun, Leon Bottou, Genevieve B. Orr, Klaus-Robert Mueller, "Efficient BackProp," in *Neural Networks: Tricks of the Trade*, 1998. URL: https://cs.nyu.edu/~yann/2006f-G22-2565-001/diglib/lecun-98b.pdf | Later engineering view of why raw backprop needed scaling, initialization, normalization, and conditioning tricks. | Yellow for Chapter 24; mostly useful as bridge to Ch27. |
| Michael Nielsen, "How the backpropagation algorithm works," 2014. URL: https://michaelnielsen.org/ddi/how-the-backpropagation-algorithm-works/ | Pedagogical support for explaining gradients without turning the chapter into a textbook. | Yellow; secondary teaching source only. |
| Geoffrey Hinton Reddit response quoted in 2020 backprop priority discussions. URL: https://www.reddit.com/r/artificial/comments/g6ypng | Useful conflict note: Hinton explicitly distinguishes invention of versions of backprop from making internal representation learning persuasive. | Yellow; use only as a conflict note, not as a scholarly anchor. |

## Scene-Level Claim Table

| Claim | Scene | Primary Anchor | Independent Confirmation | Status | Notes |
|---|---|---|---|---|---|
| The 1986 Nature paper described repeated weight adjustment to minimize output error and make hidden units represent task regularities. | PDP Demonstration | Rumelhart/Hinton/Williams 1986 Nature | LeCun/Bengio/Hinton 2015 | Yellow | Strong enough for prose. |
| Backpropagation's key mechanism is efficient chain-rule reuse over a layered computation, not a mysterious brain-like force. | Chain Rule Becomes Machinery | PDP chapter pp.326-327 | Nielsen 2014; LeCun et al. 1998 | Yellow | PDP chapter gives the forward pass/backward pass and recursive hidden-unit error signal. |
| Werbos described a related backward derivative method before the 1986 neural-network revival. | Chain Rule Becomes Machinery | Werbos thesis pp.II-23-II-26, II-33-II-34, II-83-II-86 | Griewank 2012 p.390 | Green/Yellow | Green for earlier derivative machinery; Yellow for transmission to PDP. |
| Reverse-mode automatic differentiation predates the PDP revival. | Chain Rule Becomes Machinery | Linnainmaa 1976 | Griewank 2012 pp.389, 393-395 | Yellow | Use Griewank as the history anchor unless Linnainmaa full text is later obtained. |
| The breakthrough was historically important because it trained hidden layers after the perceptron era had made single-layer limits salient. | Frozen Hidden Layer | Nature 1986 p.533; PDP chapter pp.318-320 | Minsky/Papert cited by PDP; LeCun/Bengio/Hinton 2015 | Green/Yellow | Green for PDP's Minsky/Papert bridge; Yellow only for direct Ch17 cross-link because Ch17 source file is currently skeletal. |
| Backprop was not biologically settled or obviously brain-plausible. | Delayed Infrastructure Fit | Nature 1986 p.536; Crick 1989 Nature standfirst | LeCun/Bengio/Hinton 2015 for engineering framing | Green/Yellow | Green for the general caveat; Yellow for detailed Crick-internal claims until full article access. |
| A 4k-7k chapter is feasible without padding if it uses separate evidence layers: perceptron context, backprop mechanism, prior art, PDP demonstration, compute limits, and biological caveats. | All | This source table | Chapter brief prose-capacity plan | Green/Yellow | Feasible up to about 5k now; longer stretch still needs hardware/computing-environment source. |

## Conflict Notes

- Priority is disputed. The safest formulation is: earlier derivative machinery existed; Werbos connected backward derivatives to trainable systems; Rumelhart/Hinton/Williams popularized and demonstrated backpropagation for neural-network internal representations.
- "Invented backpropagation" should not appear in prose unless qualified.
- The chapter should not imply that 1986 systems were large by modern standards. The drama is algorithmic and infrastructural: the method made hidden-layer learning executable, but the hardware still limited depth, data, and experiment scale.

## Page Anchor Worklist

- Nature 1986: Done for hidden-unit/internal-representation, perceptron-convergence contrast, algorithm sketch, demonstrations, and biological-plausibility caveat on pp.533-536.
- PDP chapter: Done for internal-representation problem, generalized delta rule/backward pass, simulation framing, symmetry task, and optional encoder task on pp.318-320, 326-329, and 337-341.
- Werbos thesis: Done for ordered derivative/dynamic feedback and backward derivative propagation on pp.II-23-II-26, II-33-II-34, and II-83-II-86; transmission to PDP remains unproven.
- Linnainmaa/Griewank: Griewank 2012 done for reverse-mode lineage and Linnainmaa priority context on pp.389-395 and 397-398; Linnainmaa 1976 full text still optional.
- Minsky/Papert: PDP chapter pp.318-320 includes the needed bridge; Ch17 remains skeletal and should later add the direct source.
- Crick 1989: Nature standfirst/metadata anchors the critique at article level; full internal passage access still needed for stronger claims.
