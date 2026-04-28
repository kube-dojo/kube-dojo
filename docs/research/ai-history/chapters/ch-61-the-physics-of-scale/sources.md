# Sources: Chapter 61 - The Physics of Scale

## Research Status

Contract is `capacity_plan_anchored` as of 2026-04-28. Sources were verified
from arXiv PDFs and GitHub API metadata via `curl` plus `pdftotext`. Gemini must
still gap-audit the scope and word cap before prose drafting.

## Primary Source Spine

| Source | Use | Verification |
|---|---|---|
| Yanping Huang et al., "GPipe: Easy Scaling with Micro-Batch Pipeline Parallelism," arXiv:1811.06965. PDF: https://arxiv.org/pdf/1811.06965 | Pipeline parallelism, micro-batches, rematerialization, bubble overhead, and 6B-parameter Transformer example. | Green: PDF downloaded 2026-04-28. Abstract/page 1 introduces GPipe as a pipeline-parallel library; Section 2/pages 3-5 defines partitions, micro-batches, synchronous gradient application, rematerialization, and bubble overhead; experiments include 1.8B AmoebaNet and 6B Transformer examples. |
| Mohammad Shoeybi et al., "Megatron-LM: Training Multi-Billion Parameter Language Models Using Model Parallelism," arXiv:1909.08053. PDF: https://arxiv.org/pdf/1909.08053 | Tensor/intra-layer model parallelism for Transformer language models. | Green: PDF downloaded 2026-04-28. Abstract/page 1 says the method is simple intra-layer model parallelism, trainable with a few communication operations, orthogonal to pipeline parallelism, and scales to an 8.3B model on 512 GPUs. Section 3/pages 4-5 describes splitting MLP/self-attention GEMMs and all-reduce placement. |
| Samyam Rajbhandari et al., "ZeRO: Memory Optimizations Toward Training Trillion Parameter Models," arXiv:1910.02054. PDF: https://arxiv.org/pdf/1910.02054 | Optimizer-state, gradient, and parameter partitioning; data-parallel memory redundancy. | Green: PDF downloaded 2026-04-28. Abstract/page 1 defines Zero Redundancy Optimizer and says it eliminates memory redundancies; introduction/pages 2-4 identify optimizer states, gradients, parameters, activation/residual memory, and the three ZeRO-DP stages. |
| DeepSpeed GitHub repository metadata. API: https://api.github.com/repos/deepspeedai/DeepSpeed | Open-source system context for ZeRO/DeepSpeed. | Green/Yellow: GitHub API opened 2026-04-28; repository created 2020-01-23 and describes DeepSpeed as a deep-learning optimization library for distributed training and inference. Use only as project context, not adoption magnitude. |
| Narayanan et al., "Efficient Large-Scale Language Model Training on GPU Clusters Using Megatron-LM," arXiv:2104.04473. PDF: https://arxiv.org/pdf/2104.04473 | PTD-P: composing pipeline, tensor, and data parallelism; trillion-parameter training on 3072 GPUs; network bandwidth constraints. | Green: PDF downloaded 2026-04-28. Abstract/page 1 says tensor, pipeline, and data parallelism can be composed to scale to thousands of GPUs and train a 1T-parameter model at 502 petaFLOP/s on 3072 GPUs. Sections 2-3 describe tensor/pipeline/data dimensions and pipeline bubbles. |
| NVIDIA Megatron-LM GitHub metadata. API: https://api.github.com/repos/NVIDIA/Megatron-LM | Repository context for Megatron-LM code. | Green/Yellow: GitHub API opened 2026-04-28; repository created 2019-03-21 and describes ongoing research training transformer models at scale. Use only as project context, not adoption magnitude. |
| Aakanksha Chowdhery et al., "PaLM: Scaling Language Modeling with Pathways," arXiv:2204.02311. PDF: https://arxiv.org/pdf/2204.02311 | Large-system example: 540B parameters, 6144 TPU v4 chips, model/data parallelism, Pathways, MFU. | Green: PDF downloaded 2026-04-28. Abstract/page 1 states 540B parameters and 6144 TPU v4 chips; Section 4/pages 7-9 describes two TPU v4 Pods, 12-way model parallelism, 256-way fully sharded data parallelism, Pathways, cross-pod gradients, and 46.2% model FLOPs utilization. |
| Jordan Hoffmann et al., "Training Compute-Optimal Large Language Models" (Chinchilla), arXiv:2203.15556. PDF: https://arxiv.org/pdf/2203.15556 | Compute/data allocation correction: scale is not only parameter count. | Green: PDF downloaded 2026-04-28. Abstract/page 1 says current large models were undertrained and model size and token count should scale equally; Chinchilla used the same compute budget as Gopher with 70B parameters and 4x more data. |

## Scene-Level Claim Table

