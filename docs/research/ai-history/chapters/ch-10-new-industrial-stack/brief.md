# Chapter 10: The New Industrial Stack (K8s, inference economics, regulation)

## Thesis
In the post-ChatGPT era, AI is no longer just computer science; it is heavy industry. The defining constraints of the field have shifted from algorithmic design to data center power envelopes, GPU supply chains, and orchestration software (like Kubernetes) required to manage clusters of unprecedented scale.

## Scope
- IN SCOPE: The economics of inference vs. training, the role of Kubernetes and Ray/vLLM in orchestrating massive GPU clusters, the geopolitical supply chain of TSMC and Nvidia (H100s), and the looming constraints of energy grids and copyright law.
- OUT OF SCOPE: The history of the Transformer (Chapter 8) or the product launch of ChatGPT (Chapter 9).

## Scenes Outline
1. **The Orchestration Layer:** Training a 1-trillion parameter model requires coordinating 20,000 GPUs for months. The failure of a single node can crash the run. The reliance on Kubernetes and advanced fault-tolerance software to make unreliable physical hardware appear as a single, continuous supercomputer.
2. **Inference Economics:** The realization that training is only the first cost. Serving ChatGPT to 100 million users requires a completely new software stack (vLLM, continuous batching) and hardware optimizations to make inference economically viable. Compute becomes a heavily rationed utility.
3. **The Power and the Policy:** The physical limits of the new stack. Tech giants realize that AI scaling laws are on a collision course with the global electrical grid (requiring dedicated nuclear reactors) and global copyright law (the exhaustion of high-quality human data). AI transitions into a macroeconomic and regulatory infrastructure.