# Brief: Chapter 26 - Bayesian Networks

## Thesis

Bayesian networks gave AI a disciplined way to reason under uncertainty without pretending that expert rules were certain. Their historical importance is not just "Bayes' theorem in software." Pearl and related researchers turned probabilistic dependence into a graph structure that could store expert knowledge, direct local computation, and make uncertain evidence composable. The chapter should frame Bayesian networks as an infrastructure bridge between symbolic AI, probability theory, and later statistical machine learning.

## Scope

- IN SCOPE: belief/Bayesian networks as directed acyclic graphical models; Pearl's 1986 belief-network propagation paper; Pearl's 1988 *Probabilistic Reasoning in Intelligent Systems*; local propagation in singly connected networks; expert-system uncertainty limits; early tutorial/secondary sources such as Charniak 1991.
- OUT OF SCOPE: full causal calculus and do-calculus (later Pearl, mostly 1990s-2000s); modern probabilistic programming; deep generative models; textbook derivations of d-separation beyond narrative necessity.

## Boundary Contract

This chapter must not treat Bayesian networks as simply "neural networks with probabilities" or as a solved route to general intelligence. They are graphical probability models: nodes represent variables/propositions, arcs encode direct dependencies, and conditional probability tables quantify those dependencies. The historical claim is that they made uncertainty computationally structured, not that they eliminated the cost of probabilistic inference.

## Scenes Outline

1. **Rules Meet Uncertainty:** Expert systems needed ways to combine partial evidence, but ad hoc certainty factors and brittle rules made uncertainty hard to maintain.
2. **The Graph as a Memory Aid:** A directed acyclic graph lets experts and machines agree on which variables directly depend on which others.
3. **Propagation Instead of Global Recalculation:** Pearl's belief-network work shows how evidence can move locally through certain network structures, turning probability into an executable architecture.
4. **The Cost Returns:** Exact inference becomes hard in general networks, so Bayesian networks are both a conceptual breakthrough and an infrastructure bargain with computational limits.

## 4k-7k Prose Capacity Plan

This chapter can support a substantial narrative if it avoids becoming a statistics lecture:

- 700-1,000 words: expert-system uncertainty problem, tied back to Ch19-Ch23.
- 800-1,100 words: plain-language explanation of a Bayesian network: variables, arrows, conditional probability tables, and evidence updates.
- 900-1,300 words: Pearl's 1986/1988 contribution, including belief propagation/local computation and the shift from isolated rules to structured probabilistic reasoning.
- 600-900 words: comparison with rule-based expert systems and why graphs helped knowledge engineering without removing elicitation work.
- 600-900 words: computational limits, including why exact inference can become expensive and why algorithms/approximations matter.
- 400-800 words: legacy bridge to probabilistic graphical models, causal reasoning, and later ML, with causal material kept as forward pointer rather than main story.

With the current anchors, a 3,500-4,500 word draft is plausible without padding. A 5,000+ word draft should wait for full Pearl 1986/1988 access or a stronger early-application/terminology source.

## Citation Bar

- Minimum primary sources before review: Pearl 1986, Pearl 1988, Lauritzen and Spiegelhalter 1988 or equivalent graphical-model inference source, Cooper 1990 for complexity limits.
- Minimum secondary sources before review: Charniak 1991 tutorial and one later survey/tutorial that distinguishes Bayesian networks from causal networks and probabilistic programming.
- Current status: Cooper 1990, Lauritzen/Spiegelhalter 1988, and Charniak 1991 have page anchors. Pearl 1986 is only abstract-level anchored from ScienceDirect p.241 because the full article is closed access; Pearl 1988 has chapter ranges and publisher-description anchors but not internal passages.
