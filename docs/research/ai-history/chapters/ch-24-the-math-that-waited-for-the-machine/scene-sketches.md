# Scene Sketches: Chapter 24 - The Math That Waited for the Machine

## Scene 1: The Frozen Hidden Layer

- **Setting:** The connectionist aftermath of the perceptron critique.
- **Beat:** A single-layer perceptron can be corrected when the output is wrong, but a hidden unit has no obvious teacher. The chapter should make this tangible: the machine fails, but the blame is distributed through invisible internal connections.
- **Narrative Use:** This scene earns chapter length by making the reader feel the practical bottleneck. The obstacle is not that researchers lacked ambition; it is that every hidden connection becomes a small unsolved accounting problem.
- **Evidence Anchors:** Nature 1986 p.533 for the perceptron-convergence contrast and fixed feature analyzers; PDP 1986 pp.318-320 for the Minsky/Papert bridge and hidden-unit recoding problem.

## Scene 2: The Chain Rule Becomes Machinery

- **Setting:** A network as a ledger of intermediate numbers.
- **Beat:** Backpropagation is not magic. It is the chain rule turned into a repeatable accounting process: compute activations forward, cache them, compute sensitivities backward, update weights.
- **Pedagogical Demonstration:** Use the PDP/Nature symmetry or encoder examples rather than an invented toy network. Do not include equations unless the prose first explains what each quantity is doing.
- **Narrative Use:** This is the math-teaching core. It should be concrete enough that a non-mathematician can explain why the error travels backward, but honest enough to avoid pretending the biological brain obviously does the same thing.
- **Evidence Anchors:** PDP 1986 pp.326-327 for the generalized delta rule, forward pass, backward pass, and hidden-unit error signal; Werbos pp.II-23-II-26 and II-33-II-34 for earlier backward derivative machinery.

## Scene 3: The PDP Demonstration

- **Setting:** Mid-1980s connectionist research, where cognitive scientists are trying to recover learning from hand-coded symbolic systems.
- **Beat:** The Nature paper's dramatic claim is that hidden units learn internal features. This makes the network more than a curve-fitting shell: it can discover representations useful for a task.
- **Narrative Use:** This is the story's "machine starts to teach itself features" moment. It can carry substantial prose if the examples are drawn directly from the paper rather than invented.
- **Evidence Anchors:** Nature 1986 pp.533-535 for internal representations, symmetry, and family-tree demonstrations; PDP 1986 pp.328-329 and 337-341 for simulation framing, encoder, and symmetry examples.

## Scene 4: The Algorithm Waiting for Machines

- **Setting:** Small simulations, not modern datacenters.
- **Beat:** Backpropagation wins historically because it has the right infrastructural shape. It is a procedure machines can repeat millions of times: multiply, sum, store activations, reuse derivatives, adjust weights.
- **Narrative Use:** Connect this chapter to the book's infrastructure thesis. The 1986 result was not yet the GPU revolution, but it made learning look like the kind of repetitive numerical workload later hardware could industrialize.
- **Evidence Anchors:** Nature/PDP sweep and example details for experiment scale; Griewank 2012 pp.397-398 for later reverse-mode memory/checkpointing context. Exact 1986 hardware remains open.

## Scene 5: The Honest Attribution

- **Setting:** A short narrative pause before the chapter moves toward the next chapter's theorem.
- **Beat:** Say plainly that 1986 was not the birth of the chain rule or even every form of backpropagation. It was the moment a dormant mathematical technique became a persuasive research program for learned representations.
- **Narrative Use:** This scene models the team rule: honesty over output. It also gives the chapter a more mature voice than a standard triumphalist AI-history account.
- **Evidence Anchors:** Werbos pp.II-23-II-26, II-33-II-34, and II-83-II-86; Griewank 2012 pp.389-395 and 397-398. Do not imply direct transmission to PDP unless a source is later found.

## Anti-Padding Rule

If the final prose needs more length, expand the mechanism and verified examples. Do not add fictional lab dialogue, invented emotional states, or unsourced "everyone knew the field had changed" claims.
