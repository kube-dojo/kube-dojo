# Sources: Chapter 26 - Bayesian Networks

## Verification Legend

- Green: source is strong enough for drafting the stated claim once page/section anchors are recorded.
- Yellow: source is relevant but needs exact passage extraction, access verification, or corroboration.
- Red: claim should not be drafted except as an open question.

## Primary Sources

| Source | Use | Verification |
|---|---|---|
| Judea Pearl, "Fusion, propagation, and structuring in belief networks," *Artificial Intelligence* 29(3), 241-288, 1986. DOI: `10.1016/0004-3702(86)90072-X`. URL: https://www.sciencedirect.com/science/article/pii/000437028690072X | Core primary source for belief-network definition, local propagation, and the idea that network links can direct data flow as well as store knowledge. | Green for abstract-level claims on p.241: belief networks as DAGs whose nodes represent propositions/variables, arcs direct dependencies, strengths conditional probabilities, links store knowledge and direct data flow, and singly connected networks permit local propagation with time proportional to the longest path. Full article is closed access per Unpaywall/ScienceDirect; non-abstract page anchors still need library access before prose lock. |
| Judea Pearl, *Probabilistic Reasoning in Intelligent Systems: Networks of Plausible Inference*, Morgan Kaufmann, 1988. URL: https://www.sciencedirect.com/book/9780080514895/probabilistic-reasoning-in-intelligent-systems | Core book source for mature presentation of probabilistic reasoning, Markov/Bayesian networks, and propagation methods. | Green for book structure and publisher description: Chapter 3 covers "Markov and Bayesian Networks" on pp.77-141; Chapter 4 covers "Belief Updating by Network Propagation" on pp.143-237; ScienceDirect description frames belief-network propagation as making semantics-based systems operational through modular declarative inputs, meaningful inferences, and parallel distributed computation. Exact internal passage anchors still need access. |
| Steffen L. Lauritzen and David J. Spiegelhalter, "Local computations with probabilities on graphical structures and their application to expert systems," *Journal of the Royal Statistical Society: Series B* 50(2), 157-224, 1988. DOI: `10.1111/j.2517-6161.1988.tb01721.x`. Stable URL: http://www.jstor.org/stable/2345762 | Independent statistical-graphical-model anchor; useful for showing that local computation with probabilities had a broader expert-system context. | Green for expert-system contrast and local-computation context: p.157 abstract says expert systems commonly use local computations on large sparse networks, non-probabilistic methods had been used for uncertainty, and the paper counters the claim that exact probabilistic methods are computationally infeasible; p.158 names certainty factors in MYCIN, quasi-probabilistic PROSPECTOR, CASNET, and INTERNIST as informal schemes; p.159 states the emphasis on exact probabilistic manipulations in large networks defined by local relationships; p.160 anchors MUNIN, EMG diagnosis, causal network structure, conditional probability tables, and the "Bayes networks" terminology in AI. |
| Gregory F. Cooper, "The computational complexity of probabilistic inference using Bayesian belief networks," *Artificial Intelligence* 42(2-3), 393-405, 1990. DOI: `10.1016/0004-3702(90)90060-D`. | Complexity limit: exact probabilistic inference in Bayesian belief networks can be computationally hard. | Green for complexity guardrail: p.393 abstract states probabilistic inference using belief networks is NP-hard and redirects research toward special-case, average-case, and approximation algorithms; p.394 distinguishes singly connected from multiply connected networks and says large multiply connected networks appear needed in complex domains such as medicine; pp.397-401 give the 3SAT-to-PIBNET construction and NP-hard proof; pp.402-403 discuss restricted diagnostic-system topology, linear-time singly connected cases, and NP-hardness for general/multiply connected networks. |

## Secondary and Context Sources

