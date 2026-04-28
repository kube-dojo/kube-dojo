# Brief: Chapter 63 - Inference Economics

## Thesis

The product era changed the economics of AI. Training a frontier model was still
expensive, but the daily business problem became serving: every prompt, token,
image, and tool call consumed accelerator time, memory bandwidth, scheduler
attention, and latency budget. This chapter should explain why inference became
an industrial discipline: the hard part was not merely "run the model," but run
many autoregressive requests cheaply enough, fast enough, and reliably enough
for a product.

## Boundary Contract

- IN SCOPE: autoregressive serving loop; batching and latency trade-offs; KV
  cache memory; FlashAttention as memory-hierarchy awareness; Orca and
  iteration-level scheduling; vLLM/PagedAttention; quantization and offload as
  cost levers; speculative decoding/sampling; prefill/decode separation and
  goodput/SLO framing.
- OUT OF SCOPE: training-scale physics (Ch61), multimodal UX/product category
  shifts except as handoff from Ch62, benchmark politics (Ch66), open-weights
  governance (Ch65), data labor/copyright (Ch68), energy-grid siting and power
  procurement (Ch70), chip geopolitics/export controls (Ch71), and detailed
  datacenter construction strategy (Ch72).
- Transition from Ch62: multimodal products raised latency and media payload
  expectations; Ch63 explains the serving machinery underneath the product.
- Transition to Ch64/70/72: inference economics exposes why edge deployment,
  power, memory bandwidth, and datacenter topology become separate constraints.

## Required Scenes

1. **The Meter Starts Running:** Product AI turns inference into a repeated
   cost, not a one-time training bill. Every generated token is a serial step.
2. **Batching Meets Autoregression:** Orca shows why ordinary request-level
   batching wastes latency for generation workloads and why iteration-level
   scheduling matters.
3. **The Memory Wall Moves Into Serving:** FlashAttention and vLLM show that
   memory access, not just FLOPs, governs the economics of long-context serving.
4. **The KV Cache Becomes The Bill:** PagedAttention makes the serving problem
   concrete: model weights are static, but per-request KV cache grows, fragments,
   and limits batch size.
5. **Compression, Offload, And Speculation:** SmoothQuant, FlexGen, and
   speculative decoding/sampling show three families of cost reduction:
   smaller arithmetic, more memory tiers, and fewer expensive target-model
   decoding passes.
6. **Prefill And Decode Split Apart:** DistServe turns inference into a
   two-phase SLO problem: time to first token and time per output token pull on
   different resource knobs.
7. **Economics Becomes Architecture:** Close by showing why product AI labs had
   to become serving-system operators, not only model trainers.

## Prose Capacity Plan

Target range: 3,400-4,500 words.

- 400-550 words: bridge from multimodal/product interfaces to repeated
  per-token serving cost; define TTFT, TPOT, throughput, latency, and goodput.
- 500-650 words: autoregressive generation and Orca's scheduling critique:
  request-level batching, iteration-level scheduling, selective batching.
- 600-750 words: memory hierarchy and attention IO using FlashAttention; explain
  why "faster math" is not enough when HBM/SRAM movement dominates.
- 650-800 words: KV cache as the central serving object; vLLM/PagedAttention,
  fragmentation, continuous batching, and throughput improvement.
- 500-700 words: cost levers: SmoothQuant, FlexGen, speculative
  decoding/sampling. Keep this comparative, not a catalog.
- 550-700 words: DistServe and prefill/decode separation: TTFT vs TPOT, phase
  interference, per-GPU goodput, and SLO-driven resource allocation.
- 200-350 words: close on architecture consequences and handoff to Ch64/70/72.

## Guardrails

- Do not use unsourced rumors about ChatGPT per-day operating cost.
- Do not quote current API prices as stable historical facts unless a dated
  source is added and the prose clearly labels the date.
- Do not turn the chapter into a benchmark leaderboard; Ch66 owns benchmark
  politics.
- Do not claim one serving trick "solved" inference economics. The source spine
  shows trade-offs among latency, throughput, memory, and quality.
- Do not overstate speculative decoding as universally free: draft acceptance,
  batch size, and decoding method affect speedups.
- Do not let energy-grid or datacenter siting overwhelm this chapter. Those are
  Ch70 and Ch72.
