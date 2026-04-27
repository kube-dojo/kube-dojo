# Scene Sketches: Chapter 29 - Support Vector Machines

## Scene 1: After the Winter, Trust Moved to Generalization

Open from Ch28: after brittle expert systems and demo-driven promises, the field needed learning methods that could explain why they would work on new data. SVMs offered a mathematical contract around generalization and capacity rather than a hand-built knowledge base.

Evidence anchors:
- Boser et al. 1992 p.1.
- Cortes/Vapnik 1995 pp.273-276.

## Scene 2: The Margin as Contract

Explain the geometry visually: if many hyperplanes separate the data, choose the one with the widest margin. The boundary is determined by the closest points, the support vectors. This is the clean narrative core.

Evidence anchors:
- Cortes/Vapnik 1995 pp.275-279.
- Burges 1998 pp.9-13.

## Scene 3: The Kernel Move

The kernel story should be practical, not mystical. The problem: useful nonlinear separators may live in enormous feature spaces. The trick: compute pairwise similarities as if operating in that space, without explicitly constructing it. Tie this to polynomial and RBF decision surfaces.

Evidence anchors:
- Boser et al. 1992 pp.2-4.
- Cortes/Vapnik 1995 pp.276, 283.
- Burges 1998 pp.20-23.

## Scene 4: Soft Margins and Real Data

Real data are not perfectly separable. Cortes/Vapnik's soft-margin extension is the practical hinge: tolerate errors/deviations while maximizing margin, and solve a convex/quadratic optimization problem.

Evidence anchors:
- Cortes/Vapnik 1995 pp.279-283.
- Burges 1998 pp.13-15.

## Scene 5: OCR as Proof Terrain

USPS and NIST digit recognition connect Ch29 to Ch27. SVMs were tested on the same kind of visible benchmark terrain where LeNet mattered. Keep datasets distinct from MNIST. Use Cortes/Vapnik's 1.1% NIST result carefully.

Evidence anchors:
- Cortes/Vapnik 1995 pp.287-289.

## Scene 6: Why SVMs Mattered Historically

Close with the infrastructure lesson: SVMs packaged theory, optimization, sparse representation, and benchmark measurement into a method that looked reliable in the 1990s. Then hand off to Ch30 statistical speech and Ch31 RL roots.

Evidence anchors:
- Burges 1998 pp.34-42 for implementation and generalization context.
