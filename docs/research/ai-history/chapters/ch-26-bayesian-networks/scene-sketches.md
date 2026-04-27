# Scene Sketches: Chapter 26 - Bayesian Networks

## Scene 1: Rules Meet Uncertainty

Open from the maintenance problem of rule-based systems: expert rules often sounded crisp, but real evidence arrived incomplete, noisy, and sometimes contradictory. The scene should not mock expert systems. It should show why uncertainty demanded a first-class representation.

Evidence anchors:
- Lauritzen/Spiegelhalter 1988 pp.157-158 for expert systems, uncertainty, MYCIN certainty factors, PROSPECTOR, CASNET, INTERNIST, and exact probabilistic alternatives.
- Pearl 1988 ScienceDirect description for probability as a language for partial belief and as a unifying view of AI uncertainty approaches.

## Scene 2: The Graph as a Memory Aid

Introduce a small medical or diagnostic-style network only as an explanatory device: symptoms, disease, test result. The point is not the example itself, but how the graph encodes direct dependence and conditional independence assumptions.

Evidence anchors:
- Pearl 1986 p.241 abstract for belief networks as DAGs with proposition/variable nodes, arcs as direct dependencies, and conditional probabilities as dependency strengths.
- Charniak 1991 pp.51-52 for a narrative definition, neighboring probabilities, conditional probability tables, and evidence updates.
- Avoid invented historical deployment unless sourced.

## Scene 3: Propagation Instead of Global Recalculation

Show how evidence at one node changes beliefs elsewhere through local message passing in appropriate network structures. This is the infrastructure moment: the graph is not only a diagram but a route for computation.

Evidence anchors:
- Pearl 1986 p.241 abstract for local propagation in singly connected networks and data-flow through links.
- Pearl 1988 Chapter 4 pp.143-237 for book-level location of belief updating by network propagation.
- Keep "singly connected" visible.

## Scene 4: The Cost Returns

End with the caveat: once networks become dense or multiply connected, exact inference can become expensive. Bayesian networks survive because they organize uncertainty, not because they make uncertainty free.

Evidence anchors:
- Cooper 1990 pp.393-403 for NP-hardness, singly versus multiply connected networks, efficient restricted cases, and special-case/average-case/approximation algorithms.
- Charniak 1991 pp.59 and 62 for an accessible evaluation-time caveat and application/software context.
