# Infrastructure Log: Chapter 24 - The Math That Waited for the Machine

## Technical Constraint

Multi-layer neural networks had many adjustable weights, but hidden units had no direct target label. The infrastructure problem was therefore not just "more math"; it was a scalable bookkeeping procedure for assigning credit and blame through layers.

## Algorithmic Infrastructure

- **Forward pass:** Store each unit's activation so later derivative calculations can reuse it.
- **Backward pass:** Move error sensitivities from output units back through hidden units using the chain rule.
- **Weight update:** Adjust each connection in proportion to its contribution to output error.
- **Hidden representation:** The useful feature is not hand-coded. It emerges as the network adjusts internal weights.
- PDP 1986 pp.326-327 anchors the forward/backward pass and states that the backward pass has the same computational complexity as the forward pass.
- Nature 1986 p.533 and PDP 1986 pp.318-320 anchor the claim that hidden units learn internal representations rather than relying on fixed feature analyzers.

## Compute and Hardware Constraints

- 1986 demonstrations ran on small networks by modern standards. The chapter should not imply ImageNet-era scale.
- Backpropagation converted learning into repeated numerical operations over weights and activations. That shape later mapped naturally to vector processors, CPUs, GPUs, and accelerators, but the 1986 systems were still constrained by memory, processor speed, and experiment turnaround.
- The bottleneck shifted: once hidden-layer training became executable, the limiting factors became data volume, initialization, local minima/plateaus, conditioning, and available compute.
- Griewank 2012 pp.397-398 anchors the later reverse-mode memory/checkpointing issue and cheap-gradient principle; use this as AD-history context, not as a claim about the exact 1986 lab machine.

## Metrics to Verify Before Prose

- Hardware or computing environment used for the reported experiments.
- Runtime or training-iteration counts beyond the reported sweep/presentation counts.
- Whether any 1985 technical report contains details omitted from the Nature letter.