| Claim | Scene | Primary Anchor | Independent Confirmation | Status | Notes |
|---|---|---|---|---|---|
| GPipe partitions a model across accelerators and pipelines micro-batches through the partitions. | The Pipeline | GPipe p.1 abstract; Section 2 | Figure 2 and Section 2 text | Green | Explain pipeline in physical terms. |
| GPipe applies gradients synchronously at the end of a mini-batch, preserving update consistency across partition counts. | The Pipeline | GPipe Section 2 p.3 | Figure 2 | Green | Avoid implying stale/asynchronous updates. |
| GPipe's pipeline bubble is idle time, amortized by more micro-batches. | The Pipeline | GPipe Section 2 p.4 | 2021 Megatron-LM pipeline-bubble discussion | Green | Good teaching metaphor, but keep technical. |
| Megatron-LM 2019 used intra-layer tensor model parallelism and only a few communication operations. | Tensor Split | Megatron 2019 p.1 abstract | Section 3 | Green | Distinguish tensor from pipeline. |
| Megatron-LM 2019 reports training an 8.3B Transformer language model with 8-way model parallelism on 512 GPUs. | Tensor Split | Megatron 2019 p.1/table text | Scaling results | Green | Do not generalize to all clusters. |
| Megatron's Transformer splitting places all-reduce operations around MLP/self-attention matrix products. | Tensor Split | Megatron 2019 Section 3 | Figure 3 text | Green | Needs plain-language prose. |
| ZeRO identifies optimizer states, gradients, and parameters as major replicated model states. | Optimizer Memory Trap | ZeRO pp.1-3 | Figure 1 | Green | Strong memory inventory scene. |
| ZeRO-DP stages partition optimizer states, then gradients, then parameters. | Optimizer Memory Trap | ZeRO p.3 | Figure 1 | Green | Use the 4x/8x/stage-3 concept carefully. |
| ZeRO argues data parallelism is compute/communication efficient but memory inefficient because it replicates model states. | Optimizer Memory Trap | ZeRO pp.2-3 | Introduction | Green | Avoid saying model parallelism became unnecessary in all cases. |
| 2021 Megatron-LM composes pipeline, tensor, and data parallelism as PTD-P. | Three-Dimensional Parallelism | Megatron 2021 p.1 | Sections 2-3 | Green | Central chapter claim. |
| 2021 Megatron-LM reports a 1T-parameter training iteration at 502 petaFLOP/s on 3072 GPUs. | Three-Dimensional Parallelism | Megatron 2021 p.1 | Results text | Green | Phrase as paper report, not universal throughput. |
| 2021 Megatron-LM emphasizes topology: tensor parallelism within high-bandwidth servers, pipeline across servers, data parallelism across model replicas. | Three-Dimensional Parallelism | Megatron 2021 p.1 and Sections 2-3 | Communication discussion | Green | This is the "physics" of the chapter. |
| PaLM trained a 540B dense Transformer on 6144 TPU v4 chips using Pathways. | Scale System | PaLM p.1 abstract | Section 4 | Green | Use as Google TPU-side comparison. |
| PaLM Section 4 describes two TPU v4 Pods, 12-way model parallelism, and 256-way fully sharded data parallelism. | Scale System | PaLM Section 4 pp.7-9 | Figure 2 | Green | Do not drift into product benchmark claims. |
| PaLM reports 46.2% model FLOPs utilization for PaLM 540B. | Scale System | PaLM Section 4 p.8 and Training Efficiency p.9 | MFU discussion | Green | Keep MFU explanatory, not leaderboard bait. |
| Chinchilla argues compute-optimal training scales parameters and training tokens together. | Scale Has A Budget | Chinchilla p.1 abstract | Section 3 | Green | Route deeper data-limit discussion to Ch69. |
| Chinchilla trained 70B parameters on 1.4T tokens with the same compute budget as Gopher. | Scale Has A Budget | Chinchilla p.1 abstract / p.2 introduction | Table 1 | Green | Do not overdo benchmark results. |
| GitHub repository metadata supports Megatron-LM and DeepSpeed project context but not historical adoption magnitude. | Context | GitHub APIs | N/A | Yellow | Do not use current stars as 2019/2020 evidence. |

## Conflict Notes

- Do not write "more GPUs equals linear scaling." GPipe, Megatron, and PaLM all
  describe idle time, communication, memory, or topology constraints.
- Do not turn training scale into inference economics. Ch63 owns serving cost,
  KV cache, batching, PagedAttention, vLLM, and production latency.
- Do not turn Chinchilla into data-exhaustion coverage. Ch69 owns data limits.
- Do not import chip export controls or energy-grid arguments; those are Ch71
  and Ch70 respectively.

## Anchor Worklist For Prose

- Use GPipe Section 2 for the pipeline/micro-batch/bubble explanation.
- Use Megatron 2019 Section 3 for tensor parallelism and all-reduce placement.
- Use ZeRO pp.1-4 for memory-state inventory and stage explanations.
- Use Megatron 2021 p.1/Sections 2-3 for PTD-P and topology.
- Use PaLM Section 4 for TPU-scale system details and MFU.
- Use Chinchilla p.1/Section 3 only as the compute-optimal correction.
