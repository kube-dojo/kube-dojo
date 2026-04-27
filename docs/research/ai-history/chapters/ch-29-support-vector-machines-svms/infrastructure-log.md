# Infrastructure Log: Chapter 29 - Support Vector Machines

## Mathematical Infrastructure

- Statistical learning theory gave the method a language of capacity, risk, and generalization. Use carefully unless stronger VC page anchors are added.
- The maximum-margin principle turned generalization into geometry.

## Optimization Infrastructure

- SVM training reduced the learning problem to convex/quadratic programming. This was a credibility advantage after neural-network local-minimum concerns.
- The support-vector representation made the solution sparse in the sense that only support vectors determine the decision surface.

## Kernel Infrastructure

- Kernels allowed nonlinear decision surfaces in high-dimensional spaces without explicitly constructing the feature space.
- This is the chapter's infrastructure equivalent of Ch27's convolutional prior: the method embeds useful assumptions into the computational form of learning.

## Benchmark Infrastructure

- USPS/NIST digit recognition provided visible, comparable terrain. This connects Ch29 to Ch27 without claiming SVMs replaced LeNet.
- Keep NIST in Cortes/Vapnik separate from later MNIST standardization.

## Prose Guardrail

SVMs should read as the 1990s answer to trust: a method with theory, optimization, and benchmarks. They were not the final architecture of AI, and they should not be written as a simple winner over neural networks.
