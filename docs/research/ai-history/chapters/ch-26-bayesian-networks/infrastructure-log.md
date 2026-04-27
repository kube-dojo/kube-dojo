# Infrastructure Log: Chapter 26 - Bayesian Networks

## Knowledge Representation

- Bayesian networks are knowledge infrastructure: the graph records conditional-dependence assumptions, and probability tables record uncertainty.
- The graph makes maintenance partly visible. If a dependency changes, the model has a place to update; this is different from scattered certainty factors in rule chains.
- This does not remove expert elicitation. Conditional probability tables can become large and hard to fill.
- Charniak 1991 pp.51-52 gives the accessible DAG/probability-table explanation: random-variable nodes, neighboring probabilities, conditional probabilities for nonroot nodes, evidence updates, and reduced probability specification.
- Lauritzen/Spiegelhalter 1988 p.160 shows the same infrastructure burden in MUNIN: every node required conditional probability tables over parent-state combinations.

## Computation

- Pearl 1986 emphasizes local propagation in singly connected networks. That is computationally attractive because evidence can move through the graph rather than requiring a monolithic recalculation.
- Pearl 1986 is currently abstract-level only for this claim; Pearl 1988 Chapter 4 is the book location for "Belief Updating by Network Propagation."
- General networks reintroduce computational difficulty. Cooper 1990 pp.393-403 is the limit-setting source, with a clear distinction between singly connected tractability and general/multiply connected hardness.
- The chapter should avoid a fake binary between "rules are brittle" and "Bayesian networks solve uncertainty." The honest claim is that Bayesian networks structure the problem.

## Data

- Early Bayesian networks were often knowledge-engineered rather than learned from massive datasets.
- Later work on learning Bayesian networks can be a forward pointer, but the main 1980s infrastructure story is representation plus inference, not big-data training.
- Lauritzen/Spiegelhalter 1988 pp.157-160 and Charniak 1991 p.59 provide early medical expert-system/application context through MUNIN and PATHFINDER; use these as bounded examples, not deployment scenes.

## Interfaces and Operations

- The graph is explainable compared with opaque numeric tables alone: domain experts can inspect nodes and arrows.
- Operational cost remains: choosing variables, deciding dependencies, filling probabilities, and revising the graph as the domain changes.
- Lauritzen/Spiegelhalter 1988 p.157 frames expert systems as separating knowledge base, patient data, and inference engine; that separation can support the chapter's infrastructure framing.

## Claims Not Yet Safe

- "Bayesian networks replaced expert systems" is too broad without deployment evidence.
- "Bayesian networks made AI Bayesian" is rhetorically tempting but historically sloppy.
- "Pearl invented all graphical models" is false/misleading; keep Lauritzen/Spiegelhalter and broader statistical context in view.