| Source | Use | Verification |
|---|---|---|
| Eugene Charniak, "Bayesian Networks without Tears," *AI Magazine* 12(4), 50-63, 1991. URL: https://www.cse.unr.edu/~bebis/CS479/Readings/BayesianNetworksWithoutTears.pdf | Accessible tutorial for explaining networks without drowning the chapter in notation. | Green for exposition anchors: p.50 says Bayesian networks had become popular in the AI probability/uncertainty community and adopts Pearl's name; pp.51-52 explain DAGs, random-variable nodes, neighboring probabilities, conditional probability tables, evidence updates, and reduced probability specification; p.59 gives PATHFINDER as medical-diagnosis example and notes IDEAL/HUGIN software; p.62 summarizes the advantage over exponential number specification and the drawback of evaluation time. |
| Richard E. Neapolitan, *Probabilistic Reasoning in Expert Systems: Theory and Algorithms*, Wiley, 1990. | Context source for expert-system framing and early algorithms. | Yellow until bibliographic/access details are verified. |
| David Heckerman, "A Tutorial on Learning with Bayesian Networks," Microsoft Research technical report, 1995/1996. | Later tutorial for separating manual knowledge engineering from learning network structure/parameters. | Yellow; later than chapter period, use only for legacy/clarity. |
| Judea Pearl, "Bayesian Networks," UCLA Cognitive Systems Laboratory technical report / encyclopedia entry, 1995. | Later definitional source if primary book page anchors are hard to access. | Yellow; use only as backup definition, not as event source. |

## Scene-Level Claim Table

| Claim | Scene | Primary Anchor | Secondary Anchor | Status | Notes |
|---|---|---|---|---|---|
| Belief/Bayesian networks represent variables/propositions as nodes in a directed acyclic graph, with arcs encoding direct dependencies and conditional probabilities quantifying them. | The Graph as a Memory Aid | Pearl 1986 p.241 abstract; Pearl 1988 Ch. 3 pp.77-141 | Charniak 1991 pp.51-52 | Green | Pearl 1986 is abstract-level only until full article access is obtained; Charniak gives a usable narrative definition. |
| Pearl's propagation work showed how evidence could be updated locally in singly connected networks, with computation tied to graph structure. | Propagation Instead of Global Recalculation | Pearl 1986 p.241 abstract; Pearl 1988 Ch. 4 pp.143-237 | Charniak 1991 pp.51-52, 59, 62 | Green/Yellow | Green for abstract-level claim and chapter location; Yellow for detailed internal Pearl passages until full access. Preserve the "singly connected" qualifier. |
| Bayesian networks helped AI move away from brittle certainty factors toward probabilistically coherent uncertainty handling. | Rules Meet Uncertainty | Lauritzen/Spiegelhalter 1988 pp.157-160; Pearl 1988 description | Charniak 1991 pp.50-52 | Green | Lauritzen/Spiegelhalter directly contrast exact probabilistic manipulation with MYCIN certainty factors and other informal schemes. |
| Exact inference in general Bayesian networks can be computationally hard. | The Cost Returns | Cooper 1990 pp.393-403 | Charniak 1991 pp.59, 62 | Green | Do not overgeneralize from singly connected networks to all networks; Cooper's limit is the reason special-case/approximation algorithms matter. |
| Bayesian networks later became a bridge to causal reasoning, but causal calculus is not the main 1980s story. | Legacy Bridge | Pearl 1988; later Pearl sources if used | Later survey/source to find | Yellow | Keep this as forward pointer unless Chapter 26 scope expands. |

## Conflict Notes

- Do not conflate Bayesian networks with neural networks. The shared word "network" is graph structure, not weighted differentiable layers.
- Do not imply inference is always efficient. Pearl 1986's local propagation result has structural assumptions.
- Do not make causal do-calculus the center of this chapter unless the book plan explicitly moves causal reasoning into Part 5.
- Do not treat probability tables as magically easier than rules; expert elicitation and model maintenance remain infrastructure costs.

## Page Anchor Worklist

- Pearl 1986: Abstract-level anchors extracted from p.241; full-article library access still needed for detailed non-abstract passages.
- Pearl 1988: Chapter/page anchors extracted from ScienceDirect table of contents and book description; exact internal passages still need access.
- Lauritzen/Spiegelhalter 1988: Done for expert-system uncertainty contrast, local computations, MUNIN/EMG, causal networks, and conditional probability tables on pp.157-160.
- Cooper 1990: Done for NP-hard abstract, definitions, 3SAT/PIBNET construction, and discussion on pp.393-403.
- Charniak 1991: Done for tutorial definition, probability-table reduction, applications, software packages, and evaluation-time caveat on pp.50-52, 59, and 62.
