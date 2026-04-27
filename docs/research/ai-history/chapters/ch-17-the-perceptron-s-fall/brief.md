# Brief: Chapter 17 - The Perceptron's Fall

## Thesis

The fall of the perceptron was not a simple story in which one XOR proof killed
neural networks. It was a collision between three things: Rosenblatt's
legitimate connectionist ambition, the physical limits of early perceptron
hardware, and Minsky/Papert's mathematical argument that a broad class of
single-layer/local perceptrons could not efficiently compute important
predicates such as parity and connectedness. The winter effect came from how
that technical critique was interpreted inside an AI funding and authority
structure increasingly organized around symbolic AI.

## Scope

This chapter should bridge Part 3's early optimism and Part 4's first winter.
It should begin with the real Mark I perceptron: a publicly demonstrated,
ONR/RADC-backed research device that learned simple pattern-recognition tasks
with electromechanical hardware. It should then explain Rosenblatt's larger
brain-model program, Minsky and Papert's restricted mathematical object, and
the later historical debate over whether the book caused or merely rationalized
the decline of neural-network work inside AI.

## Boundary Contract

- Do not say Minsky and Papert proved multilayer neural networks were
  impossible. Olazaran is explicit that the strict proof concerned single-layer
  nets defined in a particular way, while multilayer pessimism was a conjecture
  about learning.
- Do not reduce the critique to XOR alone. Parity is related to XOR, but
  Minsky/Papert's more historically important geometric examples include
  connectedness and locality/order restrictions.
- Do not say neural-network research was completely abandoned. Olazaran and
  Bottou both support a more precise claim: perceptron-style learning became
  unfashionable inside AI and funding was scarce, while some researchers moved
  ideas into signal processing, neuroscience, psychology, and later revived
  neural networks.
- Do not make Rosenblatt a naive hype figure. The ONR newsletter and Rosenblatt
  1958 both present a research program with real caveats, hardware details, and
  brain-model ambitions.
- Do not make Minsky and Papert villains. Their own introduction says they were
  not opposed to learning machines; the critique was about the need for prior
  structure and mathematical theory.

## Narrative Spine

1. **The Machine That Learned Letters:** Mark I as a real electromechanical
   demonstration with public promise and explicit research-device limits.
2. **Rosenblatt's Connectionist Bet:** information stored in associations,
   not symbolic image lookup; perception as a probabilistic/statistical system.
3. **The Mathematical Turn:** Minsky/Papert define perceptrons as linear
   predicates over partial predicates and show why locality/order restrictions
   matter.
4. **Parity, Connectedness, and Scale:** the central failure is not one toy XOR
   example, but the parity theorem and connectedness predicates whose required
   order grows with the retina. XOR belongs only as later shorthand for the
   parity issue.
5. **From Theorem to Winter:** the technical result became a social/funding
   argument during symbolic AI's institutional rise.
6. **The Door Left Open:** the chapter should close by distinguishing a killed
   fashion from a solved scientific question, setting up the later backprop and
   mathematical-resurrection chapters.

## Prose Capacity Plan

Word Count Discipline label: `3k-5k likely`

Core range: 4,000-4,700 words supported by current verified anchors.
Stretch range: 4,700-5,700 words if an additional primary reception/funding
anchor is added beyond Olazaran and Bottou. Without that primary
institutional layer, prose should cap near 4,000-4,500 words.

- 650-850 words: Mark I public demonstration and hardware limits, anchored by
  ONR Digital Computer Newsletter July 1960 pp.1-3 and Scene 1. Stay near the
  lower bound until Ch14's perceptron-origin contract is final.
- 600-750 words: Rosenblatt's connectionist theory and memory-as-association
  framing, anchored by Rosenblatt 1958 pp.386-389 and Scene 2. Avoid retelling
  the full origin story that belongs in Ch14.
- 750-950 words: Minsky/Papert's definition of perceptrons, locality/order
  restrictions, and connectedness theorem, anchored by Perceptrons intro
  pp.7-8, 12-14 and Scene 3.
- 650-850 words: scaling/prior-structure critique, anchored by Perceptrons
  intro pp.16-20 and Scene 4.
- 500-700 words: Rosenblatt's own three-layer/minimal-perceptron limits and
  multilayer/cross-coupled hopes, anchored by Rosenblatt 1961 pp.303-308,
  575-576 and Scenes 2-4.
- 550-750 words: interpretive/funding closure, anchored by Bottou 2017
  foreword pp.vii-viii and Olazaran 1996 pp.613, 629-631, 637-641 and Scene 5.
- 500-700 words: continuity handoff to symbolic AI, expert systems, and the
  later resurrection, anchored by Olazaran 1996 pp.640-641 and Ch24/Ch25/Ch31
  already-merged Part 5 context.

Honesty close: If the verified evidence runs out, cap the chapter.

Ch14 guardrail: Ch17 may summarize Rosenblatt's positive program only enough to
make the 1969 critique intelligible. The origin, promise, and first perceptron
enthusiasm should remain available for Ch14.
